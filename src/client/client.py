"""
Parallel Agents Client SDK
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
import requests
import websocket
from threading import Thread

from .agent import AgentProxy
from .exceptions import ClientError, AgentNotFoundError, ServerError


class ParallelAgentsClient:
    """Main client for interacting with Parallel Agents server"""
    
    def __init__(self, host: str = "localhost", port: int = 8000, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}/api"
        self.websocket_url = f"ws://{host}:{port}/ws"
        
        # Session management
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # WebSocket connections for log streaming
        self._websocket_connections: Dict[str, websocket.WebSocket] = {}
        self._log_callbacks: Dict[str, List[Callable]] = {}
        
        # Agent proxies
        self._agent_proxies: Dict[str, AgentProxy] = {}
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the server"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    raise ServerError(f"Server error: {error_data.get('detail', str(e))}")
                except json.JSONDecodeError:
                    raise ServerError(f"Server error: {e.response.text}")
            else:
                raise ClientError(f"Connection error: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        return self._make_request("GET", "/health/")
    
    def detailed_health_check(self) -> Dict[str, Any]:
        """Get detailed health information"""
        return self._make_request("GET", "/health/detailed")
    
    def get_config_profiles(self) -> Dict[str, Any]:
        """Get available configuration profiles"""
        return self._make_request("GET", "/config/profiles")
    
    def create_config_from_profile(self, profile_name: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a configuration from a profile"""
        data = {"profile_name": profile_name}
        if overrides:
            data["config_overrides"] = overrides
        
        return self._make_request("POST", f"/config/profiles/{profile_name}", json=overrides or {})
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a configuration"""
        return self._make_request("POST", "/config/validate", json={"config": config})
    
    def start_agent(self, agent_id: str, config: Dict[str, Any], agent_type: str = "verifier") -> 'AgentProxy':
        """Start a new agent and return a proxy object"""
        request_data = {
            "agent_id": agent_id,
            "config": config,
            "agent_type": agent_type
        }
        
        result = self._make_request("POST", "/agents/start", json=request_data)
        
        if result.get("success"):
            # Create agent proxy
            proxy = AgentProxy(agent_id, self, agent_type)
            self._agent_proxies[agent_id] = proxy
            return proxy
        else:
            raise ClientError(f"Failed to start agent: {result.get('message', 'Unknown error')}")
    
    def stop_agent(self, agent_id: str) -> Dict[str, Any]:
        """Stop an agent"""
        result = self._make_request("POST", f"/agents/stop/{agent_id}")
        
        # Clean up local resources
        if agent_id in self._agent_proxies:
            self._agent_proxies[agent_id]._cleanup()
            del self._agent_proxies[agent_id]
        
        if agent_id in self._websocket_connections:
            try:
                self._websocket_connections[agent_id].close()
            except:
                pass
            del self._websocket_connections[agent_id]
        
        if agent_id in self._log_callbacks:
            del self._log_callbacks[agent_id]
        
        return result
    
    def get_agents(self) -> Dict[str, Any]:
        """Get all agents"""
        return self._make_request("GET", "/agents/")
    
    def get_agent(self, agent_id: str) -> 'AgentProxy':
        """Get an agent proxy object"""
        if agent_id in self._agent_proxies:
            return self._agent_proxies[agent_id]
        
        # Check if agent exists on server
        try:
            result = self._make_request("GET", f"/agents/{agent_id}")
            if result.get("success"):
                # Create proxy for existing agent
                agent_type = result.get("agent_type", "verifier")
                proxy = AgentProxy(agent_id, self, agent_type)
                self._agent_proxies[agent_id] = proxy
                return proxy
            else:
                raise AgentNotFoundError(f"Agent {agent_id} not found")
        except ServerError as e:
            if "404" in str(e):
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            else:
                raise
    
    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """Get information about an agent"""
        return self._make_request("GET", f"/agents/{agent_id}")
    
    def process_files(self, agent_id: str, file_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process file changes with an agent"""
        return self._make_request("POST", f"/agents/{agent_id}/process-files", json={"changes": file_changes})
    
    def get_working_set_changes(self, working_set_dir: str = "tests/working_set") -> Dict[str, Any]:
        """Get working set changes"""
        return self._make_request("GET", f"/working-set/changes?working_set_dir={working_set_dir}")
    
    def get_working_set_files(self, working_set_dir: str = "tests/working_set") -> Dict[str, Any]:
        """Get working set files"""
        return self._make_request("GET", f"/working-set/files?working_set_dir={working_set_dir}")
    
    def cleanup_working_set(self, working_set_dir: str = "tests/working_set") -> Dict[str, Any]:
        """Clean up working set"""
        return self._make_request("POST", f"/working-set/cleanup?working_set_dir={working_set_dir}")
    
    def subscribe_to_agent_logs(self, agent_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to an agent's log stream"""
        if agent_id not in self._log_callbacks:
            self._log_callbacks[agent_id] = []
        
        self._log_callbacks[agent_id].append(callback)
        
        # Start WebSocket connection if not already running
        if agent_id not in self._websocket_connections:
            self._start_websocket_connection(agent_id)
    
    def unsubscribe_from_agent_logs(self, agent_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from an agent's log stream"""
        if agent_id in self._log_callbacks and callback in self._log_callbacks[agent_id]:
            self._log_callbacks[agent_id].remove(callback)
            
            # Close WebSocket connection if no more callbacks
            if not self._log_callbacks[agent_id]:
                del self._log_callbacks[agent_id]
                if agent_id in self._websocket_connections:
                    try:
                        self._websocket_connections[agent_id].close()
                    except:
                        pass
                    del self._websocket_connections[agent_id]
    
    def _start_websocket_connection(self, agent_id: str) -> None:
        """Start a WebSocket connection for log streaming"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("type") == "log" and data.get("agent_id") == agent_id:
                    log_data = data.get("data", {})
                    
                    # Call all callbacks for this agent
                    for callback in self._log_callbacks.get(agent_id, []):
                        try:
                            callback(log_data)
                        except Exception as e:
                            logging.error(f"Error in log callback: {e}")
                            
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON in WebSocket message: {message}")
            except Exception as e:
                logging.error(f"Error processing WebSocket message: {e}")
        
        def on_error(ws, error):
            logging.error(f"WebSocket error for agent {agent_id}: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logging.info(f"WebSocket connection closed for agent {agent_id}")
            if agent_id in self._websocket_connections:
                del self._websocket_connections[agent_id]
        
        def on_open(ws):
            logging.info(f"WebSocket connection opened for agent {agent_id}")
        
        # Create WebSocket connection
        ws_url = f"{self.websocket_url}/logs/{agent_id}"
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        self._websocket_connections[agent_id] = ws
        
        # Start WebSocket in a separate thread
        def run_websocket():
            ws.run_forever()
        
        thread = Thread(target=run_websocket, daemon=True)
        thread.start()
    
    def cleanup(self) -> None:
        """Clean up all resources"""
        # Close all WebSocket connections
        for ws in self._websocket_connections.values():
            try:
                ws.close()
            except:
                pass
        
        self._websocket_connections.clear()
        self._log_callbacks.clear()
        
        # Clean up agent proxies
        for proxy in self._agent_proxies.values():
            proxy._cleanup()
        
        self._agent_proxies.clear()
        
        # Close session
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup() 