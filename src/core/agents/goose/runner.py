import asyncio
import json
import subprocess
import copy
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from .config import VerifierConfig


class CodeAgent(ABC):
    """Base code agent class that provides common functionality for code generation tools"""
    
    def __init__(self, config: VerifierConfig, agent_type: str):
        self.config = config
        self.agent_type = agent_type
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_active = False
        
        # Set up agent-specific directories
        self.working_set_dir = self._get_working_set_dir()
        try:
            self.working_set_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # Don't fail during testing or when directories can't be created
            # The directory will be created later when actually needed
            pass
    
    @abstractmethod
    def _get_working_set_dir(self) -> Path:
        """Get the working set directory for this agent type"""
        pass
        
    @abstractmethod
    def _get_mission_prompt(self) -> str:
        """Get the mission prompt for this agent type"""
        pass
        
    @abstractmethod
    def _get_file_deltas_prompt(self, file_changes: List[Dict[str, Any]]) -> str:
        """Generate prompt for file changes specific to this agent type"""
        pass
        
    @abstractmethod
    def _get_mission_reminder(self) -> str:
        """Get the mission reminder text for this agent type"""
        pass
        
    @abstractmethod
    def _get_log_file_path(self) -> Path:
        """Get the log file path for this agent type"""
        pass
        
    @abstractmethod
    def _get_session_start_message(self) -> str:
        """Get the session start message for this agent type"""
        pass
        
    @abstractmethod
    def _get_process_success_message(self, change_count: int) -> str:
        """Get the success message after processing changes"""
        pass
        
    @abstractmethod
    async def _run_code_tool(self, prompt: str) -> str:
        """Run the code generation tool with the given prompt"""
        pass
        
    def _read_file_content(self, file_path: str) -> str:
        """Read file content safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
            
    def _reset_log_file(self):
        """Reset the log file for a new session"""
        log_file = self._get_log_file_path()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clear the log file by opening it in write mode
            with open(log_file, 'w', encoding='utf-8') as f:
                # Write a session start marker
                session_start = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "session_start",
                    "agent_type": self.agent_type,
                    "mission": self._get_mission_reminder()
                }
                f.write(json.dumps(session_start, indent=2) + '\n')
        except Exception as e:
            print(f"Failed to reset {self.agent_type} log file: {e}")
            
    def _log_code_interaction(self, prompt: str, response: str, success: bool, error: Optional[str] = None):
        """Log code tool interaction to the log file"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "response": response,
            "success": success,
            "error": error,
            "agent_type": self.agent_type,
            "mission": self._get_mission_reminder()
        }
        
        # Ensure log directory exists
        log_file = self._get_log_file_path()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to log file
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, indent=2) + '\n')
        except Exception as e:
            print(f"Failed to write to {self.agent_type} log file: {e}")
            
    async def start_session(self):
        """Start a new agent session"""
        if self.session_active:
            return
            
        # Reset the log file for a fresh session
        self._reset_log_file()
            
        mission_prompt = self._get_mission_prompt()
        
        try:
            response = await self._run_code_tool(mission_prompt)
            self.conversation_history.append({
                "type": "mission",
                "content": mission_prompt,
                "response": response
            })
            self.session_active = True
            print(self._get_session_start_message())
            
        except Exception as e:
            print(f"Failed to start {self.agent_type} session: {e}")
            
    async def process_file_changes(self, file_changes: List[Dict[str, Any]]):
        """Process file changes with this agent"""
        if not self.session_active:
            await self.start_session()
            
        # Read actual file contents for the changes
        enriched_changes = []
        for change in file_changes:
            file_path = change['file_path']
            enriched_change = change.copy()
            
            if change['action'] in ['created', 'modified']:
                enriched_change['content'] = self._read_file_content(file_path)
            
            enriched_changes.append(enriched_change)
            
        # Build the prompt with mission reminder and file changes
        mission_reminder = self._get_mission_reminder()
        changes_prompt = self._get_file_deltas_prompt(enriched_changes)
        
        full_prompt = f"{mission_reminder}\n\n{changes_prompt}"
        
        try:
            response = await self._run_code_tool(full_prompt)
            self.conversation_history.append({
                "type": "file_changes",
                "changes": enriched_changes,
                "content": full_prompt,
                "response": response
            })
            
            print(self._get_process_success_message(len(file_changes)))
            
        except Exception as e:
            print(f"Failed to process file changes with {self.agent_type}: {e}")
            
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        return copy.deepcopy(self.conversation_history)
        
    def stop_session(self):
        """Stop the agent session"""
        self.session_active = False
        print(f"{self.agent_type} agent session stopped") 