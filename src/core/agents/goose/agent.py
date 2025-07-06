"""
Block Goose agent implementations
"""

import asyncio
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from ...config.models import VerifierConfig
from ..base import BaseAgent


class BlockGooseAgent(BaseAgent):
    """Base class for Block Goose agents"""
    
    def __init__(self, config: VerifierConfig):
        super().__init__(config)
        self.goose_timeout = getattr(config, 'goose_timeout', 300)
        self.log_file = Path(getattr(config, 'goose_log_file', 'goose_logs.jsonl'))
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Verify Block Goose installation
        if not self._verify_goose_installation():
            raise RuntimeError("Block Goose is not installed or not accessible")
    
    def _verify_goose_installation(self) -> bool:
        """Verify that Block Goose is installed and accessible"""
        try:
            result = subprocess.run(
                ['goose', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logging.info(f"Block Goose version: {result.stdout.strip()}")
                return True
            else:
                logging.error(f"Block Goose version check failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logging.error("Block Goose version check timed out")
            return False
        except FileNotFoundError:
            logging.error("Block Goose not found in PATH")
            return False
        except Exception as e:
            logging.error(f"Error checking Block Goose installation: {e}")
            return False
    
    def _log_interaction(self, interaction_type: str, data: Dict[str, Any]) -> None:
        """Log interaction with Block Goose"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "data": data
        }
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logging.error(f"Failed to log interaction: {e}")
    
    def _run_goose_command(self, command: List[str], input_text: str = None) -> Dict[str, Any]:
        """Run a Block Goose command and return results"""
        full_command = ['goose'] + command
        
        self._log_interaction("command_start", {
            "command": full_command,
            "input": input_text
        })
        
        try:
            result = subprocess.run(
                full_command,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=self.goose_timeout
            )
            
            response = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            self._log_interaction("command_result", response)
            return response
            
        except subprocess.TimeoutExpired:
            error_msg = f"Block Goose command timed out after {self.goose_timeout}s"
            logging.error(error_msg)
            
            response = {
                "returncode": -1,
                "stdout": "",
                "stderr": error_msg,
                "success": False
            }
            
            self._log_interaction("command_error", response)
            return response
            
        except Exception as e:
            error_msg = f"Error running Block Goose command: {e}"
            logging.error(error_msg)
            
            response = {
                "returncode": -1,
                "stdout": "",
                "stderr": error_msg,
                "success": False
            }
            
            self._log_interaction("command_error", response)
            return response
    
    def _run_goose_headless(self, prompt: str, files: List[str] = None) -> Dict[str, Any]:
        """Run Block Goose in headless mode using 'goose run' command"""
        command = ['run']
        
        if files:
            for file in files:
                command.extend(['--file', file])
        
        command.append(prompt)
        
        return self._run_goose_command(command)
    
    async def process_file_changes(self, file_changes: List[Dict[str, Any]]) -> None:
        """Process file changes with Block Goose"""
        if not self.session_active:
            await self.start_session()
        
        for change in file_changes:
            file_path = change['file']
            action = change['action']
            
            try:
                if action == 'deleted':
                    # Handle deleted files
                    prompt = f"File {file_path} was deleted. Please review and update any dependent code."
                    result = self._run_goose_headless(prompt)
                    
                else:
                    # Handle created/modified files
                    if Path(file_path).exists():
                        prompt = f"File {file_path} was {action}. Please review and suggest improvements."
                        result = self._run_goose_headless(prompt, [file_path])
                    else:
                        logging.warning(f"File {file_path} no longer exists")
                        continue
                
                if result['success']:
                    logging.info(f"Successfully processed {file_path} with Block Goose")
                else:
                    logging.error(f"Failed to process {file_path}: {result['stderr']}")
                    
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")


class BlockGooseVerifierAgent(BlockGooseAgent):
    """Block Goose agent specialized for code verification and testing"""
    
    def __init__(self, config: VerifierConfig):
        super().__init__(config)
        self.agent_type = "verifier"
    
    async def process_file_changes(self, file_changes: List[Dict[str, Any]]) -> None:
        """Process file changes with focus on testing and verification"""
        if not self.session_active:
            await self.start_session()
        
        for change in file_changes:
            file_path = change['file']
            action = change['action']
            
            try:
                if action == 'deleted':
                    prompt = f"File {file_path} was deleted. Please check for and remove any related tests."
                    result = self._run_goose_headless(prompt)
                    
                else:
                    if Path(file_path).exists():
                        prompt = f"""
                        File {file_path} was {action}. Please:
                        1. Review the code for potential issues
                        2. Generate comprehensive tests if needed
                        3. Verify the code follows best practices
                        4. Check for security vulnerabilities
                        """
                        result = self._run_goose_headless(prompt, [file_path])
                    else:
                        logging.warning(f"File {file_path} no longer exists")
                        continue
                
                if result['success']:
                    logging.info(f"Successfully verified {file_path} with Block Goose")
                else:
                    logging.error(f"Failed to verify {file_path}: {result['stderr']}")
                    
            except Exception as e:
                logging.error(f"Error verifying file {file_path}: {e}")


class BlockGooseDocumentationAgent(BlockGooseAgent):
    """Block Goose agent specialized for documentation generation"""
    
    def __init__(self, config: VerifierConfig):
        super().__init__(config)
        self.agent_type = "documentation"
    
    async def process_file_changes(self, file_changes: List[Dict[str, Any]]) -> None:
        """Process file changes with focus on documentation"""
        if not self.session_active:
            await self.start_session()
        
        for change in file_changes:
            file_path = change['file']
            action = change['action']
            
            try:
                if action == 'deleted':
                    prompt = f"File {file_path} was deleted. Please update any related documentation."
                    result = self._run_goose_headless(prompt)
                    
                else:
                    if Path(file_path).exists():
                        prompt = f"""
                        File {file_path} was {action}. Please:
                        1. Generate comprehensive documentation
                        2. Add docstrings if missing
                        3. Create usage examples
                        4. Update any related README files
                        """
                        result = self._run_goose_headless(prompt, [file_path])
                    else:
                        logging.warning(f"File {file_path} no longer exists")
                        continue
                
                if result['success']:
                    logging.info(f"Successfully documented {file_path} with Block Goose")
                else:
                    logging.error(f"Failed to document {file_path}: {result['stderr']}")
                    
            except Exception as e:
                logging.error(f"Error documenting file {file_path}: {e}") 