"""
Agent management API routes
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from core.config.models import VerifierConfig
from server.app import get_server, ParallelAgentsServer


router = APIRouter()


class StartAgentRequest(BaseModel):
    """Request model for starting an agent"""
    agent_id: str
    config: Dict[str, Any]
    agent_type: str = "verifier"


class AgentResponse(BaseModel):
    """Response model for agent operations"""
    agent_id: str
    status: str
    agent_type: str
    config: Dict[str, Any]


@router.post("/start", response_model=Dict[str, Any])
async def start_agent(request: StartAgentRequest, server: ParallelAgentsServer = Depends(get_server)):
    """Start a new agent session"""
    try:
        # Parse config
        config = VerifierConfig(**request.config)
        
        # Start agent session
        session = await server.start_agent_session(request.agent_id, config, request.agent_type)
        
        return {
            "success": True,
            "message": f"Agent {request.agent_id} started successfully",
            "agent_id": request.agent_id,
            "agent_type": request.agent_type,
            "status": "running"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop/{agent_id}", response_model=Dict[str, Any])
async def stop_agent(agent_id: str, server: ParallelAgentsServer = Depends(get_server)):
    """Stop an agent session"""
    try:
        await server.stop_agent_session(agent_id)
        
        return {
            "success": True,
            "message": f"Agent {agent_id} stopped successfully",
            "agent_id": agent_id,
            "status": "stopped"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=Dict[str, Any])
async def get_agents(server: ParallelAgentsServer = Depends(get_server)):
    """Get all active agent sessions"""
    try:
        sessions = server.get_all_sessions()
        
        agents = {}
        for agent_id, session in sessions.items():
            agents[agent_id] = {
                "agent_id": agent_id,
                "agent_type": session.agent_type,
                "status": "running" if session.running else "stopped",
                "config": session.config.model_dump()
            }
        
        return {
            "success": True,
            "agents": agents,
            "total": len(agents),
            "running": sum(1 for s in sessions.values() if s.running)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=Dict[str, Any])
async def get_agent(agent_id: str, server: ParallelAgentsServer = Depends(get_server)):
    """Get information about a specific agent"""
    try:
        session = await server.get_agent_session(agent_id)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_type": session.agent_type,
            "status": "running" if session.running else "stopped",
            "config": session.config.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/process-files", response_model=Dict[str, Any])
async def process_files(
    agent_id: str,
    file_changes: Dict[str, Any],
    server: ParallelAgentsServer = Depends(get_server)
):
    """Process file changes with an agent"""
    try:
        session = await server.get_agent_session(agent_id)
        
        if not session.running:
            raise HTTPException(status_code=400, detail="Agent is not running")
        
        # Process file changes
        await session.agent.process_file_changes(file_changes.get("changes", []))
        
        return {
            "success": True,
            "message": f"File changes processed by agent {agent_id}",
            "agent_id": agent_id,
            "processed_files": len(file_changes.get("changes", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 