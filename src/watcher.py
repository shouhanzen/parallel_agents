#!/usr/bin/env python3
"""Compatibility shim for watcher imports"""

# Re-export watcher classes from their new locations
from core.monitoring.watcher import FilesystemWatcher, FileChangeHandler

__all__ = ['FilesystemWatcher', 'FileChangeHandler'] 