import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any
from ..config.models import VerifierConfig
from core.monitoring.watcher import FilesystemWatcher
from core.agents.mock.agent import MockVerifierAgent as VerifierAgent
from core.agents.mock.agent import MockVerifierAgent as DocumentationAgent
from core.review.reporter import ReportMonitor
from ..monitoring.delta_gate import DeltaGate, DeltaGateConfig
from ..monitoring.working_set import WorkingSetManager


class Overseer:
    """Main overseer process that coordinates all components"""
    
    def __init__(self, config: VerifierConfig):
        self.config = config
        self.agent = VerifierAgent(config)
        self.doc_agent = DocumentationAgent(config)
        self.watchers: List[FilesystemWatcher] = []
        self.report_monitor = ReportMonitor(config.error_report_file)
        self.delta_gate = DeltaGate(DeltaGateConfig())
        self.working_set = WorkingSetManager(config.working_set_dir)
        self.running = False
        
    def _on_file_change(self, file_path: str, action: str):
        """Handle file system changes"""
        if self.delta_gate.add_change(file_path, action):
            print(f"File change detected: {action} {file_path}")
        else:
            print(f"File change ignored: {action} {file_path}")
        
    def _setup_watchers(self):
        """Setup filesystem watchers for configured directories"""
        for watch_dir in self.config.watch_dirs:
            if Path(watch_dir).exists():
                watcher = FilesystemWatcher(watch_dir, self._on_file_change)
                self.watchers.append(watcher)
                print(f"Watching directory: {watch_dir}")
            else:
                print(f"Warning: Watch directory does not exist: {watch_dir}")

        
    async def _process_pending_changes(self):
        """Process any pending file changes"""
        if self.delta_gate.should_process_batch():
            batch = self.delta_gate.get_batch()
            if batch:
                # Process changes with both agents in parallel
                await asyncio.gather(
                    self.agent.process_file_changes(batch),
                    self.doc_agent.process_file_changes(batch)
                )
                print(f"Processed batch of {len(batch)} changes with both agents")
            
    def _process_error_reports(self):
        """Process any new error reports"""
        if self.report_monitor.has_new_reports():
            reports = self.report_monitor.get_new_reports()
            for report in reports:
                self._display_error_report(report)
                
    def _display_error_report(self, report: Dict[str, Any]):
        """Display an error report to the user"""
        severity_colors = {
            'high': '\033[91m',    # Red
            'medium': '\033[93m',  # Yellow
            'low': '\033[94m',     # Blue
        }
        reset_color = '\033[0m'
        
        color = severity_colors.get(report['severity'], '')
        
        print(f"\n{color}🚨 ERROR REPORT ({report['severity'].upper()}){reset_color}")
        print(f"File: {report['file']}")
        if report['line']:
            print(f"Line: {report['line']}")
        print(f"Description: {report['description']}")
        if report['suggested_fix']:
            print(f"Suggested Fix: {report['suggested_fix']}")
        print(f"Timestamp: {report['timestamp']}")
        print("-" * 50)
        
    async def start(self):
        """Start the overseer process"""
        print("Starting Verifier Overseer...")
        print(f"Configuration: {self.config.model_dump()}")
        
        # Setup components
        self._setup_watchers()
        
        # Initialize working set
        self.working_set.ensure_directory_structure()
        
        # Start watchers
        for watcher in self.watchers:
            watcher.start()
            
        # Start both agent sessions in parallel
        await asyncio.gather(
            self.agent.start_session(),
            self.doc_agent.start_session()
        )
        
        self.running = True
        print("Overseer started. Monitoring for changes...")
        
        # Main loop
        try:
            while self.running:
                # Process pending file changes
                await self._process_pending_changes()
                
                # Process error reports
                self._process_error_reports()
                
                # Sleep briefly to avoid busy waiting
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nShutdown requested...")
        finally:
            await self.stop()
            
    async def stop(self):
        """Stop the overseer process"""
        print("Stopping Verifier Overseer...")
        
        # Stop watchers
        for watcher in self.watchers:
            watcher.stop()
            
        # Stop both agent sessions
        self.agent.stop_session()
        self.doc_agent.stop_session()
        
        self.running = False
        print("Overseer stopped.")
        
    def is_running(self) -> bool:
        """Check if the overseer is running"""
        return self.running