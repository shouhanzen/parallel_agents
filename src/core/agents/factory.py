"""
Agent factory for creating different types of agents
"""

from typing import Union, Any
try:
    from ..config.models import VerifierConfig
except ImportError:
    from src.core.config.models import VerifierConfig
from .goose.agent import BlockGooseAgent, BlockGooseVerifierAgent, BlockGooseDocumentationAgent  
from .claude.agent import ClaudeCodeAgent, ClaudeCodeVerifierAgent, ClaudeCodeDocumentationAgent


def create_verifier_agent(config: VerifierConfig) -> Any:
    """Create a verifier agent based on configuration"""
    if config.code_tool == "goose":
        return BlockGooseVerifierAgent(config)
    elif config.code_tool in ["claude", "claude_code"]:
        return ClaudeCodeVerifierAgent(config)
    elif config.code_tool == "mock":
        from .mock.agent import MockVerifierAgent
        return MockVerifierAgent(config)
    else:
        raise ValueError(f"Unknown code tool: {config.code_tool}")


def create_documentation_agent(config: VerifierConfig) -> Any:
    """Create a documentation agent based on configuration"""
    if config.code_tool == "goose":
        return BlockGooseDocumentationAgent(config)
    elif config.code_tool in ["claude", "claude_code"]:
        return ClaudeCodeDocumentationAgent(config)
    elif config.code_tool == "mock":
        from .mock.agent import MockVerifierAgent
        return MockVerifierAgent(config)
    else:
        raise ValueError(f"Unknown code tool: {config.code_tool}")


def create_agent(config: VerifierConfig, agent_type: str = "verifier") -> Any:
    """Create an agent based on configuration and type"""
    if agent_type == "verifier":
        return create_verifier_agent(config)
    elif agent_type == "documentation":
        return create_documentation_agent(config)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


# For backwards compatibility - export the MockAgent class
try:
    from .mock.agent import MockVerifierAgent as MockAgent
except ImportError:
    MockAgent = None 