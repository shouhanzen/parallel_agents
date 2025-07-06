#!/usr/bin/env python3
"""Basic test of the verifier system components"""

import tempfile
import time
from pathlib import Path
from src.watcher import FilesystemWatcher
from src.delta_gate import DeltaGate
from src.config import VerifierConfig
from src.reporter import ErrorReporter
from src.working_set import WorkingSetManager


def test_filesystem_watcher():
    """Test the filesystem watcher"""
    print("Testing filesystem watcher...")
    
    changes = []
    
    def on_change(file_path, action):
        changes.append((file_path, action))
        print(f"Change detected: {action} {file_path}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        watcher = FilesystemWatcher(temp_dir, on_change)
        watcher.start()
        
        # Create a test file
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("print('hello')")
        
        # Wait a bit for the change to be detected
        time.sleep(0.5)
        
        # Modify the file
        test_file.write_text("print('hello world')")
        time.sleep(0.5)
        
        watcher.stop()
        
        print(f"Detected {len(changes)} changes")
        return len(changes) > 0


def test_delta_gate():
    """Test the delta gate"""
    print("Testing delta gate...")
    
    gate = DeltaGate()
    
    # Add some changes
    gate.add_change("/tmp/test.py", "created")
    gate.add_change("/tmp/test.pyc", "created")  # Should be ignored
    gate.add_change("/tmp/test.js", "modified")
    
    print(f"Pending changes: {gate.get_pending_count()}")
    
    # Force processing
    gate.batch_start_time = time.time() - 3.0  # Make it seem like enough time has passed
    
    if gate.should_process_batch():
        batch = gate.get_batch()
        print(f"Batch size: {len(batch)}")
        return len(batch) > 0
    
    return False


def test_error_reporter():
    """Test the error reporter"""
    print("Testing error reporter...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        report_file = Path(temp_dir) / "errors.jsonl"
        reporter = ErrorReporter(str(report_file))
        
        # Report an error
        reporter.report_error(
            file_path="/tmp/test.py",
            line=42,
            severity="high",
            description="Test error",
            suggested_fix="Fix the test"
        )
        
        # Check if error was reported
        reports = reporter.get_pending_reports()
        print(f"Pending reports: {len(reports)}")
        
        if reports:
            print(f"First report: {reports[0]}")
            
        return len(reports) > 0


def test_working_set():
    """Test the working set manager"""
    print("Testing working set manager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = WorkingSetManager(temp_dir)
        manager.ensure_directory_structure()
        
        # Create a test file
        test_file = manager.create_test_file("test_sample", "def test_example(): pass")
        print(f"Created test file: {test_file}")
        
        # List test files
        test_files = manager.list_test_files()
        print(f"Test files: {test_files}")
        
        return len(test_files) > 0


def test_config():
    """Test the configuration system"""
    print("Testing configuration...")
    
    config = VerifierConfig()
    print(f"Default config: {config.model_dump()}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "test_config.json"
        config.to_file(str(config_file))
        
        # Load it back
        loaded_config = VerifierConfig.from_file(str(config_file))
        print(f"Loaded config: {loaded_config.model_dump()}")
        
        return config.model_dump() == loaded_config.model_dump()


def main():
    """Run all tests"""
    print("Running basic verifier tests...\n")
    
    tests = [
        test_config,
        test_delta_gate,
        test_error_reporter,
        test_working_set,
        test_filesystem_watcher,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                print(f"✓ {test.__name__} passed")
                passed += 1
            else:
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! 🎉")
    else:
        print("Some tests failed 😞")


if __name__ == "__main__":
    main()