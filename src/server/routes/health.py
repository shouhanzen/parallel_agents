"""
Health check API routes
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from datetime import datetime

from ..app import get_server, ParallelAgentsServer


router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """Basic health check"""
    return {
        "success": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Parallel Agents API"
    }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(server: ParallelAgentsServer = Depends(get_server)):
    """Detailed health check with system information"""
    try:
        sessions = server.get_all_sessions()
        
        return {
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Parallel Agents API",
            "details": {
                "total_sessions": len(sessions),
                "running_sessions": sum(1 for s in sessions.values() if s.running),
                "stopped_sessions": sum(1 for s in sessions.values() if not s.running),
                "session_ids": list(sessions.keys())
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Parallel Agents API",
            "error": str(e)
        }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(server: ParallelAgentsServer = Depends(get_server)):
    """Check if the service is ready to accept requests"""
    try:
        # Basic readiness checks
        return {
            "success": True,
            "ready": True,
            "timestamp": datetime.now().isoformat(),
            "service": "Parallel Agents API"
        }
        
    except Exception as e:
        return {
            "success": False,
            "ready": False,
            "timestamp": datetime.now().isoformat(),
            "service": "Parallel Agents API",
            "error": str(e)
        } 