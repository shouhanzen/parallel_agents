"""
Parallel Agents SDK - Core API for programmatic access to agent functionality
"""

import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime

try:
    from .config import VerifierConfig
    from .overseer import Overseer
    from .mock_overseer import MockOverseer
    from .agent_factory import create_agent
    from .working_set import WorkingSetManager
    from .review_agent import CodeReviewAgent
except ImportError:
    from config import VerifierConfig
    from overseer import Overseer
    from mock_overseer import MockOverseer
    from agent_factory import create_agent
    from working_set import WorkingSetManager
    from review_agent import CodeReviewAgent


class AgentSession:
    """Represents a running agent session"""
    
    def __init__(self, agent_id: str, config: VerifierConfig, overseer: Union[Overseer, MockOverseer], 
                 mission: str, mode: str = "production"):
        self.agent_id = agent_id
        self.config = config
        self.overseer = overseer
        self.mission = mission
        self.mode = mode
        self.status = "starting"
        self.started_at = datetime.now().isoformat()
        self.stopped_at: Optional[str] = None
        self.thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
    def is_running(self) -> bool:
        """Check if the agent session is currently running"""
        return self.overseer and self.overseer.is_running()
        
    def get_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "agent_id": self.agent_id,
            "mission": self.mission,
            "status": self.status,
            "mode": self.mode,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "thread_alive": self.thread.is_alive() if self.thread else False,
            "overseer_running": self.is_running()
        }


class ParallelAgentsSDK:
    """
    Core SDK for Parallel Agents system
    
    Provides programmatic access to all agent functionality including:
    - Agent session management
    - Configuration handling
    - File monitoring and processing
    - Working set management
    - Real-time logging and status
    """
    
    def __init__(self, config_file: str = "verifier.json"):
        self.config_file = config_file
        self.config: Optional[VerifierConfig] = None
        self.sessions: Dict[str, AgentSession] = {}
        self.agent_counter = 0
        self._log_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Load initial configuration
        self.load_config()
        
    # Configuration Management
    
    def load_config(self, config_file: Optional[str] = None) -> VerifierConfig:
        """Load configuration from file"""
        if config_file:
            self.config_file = config_file
            
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                self.config = VerifierConfig.from_file(self.config_file)
                return self.config
            except Exception as e:
                raise RuntimeError(f"Error loading config from {self.config_file}: {e}")
        else:
            self.config = VerifierConfig()
            return self.config
            
    def save_config(self, config_file: Optional[str] = None) -> None:
        """Save current configuration to file"""
        if not self.config:
            raise RuntimeError("No configuration to save")
            
        target_file = config_file or self.config_file
        self.config.to_file(target_file)
        
    def init_config(self, config_file: str = "verifier.json", overwrite: bool = False) -> VerifierConfig:
        """Initialize a new configuration file"""
        config_path = Path(config_file)
        
        if config_path.exists() and not overwrite:
            raise FileExistsError(f"Configuration file {config_file} already exists")
            
        config = VerifierConfig()
        config.to_file(config_file)
        
        self.config_file = config_file
        self.config = config
        return config
        
    def validate_config(self) -> Dict[str, Any]:
        """Validate the current configuration"""
        if not self.config:
            return {"valid": False, "errors": ["No configuration loaded"]}
            
        errors = []
        warnings = []
        
        # Check watch directories
        missing_dirs = []
        for watch_dir in self.config.watch_dirs:
            if not Path(watch_dir).exists():
                missing_dirs.append(watch_dir)
                
        if missing_dirs:
            warnings.append(f"Missing watch directories: {', '.join(missing_dirs)}")
            
        # Check working set directory
        try:
            working_set_path = Path(self.config.working_set_dir)
            working_set_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Working set directory error: {e}")
            
        # Check code tool availability
        if self.config.code_tool == "goose":
            try:
                import subprocess
                result = subprocess.run(['goose', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    errors.append("Block Goose is not properly installed or configured")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                errors.append("Block Goose is not installed or not accessible")
        elif self.config.code_tool == "claude":
            try:
                import subprocess
                result = subprocess.run(['claude', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    errors.append("Claude Code is not properly installed or configured")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                errors.append("Claude Code is not installed or not accessible")
                
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    # Agent Session Management
    
    def start_agent(self, mission: Optional[str] = None, demo_mode: bool = False, 
                   agent_id: Optional[str] = None) -> str:
        """Start a new agent session"""
        if not self.config:
            raise RuntimeError("No configuration loaded")
            
        # Generate agent ID if not provided
        if not agent_id:
            self.agent_counter += 1
            agent_id = f"agent-{self.agent_counter}"
            
        if agent_id in self.sessions:
            raise ValueError(f"Agent {agent_id} already exists")
            
        # Use provided mission or config default
        effective_mission = mission or self.config.agent_mission
        
        # Create overseer
        if demo_mode:
            overseer = MockOverseer(self.config)
            mode = "demo"
        else:
            overseer = Overseer(self.config)
            mode = "production"
            
        # Create session
        session = AgentSession(agent_id, self.config, overseer, effective_mission, mode)
        self.sessions[agent_id] = session
        
        # Start in background thread
        def run_agent():
            try:
                session.status = "starting"
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                session._loop = loop
                
                loop.run_until_complete(overseer.start())
                session.status = "running"
                
            except Exception as e:
                session.status = "failed"
                # Notify error via callback if available
                self._notify_log_event({
                    "level": "error",
                    "message": f"Agent {agent_id} failed: {e}",
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat()
                })
            finally:
                session.status = "stopped"
                session.stopped_at = datetime.now().isoformat()
                
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()
        session.thread = thread
        
        return agent_id
        
    def stop_agent(self, agent_id: str) -> None:
        """Stop a specific agent session"""
        if agent_id not in self.sessions:
            raise ValueError(f"Agent {agent_id} not found")
            
        session = self.sessions[agent_id]
        
        if session.overseer and session.is_running():
            # Stop the overseer
            if session._loop and session._loop.is_running():
                session._loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(session.overseer.stop())
                )
            else:
                asyncio.run(session.overseer.stop())
                
        session.status = "stopped"
        session.stopped_at = datetime.now().isoformat()
        
    def stop_all_agents(self) -> None:
        """Stop all running agent sessions"""
        for agent_id in list(self.sessions.keys()):
            try:
                self.stop_agent(agent_id)
            except Exception as e:
                self._notify_log_event({
                    "level": "error",
                    "message": f"Error stopping agent {agent_id}: {e}",
                    "timestamp": datetime.now().isoformat()
                })
                
    def get_agents(self, include_stopped: bool = False) -> Dict[str, Dict[str, Any]]:
        """Get information about all agent sessions"""
        result = {}
        
        for agent_id, session in self.sessions.items():
            info = session.get_info()
            
            if include_stopped or info["status"] in ["running", "starting"]:
                result[agent_id] = info
                
        return result
        
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed status for a specific agent"""
        if agent_id not in self.sessions:
            raise ValueError(f"Agent {agent_id} not found")
            
        session = self.sessions[agent_id]
        info = session.get_info()
        
        # Add additional status information
        if session.overseer:
            # Get log file information
            if hasattr(session.config, 'goose_log_file') and session.config.code_tool == "goose":
                log_file = Path(session.config.goose_log_file)
            else:
                log_file = Path(session.config.claude_log_file)
                
            info["log_file"] = str(log_file)
            info["log_exists"] = log_file.exists()
            
            if log_file.exists():
                info["log_size"] = log_file.stat().st_size
                info["log_modified"] = datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                
        return info
        
    # File Processing and Working Set Management
    
    def process_file_changes(self, agent_id: str, file_changes: List[Dict[str, Any]]) -> None:
        """Manually trigger file change processing for an agent"""
        if agent_id not in self.sessions:
            raise ValueError(f"Agent {agent_id} not found")
            
        session = self.sessions[agent_id]
        
        if not session.is_running():
            raise RuntimeError(f"Agent {agent_id} is not running")
            
        # Trigger processing through the overseer
        if session._loop and session.overseer:
            session._loop.call_soon_threadsafe(
                lambda: self._process_file_changes_for_overseer(session.overseer, file_changes)
            )
        
    def get_working_set_changes(self) -> Dict[str, Any]:
        """Get information about changes in the working set"""
        if not self.config:
            raise RuntimeError("No configuration loaded")
            
        working_set_dir = Path(self.config.working_set_dir)
        
        if not working_set_dir.exists():
            return {"files": [], "total_files": 0, "by_type": {}}
            
        ws_manager = WorkingSetManager(str(working_set_dir))
        
        # Get all files
        all_files = []
        for file_path in working_set_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(working_set_dir)
                all_files.append({
                    "path": str(rel_path),
                    "full_path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "type": self._classify_file_type(file_path)
                })
                
        # Group by type
        by_type = {}
        for file_info in all_files:
            file_type = file_info["type"]
            if file_type not in by_type:
                by_type[file_type] = []
            by_type[file_type].append(file_info)
            
        return {
            "files": all_files,
            "total_files": len(all_files),
            "by_type": by_type
        }
        
    def elevate_file(self, source_path: str, dest_path: Optional[str] = None, 
                    preview: bool = False) -> Dict[str, Any]:
        """Elevate a file from working set to main codebase"""
        if not self.config:
            raise RuntimeError("No configuration loaded")
            
        working_set_dir = Path(self.config.working_set_dir)
        source_file = working_set_dir / source_path
        
        if not source_file.exists():
            raise FileNotFoundError(f"File not found in working set: {source_path}")
            
        # Auto-determine destination if not provided
        if not dest_path:
            if source_file.name.startswith('test_'):
                dest_path = f"tests/{source_file.name}"
            elif source_file.suffix == '.py':
                dest_path = f"src/{source_file.name}"
            elif source_file.suffix == '.md':
                dest_path = f"docs/{source_file.name}"
            else:
                dest_path = source_file.name
                
        dest_file = Path(dest_path)
        
        result = {
            "source": str(source_file),
            "destination": str(dest_file),
            "preview": preview,
            "would_overwrite": dest_file.exists()
        }
        
        if preview:
            result["content_preview"] = source_file.read_text()[:500]
            return result
            
        # Perform actual elevation
        try:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(source_file, dest_file)
            
            result["success"] = True
            result["message"] = f"Successfully elevated {source_path} to {dest_path}"
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            
        return result
        
    # Code Review and Suggestions
    
    def run_code_review(self, src_dir: str = "src") -> Dict[str, Any]:
        """Run code review agent and return suggestions"""
        if not self.config:
            raise RuntimeError("No configuration loaded")
            
        review_agent = CodeReviewAgent(self.config)
        
        # Run review (this will generate potential_todo.jsonl)
        review_agent.run_review()
        
        # Read and return suggestions
        potential_todo_file = Path("potential_todo.jsonl")
        
        if not potential_todo_file.exists():
            return {"suggestions": [], "total": 0}
            
        suggestions = []
        try:
            with open(potential_todo_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        suggestions.append(json.loads(line))
        except Exception as e:
            return {"error": f"Error reading suggestions: {e}"}
            
        return {
            "suggestions": suggestions,
            "total": len(suggestions),
            "by_type": self._group_suggestions_by_type(suggestions)
        }
        
    def apply_suggestions(self, filter_type: Optional[str] = None, 
                         preview: bool = False) -> Dict[str, Any]:
        """Apply suggestions from code review"""
        potential_todo_file = Path("potential_todo.jsonl")
        
        if not potential_todo_file.exists():
            return {"error": "No suggestions file found. Run code review first."}
            
        # Read suggestions
        suggestions = []
        try:
            with open(potential_todo_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        suggestion = json.loads(line)
                        if not filter_type or suggestion.get('type') == filter_type:
                            suggestions.append(suggestion)
        except Exception as e:
            return {"error": f"Error reading suggestions: {e}"}
            
        if preview:
            return {
                "suggestions": suggestions,
                "total": len(suggestions),
                "preview": True
            }
            
        # Apply suggestions (would need Claude Code integration)
        # For now, return what would be applied
        return {
            "applied": len(suggestions),
            "suggestions": suggestions,
            "message": f"Would apply {len(suggestions)} suggestions"
        }
        
    # Logging and Monitoring
    
    def add_log_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add a callback function to receive log events"""
        self._log_callbacks.append(callback)
        
    def remove_log_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a log callback function"""
        if callback in self._log_callbacks:
            self._log_callbacks.remove(callback)
            
    def get_recent_logs(self, agent_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        if not self.config:
            return []
            
        # Determine log file
        if agent_id and agent_id in self.sessions:
            session = self.sessions[agent_id]
            if session.config.code_tool == "goose":
                log_file = Path(session.config.goose_log_file)
            else:
                log_file = Path(session.config.claude_log_file)
        else:
            if self.config.code_tool == "goose":
                log_file = Path(self.config.goose_log_file)
            else:
                log_file = Path(self.config.claude_log_file)
                
        if not log_file.exists():
            return []
            
        # Read recent log entries
        logs = []
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Get last N lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                line = line.strip()
                if line:
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        # Handle non-JSON log lines
                        logs.append({
                            "timestamp": datetime.now().isoformat(),
                            "message": line,
                            "level": "info"
                        })
                        
        except Exception as e:
            logs.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"Error reading logs: {e}",
                "level": "error"
            })
            
        return logs
        
    # Utility Methods
    
    def _classify_file_type(self, file_path: Path) -> str:
        """Classify file type based on path and extension"""
        path_str = str(file_path)
        
        if 'test' in path_str:
            return 'tests'
        elif 'artifact' in path_str:
            return 'artifacts'
        elif 'report' in path_str or file_path.suffix == '.jsonl':
            return 'reports'
        elif 'log' in path_str:
            return 'logs'
        else:
            return 'other'
            
    def _group_suggestions_by_type(self, suggestions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group suggestions by type and count them"""
        by_type = {}
        for suggestion in suggestions:
            suggestion_type = suggestion.get('type', 'unknown')
            by_type[suggestion_type] = by_type.get(suggestion_type, 0) + 1
        return by_type
        
    def _notify_log_event(self, event: Dict[str, Any]) -> None:
        """Notify all log callbacks of a new event"""
        for callback in self._log_callbacks:
            try:
                callback(event)
            except Exception as e:
                # Don't let callback errors break the system
                pass
                
    # Context Management
    
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up resources"""
        self.stop_all_agents()
        
    def _process_file_changes_for_overseer(self, overseer, file_changes: List[Dict[str, Any]]):
        """Process file changes for an overseer by adding them to the delta gate"""
        for change in file_changes:
            overseer.delta_gate.add_change(change['file'], change['action'])
        
        # Trigger processing if needed
        asyncio.create_task(overseer._process_pending_changes())
    
    def cleanup(self) -> None:
        """Clean up all resources"""
        self.stop_all_agents()
        self._log_callbacks.clear()


# Convenience functions for easy SDK usage

def create_sdk(config_file: str = "verifier.json") -> ParallelAgentsSDK:
    """Create a new SDK instance"""
    return ParallelAgentsSDK(config_file)

def start_monitoring(mission: str = "testing", demo_mode: bool = False, 
                    config_file: str = "verifier.json") -> ParallelAgentsSDK:
    """Quick start function to begin monitoring with default settings"""
    sdk = ParallelAgentsSDK(config_file)
    agent_id = sdk.start_agent(mission=mission, demo_mode=demo_mode)
    return sdk 