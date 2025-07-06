#!/usr/bin/env python3
"""Compatibility shim for config imports"""

# Re-export config classes from their new locations
from core.config.models import ParallelAgentsConfig as VerifierConfig
from core.config.profiles import SDKConfigManager

# For backward compatibility, also export the original name
__all__ = ['VerifierConfig', 'SDKConfigManager'] 