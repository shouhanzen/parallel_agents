#!/usr/bin/env python3
"""Unit tests for the delta gate module"""

import pytest
import tempfile
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.monitoring.delta_gate import DeltaGate, DeltaGateConfig, FileChange


class TestFileChange:
    """Test the FileChange dataclass"""
    
    def test_file_change_creation(self):
        """Test creating a FileChange instance"""
        change = FileChange(
            file_path="/test/file.py",
            action="modified",
            timestamp=1234567890.0,
            size=1024
        )
        
        assert change.file_path == "/test/file.py"
        assert change.action == "modified"
        assert change.timestamp == 1234567890.0
        assert change.size == 1024
        
    def test_file_change_without_size(self):
        """Test creating a FileChange without size"""
        change = FileChange(
            file_path="/test/file.py",
            action="deleted",
            timestamp=1234567890.0
        )
        
        assert change.file_path == "/test/file.py"
        assert change.action == "deleted"
        assert change.timestamp == 1234567890.0
        assert change.size is None


class TestDeltaGateConfig:
    """Test the DeltaGateConfig class"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = DeltaGateConfig()
        
        assert config.min_change_interval == 0.5
        assert config.batch_timeout == 2.0
        assert config.min_file_size == 1
        assert config.max_file_size == 1024 * 1024
        assert '*.pyc' in config.ignore_patterns
        assert '__pycache__' in config.ignore_patterns
        assert '.git' in config.ignore_patterns
        
    def test_custom_config(self):
        """Test creating config with custom values"""
        config = DeltaGateConfig(
            min_change_interval=1.0,
            batch_timeout=5.0,
            min_file_size=10,
            max_file_size=2048,
            ignore_patterns={'*.log', '*.tmp'}
        )
        
        assert config.min_change_interval == 1.0
        assert config.batch_timeout == 5.0
        assert config.min_file_size == 10
        assert config.max_file_size == 2048
        assert config.ignore_patterns == {'*.log', '*.tmp'}


class TestDeltaGate:
    """Test the DeltaGate class"""
    
    def test_delta_gate_creation(self):
        """Test creating a DeltaGate instance"""
        gate = DeltaGate()
        
        assert gate.config is not None
        assert gate.pending_changes == {}
        assert gate.last_processing_time == 0
        assert gate.batch_start_time == 0
        
    def test_delta_gate_with_custom_config(self):
        """Test creating DeltaGate with custom config"""
        config = DeltaGateConfig(min_change_interval=1.0)
        gate = DeltaGate(config)
        
        assert gate.config.min_change_interval == 1.0
        
    def test_should_ignore_file_patterns(self):
        """Test file ignore patterns"""
        gate = DeltaGate()
        
        # Should ignore these files
        assert gate._should_ignore_file("test.pyc")
        assert gate._should_ignore_file("path/__pycache__/test.py")  # __pycache__ in path
        assert gate._should_ignore_file(".git/config")
        assert gate._should_ignore_file("app.log")
        assert gate._should_ignore_file("temp.tmp")
        assert gate._should_ignore_file(".DS_Store")
        
        # Should not ignore these files
        assert not gate._should_ignore_file("test.py")
        assert not gate._should_ignore_file("app.js")
        assert not gate._should_ignore_file("README.md")
        
    def test_should_ignore_hidden_files(self):
        """Test that hidden files are ignored"""
        gate = DeltaGate()
        
        assert gate._should_ignore_file(".hidden")
        assert gate._should_ignore_file("dir/.hidden")
        assert gate._should_ignore_file("path/to/.hidden")
        
    def test_get_file_size(self):
        """Test getting file size"""
        gate = DeltaGate()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name
            
        try:
            size = gate._get_file_size(temp_file)
            assert size is not None
            assert size > 0
        finally:
            Path(temp_file).unlink()
            
        # Test with non-existent file
        size = gate._get_file_size("/nonexistent/file.txt")
        assert size is None
        
    def test_add_change_valid_file(self):
        """Test adding a valid file change"""
        gate = DeltaGate()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')")
            temp_file = f.name
            
        try:
            result = gate.add_change(temp_file, "modified")
            assert result is True
            assert len(gate.pending_changes) == 1
            assert temp_file in gate.pending_changes
        finally:
            Path(temp_file).unlink()
            
    def test_add_change_ignored_file(self):
        """Test adding a change for an ignored file"""
        gate = DeltaGate()
        
        result = gate.add_change("test.pyc", "modified")
        assert result is False
        assert len(gate.pending_changes) == 0
        
    def test_add_change_file_too_large(self):
        """Test adding a change for a file that's too large"""
        config = DeltaGateConfig(max_file_size=10)  # Very small limit
        gate = DeltaGate(config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x" * 100)  # Write more than the limit
            temp_file = f.name
            
        try:
            result = gate.add_change(temp_file, "modified")
            assert result is False
            assert len(gate.pending_changes) == 0
        finally:
            Path(temp_file).unlink()
            
    def test_add_change_file_too_small(self):
        """Test adding a change for a file that's too small"""
        config = DeltaGateConfig(min_file_size=100)  # Large minimum
        gate = DeltaGate(config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x")  # Write less than the minimum
            temp_file = f.name
            
        try:
            result = gate.add_change(temp_file, "modified")
            assert result is False
            assert len(gate.pending_changes) == 0
        finally:
            Path(temp_file).unlink()
            
    def test_add_change_deleted_file(self):
        """Test adding a change for a deleted file"""
        gate = DeltaGate()
        
        result = gate.add_change("/tmp/deleted.py", "deleted")
        assert result is True
        assert len(gate.pending_changes) == 1
        
    def test_add_multiple_changes_same_file(self):
        """Test adding multiple changes for the same file"""
        gate = DeltaGate()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')")
            temp_file = f.name
            
        try:
            gate.add_change(temp_file, "created")
            gate.add_change(temp_file, "modified")
            
            # Should only have one entry (the latest)
            assert len(gate.pending_changes) == 1
            assert gate.pending_changes[temp_file].action == "modified"
        finally:
            Path(temp_file).unlink()
            
    def test_get_pending_count(self):
        """Test getting pending changes count"""
        gate = DeltaGate()
        
        assert gate.get_pending_count() == 0
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("test")
            temp_file = f.name
            
        try:
            gate.add_change(temp_file, "modified")
            assert gate.get_pending_count() == 1
        finally:
            Path(temp_file).unlink()
            
    def test_clear_pending(self):
        """Test clearing pending changes"""
        gate = DeltaGate()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("test")
            temp_file = f.name
            
        try:
            gate.add_change(temp_file, "modified")
            assert gate.get_pending_count() == 1
            
            gate.clear_pending()
            assert gate.get_pending_count() == 0
            assert gate.batch_start_time == 0
        finally:
            Path(temp_file).unlink()
            
    def test_should_process_batch_no_changes(self):
        """Test batch processing with no changes"""
        gate = DeltaGate()
        
        assert gate.should_process_batch() is False
        
    def test_should_process_batch_timeout(self):
        """Test batch processing with timeout"""
        config = DeltaGateConfig(batch_timeout=0.1)
        gate = DeltaGate(config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("test")
            temp_file = f.name
            
        try:
            gate.add_change(temp_file, "modified")
            
            # Should not process immediately
            assert gate.should_process_batch() is False
            
            # Wait for timeout
            time.sleep(0.2)
            assert gate.should_process_batch() is True
        finally:
            Path(temp_file).unlink()
            
    def test_should_process_batch_min_interval(self):
        """Test batch processing with minimum interval"""
        config = DeltaGateConfig(min_change_interval=0.1, batch_timeout=0.05)
        gate = DeltaGate(config)
        
        # Set last processing time to recent
        gate.last_processing_time = time.time()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("test")
            temp_file = f.name
            
        try:
            gate.add_change(temp_file, "modified")
            
            # Should not process due to minimum interval
            assert gate.should_process_batch() is False
            
            # Wait for minimum interval
            time.sleep(0.15)
            assert gate.should_process_batch() is True
        finally:
            Path(temp_file).unlink()
            
    def test_get_batch(self):
        """Test getting a batch of changes"""
        gate = DeltaGate()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
            f1.write("test1")
            temp_file1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f2:
            f2.write("test2")
            temp_file2 = f2.name
            
        try:
            gate.add_change(temp_file1, "modified")
            gate.add_change(temp_file2, "created")
            
            batch = gate.get_batch()
            
            assert len(batch) == 2
            assert gate.get_pending_count() == 0
            assert gate.last_processing_time > 0
            assert gate.batch_start_time == 0
            
            # Check batch content
            file_paths = [change['file_path'] for change in batch]
            assert temp_file1 in file_paths
            assert temp_file2 in file_paths
            
        finally:
            Path(temp_file1).unlink()
            Path(temp_file2).unlink()
            
    def test_get_batch_empty(self):
        """Test getting a batch when there are no changes"""
        gate = DeltaGate()
        
        batch = gate.get_batch()
        assert batch == []


if __name__ == '__main__':
    pytest.main([__file__])