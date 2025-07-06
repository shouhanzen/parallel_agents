import asyncio
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from ..base import BaseAgent
from ...config.models import VerifierConfig


class ClaudeCodeAgent(BaseAgent):
    """Agent that interfaces with Claude Code to generate and run code"""
    
    def __init__(self, config: VerifierConfig, agent_type: str):
        super().__init__(config, agent_type)
        
    def _get_working_set_dir(self) -> Path:
        """Get the working set directory for this agent type"""
        if self.agent_type == "verifier":
            return Path(self.config.working_set_dir)
        elif self.agent_type == "documentation":
            return Path("docs/working_set")
        else:
            return Path(f"{self.agent_type}_working_set")
        
    def _get_mission_prompt(self) -> str:
        """Get the mission prompt for this agent type"""
        if self.agent_type == "verifier":
            return f"""
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
""".strip()
        elif self.agent_type == "documentation":
            return f"""
You are a documentation agent running in background mode. Your mission is to automatically generate and update documentation for code changes.

IMPORTANT INSTRUCTIONS:
- You are monitoring source code changes and automatically generating documentation
- Write documentation files in the working_set directory: docs/working_set
- Generate comprehensive documentation that includes:
  * API documentation for new functions/classes
  * Usage examples
  * Architecture diagrams when relevant
  * Code explanations and comments
- Keep documentation up-to-date with code changes
- Always remind yourself of your mission when new changes are injected
- Focus on creating clear, helpful documentation that explains both what the code does and how to use it

DOCUMENTATION STANDARDS:
- Use markdown format for all documentation
- Include code examples where appropriate
- Explain complex algorithms or logic
- Document function parameters, return values, and exceptions
- Provide usage examples for new features
- Update existing documentation when code changes

CURRENT MISSION: Generate comprehensive documentation for code changes and write to docs/working_set
""".strip()
        else:
            return f"""
You are a {self.agent_type} agent running in background mode. Your mission is: {self.config.agent_mission}

IMPORTANT INSTRUCTIONS:
- You are monitoring source code changes and automatically processing them
- Keep your session active and process file changes as they come
- Always remind yourself of your mission when new changes are injected

CURRENT MISSION: {self.config.agent_mission}
""".strip()
        
    def _get_file_deltas_prompt(self, file_changes: List[Dict[str, Any]]) -> str:
        """Generate prompt for file changes"""
        changes_text = []
        for change in file_changes:
            changes_text.append(f"- {change['action']}: {change['file_path']}")
            if change.get('content'):
                changes_text.append(f"  Content preview: {change['content'][:200]}...")
                
        if self.agent_type == "verifier":
            return f"""
FILE CHANGES DETECTED:
{chr(10).join(changes_text)}

Please analyze these changes and:
1. Generate appropriate tests for the changes
2. Run the tests to verify they work
3. If you find bugs, report them to the error report file
4. Continue monitoring for more changes
"""
        elif self.agent_type == "documentation":
            return f"""
FILE CHANGES DETECTED:
{chr(10).join(changes_text)}

Please analyze these changes and:
1. Generate or update documentation for the changes
2. Include API documentation, usage examples, and explanations
3. Write documentation files to the working_set directory
4. Continue monitoring for more changes
"""
        else:
            return f"""
FILE CHANGES DETECTED:
{chr(10).join(changes_text)}

Please analyze these changes and process them according to your mission.
"""
        
    def _get_mission_reminder(self) -> str:
        """Get the mission reminder text for this agent type"""
        return f"MISSION REMINDER: {self.config.agent_mission}"
        
    def _get_log_file_path(self) -> Path:
        """Get the log file path for this agent type"""
        return Path(self.config.claude_log_file)
        
    def _get_session_start_message(self) -> str:
        """Get the session start message for this agent type"""
        return f"Claude Code {self.agent_type} agent session started. Mission: {self.config.agent_mission}"
        
    def _get_process_success_message(self, change_count: int) -> str:
        """Get the success message after processing changes"""
        return f"Claude Code processed {change_count} file changes"
        
    async def _run_code_tool(self, prompt: str) -> str:
        """Run Claude Code with the given prompt"""
        response = ""
        error = None
        success = False
        
        try:
            # Run claude with the prompt directly as an argument
            cmd = ['claude', '--print', '--dangerously-skip-permissions', prompt]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(Path.cwd())
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.claude_timeout
            )
            
            if process.returncode != 0:
                error = f"Claude Code failed: {stderr.decode()}"
                raise RuntimeError(error)
                
            response = stdout.decode()
            success = True
            return response
            
        except asyncio.TimeoutError:
            error = f"Claude Code timed out after {self.config.claude_timeout}s"
            raise RuntimeError(error)
        except Exception as e:
            error = f"Failed to run Claude Code: {e}"
            raise RuntimeError(error)
        finally:
            # Log the interaction regardless of success or failure
            self._log_claude_interaction(prompt, response, success, error)


class ClaudeCodeVerifierAgent(ClaudeCodeAgent):
    """Claude Code agent specialized for verification tasks"""
    
    def __init__(self, config: VerifierConfig):
        super().__init__(config, "verifier")


class ClaudeCodeDocumentationAgent(ClaudeCodeAgent):
    """Claude Code agent specialized for documentation tasks"""
    
    def __init__(self, config: VerifierConfig):
        super().__init__(config, "documentation") 