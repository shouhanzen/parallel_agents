import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


class WorkingSetManager:
    """Manages the working set directory for generated tests and artifacts"""
    
    def __init__(self, working_set_dir: str):
        self.working_set_dir = Path(working_set_dir)
        self.working_set_dir.mkdir(parents=True, exist_ok=True)
        
    def create_test_file(self, test_name: str, content: str) -> Path:
        """Create a test file in the working set"""
        test_file = self.working_set_dir / f"{test_name}.py"
        test_file.write_text(content)
        return test_file
        
    def list_test_files(self) -> List[Path]:
        """List all test files in the working set"""
        return sorted(self.working_set_dir.glob("test_*.py"))
        
    def remove_test_file(self, test_name: str) -> bool:
        """Remove a test file from the working set"""
        test_file = self.working_set_dir / f"{test_name}.py"
        if test_file.exists():
            test_file.unlink()
            return True
        return False
        
    def clean_working_set(self):
        """Clean the working set directory"""
        if self.working_set_dir.exists():
            shutil.rmtree(self.working_set_dir)
            self.working_set_dir.mkdir(parents=True, exist_ok=True)
            
    def get_working_set_size(self) -> int:
        """Get the number of files in the working set"""
        return len(list(self.working_set_dir.glob("*")))
        
    def create_metadata_file(self, metadata: Dict[str, Any]) -> Path:
        """Create a metadata file for the working set"""
        metadata_file = self.working_set_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        return metadata_file
        
    def read_metadata(self) -> Optional[Dict[str, Any]]:
        """Read metadata from the working set"""
        metadata_file = self.working_set_dir / "metadata.json"
        if metadata_file.exists():
            return json.loads(metadata_file.read_text())
        return None
        
    def ensure_directory_structure(self):
        """Ensure the working set has proper directory structure"""
        subdirs = ['tests', 'artifacts', 'reports']
        for subdir in subdirs:
            (self.working_set_dir / subdir).mkdir(exist_ok=True)
            
    def get_working_set_path(self) -> Path:
        """Get the working set directory path"""
        return self.working_set_dir