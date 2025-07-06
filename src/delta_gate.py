#!/usr/bin/env python3
"""Compatibility shim for delta gate imports"""

# Re-export delta gate classes from their new locations
from core.monitoring.delta_gate import DeltaGate, DeltaGateConfig

__all__ = ['DeltaGate', 'DeltaGateConfig'] 