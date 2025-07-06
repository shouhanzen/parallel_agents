#!/usr/bin/env python3
"""Compatibility shim for agent imports"""

# Re-export agent classes from their new locations
from core.agents.mock.agent import MockVerifierAgent

# For test compatibility, alias as VerifierAgent
VerifierAgent = MockVerifierAgent

# Also expose the factory function
try:
    from core.agents.factory import create_verifier_agent
except ImportError:
    # If factory doesn't exist, create a simple one
    def create_verifier_agent(config):
        return MockVerifierAgent(config)

# For backward compatibility
__all__ = ['VerifierAgent', 'MockVerifierAgent', 'create_verifier_agent'] 