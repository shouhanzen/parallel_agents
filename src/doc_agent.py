from pathlib import Path
from typing import List, Dict, Any
from .config import VerifierConfig
from .agent_factory import create_documentation_agent


class DocumentationAgent:
    """Agent that interfaces with code generation tools to generate and update documentation"""
    
    def __init__(self, config: VerifierConfig):
        self._agent = create_documentation_agent(config)
        
    def __getattr__(self, name):
        """Delegate all attribute access to the underlying agent"""
        return getattr(self._agent, name)