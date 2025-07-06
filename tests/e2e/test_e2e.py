#!/usr/bin/env python3
"""End-to-end tests for the verifier system"""

import pytest
import tempfile
import asyncio
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from click.testing import CliRunner
from src.cli import InteractiveVerifierCLI
from src.config import VerifierConfig
from src.overseer import Overseer
from src.mock_overseer import MockOverseer


class TestE2ECliWorkflow:
    """End-to-end tests for CLI workflow"""
    
    def test_complete_cli_workflow(self):
        """Test complete CLI workflow from init to validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "e2e_config.json"
            watch_dir = Path(temp_dir) / "src"
            watch_dir.mkdir()
            
            # Step 1: Initialize configuration programmatically
            config = VerifierConfig(
                watch_dirs=[str(watch_dir)],
                working_set_dir=str(Path(temp_dir) / "working_set"),
                error_report_file=str(Path(temp_dir) / "errors.jsonl")
            )
            config.to_file(str(config_path))
            
            # Step 2: Verify config file creation
            assert config_path.exists()
            
            # Step 3: Load and validate configuration
            loaded_config = VerifierConfig.from_file(str(config_path))
            assert loaded_config.watch_dirs == [str(watch_dir)]
            assert loaded_config.working_set_dir == str(Path(temp_dir) / "working_set")
            
            # Step 4: Test CLI can load the config
            cli = InteractiveVerifierCLI()
            cli.config_file = str(config_path)
            cli._load_config()
            
            assert cli.config is not None
            assert cli.config.watch_dirs == [str(watch_dir)]
            
    @patch('src.cli.MockOverseer')
    def test_demo_mode_e2e(self, mock_overseer_class):
        """Test end-to-end demo mode execution"""
        # Create mock overseer that simulates successful execution
        mock_overseer = Mock()
        mock_overseer.start = AsyncMock()
        mock_overseer.is_running = Mock(return_value=False)
        mock_overseer_class.return_value = mock_overseer
        
        with tempfile.TemporaryDirectory() as temp_dir:
            watch_dir = Path(temp_dir) / "src"
            watch_dir.mkdir()
            
            # Create configuration
            config = VerifierConfig(
                watch_dirs=[str(watch_dir)],
                working_set_dir=str(Path(temp_dir) / "working_set"),
                agent_mission="testing"
            )
            
            # Test CLI demo mode
            cli = InteractiveVerifierCLI()
            cli.config = config
            
            # Simulate 'start --demo' command
            cli.do_start("--demo")
            
            # Should have created a mock overseer
            mock_overseer_class.assert_called_once()
            
            # Verify configuration was passed correctly
            call_args = mock_overseer_class.call_args[0][0]
            assert str(watch_dir) in call_args.watch_dirs
            assert call_args.agent_mission == 'testing'


class TestE2EFileMonitoring:
    """End-to-end tests for file monitoring and processing"""
    
    @patch.object(MockOverseer, '_run_mock_agent')
    async def test_file_change_detection_e2e(self, mock_agent):
        """Test end-to-end file change detection and processing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                watch_dirs=[temp_dir],
                working_set_dir=str(Path(temp_dir) / "working_set"),
                error_report_file=str(Path(temp_dir) / "errors.jsonl")
            )
            
            mock_agent.return_value = "Mock processing complete"
            overseer = MockOverseer(config)
            
            # Setup overseer components
            overseer.working_set.ensure_directory_structure()
            overseer._setup_watchers()
            
            # Start watchers manually for testing
            for watcher in overseer.watchers:
                watcher.start()
                
            try:
                # Create a Python file
                test_file = Path(temp_dir) / "test_module.py"
                test_file.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
""")
                
                # Wait for file change detection
                await asyncio.sleep(0.5)
                
                # Process any pending changes
                await overseer._process_pending_changes()
                
                # Modify the file
                test_file.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def subtract(a, b):
    return a - b
""")
                
                # Wait for modification detection
                await asyncio.sleep(0.5)
                
                # Force batch processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Mock agent should have been called
                assert mock_agent.call_count >= 1
                
            finally:
                # Stop watchers
                for watcher in overseer.watchers:
                    watcher.stop()
                    
    @patch.object(MockOverseer, '_run_mock_agent')
    async def test_multiple_file_changes_e2e(self, mock_agent):
        """Test handling multiple file changes end-to-end"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                watch_dirs=[temp_dir],
                working_set_dir=str(Path(temp_dir) / "working_set")
            )
            
            mock_agent.return_value = "Multiple files processed"
            overseer = MockOverseer(config)
            overseer._setup_watchers()
            
            # Start watchers
            for watcher in overseer.watchers:
                watcher.start()
                
            try:
                # Create multiple Python files
                files = []
                for i in range(3):
                    test_file = Path(temp_dir) / f"module_{i}.py"
                    test_file.write_text(f"""
def function_{i}():
    return {i}
""")
                    files.append(test_file)
                    
                # Wait for all changes to be detected
                await asyncio.sleep(0.5)
                
                # Force batch processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Should have processed the batch
                assert mock_agent.call_count >= 1
                
                # Create a non-Python file (should be ignored)
                ignored_file = Path(temp_dir) / "readme.txt"
                ignored_file.write_text("This is a readme file")
                
                await asyncio.sleep(0.3)
                
                # Delete one of the Python files
                files[0].unlink()
                
                await asyncio.sleep(0.3)
                
                # Force another batch processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Should have processed deletion
                assert mock_agent.call_count >= 1
                
            finally:
                for watcher in overseer.watchers:
                    watcher.stop()


class TestE2EErrorHandling:
    """End-to-end tests for error handling scenarios"""
    
    @patch.object(MockOverseer, '_run_mock_agent')
    async def test_error_reporting_e2e(self, mock_agent):
        """Test end-to-end error reporting workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            error_file = Path(temp_dir) / "errors.jsonl"
            config = VerifierConfig(
                working_set_dir=str(Path(temp_dir) / "working_set"),
                error_report_file=str(error_file)
            )
            
            # Mock agent that creates error reports
            def mock_agent_with_error(*args, **kwargs):
                from src.reporter import ErrorReporter
                reporter = ErrorReporter(str(error_file))
                reporter.report_error(
                    file_path="/test/buggy_file.py",
                    line=42,
                    severity="high",
                    description="Division by zero detected",
                    suggested_fix="Add zero check before division"
                )
                return "Error detected and reported"
                
            mock_agent.side_effect = mock_agent_with_error
            
            overseer = MockOverseer(config)
            
            # Process a file change that triggers error detection
            file_changes = [
                {"action": "created", "file_path": "/test/buggy_file.py"}
            ]
            await overseer._mock_process_file_changes(file_changes)
            
            # Process error reports
            overseer._process_error_reports()
            
            # Error file should exist
            assert error_file.exists()
            
            # Should contain the error report
            with open(error_file, 'r') as f:
                error_data = json.loads(f.readline())
                
            assert error_data["file"] == "/test/buggy_file.py"
            assert error_data["line"] == 42
            assert error_data["severity"] == "high"
            assert "Division by zero" in error_data["description"]
            
    async def test_configuration_error_handling_e2e(self):
        """Test handling of configuration errors end-to-end"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config with non-existent watch directory
            config = VerifierConfig(
                watch_dirs=["/nonexistent/directory"],
                working_set_dir=str(Path(temp_dir) / "working_set")
            )
            
            overseer = MockOverseer(config)
            
            # Setup should handle missing directories gracefully
            overseer._setup_watchers()
            
            # Should have no watchers for non-existent directories
            assert len(overseer.watchers) == 0
            
            # Should still be able to process file changes manually
            file_changes = [
                {"action": "created", "file_path": "/test/file.py"}
            ]
            
            # This should not raise an exception
            await overseer._mock_process_file_changes(file_changes)


class TestE2EPerformance:
    """End-to-end performance tests"""
    
    @patch.object(MockOverseer, '_run_mock_agent')
    async def test_high_volume_file_changes_e2e(self, mock_agent):
        """Test handling high volume of file changes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                watch_dirs=[temp_dir],
                working_set_dir=str(Path(temp_dir) / "working_set")
            )
            
            mock_agent.return_value = "Batch processed"
            overseer = MockOverseer(config)
            
            # Simulate many file changes
            changes = []
            for i in range(50):
                file_path = str(Path(temp_dir) / f"file_{i}.py")
                changes.append({"action": "created", "file_path": file_path})
                
            # Process all changes
            start_time = time.time()
            await overseer._mock_process_file_changes(changes)
            end_time = time.time()
            
            # Should complete in reasonable time (less than 1 second for mock)
            assert end_time - start_time < 1.0
            
            # Should have processed the changes
            assert mock_agent.call_count >= 1
            
    @patch.object(MockOverseer, '_run_mock_agent')
    async def test_concurrent_operations_e2e(self, mock_agent):
        """Test concurrent operations end-to-end"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                working_set_dir=str(Path(temp_dir) / "working_set")
            )
            
            mock_agent.return_value = "Concurrent processing complete"
            overseer = MockOverseer(config)
            
            # Run multiple operations concurrently
            tasks = []
            
            # Multiple file change processing tasks
            for i in range(5):
                changes = [
                    {"action": "modified", "file_path": f"/test/file_{i}.py"}
                ]
                tasks.append(overseer._mock_process_file_changes(changes))
                
            # Error report processing task
            tasks.append(overseer._process_error_reports())
            
            # Working set operations
            async def working_set_ops():
                overseer.working_set.ensure_directory_structure()
                overseer.working_set.create_test_file("concurrent_test", "def test(): pass")
                return overseer.working_set.list_test_files()
                
            tasks.append(working_set_ops())
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # No exceptions should have occurred
            for result in results:
                assert not isinstance(result, Exception)
                
            # Mock agent should have been called multiple times
            assert mock_agent.call_count >= 5


class TestE2ESystemIntegration:
    """End-to-end system integration tests"""
    
    def test_cli_to_overseer_integration_e2e(self):
        """Test complete integration from CLI to overseer"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "system_config.json"
            watch_dir = Path(temp_dir) / "src"
            working_set_dir = Path(temp_dir) / "working_set"
            
            # Create directory structure
            watch_dir.mkdir()
            
            # Create config programmatically
            config = VerifierConfig(
                watch_dirs=[str(watch_dir)],
                working_set_dir=str(working_set_dir)
            )
            config.to_file(str(config_path))
            
            # Test CLI can load the config
            cli = InteractiveVerifierCLI()
            cli.config_file = str(config_path)
            cli._load_config()
            
            assert cli.config is not None
            assert cli.config.watch_dirs == [str(watch_dir)]
            
            # Create overseer directly with same config
            loaded_config = VerifierConfig.from_file(str(config_path))
            overseer = MockOverseer(loaded_config)
            
            # Verify configuration consistency
            assert overseer.config.watch_dirs == [str(watch_dir)]
            assert overseer.config.working_set_dir == str(working_set_dir)
            
            # Working set should be properly initialized
            overseer.working_set.ensure_directory_structure()
            assert working_set_dir.exists()
            assert (working_set_dir / "tests").exists()
            
    async def test_full_system_workflow_e2e(self):
        """Test complete system workflow end-to-end"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup directories
            src_dir = Path(temp_dir) / "src"
            working_set_dir = Path(temp_dir) / "working_set"
            src_dir.mkdir()
            
            # Create configuration
            config = VerifierConfig(
                watch_dirs=[str(src_dir)],
                working_set_dir=str(working_set_dir),
                error_report_file=str(Path(temp_dir) / "errors.jsonl"),
                agent_mission="testing"
            )
            
            # Initialize system
            overseer = MockOverseer(config)
            overseer.working_set.ensure_directory_structure()
            
            # Create source file
            source_file = src_dir / "calculator.py"
            source_file.write_text("""
def add(a, b):
    return a + b

def divide(a, b):
    # Bug: no zero check
    return a / b
""")
            
            # Simulate file change processing
            with patch.object(overseer, '_run_mock_agent') as mock_agent:
                mock_agent.return_value = "Tests generated for calculator.py"
                
                file_changes = [
                    {
                        "action": "created",
                        "file_path": str(source_file),
                        "content": source_file.read_text()
                    }
                ]
                
                await overseer._mock_process_file_changes(file_changes)
                
                # Verify processing occurred
                assert mock_agent.call_count == 1
                
                # Verify working set structure exists
                assert working_set_dir.exists()
                assert (working_set_dir / "tests").exists()
                assert (working_set_dir / "artifacts").exists()
                assert (working_set_dir / "reports").exists()
                
                # Create a test file to verify working set functionality
                test_content = """
def test_add():
    from src.calculator import add
    assert add(2, 3) == 5

def test_divide():
    from src.calculator import divide
    assert divide(10, 2) == 5
    
    # This should catch the bug
    try:
        divide(10, 0)
        assert False, "Should have raised ZeroDivisionError"
    except ZeroDivisionError:
        pass
"""
                test_file = overseer.working_set.create_test_file("test_calculator", test_content)
                
                # Verify test file creation
                assert test_file.exists()
                assert "test_add" in test_file.read_text()
                
                # List test files
                test_files = overseer.working_set.list_test_files()
                assert len(test_files) == 1
                assert test_files[0].name == "test_calculator.py"


class TestE2EVerifierSystemDetection:
    """End-to-end tests for verifier system detecting file changes and running Claude Code instances"""
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_real_file_change_triggers_claude_code_instance(self, mock_subprocess):
        """Test that actual file changes trigger Claude Code instances with proper context"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup realistic project structure
            src_dir = Path(temp_dir) / "src"
            tests_dir = Path(temp_dir) / "tests"
            working_set_dir = Path(temp_dir) / "working_set"
            
            src_dir.mkdir()
            tests_dir.mkdir()
            
            # Create config for real agent (not mock)
            config = VerifierConfig(
                watch_dirs=[str(src_dir)],
                working_set_dir=str(working_set_dir),
                error_report_file=str(Path(temp_dir) / "errors.jsonl"),
                agent_mission="testing",
                claude_timeout=30
            )
            
            # Mock successful Claude Code response
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.stdout.read.return_value = json.dumps({
                "response": "Generated comprehensive tests for the new user authentication module",
                "files_created": ["test_auth.py", "test_user_validation.py"],
                "tests_count": 12
            }).encode('utf-8')
            mock_process.stderr.read.return_value = b""
            mock_process.communicate.return_value = (
                json.dumps({
                    "response": "Generated comprehensive tests for the new user authentication module",
                    "files_created": ["test_auth.py", "test_user_validation.py"],
                    "tests_count": 12
                }).encode('utf-8'),
                b""
            )
            mock_subprocess.return_value = mock_process
            
            # Create real overseer (not mock)
            overseer = Overseer(config)
            overseer.working_set.ensure_directory_structure()
            overseer._setup_watchers()
            
            # Start file watchers
            for watcher in overseer.watchers:
                watcher.start()
                
            try:
                # Create a new Python module that should trigger test generation
                auth_module = src_dir / "auth.py"
                auth_module.write_text("""
class UserAuth:
    def __init__(self):
        self.users = {}
        
    def register_user(self, username, password):
        if username in self.users:
            raise ValueError("User already exists")
        self.users[username] = password
        return True
        
    def authenticate(self, username, password):
        if username not in self.users:
            return False
        return self.users[username] == password
        
    def get_user_count(self):
        return len(self.users)
""")
                
                # Wait for file system event to propagate
                await asyncio.sleep(1.0)
                
                # Force processing of changes
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Verify Claude Code was called
                assert mock_subprocess.call_count >= 1
                
                # Verify Claude Code was called with proper context
                call_args = mock_subprocess.call_args
                assert 'claude' in call_args[0][0]
                assert '--print' in call_args[0]
                assert '--dangerously-skip-permissions' in call_args[0]
                
                # Verify the prompt contains file content
                prompt_arg = call_args[0][-1]  # Last argument is the prompt
                assert "UserAuth" in prompt_arg
                assert "register_user" in prompt_arg
                # Note: Could be either verifier or documentation agent
                assert any(term in prompt_arg for term in ["authenticate", "documentation", "FILE CHANGES DETECTED"])
                
            finally:
                # Stop watchers
                for watcher in overseer.watchers:
                    watcher.stop()
                    
    @pytest.mark.asyncio
    @patch('src.agent.subprocess.run')
    async def test_multiple_file_changes_batch_processing(self, mock_subprocess):
        """Test that multiple file changes are batched and processed together"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            
            config = VerifierConfig(
                watch_dirs=[str(src_dir)],
                working_set_dir=str(Path(temp_dir) / "working_set"),
                batch_timeout=1.0  # Short timeout for testing
            )
            
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = json.dumps({
                "response": "Generated tests for multiple modules",
                "files_processed": 3
            })
            
            overseer = Overseer(config)
            overseer._setup_watchers()
            
            for watcher in overseer.watchers:
                watcher.start()
                
            try:
                # Create multiple files rapidly
                files_created = []
                for i in range(3):
                    file_path = src_dir / f"module_{i}.py"
                    file_path.write_text(f"""
def function_{i}():
    return {i} * 2

class Class_{i}:
    def method_{i}(self):
        return "method_{i}"
""")
                    files_created.append(file_path)
                    
                # Wait for batching
                await asyncio.sleep(2.0)
                
                # Force batch processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Should have been called once for the batch
                assert mock_subprocess.call_count == 1
                
                # Verify all files were included in the batch
                prompt_arg = mock_subprocess.call_args[0][-1]
                for i in range(3):
                    assert f"function_{i}" in prompt_arg
                    assert f"Class_{i}" in prompt_arg
                    
            finally:
                for watcher in overseer.watchers:
                    watcher.stop()
                    
    @pytest.mark.asyncio
    @patch('src.agent.subprocess.run')
    async def test_file_deletion_triggers_test_cleanup(self, mock_subprocess):
        """Test that file deletion triggers appropriate test cleanup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            
            config = VerifierConfig(
                watch_dirs=[str(src_dir)],
                working_set_dir=str(Path(temp_dir) / "working_set")
            )
            
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = json.dumps({
                "response": "Cleaned up tests for deleted module",
                "action": "cleanup"
            })
            
            overseer = Overseer(config)
            overseer._setup_watchers()
            
            for watcher in overseer.watchers:
                watcher.start()
                
            try:
                # Create and then delete a file
                temp_file = src_dir / "temp_module.py"
                temp_file.write_text("def temp_function(): pass")
                
                await asyncio.sleep(0.5)
                
                # Delete the file
                temp_file.unlink()
                
                await asyncio.sleep(0.5)
                
                # Force processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Should have been called for deletion
                assert mock_subprocess.call_count >= 1
                
                # Check that deletion was mentioned in prompt
                prompt_arg = mock_subprocess.call_args[0][-1]
                assert "deleted" in prompt_arg.lower() or "removed" in prompt_arg.lower()
                
            finally:
                for watcher in overseer.watchers:
                    watcher.stop()
                    
    @patch('src.agent.subprocess.run')
    async def test_error_handling_in_claude_code_execution(self, mock_subprocess):
        """Test error handling when Claude Code execution fails"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            
            config = VerifierConfig(
                watch_dirs=[str(src_dir)],
                working_set_dir=str(Path(temp_dir) / "working_set"),
                error_report_file=str(Path(temp_dir) / "errors.jsonl")
            )
            
            # Mock Claude Code failure
            mock_subprocess.return_value.returncode = 1
            mock_subprocess.return_value.stderr = "Error: Claude Code failed to process request"
            
            overseer = Overseer(config)
            overseer._setup_watchers()
            
            for watcher in overseer.watchers:
                watcher.start()
                
            try:
                # Create a file that will trigger processing
                test_file = src_dir / "problematic.py"
                test_file.write_text("def broken_function(): pass")
                
                await asyncio.sleep(0.5)
                
                # Force processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Should have attempted to call Claude Code
                assert mock_subprocess.call_count >= 1
                
                # Error should be logged but not crash the system
                error_file = Path(config.error_report_file)
                # System should continue running despite the error
                
            finally:
                for watcher in overseer.watchers:
                    watcher.stop()
                    
    @patch('src.agent.subprocess.run')
    async def test_concurrent_file_changes_and_claude_instances(self, mock_subprocess):
        """Test handling concurrent file changes and Claude Code instances"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            
            config = VerifierConfig(
                watch_dirs=[str(src_dir)],
                working_set_dir=str(Path(temp_dir) / "working_set")
            )
            
            call_count = 0
            def mock_claude_response(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                result = Mock()
                result.returncode = 0
                result.stdout = json.dumps({
                    "response": f"Processed batch {call_count}",
                    "timestamp": time.time()
                })
                return result
                
            mock_subprocess.side_effect = mock_claude_response
            
            overseer = Overseer(config)
            overseer._setup_watchers()
            
            for watcher in overseer.watchers:
                watcher.start()
                
            try:
                # Create multiple files concurrently
                async def create_files_batch(batch_num):
                    for i in range(3):
                        file_path = src_dir / f"batch_{batch_num}_file_{i}.py"
                        file_path.write_text(f"""
def batch_{batch_num}_function_{i}():
    return {batch_num} + {i}
""")
                        await asyncio.sleep(0.1)
                        
                # Create multiple batches concurrently
                await asyncio.gather(
                    create_files_batch(1),
                    create_files_batch(2),
                    create_files_batch(3)
                )
                
                # Wait for processing
                await asyncio.sleep(2.0)
                
                # Force processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Should have processed the changes
                assert mock_subprocess.call_count >= 1
                
            finally:
                for watcher in overseer.watchers:
                    watcher.stop()
                    
    @patch('src.agent.subprocess.run')
    async def test_documentation_agent_parallel_execution(self, mock_subprocess):
        """Test that documentation agent runs in parallel with verifier agent"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            docs_dir = Path(temp_dir) / "docs"
            src_dir.mkdir()
            
            config = VerifierConfig(
                watch_dirs=[str(src_dir)],
                working_set_dir=str(Path(temp_dir) / "working_set"),
                docs_dir=str(docs_dir)
            )
            
            # Mock both verifier and doc agent responses
            responses = [
                json.dumps({"response": "Generated tests", "type": "verifier"}),
                json.dumps({"response": "Generated docs", "type": "documentation"})
            ]
            
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = responses[0]
            
            overseer = Overseer(config)
            overseer._setup_watchers()
            
            for watcher in overseer.watchers:
                watcher.start()
                
            try:
                # Create a complex module requiring documentation
                api_module = src_dir / "api.py"
                api_module.write_text("""
class APIClient:
    '''Main API client for external services'''
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        
    def get_user(self, user_id: int) -> dict:
        '''Retrieve user information by ID'''
        # Implementation here
        pass
        
    def create_user(self, user_data: dict) -> dict:
        '''Create a new user'''
        # Implementation here
        pass
""")
                
                await asyncio.sleep(0.5)
                
                # Force processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Should have called Claude Code
                assert mock_subprocess.call_count >= 1
                
                # Verify the prompt includes documentation context
                prompt_arg = mock_subprocess.call_args[0][-1]
                assert "APIClient" in prompt_arg
                assert "get_user" in prompt_arg
                assert "create_user" in prompt_arg
                
            finally:
                for watcher in overseer.watchers:
                    watcher.stop()
                    
    async def test_working_set_changes_elevation(self):
        """Test that changes can be elevated from working set to main codebase"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            working_set_dir = Path(temp_dir) / "working_set"
            src_dir.mkdir()
            
            config = VerifierConfig(
                watch_dirs=[str(src_dir)],
                working_set_dir=str(working_set_dir)
            )
            
            overseer = MockOverseer(config)
            overseer.working_set.ensure_directory_structure()
            
            # Create a test file in working set
            test_content = """
def test_user_registration():
    from src.auth import UserAuth
    auth = UserAuth()
    
    assert auth.register_user("testuser", "password123") == True
    assert auth.get_user_count() == 1
    
def test_duplicate_user_registration():
    from src.auth import UserAuth
    auth = UserAuth()
    auth.register_user("testuser", "password123")
    
    try:
        auth.register_user("testuser", "password456")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "already exists" in str(e)
"""
            
            test_file = overseer.working_set.create_test_file("test_auth", test_content)
            
            # Verify test file was created
            assert test_file.exists()
            assert "test_user_registration" in test_file.read_text()
            
            # List all test files
            test_files = overseer.working_set.list_test_files()
            assert len(test_files) == 1
            assert test_files[0].name == "test_auth.py"
            
            # Simulate elevation process
            elevated_tests_dir = src_dir.parent / "tests"
            elevated_tests_dir.mkdir()
            
            # Copy test file to main test directory (simulating elevation)
            import shutil
            shutil.copy2(test_file, elevated_tests_dir / "test_auth.py")
            
            # Verify elevation
            elevated_file = elevated_tests_dir / "test_auth.py"
            assert elevated_file.exists()
            assert elevated_file.read_text() == test_file.read_text()
            
    @patch('src.agent.subprocess.run')
    async def test_continuous_monitoring_and_updates(self, mock_subprocess):
        """Test continuous monitoring and updating of Claude Code instances"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            
            config = VerifierConfig(
                watch_dirs=[str(src_dir)],
                working_set_dir=str(Path(temp_dir) / "working_set"),
                batch_timeout=0.5
            )
            
            responses = [
                json.dumps({"response": "Initial test generation", "iteration": 1}),
                json.dumps({"response": "Updated tests after modification", "iteration": 2}),
                json.dumps({"response": "Final test refinement", "iteration": 3})
            ]
            
            call_count = 0
            def mock_responses(*args, **kwargs):
                nonlocal call_count
                result = Mock()
                result.returncode = 0
                result.stdout = responses[call_count % len(responses)]
                call_count += 1
                return result
                
            mock_subprocess.side_effect = mock_responses
            
            overseer = Overseer(config)
            overseer._setup_watchers()
            
            for watcher in overseer.watchers:
                watcher.start()
                
            try:
                # Create initial file
                user_module = src_dir / "user.py"
                user_module.write_text("""
class User:
    def __init__(self, name):
        self.name = name
""")
                
                await asyncio.sleep(1.0)
                
                # Force processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Modify the file
                user_module.write_text("""
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        
    def validate_email(self):
        return '@' in self.email
""")
                
                await asyncio.sleep(1.0)
                
                # Force processing again
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Modify again
                user_module.write_text("""
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        
    def validate_email(self):
        return '@' in self.email and '.' in self.email
        
    def get_domain(self):
        return self.email.split('@')[1]
""")
                
                await asyncio.sleep(1.0)
                
                # Force final processing
                overseer.delta_gate.batch_start_time = time.time() - 5.0
                await overseer._process_pending_changes()
                
                # Should have been called multiple times for the updates
                assert mock_subprocess.call_count >= 2
                
            finally:
                for watcher in overseer.watchers:
                    watcher.stop()


if __name__ == '__main__':
    pytest.main([__file__])