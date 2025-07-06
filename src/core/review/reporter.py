import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


class ErrorReporter:
    """Handles error reporting to JSONL files"""
    
    def __init__(self, report_file: str):
        self.report_file = Path(report_file)
        self.report_file.parent.mkdir(parents=True, exist_ok=True)
        
    def report_error(self, file_path: str, line: Optional[int], severity: str, 
                    description: str, suggested_fix: Optional[str] = None):
        """Report an error to the JSONL file"""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "file": file_path,
            "line": line,
            "severity": severity,
            "description": description,
            "suggested_fix": suggested_fix
        }
        
        with open(self.report_file, 'a') as f:
            f.write(json.dumps(report) + '\n')
            
    def get_pending_reports(self) -> List[Dict[str, Any]]:
        """Get all pending error reports"""
        if not self.report_file.exists():
            return []
            
        reports = []
        try:
            with open(self.report_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        reports.append(json.loads(line))
        except Exception as e:
            print(f"Error reading reports: {e}")
            
        return reports
        
    def clear_reports(self):
        """Clear all reports (used by overseer after processing)"""
        if self.report_file.exists():
            self.report_file.unlink()
            
    def pop_report(self) -> Optional[Dict[str, Any]]:
        """Pop the first report from the file"""
        reports = self.get_pending_reports()
        if not reports:
            return None
            
        # Get the first report
        first_report = reports[0]
        remaining_reports = reports[1:]
        
        # Rewrite the file with remaining reports
        if remaining_reports:
            with open(self.report_file, 'w') as f:
                for report in remaining_reports:
                    f.write(json.dumps(report) + '\n')
        else:
            self.clear_reports()
            
        return first_report


class ReportMonitor:
    """Monitors the error report file for changes"""
    
    def __init__(self, report_file: str):
        self.report_file = Path(report_file)
        self.reporter = ErrorReporter(report_file)
        self.last_modified = 0
        
    def has_new_reports(self) -> bool:
        """Check if there are new reports since last check"""
        if not self.report_file.exists():
            return False
            
        current_modified = self.report_file.stat().st_mtime
        if current_modified > self.last_modified:
            self.last_modified = current_modified
            return True
            
        return False
        
    def get_new_reports(self) -> List[Dict[str, Any]]:
        """Get new reports and mark them as processed"""
        reports = []
        
        while True:
            report = self.reporter.pop_report()
            if report is None:
                break
            reports.append(report)
            
        return reports