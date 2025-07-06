"""
FastAPI server for Parallel Agents
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config.models import VerifierConfig
from core.agents.factory import create_agent
from core.overseer.overseer import Overseer
from core.overseer.mock_overseer import MockOverseer


class ServerConfig(BaseModel):
    """Server configuration"""
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"


class AgentSession:
    """Represents an active agent session"""
    
    def __init__(self, agent_id: str, config: VerifierConfig, agent_type: str = "verifier"):
        self.agent_id = agent_id
        self.config = config
        self.agent_type = agent_type
        self.agent = None
        self.overseer = None
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.log_subscribers: Dict[str, asyncio.Queue] = {}
        self.running = False
        
    async def start(self):
        """Start the agent session"""
        if self.running:
            return
            
        try:
            # Create agent
            self.agent = create_agent(self.config, self.agent_type)
            
            # Create overseer (mock for now)
            self.overseer = MockOverseer(self.config)
            
            # Start session
            await self.agent.start_session()
            self.running = True
            
            # Start log monitoring
            asyncio.create_task(self._monitor_logs())
            
        except Exception as e:
            logging.error(f"Failed to start agent session {self.agent_id}: {e}")
            raise
    
    async def stop(self):
        """Stop the agent session"""
        if not self.running:
            return
            
        try:
            if self.agent:
                await self.agent.stop_session()
            
            if self.overseer:
                await self.overseer.stop()
                
            self.running = False
            
            # Close WebSocket connections
            for connection in self.websocket_connections.values():
                try:
                    await connection.close()
                except:
                    pass
                    
        except Exception as e:
            logging.error(f"Failed to stop agent session {self.agent_id}: {e}")
    
    async def _monitor_logs(self):
        """Monitor logs and broadcast to subscribers"""
        log_file = Path(self.config.goose_log_file if self.config.code_tool == "goose" else self.config.claude_log_file)
        
        if not log_file.exists():
            return
            
        try:
            # Read existing log entries
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Monitor for new entries
            while self.running:
                try:
                    with open(log_file, 'r') as f:
                        new_lines = f.readlines()
                        
                    if len(new_lines) > len(lines):
                        # Process new log entries
                        for line in new_lines[len(lines):]:
                            if line.strip():
                                await self._broadcast_log_entry(line.strip())
                        
                        lines = new_lines
                        
                except Exception as e:
                    logging.error(f"Error monitoring logs: {e}")
                
                await asyncio.sleep(1)  # Check every second
                
        except Exception as e:
            logging.error(f"Error in log monitoring: {e}")
    
    async def _broadcast_log_entry(self, log_entry: str):
        """Broadcast a log entry to all subscribers"""
        try:
            # Parse log entry
            log_data = json.loads(log_entry)
            
            # Broadcast to WebSocket connections
            for connection in list(self.websocket_connections.values()):
                try:
                    await connection.send_json({
                        "type": "log",
                        "agent_id": self.agent_id,
                        "data": log_data
                    })
                except:
                    # Remove failed connections
                    pass
                    
            # Add to subscriber queues
            for queue in self.log_subscribers.values():
                try:
                    await queue.put(log_data)
                except:
                    pass
                    
        except json.JSONDecodeError:
            # Handle non-JSON log entries
            log_data = {
                "timestamp": "",
                "message": log_entry,
                "level": "info"
            }
            
            for connection in list(self.websocket_connections.values()):
                try:
                    await connection.send_json({
                        "type": "log",
                        "agent_id": self.agent_id,
                        "data": log_data
                    })
                except:
                    pass
    
    def add_websocket_connection(self, connection_id: str, websocket: WebSocket):
        """Add a WebSocket connection for log streaming"""
        self.websocket_connections[connection_id] = websocket
    
    def remove_websocket_connection(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.websocket_connections:
            del self.websocket_connections[connection_id]
    
    def add_log_subscriber(self, subscriber_id: str) -> asyncio.Queue:
        """Add a log subscriber and return the queue"""
        queue = asyncio.Queue()
        self.log_subscribers[subscriber_id] = queue
        return queue
    
    def remove_log_subscriber(self, subscriber_id: str):
        """Remove a log subscriber"""
        if subscriber_id in self.log_subscribers:
            del self.log_subscribers[subscriber_id]


class ParallelAgentsServer:
    """Main server class for Parallel Agents"""
    
    def __init__(self, config: ServerConfig = None):
        self.config = config or ServerConfig()
        self.app = FastAPI(title="Parallel Agents API", version="1.0.0")
        self.sessions: Dict[str, AgentSession] = {}
        self.setup_middleware()
        self.setup_routes()
        
    def setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        from .routes import agents, config, health, working_set
        
        # Include route modules
        self.app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
        self.app.include_router(config.router, prefix="/api/config", tags=["config"])
        self.app.include_router(health.router, prefix="/api/health", tags=["health"])
        self.app.include_router(working_set.router, prefix="/api/working-set", tags=["working-set"])
        
        # WebSocket endpoint for log streaming
        @self.app.websocket("/ws/logs/{agent_id}")
        async def websocket_logs(websocket: WebSocket, agent_id: str):
            await websocket.accept()
            
            session = self.sessions.get(agent_id)
            if not session:
                await websocket.close(code=4004, reason="Agent not found")
                return
            
            connection_id = f"{agent_id}_{id(websocket)}"
            session.add_websocket_connection(connection_id, websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
                    
            except WebSocketDisconnect:
                session.remove_websocket_connection(connection_id)
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
                session.remove_websocket_connection(connection_id)
    
    async def start_agent_session(self, agent_id: str, config: VerifierConfig, agent_type: str = "verifier") -> AgentSession:
        """Start a new agent session"""
        if agent_id in self.sessions:
            raise HTTPException(status_code=400, detail=f"Agent {agent_id} already exists")
        
        session = AgentSession(agent_id, config, agent_type)
        await session.start()
        self.sessions[agent_id] = session
        
        return session
    
    async def stop_agent_session(self, agent_id: str):
        """Stop an agent session"""
        if agent_id not in self.sessions:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        session = self.sessions[agent_id]
        await session.stop()
        del self.sessions[agent_id]
    
    async def get_agent_session(self, agent_id: str) -> AgentSession:
        """Get an agent session"""
        if agent_id not in self.sessions:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return self.sessions[agent_id]
    
    def get_all_sessions(self) -> Dict[str, AgentSession]:
        """Get all active sessions"""
        return self.sessions
    
    async def cleanup(self):
        """Cleanup all sessions"""
        for session in list(self.sessions.values()):
            await session.stop()
        self.sessions.clear()


# Global server instance
_server_instance: Optional[ParallelAgentsServer] = None


def get_server() -> ParallelAgentsServer:
    """Get the global server instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = ParallelAgentsServer()
    return _server_instance


async def start_server(host: str = "localhost", port: int = 8000, debug: bool = False) -> ParallelAgentsServer:
    """Start the Parallel Agents server"""
    import uvicorn
    
    config = ServerConfig(host=host, port=port, debug=debug)
    server = ParallelAgentsServer(config)
    
    # Store as global instance
    global _server_instance
    _server_instance = server
    
    # Start server
    uvicorn.run(server.app, host=host, port=port, log_level=config.log_level.lower())
    
    return server 


# Module-level exports for testing
server = get_server()
app = server.app
agent_sessions = server.sessions 