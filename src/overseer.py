#!/usr/bin/env python3
"""Compatibility shim for overseer imports"""

# Re-export overseer classes from their new locations
from core.overseer.overseer import Overseer

__all__ = ['Overseer'] 