from pathlib import Path
from typing import List, Dict, Any
from .base_agent import BaseAgent
from .config import VerifierConfig


class VerifierAgent(BaseAgent):
    """Agent that interfaces with Claude Code to generate and run tests"""
    
    def __init__(self, config: VerifierConfig):
        super().__init__(config, "verifier")
        
    def _get_working_set_dir(self) -> Path:
        """Get the working set directory for the verifier agent"""
        return Path(self.config.working_set_dir)
        
    def _get_mission_prompt(self) -> str:
        """Get the mission prompt for the verifier agent"""
        base_prompt = f"""
You are a verifier agent running in background mode. Your mission is: {self.config.agent_mission}

IMPORTANT INSTRUCTIONS:
- You are monitoring source code changes and automatically generating tests
- Write tests in the working_set directory: {self.config.working_set_dir}
- Run tests automatically after generating them
- If you find actual bugs (not just test issues), report them to: {self.config.error_report_file}
- Keep your session active and process file changes as they come
- Always remind yourself of your mission when new changes are injected

ERROR REPORT FORMAT:
When you find bugs, append to the JSONL file in this format:
{{"timestamp": "ISO_TIMESTAMP", "file": "path/to/file", "line": 123, "severity": "high|medium|low", "description": "Bug description", "suggested_fix": "Optional fix suggestion"}}

CURRENT MISSION: {self.config.agent_mission}
"""
        return base_prompt.strip()
        
    def _get_file_deltas_prompt(self, file_changes: List[Dict[str, Any]]) -> str:
        """Generate prompt for file changes"""
        changes_text = []
        for change in file_changes:
            changes_text.append(f"- {change['action']}: {change['file_path']}")
            if change.get('content'):
                changes_text.append(f"  Content preview: {change['content'][:200]}...")
                
        return f"""
FILE CHANGES DETECTED:
{chr(10).join(changes_text)}

Please analyze these changes and:
1. Generate appropriate tests for the changes
2. Run the tests to verify they work
3. If you find bugs, report them to the error report file
4. Continue monitoring for more changes
"""
        
    def _get_mission_reminder(self) -> str:
        """Get the mission reminder text for the verifier agent"""
        return f"MISSION REMINDER: {self.config.agent_mission}"
        
    def _get_log_file_path(self) -> Path:
        """Get the log file path for the verifier agent"""
        return Path(self.config.claude_log_file)
        
    def _get_session_start_message(self) -> str:
        """Get the session start message for the verifier agent"""
        return f"Verifier agent session started. Mission: {self.config.agent_mission}"
        
    def _get_process_success_message(self, change_count: int) -> str:
        """Get the success message after processing changes"""
        return f"Processed {change_count} file changes"