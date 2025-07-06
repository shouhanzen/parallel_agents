#!/usr/bin/env python3
"""Integration tests for verifier components"""

import pytest
import tempfile
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from src.config import VerifierConfig
from src.agent import VerifierAgent
from src.watcher import FilesystemWatcher
from src.delta_gate import DeltaGate, DeltaGateConfig
from src.reporter import ErrorReporter, ReportMonitor
from src.working_set import WorkingSetManager
from src.overseer import Overseer


class TestConfigIntegration:
    """Test configuration integration with other components"""
    
    def test_config_with_agent(self):
        """Test that configuration properly initializes agent"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                working_set_dir=temp_dir,
                agent_mission="docs",
                claude_timeout=120
            )
            
            agent = VerifierAgent(config)
            
            assert agent.config == config
            assert agent.working_set_dir == Path(temp_dir)
            assert str(agent.working_set_dir) in agent._get_mission_prompt()
            assert "docs" in agent._get_mission_prompt()
            
    def test_config_with_working_set(self):
        """Test that configuration properly initializes working set"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(working_set_dir=temp_dir)
            
            working_set = WorkingSetManager(config.working_set_dir)
            
            assert working_set.working_set_dir == Path(temp_dir)
            assert working_set.working_set_dir.exists()
            
    def test_config_with_reporter(self):
        """Test that configuration properly initializes reporter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            error_file = Path(temp_dir) / "errors.jsonl"
            config = VerifierConfig(error_report_file=str(error_file))
            
            reporter = ErrorReporter(config.error_report_file)
            
            assert reporter.report_file == error_file
            assert reporter.report_file.parent.exists()


class TestWatcherDeltaGateIntegration:
    """Test integration between filesystem watcher and delta gate"""
    
    def test_watcher_feeds_delta_gate(self):
        """Test that watcher properly feeds changes to delta gate"""
        changes = []
        gate = DeltaGate()
        
        def on_change(file_path, action):
            if gate.add_change(file_path, action):
                changes.append((file_path, action))
                
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, on_change)
            watcher.start()
            
            try:
                # Create a Python file
                test_file = Path(temp_dir) / "test.py"
                test_file.write_text("def test(): pass")
                
                # Wait for change detection
                time.sleep(0.5)
                
                # Should have detected and accepted the change
                assert len(changes) > 0
                assert gate.get_pending_count() > 0
                
                # Create an ignored file
                ignored_file = Path(temp_dir) / "test.pyc"
                ignored_file.write_text("compiled")
                
                # Wait a bit more
                time.sleep(0.5)
                
                # Should not have added the ignored file
                pending_files = [change['file_path'] for change in gate.get_batch()]
                assert str(ignored_file) not in pending_files
                
            finally:
                watcher.stop()
                
    def test_delta_gate_batching_with_watcher(self):
        """Test delta gate batching behavior with real file changes"""
        changes = []
        config = DeltaGateConfig(batch_timeout=0.2)
        gate = DeltaGate(config)
        
        def on_change(file_path, action):
            gate.add_change(file_path, action)
            
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, on_change)
            watcher.start()
            
            try:
                # Create multiple files rapidly
                for i in range(3):
                    test_file = Path(temp_dir) / f"test_{i}.py"
                    test_file.write_text(f"def test_{i}(): pass")
                    
                # Wait for all changes to be detected
                time.sleep(0.1)
                
                # Should not process yet (within batching window)
                assert not gate.should_process_batch()
                
                # Wait for batch timeout
                time.sleep(0.3)
                
                # Now should be ready to process
                assert gate.should_process_batch()
                
                batch = gate.get_batch()
                assert len(batch) >= 3
                
            finally:
                watcher.stop()


class TestAgentWorkingSetIntegration:
    """Test integration between agent and working set manager"""
    
    @patch.object(VerifierAgent, '_run_claude_code')
    async def test_agent_creates_working_set_structure(self, mock_run_claude):
        """Test that agent can work with working set manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(working_set_dir=temp_dir)
            agent = VerifierAgent(config)
            working_set = WorkingSetManager(config.working_set_dir)
            
            mock_run_claude.return_value = "Tests generated successfully"
            
            # Ensure directory structure
            working_set.ensure_directory_structure()
            
            # Start agent session
            await agent.start_session()
            
            # Process some file changes
            file_changes = [
                {"action": "created", "file_path": "/src/module.py"}
            ]
            await agent.process_file_changes(file_changes)
            
            # Working set should have structure
            assert (agent.working_set_dir / "tests").exists()
            assert (agent.working_set_dir / "artifacts").exists()
            assert (agent.working_set_dir / "reports").exists()
            
            # Agent should have conversation history
            history = agent.get_conversation_history()
            assert len(history) >= 2  # Mission + file changes


class TestReporterIntegration:
    """Test integration between reporter and other components"""
    
    def test_reporter_monitor_integration(self):
        """Test reporter and monitor working together"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            monitor = ReportMonitor(str(report_file))
            
            # Initially no reports
            assert not monitor.has_new_reports()
            
            # Add a report
            reporter.report_error(
                file_path="/test/file.py",
                line=42,
                severity="high",
                description="Test error"
            )
            
            # Monitor should detect new report
            assert monitor.has_new_reports()
            
            # Get new reports
            reports = monitor.get_new_reports()
            assert len(reports) == 1
            assert reports[0]["file"] == "/test/file.py"
            
            # After processing, should be no more reports
            assert not monitor.has_new_reports()


class TestOverseerIntegration:
    """Test overseer integration with all components"""
    
    @patch.object(VerifierAgent, '_run_claude_code')
    async def test_overseer_component_initialization(self, mock_run_claude):
        """Test that overseer properly initializes all components"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                watch_dirs=[temp_dir],
                working_set_dir=str(Path(temp_dir) / "working_set"),
                error_report_file=str(Path(temp_dir) / "errors.jsonl")
            )
            
            overseer = Overseer(config)
            
            # Check components are initialized
            assert overseer.agent is not None
            assert overseer.delta_gate is not None
            assert overseer.working_set is not None
            assert overseer.report_monitor is not None
            assert isinstance(overseer.watchers, list)
            
            # Agent should have correct config
            assert overseer.agent.config == config
            
            # Working set should be properly configured
            assert overseer.working_set.working_set_dir == Path(config.working_set_dir)
            
    @patch.object(VerifierAgent, '_run_claude_code')
    async def test_overseer_file_change_flow(self, mock_run_claude):
        """Test complete file change flow through overseer"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                watch_dirs=[temp_dir],
                working_set_dir=str(Path(temp_dir) / "working_set")
            )
            
            overseer = Overseer(config)
            mock_run_claude.return_value = "Processing complete"
            
            # Setup components
            overseer.working_set.ensure_directory_structure()
            
            # Simulate file change
            test_file = str(Path(temp_dir) / "test.py")
            overseer._on_file_change(test_file, "created")
            
            # Should have pending changes
            assert overseer.delta_gate.get_pending_count() > 0
            
            # Force processing by setting batch time
            overseer.delta_gate.batch_start_time = time.time() - 3.0
            
            # Process pending changes
            await overseer._process_pending_changes()
            
            # Agent should have processed the changes
            mock_run_claude.assert_called()
            
            # Delta gate should be empty
            assert overseer.delta_gate.get_pending_count() == 0


class TestEndToEndWorkflow:
    """End-to-end integration tests"""
    
    @patch.object(VerifierAgent, '_run_claude_code')
    async def test_complete_file_monitoring_workflow(self, mock_run_claude):
        """Test complete workflow from file change to processing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                watch_dirs=[temp_dir],
                working_set_dir=str(Path(temp_dir) / "working_set"),
                error_report_file=str(Path(temp_dir) / "errors.jsonl")
            )
            
            overseer = Overseer(config)
            mock_run_claude.return_value = "File processed successfully"
            
            # Initialize
            overseer.working_set.ensure_directory_structure()
            
            # Set up watchers (but don't start them for this test)
            overseer._setup_watchers()
            
            # Simulate rapid file changes
            changes = []
            for i in range(3):
                file_path = str(Path(temp_dir) / f"module_{i}.py")
                overseer._on_file_change(file_path, "created")
                changes.append(file_path)
                
            # Verify changes are batched
            assert overseer.delta_gate.get_pending_count() == 3
            
            # Force batch processing
            overseer.delta_gate.batch_start_time = time.time() - 5.0
            
            # Process the batch
            await overseer._process_pending_changes()
            
            # Verify processing
            mock_run_claude.assert_called_once()
            assert overseer.delta_gate.get_pending_count() == 0
            
            # Check agent conversation history
            history = overseer.agent.get_conversation_history()
            assert len(history) >= 1
            
    def test_configuration_persistence_workflow(self):
        """Test configuration persistence across component interactions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            working_dir = Path(temp_dir) / "working_set"
            error_file = Path(temp_dir) / "errors.jsonl"
            
            # Create and save configuration
            config = VerifierConfig(
                watch_dirs=[temp_dir],
                working_set_dir=str(working_dir),
                error_report_file=str(error_file),
                agent_mission="docs",
                claude_timeout=180
            )
            config.to_file(str(config_file))
            
            # Load configuration and initialize components
            loaded_config = VerifierConfig.from_file(str(config_file))
            
            # Initialize all components with loaded config
            agent = VerifierAgent(loaded_config)
            working_set = WorkingSetManager(loaded_config.working_set_dir)
            reporter = ErrorReporter(loaded_config.error_report_file)
            overseer = Overseer(loaded_config)
            
            # Verify all components have consistent configuration
            assert agent.config.agent_mission == "docs"
            assert agent.config.claude_timeout == 180
            assert working_set.working_set_dir == working_dir
            assert reporter.report_file == error_file
            assert overseer.config.agent_mission == "docs"
            
    @patch.object(VerifierAgent, '_run_claude_code')
    async def test_error_reporting_workflow(self, mock_run_claude):
        """Test error reporting workflow integration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                working_set_dir=str(Path(temp_dir) / "working_set"),
                error_report_file=str(Path(temp_dir) / "errors.jsonl")
            )
            
            # Initialize components
            reporter = ErrorReporter(config.error_report_file)
            monitor = ReportMonitor(config.error_report_file)
            overseer = Overseer(config)
            
            mock_run_claude.return_value = "Error detected and reported"
            
            # Simulate error being reported
            reporter.report_error(
                file_path="/src/buggy_module.py",
                line=25,
                severity="high",
                description="Null pointer dereference",
                suggested_fix="Add null check"
            )
            
            # Process error reports
            overseer._process_error_reports()
            
            # Monitor should detect and process the error
            assert not monitor.has_new_reports()  # Should be processed


class TestConcurrencyIntegration:
    """Test concurrent operations between components"""
    
    @patch.object(VerifierAgent, '_run_claude_code')
    async def test_concurrent_file_changes_and_processing(self, mock_run_claude):
        """Test handling concurrent file changes and processing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                watch_dirs=[temp_dir],
                working_set_dir=str(Path(temp_dir) / "working_set")
            )
            
            overseer = Overseer(config)
            mock_run_claude.return_value = "Concurrent processing complete"
            
            # Simulate concurrent file changes
            async def simulate_changes():
                for i in range(5):
                    file_path = str(Path(temp_dir) / f"concurrent_{i}.py")
                    overseer._on_file_change(file_path, "created")
                    await asyncio.sleep(0.01)  # Small delay
                    
            # Simulate concurrent processing
            async def process_changes():
                for _ in range(3):
                    await asyncio.sleep(0.05)
                    if overseer.delta_gate.get_pending_count() > 0:
                        # Force processing
                        overseer.delta_gate.batch_start_time = time.time() - 5.0
                        await overseer._process_pending_changes()
                        
            # Run both concurrently
            await asyncio.gather(
                simulate_changes(),
                process_changes()
            )
            
            # Should have processed some changes
            assert mock_run_claude.call_count >= 1
            
    def test_component_isolation(self):
        """Test that components can operate independently"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(working_set_dir=temp_dir)
            
            # Create multiple instances of each component
            agent1 = VerifierAgent(config)
            agent2 = VerifierAgent(config)
            
            working_set1 = WorkingSetManager(str(Path(temp_dir) / "ws1"))
            working_set2 = WorkingSetManager(str(Path(temp_dir) / "ws2"))
            
            # Components should operate independently
            working_set1.create_test_file("test1", "content1")
            working_set2.create_test_file("test2", "content2")
            
            # Each should have only its own files
            files1 = working_set1.list_test_files()
            files2 = working_set2.list_test_files()
            
            assert len(files1) == 1
            assert len(files2) == 1
            assert files1[0].name == "test1.py"
            assert files2[0].name == "test2.py"


if __name__ == '__main__':
    pytest.main([__file__])