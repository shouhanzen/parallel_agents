#!/usr/bin/env python3
"""Compatibility shim for working set imports"""

# Re-export working set classes from their new locations
from core.monitoring.working_set import WorkingSetManager

__all__ = ['WorkingSetManager'] 