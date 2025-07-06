import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from ...config.models import VerifierConfig
from ...monitoring.working_set import WorkingSetManager


class MockVerifierAgent:
    """Mock agent for testing purposes (replaces Claude Code integration)"""
    
    def __init__(self, config: VerifierConfig):
        self.config = config
        self.working_set = WorkingSetManager(config.working_set_dir)
        self.conversation_history: List[Dict[str, str]] = []
        self.session_active = False
        
    def _generate_mock_test(self, file_path: str, action: str) -> str:
        """Generate a mock test for the given file change"""
        file_name = Path(file_path).stem
        
        if action == 'created':
            test_content = f"""
import unittest
from pathlib import Path
import sys

# Add the source directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class Test{file_name.title()}(unittest.TestCase):
    '''Generated test for {file_path} (created)'''
    
    def test_file_exists(self):
        '''Test that the file exists'''
        self.assertTrue(Path('{file_path}').exists())
    
    def test_basic_functionality(self):
        '''Test basic functionality'''
        # This is a generated test - you may need to customize it
        try:
            # Try to import the module
            import {file_name}
            self.assertIsNotNone({file_name})
        except ImportError:
            self.skipTest(f"Could not import {file_name}")

if __name__ == '__main__':
    unittest.main()
"""
        elif action == 'modified':
            test_content = f"""
import unittest
from pathlib import Path
import sys

# Add the source directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class Test{file_name.title()}Modified(unittest.TestCase):
    '''Generated test for {file_path} (modified)'''
    
    def test_file_exists(self):
        '''Test that the file still exists after modification'''
        self.assertTrue(Path('{file_path}').exists())
    
    def test_syntax_valid(self):
        '''Test that the file has valid syntax'''
        try:
            with open('{file_path}', 'r') as f:
                content = f.read()
            compile(content, '{file_path}', 'exec')
        except SyntaxError as e:
            self.fail(f"Syntax error in {file_path}: {{e}}")
    
    def test_updated_functionality(self):
        '''Test functionality after modification'''
        # This is a generated test - you may need to customize it
        try:
            import {file_name}
            # Add specific tests for the modified functionality
            self.assertIsNotNone({file_name})
        except ImportError:
            self.skipTest(f"Could not import {file_name}")

if __name__ == '__main__':
    unittest.main()
"""
        else:  # deleted
            test_content = f"""
import unittest
from pathlib import Path

class Test{file_name.title()}Deleted(unittest.TestCase):
    '''Generated test for {file_path} (deleted)'''
    
    def test_file_deleted(self):
        '''Test that the file has been deleted'''
        self.assertFalse(Path('{file_path}').exists())
    
    def test_cleanup_complete(self):
        '''Test that related files are cleaned up'''
        # Check for .pyc files, etc.
        pyc_file = Path('{file_path}').with_suffix('.pyc')
        if pyc_file.exists():
            self.fail(f"Compiled file still exists: {{pyc_file}}")

if __name__ == '__main__':
    unittest.main()
"""
        
        return test_content.strip()
    
    def _run_mock_test(self, test_file: Path) -> Dict[str, Any]:
        """Run a mock test and return results"""
        # Simple mock test execution
        try:
            # Check if test file exists
            if not test_file.exists():
                return {
                    "success": False,
                    "error": f"Test file not found: {test_file}",
                    "output": ""
                }
            
            # For demo purposes, just return success
            return {
                "success": True,
                "error": None,
                "output": f"Mock test passed for {test_file.name}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }
    
    def _check_for_bugs(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Simple bug detection (mock)"""
        bugs = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Mock bug detection rules
            if 'TODO' in line or 'FIXME' in line:
                bugs.append({
                    "line": i,
                    "severity": "low",
                    "description": f"TODO or FIXME comment found: {line.strip()}",
                    "suggested_fix": "Complete the TODO item"
                })
            
            if 'print(' in line and 'debug' in line.lower():
                bugs.append({
                    "line": i,
                    "severity": "medium",
                    "description": f"Debug print statement found: {line.strip()}",
                    "suggested_fix": "Remove debug print statement"
                })
        
        return bugs
    
    def _write_error_report(self, file_path: str, bugs: List[Dict[str, Any]]):
        """Write bugs to error report file"""
        if not bugs:
            return
            
        error_report_path = Path(self.config.error_report_file)
        error_report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(error_report_path, 'a') as f:
            for bug in bugs:
                report = {
                    "timestamp": "2025-07-05T08:20:00Z",  # Mock timestamp
                    "file": file_path,
                    "line": bug["line"],
                    "severity": bug["severity"],
                    "description": bug["description"],
                    "suggested_fix": bug["suggested_fix"]
                }
                f.write(json.dumps(report) + '\n')
    
    async def start_session(self):
        """Start a new verifier session"""
        if self.session_active:
            return
            
        self.conversation_history.append({
            "type": "mission",
            "content": f"Mock agent started with mission: {self.config.agent_mission}",
            "response": "Mock session started successfully"
        })
        self.session_active = True
        print(f"Mock verifier agent session started. Mission: {self.config.agent_mission}")
    
    async def process_file_changes(self, file_changes: List[Dict[str, Any]]):
        """Process file changes and generate tests"""
        if not self.session_active:
            await self.start_session()
        
        print(f"Mock agent processing {len(file_changes)} file changes...")
        
        for change in file_changes:
            file_path = change['file_path']
            action = change['action']
            
            print(f"Processing: {action} {file_path}")
            
            # Generate test for the change
            if action in ['created', 'modified']:
                test_name = f"test_{Path(file_path).stem}_{action}"
                test_content = self._generate_mock_test(file_path, action)
                
                # Write test to working set
                test_file = self.working_set.create_test_file(test_name, test_content)
                print(f"Generated test: {test_file}")
                
                # Run the test
                test_result = self._run_mock_test(test_file)
                if test_result["success"]:
                    print(f"Test passed: {test_file.name}")
                else:
                    print(f"Test failed: {test_result['error']}")
                
                # Check for bugs if file was modified
                if action == 'modified' and Path(file_path).exists():
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        bugs = self._check_for_bugs(file_path, content)
                        if bugs:
                            self._write_error_report(file_path, bugs)
                            print(f"Found {len(bugs)} potential issues in {file_path}")
                    except Exception as e:
                        print(f"Error checking file {file_path}: {e}")
        
        # Record in conversation history
        self.conversation_history.append({
            "type": "file_changes",
            "changes": file_changes,
            "content": f"Processed {len(file_changes)} changes",
            "response": "Mock processing completed"
        })
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        return self.conversation_history.copy()
    
    def stop_session(self):
        """Stop the verifier session"""
        self.session_active = False
        print("Mock verifier agent session stopped")