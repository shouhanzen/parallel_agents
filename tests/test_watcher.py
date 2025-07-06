#!/usr/bin/env python3
"""Unit tests for the watcher module"""

import pytest
import tempfile
import time
import threading
from pathlib import Path
from src.watcher import FilesystemWatcher, FileChangeHandler


class TestFileChangeHandler:
    """Test the FileChangeHandler class"""
    
    def test_file_change_handler_creation(self):
        """Test creating a FileChangeHandler instance"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        handler = FileChangeHandler(callback)
        
        assert handler.callback == callback
        assert '.py' in handler.watch_extensions
        assert '.js' in handler.watch_extensions
        
    def test_file_change_handler_custom_extensions(self):
        """Test creating handler with custom extensions"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        custom_extensions = {'.py', '.md'}
        handler = FileChangeHandler(callback, custom_extensions)
        
        assert handler.watch_extensions == custom_extensions
        
    def test_should_process_file(self):
        """Test file extension filtering"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        handler = FileChangeHandler(callback)
        
        # Should process these files
        assert handler._should_process_file("test.py")
        assert handler._should_process_file("app.js")
        assert handler._should_process_file("component.tsx")
        assert handler._should_process_file("main.cpp")
        
        # Should not process these files
        assert not handler._should_process_file("test.txt")
        assert not handler._should_process_file("image.png")
        assert not handler._should_process_file("data.csv")
        
    def test_should_process_file_case_insensitive(self):
        """Test that file extension check is case insensitive"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        handler = FileChangeHandler(callback)
        
        assert handler._should_process_file("test.PY")
        assert handler._should_process_file("app.JS")
        assert handler._should_process_file("component.TSX")


class TestFilesystemWatcher:
    """Test the FilesystemWatcher class"""
    
    def test_filesystem_watcher_creation(self):
        """Test creating a FilesystemWatcher instance"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, callback)
            
            assert watcher.watch_dir == Path(temp_dir)
            assert watcher.callback == callback
            assert watcher.observer is not None
            assert watcher.handler is not None
            
    def test_filesystem_watcher_nonexistent_directory(self):
        """Test creating watcher for non-existent directory"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        watcher = FilesystemWatcher("/nonexistent/directory", callback)
        
        with pytest.raises(FileNotFoundError):
            watcher.start()
            
    def test_filesystem_watcher_start_stop(self):
        """Test starting and stopping the watcher"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, callback)
            
            # Start watcher
            watcher.start()
            assert watcher.is_alive()
            
            # Stop watcher
            watcher.stop()
            assert not watcher.is_alive()
            
    def test_filesystem_watcher_detects_file_creation(self):
        """Test that watcher detects file creation"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, callback)
            watcher.start()
            
            try:
                # Create a file
                test_file = Path(temp_dir) / "test.py"
                test_file.write_text("print('hello')")
                
                # Wait for the event to be processed
                time.sleep(0.5)
                
                # Check if change was detected
                assert len(changes) > 0
                
                # Find the creation event
                creation_events = [c for c in changes if c[1] == 'created']
                assert len(creation_events) > 0
                
                # Check that the file path is correct
                event_path = creation_events[0][0]
                assert Path(event_path).name == "test.py"
                
            finally:
                watcher.stop()
                
    def test_filesystem_watcher_detects_file_modification(self):
        """Test that watcher detects file modification"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file first
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")
            
            # Start watcher
            watcher = FilesystemWatcher(temp_dir, callback)
            watcher.start()
            
            try:
                # Modify the file
                test_file.write_text("print('hello world')")
                
                # Wait for the event to be processed
                time.sleep(0.5)
                
                # Check if change was detected
                assert len(changes) > 0
                
                # Find the modification event
                modification_events = [c for c in changes if c[1] == 'modified']
                assert len(modification_events) > 0
                
                # Check that the file path is correct
                event_path = modification_events[0][0]
                assert Path(event_path).name == "test.py"
                
            finally:
                watcher.stop()
                
    def test_filesystem_watcher_detects_file_deletion(self):
        """Test that watcher detects file deletion"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file first
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")
            
            # Start watcher
            watcher = FilesystemWatcher(temp_dir, callback)
            watcher.start()
            
            try:
                # Delete the file
                test_file.unlink()
                
                # Wait for the event to be processed
                time.sleep(0.5)
                
                # Check if change was detected
                assert len(changes) > 0
                
                # Find the deletion event
                deletion_events = [c for c in changes if c[1] == 'deleted']
                assert len(deletion_events) > 0
                
                # Check that the file path is correct
                event_path = deletion_events[0][0]
                assert Path(event_path).name == "test.py"
                
            finally:
                watcher.stop()
                
    def test_filesystem_watcher_ignores_unwatched_extensions(self):
        """Test that watcher ignores files with unwatched extensions"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, callback)
            watcher.start()
            
            try:
                # Create a file with unwatched extension
                test_file = Path(temp_dir) / "test.txt"
                test_file.write_text("some text")
                
                # Wait for potential event processing
                time.sleep(0.5)
                
                # Should not detect any changes
                assert len(changes) == 0
                
            finally:
                watcher.stop()
                
    def test_filesystem_watcher_recursive(self):
        """Test that watcher detects changes in subdirectories"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a subdirectory
            subdir = Path(temp_dir) / "subdir"
            subdir.mkdir()
            
            watcher = FilesystemWatcher(temp_dir, callback)
            watcher.start()
            
            try:
                # Create a file in the subdirectory
                test_file = subdir / "test.py"
                test_file.write_text("print('hello')")
                
                # Wait for the event to be processed
                time.sleep(0.5)
                
                # Check if change was detected
                assert len(changes) > 0
                
                # Find the creation event
                creation_events = [c for c in changes if c[1] == 'created']
                assert len(creation_events) > 0
                
                # Check that the file path includes the subdirectory
                event_path = creation_events[0][0]
                assert "subdir" in event_path
                assert Path(event_path).name == "test.py"
                
            finally:
                watcher.stop()
                
    def test_filesystem_watcher_ignores_directories(self):
        """Test that watcher ignores directory events"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, callback)
            watcher.start()
            
            try:
                # Create a directory
                new_dir = Path(temp_dir) / "new_directory"
                new_dir.mkdir()
                
                # Wait for potential event processing
                time.sleep(0.5)
                
                # Should not detect directory creation
                assert len(changes) == 0
                
            finally:
                watcher.stop()
                
    def test_filesystem_watcher_multiple_files(self):
        """Test that watcher detects changes to multiple files"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, callback)
            watcher.start()
            
            try:
                # Create multiple files
                for i in range(3):
                    test_file = Path(temp_dir) / f"test{i}.py"
                    test_file.write_text(f"print('hello {i}')")
                    
                # Wait for events to be processed
                time.sleep(0.5)
                
                # Should detect all file creations
                assert len(changes) >= 3
                
                # Check that all files were detected
                created_files = [Path(c[0]).name for c in changes if c[1] == 'created']
                assert "test0.py" in created_files
                assert "test1.py" in created_files
                assert "test2.py" in created_files
                
            finally:
                watcher.stop()


class TestWatcherIntegration:
    """Integration tests for the watcher module"""
    
    def test_watcher_with_rapid_changes(self):
        """Test watcher behavior with rapid file changes"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, callback)
            watcher.start()
            
            try:
                test_file = Path(temp_dir) / "test.py"
                
                # Make rapid changes
                for i in range(5):
                    test_file.write_text(f"print('version {i}')")
                    time.sleep(0.1)
                    
                # Wait for all events to be processed
                time.sleep(1.0)
                
                # Should detect at least some changes
                assert len(changes) > 0
                
                # Should include both creation and modification events
                actions = [c[1] for c in changes]
                assert 'created' in actions or 'modified' in actions
                
            finally:
                watcher.stop()
                
    def test_watcher_thread_safety(self):
        """Test that watcher is thread-safe"""
        changes = []
        
        def callback(file_path, action):
            changes.append((file_path, action))
            
        def create_files(temp_dir, start_idx, count):
            for i in range(count):
                test_file = Path(temp_dir) / f"test{start_idx + i}.py"
                test_file.write_text(f"print('hello {start_idx + i}')")
                time.sleep(0.01)
                
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = FilesystemWatcher(temp_dir, callback)
            watcher.start()
            
            try:
                # Create files from multiple threads
                threads = []
                for i in range(3):
                    thread = threading.Thread(target=create_files, args=(temp_dir, i * 5, 5))
                    threads.append(thread)
                    thread.start()
                    
                # Wait for all threads to complete
                for thread in threads:
                    thread.join()
                    
                # Wait for all events to be processed
                time.sleep(1.0)
                
                # Should detect all file creations
                assert len(changes) >= 15  # 3 threads * 5 files each
                
            finally:
                watcher.stop()


if __name__ == '__main__':
    pytest.main([__file__])