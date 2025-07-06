from pathlib import Path
from typing import List, Dict, Any
from .base_agent import BaseAgent
from .config import VerifierConfig


class DocumentationAgent(BaseAgent):
    """Agent that interfaces with Claude Code to generate and update documentation"""
    
    def __init__(self, config: VerifierConfig):
        super().__init__(config, "documentation")
        
    def _get_working_set_dir(self) -> Path:
        """Get the working set directory for the documentation agent"""
        return Path("docs/working_set")
        
    def _get_mission_prompt(self) -> str:
        """Get the mission prompt for the documentation agent"""
        base_prompt = f"""
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
1. Generate appropriate documentation for the changes
2. Update existing documentation if needed
3. Write documentation files to docs/working_set directory
4. Include usage examples and API documentation
5. Continue monitoring for more changes

Focus on creating comprehensive documentation that helps users understand:
- What the code does
- How to use it
- Examples of usage
- Any breaking changes or new features
"""
        
    def _get_mission_reminder(self) -> str:
        """Get the mission reminder text for the documentation agent"""
        return "MISSION REMINDER: Generate comprehensive documentation for code changes and write to docs/working_set"
        
    def _get_log_file_path(self) -> Path:
        """Get the log file path for the documentation agent"""
        return Path("docs/working_set/doc_agent.log")
        
    def _get_session_start_message(self) -> str:
        """Get the session start message for the documentation agent"""
        return "Documentation agent session started. Mission: Generate comprehensive documentation"
        
    def _get_process_success_message(self, change_count: int) -> str:
        """Get the success message after processing changes"""
        return f"Generated documentation for {change_count} file changes"