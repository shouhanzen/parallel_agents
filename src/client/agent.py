"""
Agent proxy objects for client-side agent interaction
"""

from typing import Dict, Any, Optional, Callable, List, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .client import ParallelAgentsClient

from .exceptions import ClientError


class AgentProxy:
    """Proxy object for interacting with a remote agent"""
    
    def __init__(self, agent_id: str, client: 'ParallelAgentsClient', agent_type: str = "verifier"):
        self.agent_id = agent_id
        self.client = client
        self.agent_type = agent_type
        self._log_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
    @property
    def status(self) -> Dict[str, Any]:
        """Get the current status of the agent"""
        try:
            return self.client.get_agent_info(self.agent_id)
        except Exception as e:
            raise ClientError(f"Failed to get agent status: {str(e)}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the agent's configuration"""
        try:
            info = self.client.get_agent_info(self.agent_id)
            return info.get("config", {})
        except Exception as e:
            raise ClientError(f"Failed to get agent config: {str(e)}")
    
    @property
    def logs(self) -> List[Dict[str, Any]]:
        """Get recent logs for this agent (placeholder - would need server endpoint)"""
        # This would require a server endpoint to get recent logs
        # For now, return empty list
        return []
    
    def process_files(self, file_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process file changes with this agent"""
        try:
            return self.client.process_files(self.agent_id, file_changes)
        except Exception as e:
            raise ClientError(f"Failed to process files: {str(e)}")
    
    def stop(self) -> Dict[str, Any]:
        """Stop this agent"""
        try:
            return self.client.stop_agent(self.agent_id)
        except Exception as e:
            raise ClientError(f"Failed to stop agent: {str(e)}")
    
    def subscribe_to_logs(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to this agent's log stream"""
        self._log_callbacks.append(callback)
        self.client.subscribe_to_agent_logs(self.agent_id, callback)
    
    def unsubscribe_from_logs(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from this agent's log stream"""
        if callback in self._log_callbacks:
            self._log_callbacks.remove(callback)
            self.client.unsubscribe_from_agent_logs(self.agent_id, callback)
    
    def _cleanup(self) -> None:
        """Clean up resources"""
        # Unsubscribe from all log callbacks
        for callback in self._log_callbacks[:]:
            self.unsubscribe_from_logs(callback)
        
        self._log_callbacks.clear()
    
    def __repr__(self) -> str:
        return f"AgentProxy(agent_id='{self.agent_id}', type='{self.agent_type}')"
    
    def __str__(self) -> str:
        return f"Agent {self.agent_id} ({self.agent_type})" 