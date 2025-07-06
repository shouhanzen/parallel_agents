from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ParallelAgentsConfig(BaseModel):
    """Configuration for the parallel agents system"""
    
    # Core agent configuration
    code_tool: str = Field(
        default="goose",
        description="Code generation tool to use ('goose', 'claude_code', 'mock')"
    )
    
    agent_mission: str = Field(
        default="You are a helpful AI assistant",
        description="Mission statement for the agent"
    )
    
    # Directory configuration
    working_set_dir: str = Field(
        default='tests/working_set', 
        description="Working set directory for generated tests"
    )
    
    watch_dirs: List[str] = Field(
        default=['src'], 
        description="Directories to watch for changes"
    )
    
    test_dir: str = Field(
        default='tests', 
        description="Directory to write tests"
    )
    
    # File patterns
    watch_extensions: List[str] = Field(
        default=['.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c', '.h'],
        description="File extensions to watch"
    )
    
    # Error reporting
    error_report_file: str = Field(
        default='tests/working_set/error_report.jsonl',
        description="File to write error reports"
    )
    
    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Agent behavior configuration
    max_iterations: int = Field(
        default=10,
        description="Maximum number of iterations for agent operations"
    )
    
    timeout: int = Field(
        default=300,
        description="General timeout for operations in seconds"
    )
    
    # Tool-specific configuration
    goose_timeout: int = Field(
        default=600,
        description="Timeout for Block Goose operations in seconds"
    )
    
    goose_log_file: str = Field(
        default="goose.log",
        description="File to write Block Goose interaction logs"
    )
    
    claude_timeout: int = Field(
        default=600,
        description="Timeout for Claude Code operations in seconds"
    )
    
    claude_log_file: str = Field(
        default="claude_code.log",
        description="File to write Claude Code interaction logs"
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParallelAgentsConfig':
        """Create configuration from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return self.model_dump()
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ParallelAgentsConfig':
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
            
        return cls.from_dict(data)
        
    def to_file(self, config_path: str):
        """Save configuration to file"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        if config_file.suffix == '.json':
            import json
            with open(config_file, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {config_file.suffix}")


# Legacy support - keep the old VerifierConfig for backward compatibility
class VerifierConfig(BaseModel):
    """Legacy configuration for backward compatibility"""
    
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
    """Get default legacy configuration"""
    return VerifierConfig()


def get_default_parallel_config() -> ParallelAgentsConfig:
    """Get default parallel agents configuration"""
    return ParallelAgentsConfig()