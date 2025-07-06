#!/usr/bin/env python3
"""Unit tests for the reporter module"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from src.reporter import ErrorReporter, ReportMonitor


class TestErrorReporter:
    """Test the ErrorReporter class"""
    
    def test_error_reporter_creation(self):
        """Test creating an ErrorReporter instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            assert reporter.report_file == report_file
            assert reporter.report_file.parent.exists()
            
    def test_error_reporter_creates_directory(self):
        """Test that ErrorReporter creates parent directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "nested" / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            assert reporter.report_file.parent.exists()
            
    def test_report_error_basic(self):
        """Test reporting a basic error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            reporter.report_error(
                file_path="test.py",
                line=42,
                severity="high",
                description="Test error",
                suggested_fix="Fix it"
            )
            
            assert report_file.exists()
            
            # Read the report
            with open(report_file, 'r') as f:
                line = f.readline().strip()
                report = json.loads(line)
                
            assert report["file"] == "test.py"
            assert report["line"] == 42
            assert report["severity"] == "high"
            assert report["description"] == "Test error"
            assert report["suggested_fix"] == "Fix it"
            assert "timestamp" in report
            
    def test_report_error_without_line(self):
        """Test reporting an error without line number"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            reporter.report_error(
                file_path="test.py",
                line=None,
                severity="medium",
                description="General error"
            )
            
            with open(report_file, 'r') as f:
                line = f.readline().strip()
                report = json.loads(line)
                
            assert report["line"] is None
            assert report["suggested_fix"] is None
            
    def test_report_multiple_errors(self):
        """Test reporting multiple errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            reporter.report_error("test1.py", 10, "high", "Error 1")
            reporter.report_error("test2.py", 20, "low", "Error 2")
            
            with open(report_file, 'r') as f:
                lines = f.readlines()
                
            assert len(lines) == 2
            
            report1 = json.loads(lines[0].strip())
            report2 = json.loads(lines[1].strip())
            
            assert report1["file"] == "test1.py"
            assert report1["line"] == 10
            assert report2["file"] == "test2.py"
            assert report2["line"] == 20
            
    def test_get_pending_reports_empty(self):
        """Test getting pending reports when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            reports = reporter.get_pending_reports()
            assert reports == []
            
    def test_get_pending_reports(self):
        """Test getting pending reports"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            # Add some reports
            reporter.report_error("test1.py", 10, "high", "Error 1")
            reporter.report_error("test2.py", 20, "low", "Error 2")
            
            reports = reporter.get_pending_reports()
            assert len(reports) == 2
            assert reports[0]["file"] == "test1.py"
            assert reports[1]["file"] == "test2.py"
            
    def test_get_pending_reports_malformed(self):
        """Test getting pending reports with malformed JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            # Write malformed JSON
            with open(report_file, 'w') as f:
                f.write('{"valid": true}\n')
                f.write('invalid json\n')
                f.write('{"also_valid": true}\n')
                
            reports = reporter.get_pending_reports()
            # Should handle the error gracefully
            assert isinstance(reports, list)
            
    def test_clear_reports(self):
        """Test clearing all reports"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            # Add a report
            reporter.report_error("test.py", 10, "high", "Error")
            assert report_file.exists()
            
            # Clear reports
            reporter.clear_reports()
            assert not report_file.exists()
            
    def test_clear_reports_nonexistent(self):
        """Test clearing reports when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            # Should not raise error
            reporter.clear_reports()
            
    def test_pop_report(self):
        """Test popping a report from the file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            # Add reports
            reporter.report_error("test1.py", 10, "high", "Error 1")
            reporter.report_error("test2.py", 20, "low", "Error 2")
            
            # Pop first report
            report = reporter.pop_report()
            assert report["file"] == "test1.py"
            
            # Check remaining reports
            remaining = reporter.get_pending_reports()
            assert len(remaining) == 1
            assert remaining[0]["file"] == "test2.py"
            
    def test_pop_report_empty(self):
        """Test popping a report when file is empty"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            report = reporter.pop_report()
            assert report is None
            
    def test_pop_report_last_one(self):
        """Test popping the last report"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            # Add one report
            reporter.report_error("test.py", 10, "high", "Error")
            
            # Pop the report
            report = reporter.pop_report()
            assert report["file"] == "test.py"
            
            # File should be deleted
            assert not report_file.exists()
            
    def test_timestamp_format(self):
        """Test that timestamps are in ISO format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            reporter = ErrorReporter(str(report_file))
            
            reporter.report_error("test.py", 10, "high", "Error")
            
            reports = reporter.get_pending_reports()
            timestamp = reports[0]["timestamp"]
            
            # Should be able to parse as ISO format
            parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            assert parsed.tzinfo is not None


class TestReportMonitor:
    """Test the ReportMonitor class"""
    
    def test_report_monitor_creation(self):
        """Test creating a ReportMonitor instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            monitor = ReportMonitor(str(report_file))
            
            assert monitor.report_file == report_file
            assert isinstance(monitor.reporter, ErrorReporter)
            assert monitor.last_modified == 0
            
    def test_has_new_reports_nonexistent(self):
        """Test checking for new reports when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            monitor = ReportMonitor(str(report_file))
            
            assert monitor.has_new_reports() is False
            
    def test_has_new_reports_no_changes(self):
        """Test checking for new reports when file hasn't changed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            monitor = ReportMonitor(str(report_file))
            
            # Create file
            report_file.touch()
            
            # First check should return True
            assert monitor.has_new_reports() is True
            
            # Second check should return False (no changes)
            assert monitor.has_new_reports() is False
            
    def test_has_new_reports_with_changes(self):
        """Test checking for new reports when file has changed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            monitor = ReportMonitor(str(report_file))
            
            # Create file
            report_file.touch()
            monitor.has_new_reports()  # Initialize last_modified
            
            # Modify file
            time.sleep(0.1)  # Ensure different timestamp
            with open(report_file, 'w') as f:
                f.write('{"test": true}\n')
                
            assert monitor.has_new_reports() is True
            
    def test_get_new_reports(self):
        """Test getting new reports"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            monitor = ReportMonitor(str(report_file))
            
            # Add reports using the reporter
            monitor.reporter.report_error("test1.py", 10, "high", "Error 1")
            monitor.reporter.report_error("test2.py", 20, "low", "Error 2")
            
            # Get new reports
            reports = monitor.get_new_reports()
            
            assert len(reports) == 2
            assert reports[0]["file"] == "test1.py"
            assert reports[1]["file"] == "test2.py"
            
            # File should be empty after getting reports
            assert not report_file.exists()
            
    def test_get_new_reports_empty(self):
        """Test getting new reports when there are none"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            monitor = ReportMonitor(str(report_file))
            
            reports = monitor.get_new_reports()
            assert reports == []
            
    def test_get_new_reports_processes_all(self):
        """Test that get_new_reports processes all reports"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "errors.jsonl"
            monitor = ReportMonitor(str(report_file))
            
            # Add multiple reports
            for i in range(5):
                monitor.reporter.report_error(f"test{i}.py", i * 10, "high", f"Error {i}")
                
            # Get all reports
            reports = monitor.get_new_reports()
            
            assert len(reports) == 5
            for i, report in enumerate(reports):
                assert report["file"] == f"test{i}.py"
                assert report["line"] == i * 10
                
            # File should be empty
            assert not report_file.exists()


if __name__ == '__main__':
    pytest.main([__file__])