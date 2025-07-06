import asyncio
import os
from pathlib import Path
from typing import Callable, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str, str], None], watch_extensions: Optional[Set[str]] = None):
        self.callback = callback
        self.watch_extensions = watch_extensions or {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c', '.h'}
        
    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed based on extension"""
        return Path(file_path).suffix.lower() in self.watch_extensions
        
    def on_modified(self, event):
        if not event.is_directory and self._should_process_file(event.src_path):
            self.callback(event.src_path, 'modified')
            
    def on_created(self, event):
        if not event.is_directory and self._should_process_file(event.src_path):
            self.callback(event.src_path, 'created')
            
    def on_deleted(self, event):
        if not event.is_directory and self._should_process_file(event.src_path):
            self.callback(event.src_path, 'deleted')


class FilesystemWatcher:
    def __init__(self, watch_dir: str, callback: Callable[[str, str], None]):
        self.watch_dir = Path(watch_dir)
        self.callback = callback
        self.observer = Observer()
        self.handler = FileChangeHandler(self.callback)
        
    def start(self):
        """Start watching the directory"""
        if not self.watch_dir.exists():
            raise FileNotFoundError(f"Watch directory does not exist: {self.watch_dir}")
            
        self.observer.schedule(self.handler, str(self.watch_dir), recursive=True)
        self.observer.start()
        
    def stop(self):
        """Stop watching the directory"""
        self.observer.stop()
        self.observer.join()
        
    def is_alive(self) -> bool:
        """Check if the watcher is running"""
        return self.observer.is_alive()