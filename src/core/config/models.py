from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VerifierConfig(BaseModel):
    """Configuration for the verifier system"""
    
    # Directories to watch
    watch_dirs: List[str] = Field(default=['src'], description="Directories to watch for changes")
    
    # Test directory configuration
    test_dir: str = Field(default='tests', description="Directory to write tests")
    working_set_dir: str = Field(default='tests/working_set', description="Working set directory for generated tests")
    
    # File patterns
    watch_extensions: List[str] = Field(
        default=['.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c', '.h'],
        description="File extensions to watch"
    )
    
    # Agent configuration
    agent_mission: str = Field(
        default="testing", 
        description="Mission for the verifier agent (testing, docs, tooling)"
    )
    
    # Tool configuration
    code_tool: str = Field(
        default="goose",
        description="Code generation tool to use ('goose' for Block Goose, 'claude' for Claude Code)"
    )
    
    # Error reporting
    error_report_file: str = Field(
        default='tests/working_set/error_report.jsonl',
        description="File to write error reports"
    )
    
    # Claude Code configuration
    claude_timeout: int = Field(default=300, description="Timeout for Claude Code operations in seconds")
    claude_log_file: str = Field(
        default='tests/working_set/claude_logs.jsonl',
        description="File to write Claude code interaction logs"
    )
    
    # Block Goose configuration
    goose_timeout: int = Field(default=300, description="Timeout for Block Goose operations in seconds")
    goose_log_file: str = Field(
        default='tests/working_set/goose_logs.jsonl',
        description="File to write Block Goose interaction logs"
    )
    
    @classmethod
    def from_file(cls, config_path: str) -> 'VerifierConfig':
        """Load configuration from file"""
        config_file = Path(config_path)
        if not config_file.exists():
            return cls()  # Return default config
            
        if config_file.suffix == '.json':
            import json
            with open(config_file, 'r') as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_file.suffix}")
            
        return cls(**data)
        
    def to_file(self, config_path: str):
        """Save configuration to file"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        if config_file.suffix == '.json':
            import json
            with open(config_file, 'w') as f:
                json.dump(self.model_dump(), f, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {config_file.suffix}")


def get_default_config() -> VerifierConfig:
    """Get default configuration"""
    return VerifierConfig()