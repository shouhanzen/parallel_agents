import time
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, field


@dataclass
class FileChange:
    """Represents a file change event"""
    file_path: str
    action: str  # 'created', 'modified', 'deleted'
    timestamp: float
    size: Optional[int] = None
    
    
@dataclass
class DeltaGateConfig:
    """Configuration for the delta gate"""
    min_change_interval: float = 0.5  # Minimum seconds between processing changes
    batch_timeout: float = 2.0  # Max seconds to wait for batching changes
    ignore_patterns: Set[str] = field(default_factory=lambda: {
        '*.pyc', '*.pyo', '*.pyd', '__pycache__', '.git', '.gitignore',
        '*.log', '*.tmp', '*.swp', '*.swo', '.DS_Store', 'node_modules'
    })
    min_file_size: int = 1  # Minimum file size to process
    max_file_size: int = 1024 * 1024  # Maximum file size to process (1MB)


class DeltaGate:
    """Filters and batches file changes to determine if they warrant processing"""
    
    def __init__(self, config: DeltaGateConfig = None):
        self.config = config or DeltaGateConfig()
        self.pending_changes: Dict[str, FileChange] = {}
        self.last_processing_time = 0
        self.batch_start_time = 0
        
    def _should_ignore_file(self, file_path: str) -> bool:
        """Check if a file should be ignored based on patterns"""
        path = Path(file_path)
        file_str = str(path)
        
        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            # Handle different pattern types
            if pattern.startswith('*'):
                # Extension patterns like *.pyc
                if file_str.endswith(pattern[1:]):
                    return True
            elif '*' in pattern:
                # Wildcard patterns
                import fnmatch
                if fnmatch.fnmatch(file_str, pattern):
                    return True
            else:
                # Direct string matches - check if pattern is in any part of path
                if pattern in path.parts or pattern in file_str:
                    return True
        
        # Check for hidden files (starting with .)
        if any(part.startswith('.') for part in path.parts):
            return True
                
        return False
        
    def _get_file_size(self, file_path: str) -> Optional[int]:
        """Get file size safely"""
        try:
            return Path(file_path).stat().st_size
        except:
            return None
            
    def _should_process_change(self, change: FileChange) -> bool:
        """Determine if a change should be processed"""
        # Check if file should be ignored
        if self._should_ignore_file(change.file_path):
            return False
            
        # Check file size constraints
        if change.action != 'deleted' and change.size is not None:
            if change.size < self.config.min_file_size or change.size > self.config.max_file_size:
                return False
                
        return True
        
    def add_change(self, file_path: str, action: str) -> bool:
        """Add a file change to the gate"""
        current_time = time.time()
        
        # Create change object
        change = FileChange(
            file_path=file_path,
            action=action,
            timestamp=current_time,
            size=self._get_file_size(file_path) if action != 'deleted' else None
        )
        
        # Check if we should process this change
        if not self._should_process_change(change):
            return False
            
        # Add to pending changes (overwrites previous change for same file)
        self.pending_changes[file_path] = change
        
        # Set batch start time if this is the first change
        if len(self.pending_changes) == 1:
            self.batch_start_time = current_time
            
        return True
        
    def should_process_batch(self) -> bool:
        """Check if we should process the current batch of changes"""
        if not self.pending_changes:
            return False
            
        current_time = time.time()
        
        # Check if minimum interval has passed since last processing
        if current_time - self.last_processing_time < self.config.min_change_interval:
            return False
            
        # Check if batch timeout has been reached
        if current_time - self.batch_start_time >= self.config.batch_timeout:
            return True
            
        return False
        
    def get_batch(self) -> List[Dict[str, Any]]:
        """Get the current batch of changes and reset"""
        if not self.pending_changes:
            return []
            
        # Convert to list format
        batch = []
        for change in self.pending_changes.values():
            batch.append({
                'file_path': change.file_path,
                'action': change.action,
                'timestamp': change.timestamp,
                'size': change.size
            })
            
        # Reset state
        self.pending_changes.clear()
        self.last_processing_time = time.time()
        self.batch_start_time = 0
        
        return batch
        
    def get_pending_count(self) -> int:
        """Get the number of pending changes"""
        return len(self.pending_changes)
        
    def clear_pending(self):
        """Clear all pending changes"""
        self.pending_changes.clear()
        self.batch_start_time = 0