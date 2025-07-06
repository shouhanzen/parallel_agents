from pathlib import Path
from typing import List, Dict, Any
from .config import VerifierConfig
from .agent_factory import create_verifier_agent


class VerifierAgent:
    """Agent that interfaces with code generation tools to generate and run tests"""
    
    def __init__(self, config: VerifierConfig):
        self._agent = create_verifier_agent(config)
        
    def __getattr__(self, name):
        """Delegate all attribute access to the underlying agent"""
        return getattr(self._agent, name)