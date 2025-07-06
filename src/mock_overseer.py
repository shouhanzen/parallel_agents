#!/usr/bin/env python3
"""Compatibility shim for mock overseer imports"""

# Re-export mock overseer classes from their new locations
from core.overseer.mock_overseer import MockOverseer

__all__ = ['MockOverseer'] 