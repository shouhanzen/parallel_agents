"""
SDK API Functions - Programmatic replacements for CLI commands
"""

from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
import asyncio
import threading
from datetime import datetime

try:
    from .sdk import ParallelAgentsSDK, create_sdk
    from .config import VerifierConfig
except ImportError:
    from sdk import ParallelAgentsSDK, create_sdk
    from config import VerifierConfig


# Global SDK instance for stateful operations
_global_sdk: Optional[ParallelAgentsSDK] = None


def get_sdk(config_file: str = "verifier.json") -> ParallelAgentsSDK:
    """Get or create the global SDK instance"""
    global _global_sdk
    
    if _global_sdk is None or _global_sdk.config_file != config_file:
        _global_sdk = create_sdk(config_file)
    
    return _global_sdk


# Configuration Management API

def init_config(config_file: str = "verifier.json", overwrite: bool = False) -> Dict[str, Any]:
    """
    Initialize a new configuration file
    
    Args:
        config_file: Path to configuration file
        overwrite: Whether to overwrite existing file
        
    Returns:
        Dictionary with success status and configuration
    """
    try:
        sdk = get_sdk()
        config = sdk.init_config(config_file, overwrite)
        
        return {
            "success": True,
            "config_file": config_file,
            "config": config.model_dump(),
            "message": f"Configuration initialized: {config_file}"
        }
    except FileExistsError:
        return {
            "success": False,
            "error": f"Configuration file {config_file} already exists. Use overwrite=True to replace."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to initialize config: {e}"
        }


def load_config(config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Load configuration from file
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with configuration data
    """
    try:
        sdk = get_sdk(config_file)
        config = sdk.load_config()
        
        return {
            "success": True,
            "config_file": config_file,
            "config": config.model_dump()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load config: {e}"
        }


def validate_config(config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Validate configuration and check prerequisites
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with validation results
    """
    try:
        sdk = get_sdk(config_file)
        result = sdk.validate_config()
        
        return {
            "success": True,
            "config_file": config_file,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to validate config: {e}"
        }


def get_config(config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Get current configuration
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with current configuration
    """
    try:
        sdk = get_sdk(config_file)
        
        if not sdk.config:
            return {
                "success": False,
                "error": "No configuration loaded"
            }
            
        return {
            "success": True,
            "config_file": config_file,
            "config": sdk.config.model_dump()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get config: {e}"
        }


def update_config(updates: Dict[str, Any], config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Update configuration with new values
    
    Args:
        updates: Dictionary of configuration updates
        config_file: Path to configuration file
        
    Returns:
        Dictionary with update results
    """
    try:
        sdk = get_sdk(config_file)
        
        if not sdk.config:
            return {
                "success": False,
                "error": "No configuration loaded"
            }
            
        # Apply updates
        config_dict = sdk.config.model_dump()
        config_dict.update(updates)
        
        # Create new config and save
        new_config = VerifierConfig(**config_dict)
        sdk.config = new_config
        sdk.save_config()
        
        return {
            "success": True,
            "config_file": config_file,
            "updated_fields": list(updates.keys()),
            "config": new_config.model_dump()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update config: {e}"
        }


# Agent Management API

def start_agent(mission: Optional[str] = None, demo_mode: bool = False, 
               agent_id: Optional[str] = None, config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Start a new agent session
    
    Args:
        mission: Agent mission (overrides config default)
        demo_mode: Whether to use demo/mock mode
        agent_id: Custom agent identifier
        config_file: Path to configuration file
        
    Returns:
        Dictionary with agent information
    """
    try:
        sdk = get_sdk(config_file)
        
        # Validate configuration first
        validation = sdk.validate_config()
        if not validation["valid"]:
            return {
                "success": False,
                "error": f"Configuration validation failed: {validation['errors']}"
            }
            
        agent_id = sdk.start_agent(mission, demo_mode, agent_id)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "mission": mission or (sdk.config.agent_mission if sdk.config else "testing"),
            "mode": "demo" if demo_mode else "production",
            "config_file": config_file,
            "message": f"Agent {agent_id} started successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to start agent: {e}"
        }


def stop_agent(agent_id: str, config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Stop a specific agent session
    
    Args:
        agent_id: Agent identifier
        config_file: Path to configuration file
        
    Returns:
        Dictionary with stop results
    """
    try:
        sdk = get_sdk(config_file)
        sdk.stop_agent(agent_id)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent {agent_id} stopped successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to stop agent: {e}"
        }


def stop_all_agents(config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Stop all running agent sessions
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with stop results
    """
    try:
        sdk = get_sdk(config_file)
        agents_before = sdk.get_agents()
        sdk.stop_all_agents()
        
        return {
            "success": True,
            "stopped_agents": list(agents_before.keys()),
            "count": len(agents_before),
            "message": f"Stopped {len(agents_before)} agents"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to stop agents: {e}"
        }


def get_agents(include_stopped: bool = False, config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Get information about all agent sessions
    
    Args:
        include_stopped: Whether to include stopped agents
        config_file: Path to configuration file
        
    Returns:
        Dictionary with agent information
    """
    try:
        sdk = get_sdk(config_file)
        agents = sdk.get_agents(include_stopped)
        
        # Add summary statistics
        running_count = sum(1 for agent in agents.values() if agent["status"] == "running")
        
        return {
            "success": True,
            "agents": agents,
            "total": len(agents),
            "running": running_count,
            "stopped": len(agents) - running_count
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get agents: {e}"
        }


def get_agent_status(agent_id: str, config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Get detailed status for a specific agent
    
    Args:
        agent_id: Agent identifier
        config_file: Path to configuration file
        
    Returns:
        Dictionary with detailed agent status
    """
    try:
        sdk = get_sdk(config_file)
        status = sdk.get_agent_status(agent_id)
        
        return {
            "success": True,
            "agent_id": agent_id,
            **status
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get agent status: {e}"
        }


# File Processing API

def process_file_changes(agent_id: str, file_changes: List[Dict[str, Any]], 
                        config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Manually trigger file change processing for an agent
    
    Args:
        agent_id: Agent identifier
        file_changes: List of file change dictionaries
        config_file: Path to configuration file
        
    Returns:
        Dictionary with processing results
    """
    try:
        sdk = get_sdk(config_file)
        sdk.process_file_changes(agent_id, file_changes)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "changes_processed": len(file_changes),
            "message": f"Processed {len(file_changes)} file changes"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process file changes: {e}"
        }


def get_working_set_changes(config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Get information about changes in the working set
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with working set information
    """
    try:
        sdk = get_sdk(config_file)
        changes = sdk.get_working_set_changes()
        
        return {
            "success": True,
            **changes
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get working set changes: {e}"
        }


def elevate_file(source_path: str, dest_path: Optional[str] = None, 
                preview: bool = False, config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Elevate a file from working set to main codebase
    
    Args:
        source_path: Path to source file in working set
        dest_path: Destination path (auto-determined if None)
        preview: Whether to preview the operation
        config_file: Path to configuration file
        
    Returns:
        Dictionary with elevation results
    """
    try:
        sdk = get_sdk(config_file)
        result = sdk.elevate_file(source_path, dest_path, preview)
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to elevate file: {e}"
        }


# Code Review API

def run_code_review(src_dir: str = "src", config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Run code review agent and return suggestions
    
    Args:
        src_dir: Source directory to review
        config_file: Path to configuration file
        
    Returns:
        Dictionary with review results and suggestions
    """
    try:
        sdk = get_sdk(config_file)
        result = sdk.run_code_review(src_dir)
        
        return {
            "success": True,
            "src_dir": src_dir,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run code review: {e}"
        }


def get_suggestions(filter_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Get code review suggestions from potential_todo.jsonl
    
    Args:
        filter_type: Optional filter by suggestion type
        
    Returns:
        Dictionary with suggestions
    """
    try:
        potential_todo_file = Path("potential_todo.jsonl")
        
        if not potential_todo_file.exists():
            return {
                "success": False,
                "error": "No suggestions file found. Run code review first."
            }
            
        suggestions = []
        with open(potential_todo_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    suggestion = json.loads(line)
                    if not filter_type or suggestion.get('type') == filter_type:
                        suggestions.append(suggestion)
                        
        # Group by type
        by_type = {}
        for suggestion in suggestions:
            suggestion_type = suggestion.get('type', 'unknown')
            by_type[suggestion_type] = by_type.get(suggestion_type, 0) + 1
            
        return {
            "success": True,
            "suggestions": suggestions,
            "total": len(suggestions),
            "by_type": by_type,
            "filter_type": filter_type
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get suggestions: {e}"
        }


def apply_suggestions(filter_type: Optional[str] = None, preview: bool = False, 
                     config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Apply code review suggestions
    
    Args:
        filter_type: Optional filter by suggestion type
        preview: Whether to preview what would be applied
        config_file: Path to configuration file
        
    Returns:
        Dictionary with application results
    """
    try:
        sdk = get_sdk(config_file)
        result = sdk.apply_suggestions(filter_type, preview)
        
        return {
            "success": True,
            "filter_type": filter_type,
            "preview": preview,
            **result
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to apply suggestions: {e}"
        }


# Monitoring and Logging API

def get_logs(agent_id: Optional[str] = None, limit: int = 10, 
            config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Get recent log entries
    
    Args:
        agent_id: Optional agent identifier
        limit: Maximum number of log entries
        config_file: Path to configuration file
        
    Returns:
        Dictionary with log entries
    """
    try:
        sdk = get_sdk(config_file)
        logs = sdk.get_recent_logs(agent_id, limit)
        
        return {
            "success": True,
            "logs": logs,
            "count": len(logs),
            "agent_id": agent_id,
            "limit": limit
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get logs: {e}"
        }


def start_log_streaming(agent_id: Optional[str] = None, 
                       callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                       config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Start streaming logs in real-time
    
    Args:
        agent_id: Optional agent identifier
        callback: Optional callback function for log events
        config_file: Path to configuration file
        
    Returns:
        Dictionary with streaming status
    """
    try:
        sdk = get_sdk(config_file)
        
        if callback:
            sdk.add_log_callback(callback)
            
        return {
            "success": True,
            "streaming": True,
            "agent_id": agent_id,
            "message": "Log streaming started"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to start log streaming: {e}"
        }


def stop_log_streaming(callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                      config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Stop streaming logs
    
    Args:
        callback: Optional callback function to remove
        config_file: Path to configuration file
        
    Returns:
        Dictionary with streaming status
    """
    try:
        sdk = get_sdk(config_file)
        
        if callback:
            sdk.remove_log_callback(callback)
        else:
            # Remove all callbacks
            sdk._log_callbacks.clear()
            
        return {
            "success": True,
            "streaming": False,
            "message": "Log streaming stopped"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to stop log streaming: {e}"
        }


# Utility API

def get_system_status(config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Get comprehensive system status
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with system status
    """
    try:
        sdk = get_sdk(config_file)
        
        # Get basic info
        config_result = get_config(config_file)
        validation_result = validate_config(config_file)
        agents_result = get_agents(config_file=config_file)
        working_set_result = get_working_set_changes(config_file)
        
        return {
            "success": True,
            "config": config_result,
            "validation": validation_result,
            "agents": agents_result,
            "working_set": working_set_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get system status: {e}"
        }


def health_check(config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Perform a health check of the system
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with health check results
    """
    try:
        sdk = get_sdk(config_file)
        
        health = {
            "config_loaded": sdk.config is not None,
            "config_valid": False,
            "agents_running": 0,
            "working_set_accessible": False,
            "code_tool_available": False
        }
        
        # Check config validation
        if sdk.config:
            validation = sdk.validate_config()
            health["config_valid"] = validation["valid"]
            health["config_errors"] = validation.get("errors", [])
            health["config_warnings"] = validation.get("warnings", [])
            
        # Check running agents
        agents = sdk.get_agents()
        health["agents_running"] = sum(1 for agent in agents.values() if agent["status"] == "running")
        
        # Check working set
        try:
            working_set_dir = Path(sdk.config.working_set_dir) if sdk.config else None
            health["working_set_accessible"] = working_set_dir and (working_set_dir.exists() or working_set_dir.parent.exists())
        except:
            health["working_set_accessible"] = False
            
        # Check code tool
        try:
            import subprocess
            if sdk.config and sdk.config.code_tool == "goose":
                result = subprocess.run(['goose', '--version'], capture_output=True, timeout=5)
                health["code_tool_available"] = result.returncode == 0
            elif sdk.config and sdk.config.code_tool == "claude":
                result = subprocess.run(['claude', '--version'], capture_output=True, timeout=5)
                health["code_tool_available"] = result.returncode == 0
        except:
            health["code_tool_available"] = False
            
        # Overall health
        health["healthy"] = (
            health["config_loaded"] and 
            health["config_valid"] and 
            health["working_set_accessible"] and 
            health["code_tool_available"]
        )
        
        return {
            "success": True,
            "health": health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Health check failed: {e}"
        }


# Cleanup function
def cleanup(config_file: str = "verifier.json") -> Dict[str, Any]:
    """
    Clean up all resources and stop all agents
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with cleanup results
    """
    try:
        global _global_sdk
        
        if _global_sdk:
            _global_sdk.cleanup()
            _global_sdk = None
            
        return {
            "success": True,
            "message": "Cleanup completed successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Cleanup failed: {e}"
        } 