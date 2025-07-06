from typing import Union
from .config import VerifierConfig
from .code_agent import CodeAgent
from .goose_agent import BlockGooseVerifierAgent, BlockGooseDocumentationAgent
from .claude_code_agent import ClaudeCodeVerifierAgent, ClaudeCodeDocumentationAgent


def create_verifier_agent(config: VerifierConfig) -> CodeAgent:
    """Create a verifier agent based on the configuration"""
    if config.code_tool == "goose":
        return BlockGooseVerifierAgent(config)
    elif config.code_tool == "claude":
        return ClaudeCodeVerifierAgent(config)
    else:
        raise ValueError(f"Unknown code tool: {config.code_tool}. Must be 'goose' or 'claude'")


def create_documentation_agent(config: VerifierConfig) -> CodeAgent:
    """Create a documentation agent based on the configuration"""
    if config.code_tool == "goose":
        return BlockGooseDocumentationAgent(config)
    elif config.code_tool == "claude":
        return ClaudeCodeDocumentationAgent(config)
    else:
        raise ValueError(f"Unknown code tool: {config.code_tool}. Must be 'goose' or 'claude'")


def create_agent(config: VerifierConfig, agent_type: str) -> CodeAgent:
    """Create any agent type based on the configuration"""
    if agent_type == "verifier":
        return create_verifier_agent(config)
    elif agent_type == "documentation":
        return create_documentation_agent(config)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}. Must be 'verifier' or 'documentation'") 