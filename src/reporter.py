#!/usr/bin/env python3
"""Compatibility shim for reporter imports"""

# Re-export reporter classes from their new locations
from core.review.reporter import ErrorReporter, ReportMonitor

# Create ReportMonitor as an alias or simple wrapper
class ReportMonitor:
    """Report monitor compatibility class"""
    
    def __init__(self, report_file):
        self.report_file = report_file
        self._last_check = 0
    
    def has_new_reports(self):
        """Check if there are new reports"""
        try:
            from pathlib import Path
            report_path = Path(self.report_file)
            if report_path.exists():
                current_mtime = report_path.stat().st_mtime
                if current_mtime > self._last_check:
                    return True
            return False
        except:
            return False
    
    def get_new_reports(self):
        """Get new reports"""
        try:
            from pathlib import Path
            import json
            report_path = Path(self.report_file)
            if report_path.exists():
                self._last_check = report_path.stat().st_mtime
                with open(report_path, 'r') as f:
                    return [json.loads(line) for line in f if line.strip()]
            return []
        except:
            return []

__all__ = ['ErrorReporter', 'ReportMonitor'] 