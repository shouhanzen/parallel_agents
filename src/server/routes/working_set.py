"""
Working set management API routes
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path

from core.monitoring.working_set import WorkingSetManager
from server.app import get_server, ParallelAgentsServer


router = APIRouter()


@router.get("/changes", response_model=Dict[str, Any])
async def get_working_set_changes(working_set_dir: str = "tests/working_set"):
    """Get changes in the working set directory"""
    try:
        manager = WorkingSetManager(working_set_dir)
        changes = manager.get_changes()
        
        return {
            "success": True,
            "working_set_dir": working_set_dir,
            "changes": changes,
            "total_files": len(changes),
            "by_type": _group_files_by_type(changes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files", response_model=Dict[str, Any])
async def get_working_set_files(working_set_dir: str = "tests/working_set"):
    """Get all files in the working set directory"""
    try:
        working_set_path = Path(working_set_dir)
        
        if not working_set_path.exists():
            return {
                "success": True,
                "working_set_dir": working_set_dir,
                "files": [],
                "total_files": 0,
                "by_type": {}
            }
        
        files = []
        for file_path in working_set_path.rglob("*"):
            if file_path.is_file():
                files.append({
                    "path": str(file_path),
                    "relative_path": str(file_path.relative_to(working_set_path)),
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })
        
        return {
            "success": True,
            "working_set_dir": working_set_dir,
            "files": files,
            "total_files": len(files),
            "by_type": _group_files_by_type(files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_working_set(working_set_dir: str = "tests/working_set"):
    """Clean up the working set directory"""
    try:
        manager = WorkingSetManager(working_set_dir)
        
        # Get files before cleanup
        files_before = list(Path(working_set_dir).rglob("*")) if Path(working_set_dir).exists() else []
        
        # Cleanup
        manager.cleanup()
        
        # Get files after cleanup
        files_after = list(Path(working_set_dir).rglob("*")) if Path(working_set_dir).exists() else []
        
        return {
            "success": True,
            "working_set_dir": working_set_dir,
            "files_before": len(files_before),
            "files_after": len(files_after),
            "files_removed": len(files_before) - len(files_after)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _group_files_by_type(files: list) -> Dict[str, int]:
    """Group files by type and count them"""
    by_type = {}
    
    for file_info in files:
        path = file_info.get("path") or file_info.get("relative_path", "")
        file_path = Path(path)
        
        if 'test' in path.lower():
            file_type = 'tests'
        elif 'artifact' in path.lower():
            file_type = 'artifacts'
        elif 'report' in path.lower() or file_path.suffix == '.jsonl':
            file_type = 'reports'
        elif 'log' in path.lower():
            file_type = 'logs'
        else:
            file_type = 'other'
        
        by_type[file_type] = by_type.get(file_type, 0) + 1
    
    return by_type 