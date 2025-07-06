#!/usr/bin/env python3
"""Unit tests for the overseer module"""

import pytest
import asyncio
import tempfile
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.overseer.overseer import Overseer
from core.config.models import VerifierConfig
from core.monitoring.delta_gate import DeltaGateConfig

pytestmark = pytest.mark.asyncio


class TestOverseer:
    """Test the Overseer class"""
    
    def test_overseer_creation(self):
        """Test creating an Overseer instance"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        assert overseer.config == config
        assert overseer.agent is not None
        assert overseer.doc_agent is not None
        assert overseer.watchers == []
        assert overseer.report_monitor is not None
        assert overseer.delta_gate is not None
        assert overseer.working_set is not None
        assert overseer.running is False
        
    def test_overseer_with_custom_config(self):
        """Test creating overseer with custom configuration"""
        config = VerifierConfig(
            watch_dirs=['custom_src', 'lib'],
            agent_mission='docs',
            working_set_dir='custom/working/set'
        )
        overseer = Overseer(config)
        
        assert overseer.config.watch_dirs == ['custom_src', 'lib']
        assert overseer.config.agent_mission == 'docs'
        assert overseer.config.working_set_dir == 'custom/working/set'
        
    def test_on_file_change_accepted(self):
        """Test file change handling when delta gate accepts change"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        # Mock delta gate to accept changes
        with patch.object(overseer.delta_gate, 'add_change', return_value=True):
            overseer._on_file_change('test.py', 'modified')
            
    def test_on_file_change_rejected(self):
        """Test file change handling when delta gate rejects change"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        # Mock delta gate to reject changes
        with patch.object(overseer.delta_gate, 'add_change', return_value=False):
            overseer._on_file_change('test.pyc', 'modified')
            
    def test_setup_watchers_existing_directories(self):
        """Test setting up watchers for existing directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(watch_dirs=[temp_dir])
            overseer = Overseer(config)
            
            with patch('core.overseer.overseer.FilesystemWatcher') as mock_watcher_class:
                mock_watcher = Mock()
                mock_watcher_class.return_value = mock_watcher
                
                overseer._setup_watchers()
                
                assert len(overseer.watchers) == 1
                mock_watcher_class.assert_called_once_with(temp_dir, overseer._on_file_change)
                
    def test_setup_watchers_nonexistent_directories(self):
        """Test setting up watchers for non-existent directories"""
        config = VerifierConfig(watch_dirs=['/nonexistent/directory'])
        overseer = Overseer(config)
        
        overseer._setup_watchers()
        
        # Should not create watchers for non-existent directories
        assert len(overseer.watchers) == 0
        
    async def test_process_pending_changes_no_batch(self):
        """Test processing pending changes when no batch is ready"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        with patch.object(overseer.delta_gate, 'should_process_batch', return_value=False):
            await overseer._process_pending_changes()
            
    async def test_process_pending_changes_with_batch(self):
        """Test processing pending changes with a batch"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        mock_batch = [
            {'file_path': 'test.py', 'action': 'modified', 'timestamp': time.time()}
        ]
        
        with patch.object(overseer.delta_gate, 'should_process_batch', return_value=True):
            with patch.object(overseer.delta_gate, 'get_batch', return_value=mock_batch):
                with patch.object(overseer.agent, 'process_file_changes') as mock_agent:
                    with patch.object(overseer.doc_agent, 'process_file_changes') as mock_doc_agent:
                        mock_agent.return_value = asyncio.Future()
                        mock_agent.return_value.set_result(None)
                        mock_doc_agent.return_value = asyncio.Future()
                        mock_doc_agent.return_value.set_result(None)
                        
                        await overseer._process_pending_changes()
                        
                        mock_agent.assert_called_once_with(mock_batch)
                        mock_doc_agent.assert_called_once_with(mock_batch)
                        
    async def test_process_pending_changes_empty_batch(self):
        """Test processing pending changes with empty batch"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        with patch.object(overseer.delta_gate, 'should_process_batch', return_value=True):
            with patch.object(overseer.delta_gate, 'get_batch', return_value=[]):
                with patch.object(overseer.agent, 'process_file_changes') as mock_agent:
                    with patch.object(overseer.doc_agent, 'process_file_changes') as mock_doc_agent:
                        await overseer._process_pending_changes()
                        
                        mock_agent.assert_not_called()
                        mock_doc_agent.assert_not_called()
                        
    def test_process_error_reports_no_reports(self):
        """Test processing error reports when there are none"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        with patch.object(overseer.report_monitor, 'has_new_reports', return_value=False):
            overseer._process_error_reports()
            
    def test_process_error_reports_with_reports(self):
        """Test processing error reports when there are some"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        mock_reports = [
            {
                'file': 'test.py',
                'line': 10,
                'severity': 'high',
                'description': 'Test error',
                'suggested_fix': 'Fix the test',
                'timestamp': '2024-01-01T00:00:00Z'
            }
        ]
        
        with patch.object(overseer.report_monitor, 'has_new_reports', return_value=True):
            with patch.object(overseer.report_monitor, 'get_new_reports', return_value=mock_reports):
                with patch.object(overseer, '_display_error_report') as mock_display:
                    overseer._process_error_reports()
                    
                    mock_display.assert_called_once_with(mock_reports[0])
                    
    def test_display_error_report_high_severity(self):
        """Test displaying high severity error report"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        report = {
            'file': 'test.py',
            'line': 10,
            'severity': 'high',
            'description': 'Critical error',
            'suggested_fix': 'Fix immediately',
            'timestamp': '2024-01-01T00:00:00Z'
        }
        
        # Just test that it doesn't crash
        overseer._display_error_report(report)
        
    def test_display_error_report_medium_severity(self):
        """Test displaying medium severity error report"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        report = {
            'file': 'test.py',
            'line': 15,
            'severity': 'medium',
            'description': 'Warning',
            'suggested_fix': 'Consider fixing',
            'timestamp': '2024-01-01T00:00:00Z'
        }
        
        # Just test that it doesn't crash
        overseer._display_error_report(report)
        
    def test_display_error_report_no_line(self):
        """Test displaying error report without line number"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        report = {
            'file': 'test.py',
            'line': None,
            'severity': 'low',
            'description': 'General issue',
            'suggested_fix': None,
            'timestamp': '2024-01-01T00:00:00Z'
        }
        
        # Just test that it doesn't crash
        overseer._display_error_report(report)
        
    def test_is_running_initial_state(self):
        """Test that overseer is not running initially"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        assert overseer.is_running() is False
        
    def test_is_running_after_start_flag(self):
        """Test is_running after setting the running flag"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        overseer.running = True
        assert overseer.is_running() is True
        
        overseer.running = False
        assert overseer.is_running() is False


class TestOverseerIntegration:
    """Integration tests for the Overseer class"""
    
    @patch('core.overseer.overseer.FilesystemWatcher')
    async def test_start_and_stop_cycle(self, mock_watcher_class):
        """Test complete start and stop cycle"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(
                watch_dirs=[temp_dir],
                working_set_dir=temp_dir + '/working_set'
            )
            overseer = Overseer(config)
            
            # Mock watcher
            mock_watcher = Mock()
            mock_watcher_class.return_value = mock_watcher
            
            # Mock agent sessions
            with patch.object(overseer.agent, 'start_session') as mock_agent_start:
                with patch.object(overseer.doc_agent, 'start_session') as mock_doc_start:
                    with patch.object(overseer.agent, 'stop_session') as mock_agent_stop:
                        with patch.object(overseer.doc_agent, 'stop_session') as mock_doc_stop:
                            mock_agent_start.return_value = asyncio.Future()
                            mock_agent_start.return_value.set_result(None)
                            mock_doc_start.return_value = asyncio.Future()
                            mock_doc_start.return_value.set_result(None)
                            
                            # Start overseer in the background
                            start_task = asyncio.create_task(overseer.start())
                            
                            # Wait a bit for startup
                            await asyncio.sleep(0.1)
                            
                            # Should be running
                            assert overseer.is_running() is True
                            
                            # Stop overseer
                            await overseer.stop()
                            
                            # Should not be running
                            assert overseer.is_running() is False
                            
                            # Check that agent sessions were started and stopped
                            mock_agent_start.assert_called_once()
                            mock_doc_start.assert_called_once()
                            mock_agent_stop.assert_called_once()
                            mock_doc_stop.assert_called_once()
                            
                            # Check that watcher was started and stopped
                            mock_watcher.start.assert_called_once()
                            mock_watcher.stop.assert_called_once()
                            
                            # Cancel the start task
                            start_task.cancel()
                            try:
                                await start_task
                            except asyncio.CancelledError:
                                pass
                            
    async def test_file_change_processing_workflow(self):
        """Test the complete file change processing workflow"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        # Mock components
        with patch.object(overseer.delta_gate, 'add_change') as mock_add_change:
            with patch.object(overseer.delta_gate, 'should_process_batch', return_value=True):
                with patch.object(overseer.delta_gate, 'get_batch') as mock_get_batch:
                    with patch.object(overseer.agent, 'process_file_changes') as mock_agent:
                        with patch.object(overseer.doc_agent, 'process_file_changes') as mock_doc_agent:
                            mock_add_change.return_value = True
                            mock_get_batch.return_value = [
                                {'file_path': 'test.py', 'action': 'modified', 'timestamp': time.time()}
                            ]
                            mock_agent.return_value = asyncio.Future()
                            mock_agent.return_value.set_result(None)
                            mock_doc_agent.return_value = asyncio.Future()
                            mock_doc_agent.return_value.set_result(None)
                            
                            # Simulate file change
                            overseer._on_file_change('test.py', 'modified')
                            
                            # Process pending changes
                            await overseer._process_pending_changes()
                            
                            # Check that change was added to delta gate
                            mock_add_change.assert_called_once_with('test.py', 'modified')
                            
                            # Check that batch was retrieved and processed
                            mock_get_batch.assert_called_once()
                            mock_agent.assert_called_once()
                            mock_doc_agent.assert_called_once()
                            
    async def test_error_reporting_workflow(self):
        """Test the error reporting workflow"""
        config = VerifierConfig()
        overseer = Overseer(config)
        
        mock_reports = [
            {
                'file': 'test.py',
                'line': 10,
                'severity': 'high',
                'description': 'Test error',
                'suggested_fix': 'Fix it',
                'timestamp': '2024-01-01T00:00:00Z'
            },
            {
                'file': 'other.py',
                'line': 20,
                'severity': 'medium',
                'description': 'Another error',
                'suggested_fix': 'Fix this too',
                'timestamp': '2024-01-01T00:01:00Z'
            }
        ]
        
        with patch.object(overseer.report_monitor, 'has_new_reports', return_value=True):
            with patch.object(overseer.report_monitor, 'get_new_reports', return_value=mock_reports):
                with patch.object(overseer, '_display_error_report') as mock_display:
                    overseer._process_error_reports()
                    
                    # Should display both reports
                    assert mock_display.call_count == 2
                    mock_display.assert_any_call(mock_reports[0])
                    mock_display.assert_any_call(mock_reports[1])
                    
    @patch('core.overseer.overseer.FilesystemWatcher')
    async def test_multiple_watchers(self, mock_watcher_class):
        """Test overseer with multiple watch directories"""
        with tempfile.TemporaryDirectory() as temp_dir1:
            with tempfile.TemporaryDirectory() as temp_dir2:
                config = VerifierConfig(
                    watch_dirs=[temp_dir1, temp_dir2],
                    working_set_dir=temp_dir1 + '/working_set'
                )
                overseer = Overseer(config)
                
                # Mock watchers
                mock_watcher1 = Mock()
                mock_watcher2 = Mock()
                mock_watcher_class.side_effect = [mock_watcher1, mock_watcher2]
                
                # Setup watchers
                overseer._setup_watchers()
                
                # Should create two watchers
                assert len(overseer.watchers) == 2
                assert mock_watcher_class.call_count == 2
                
                # Mock agent sessions
                with patch.object(overseer.agent, 'start_session') as mock_agent_start:
                    with patch.object(overseer.doc_agent, 'start_session') as mock_doc_start:
                        with patch.object(overseer.agent, 'stop_session') as mock_agent_stop:
                            with patch.object(overseer.doc_agent, 'stop_session') as mock_doc_stop:
                                mock_agent_start.return_value = asyncio.Future()
                                mock_agent_start.return_value.set_result(None)
                                mock_doc_start.return_value = asyncio.Future()
                                mock_doc_start.return_value.set_result(None)
                                
                                # Start overseer
                                start_task = asyncio.create_task(overseer.start())
                                
                                # Wait a bit for startup
                                await asyncio.sleep(0.1)
                                
                                # Both watchers should be started
                                mock_watcher1.start.assert_called_once()
                                mock_watcher2.start.assert_called_once()
                                
                                # Stop overseer
                                await overseer.stop()
                                
                                # Both watchers should be stopped
                                mock_watcher1.stop.assert_called_once()
                                mock_watcher2.stop.assert_called_once()
                                
                                # Cancel the start task
                                start_task.cancel()
                                try:
                                    await start_task
                                except asyncio.CancelledError:
                                    pass


class TestOverseerConfiguration:
    """Test overseer configuration handling"""
    
    def test_overseer_respects_config_settings(self):
        """Test that overseer respects various configuration settings"""
        config = VerifierConfig(
            watch_dirs=['src', 'lib', 'tests'],
            working_set_dir='custom/working/set',
            error_report_file='custom/errors.jsonl',
            agent_mission='docs'
        )
        overseer = Overseer(config)
        
        assert overseer.config.watch_dirs == ['src', 'lib', 'tests']
        assert overseer.config.working_set_dir == 'custom/working/set'
        assert overseer.config.error_report_file == 'custom/errors.jsonl'
        assert overseer.config.agent_mission == 'docs'
        
    async def test_overseer_working_set_initialization(self):
        """Test that overseer initializes working set correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(working_set_dir=temp_dir)
            overseer = Overseer(config)
            
            with patch.object(overseer.working_set, 'ensure_directory_structure') as mock_ensure:
                with patch.object(overseer.agent, 'start_session') as mock_agent_start:
                    with patch.object(overseer.doc_agent, 'start_session') as mock_doc_start:
                        mock_agent_start.return_value = asyncio.Future()
                        mock_agent_start.return_value.set_result(None)
                        mock_doc_start.return_value = asyncio.Future()
                        mock_doc_start.return_value.set_result(None)
                        
                        # Start overseer
                        start_task = asyncio.create_task(overseer.start())
                        
                        # Wait a bit for startup
                        await asyncio.sleep(0.1)
                        
                        # Should initialize working set
                        mock_ensure.assert_called_once()
                        
                        # Stop overseer
                        await overseer.stop()
                        
                        # Cancel the start task
                        start_task.cancel()
                        try:
                            await start_task
                        except asyncio.CancelledError:
                            pass


if __name__ == '__main__':
    pytest.main([__file__])