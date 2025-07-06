"""
Agent factory for creating different types of agents
"""

from typing import Union
try:
    from ..config.models import VerifierConfig
except ImportError:
    from src.core.config.models import VerifierConfig
from .goose.agent import BlockGooseAgent, BlockGooseVerifierAgent, BlockGooseDocumentationAgent  
from .claude.agent import ClaudeCodeAgent, ClaudeCodeVerifierAgent, ClaudeCodeDocumentationAgent


def create_verifier_agent(config: VerifierConfig) -> Union[BlockGooseVerifierAgent, ClaudeCodeVerifierAgent]:
    """Create a verifier agent based on configuration"""
    if config.code_tool == "goose":
        return BlockGooseVerifierAgent(config)
    elif config.code_tool == "claude":
        return ClaudeCodeVerifierAgent(config)
    else:
        raise ValueError(f"Unknown code tool: {config.code_tool}")


def create_documentation_agent(config: VerifierConfig) -> Union[BlockGooseDocumentationAgent, ClaudeCodeDocumentationAgent]:
    """Create a documentation agent based on configuration"""
    if config.code_tool == "goose":
        return BlockGooseDocumentationAgent(config)
    elif config.code_tool == "claude":
        return ClaudeCodeDocumentationAgent(config)
    else:
        raise ValueError(f"Unknown code tool: {config.code_tool}")


def create_agent(config: VerifierConfig, agent_type: str = "verifier") -> Union[BlockGooseAgent, ClaudeCodeAgent]:
    """Create an agent based on configuration and type"""
    if agent_type == "verifier":
        return create_verifier_agent(config)
    elif agent_type == "documentation":
        return create_documentation_agent(config)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}") 