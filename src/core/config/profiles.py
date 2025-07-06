"""
SDK Configuration Management - Enhanced configuration utilities for the SDK
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

try:
    from .models import VerifierConfig, ParallelAgentsConfig
except ImportError:
    from models import VerifierConfig, ParallelAgentsConfig


# New profile system for ParallelAgentsConfig
PARALLEL_PROFILES = {
    "testing": {
        "description": "Optimized for testing and development",
        "config": {
            "code_tool": "goose",
            "agent_mission": "Generate and verify tests for the codebase",
            "log_level": "DEBUG",
            "max_iterations": 3,
            "timeout": 120,
            "goose_timeout": 300,
            "goose_log_file": "tests/goose_testing.log"
        }
    },
    
    "documentation": {
        "description": "Optimized for documentation generation",
        "config": {
            "code_tool": "goose",
            "agent_mission": "Generate comprehensive documentation for the codebase including API docs, examples, and guides",
            "log_level": "INFO",
            "max_iterations": 5,
            "timeout": 300,
            "goose_timeout": 600,
            "goose_log_file": "docs/goose_docs.log"
        }
    },
    
    "demo": {
        "description": "Demo mode with mock agents for presentations",
        "config": {
            "code_tool": "mock",
            "agent_mission": "Demonstrate parallel agents capabilities",
            "log_level": "INFO",
            "max_iterations": 3,
            "timeout": 60,
            "goose_timeout": 120,
            "goose_log_file": "demo/mock_demo.log"
        }
    },
    
    "minimal": {
        "description": "Minimal configuration for small projects",
        "config": {
            "code_tool": "goose",
            "agent_mission": "Provide basic code assistance",
            "log_level": "WARNING",
            "max_iterations": 2,
            "timeout": 60,
            "goose_timeout": 180,
            "goose_log_file": "minimal.log"
        }
    },
    
    "full_stack": {
        "description": "Full-featured configuration for large projects",
        "config": {
            "code_tool": "goose",
            "agent_mission": "Comprehensive code analysis, testing, and documentation for full-stack applications",
            "log_level": "INFO",
            "max_iterations": 10,
            "timeout": 600,
            "goose_timeout": 1200,
            "goose_log_file": "full_stack/goose.log"
        }
    }
}


def get_profile(profile_name: str) -> Optional[ParallelAgentsConfig]:
    """Get a configuration profile by name"""
    if profile_name not in PARALLEL_PROFILES:
        return None
    
    profile_data = PARALLEL_PROFILES[profile_name]
    return ParallelAgentsConfig.from_dict(profile_data["config"])


def list_profiles() -> Dict[str, Dict[str, Any]]:
    """List all available configuration profiles"""
    return {
        name: {
            "description": profile["description"],
            "config": profile["config"]
        }
        for name, profile in PARALLEL_PROFILES.items()
    }


def get_profile_info(profile_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific profile"""
    if profile_name not in PARALLEL_PROFILES:
        return None
    
    return PARALLEL_PROFILES[profile_name]


def create_custom_profile(name: str, description: str, config: Dict[str, Any]) -> ParallelAgentsConfig:
    """Create a custom configuration profile"""
    # Validate the config by creating a ParallelAgentsConfig from it
    parallel_config = ParallelAgentsConfig.from_dict(config)
    
    # Add to the profiles (runtime only, not persisted)
    PARALLEL_PROFILES[name] = {
        "description": description,
        "config": config
    }
    
    return parallel_config


@dataclass
class SDKProfile:
    """Configuration profile for different use cases"""
    name: str
    description: str
    config_overrides: Dict[str, Any]
    
    
class SDKConfigManager:
    """Enhanced configuration manager with profiles and validation"""
    
    # Built-in configuration profiles
    PROFILES = {
        "testing": SDKProfile(
            name="testing",
            description="Optimized for test generation and validation",
            config_overrides={
                "agent_mission": "testing",
                "watch_dirs": ["src"],
                "test_dir": "tests",
                "working_set_dir": "tests/working_set",
                "watch_extensions": [".py", ".js", ".ts", ".jsx", ".tsx"],
                "code_tool": "goose",
                "goose_timeout": 120,
                "claude_timeout": 300
            }
        ),
        
        "documentation": SDKProfile(
            name="documentation",
            description="Optimized for documentation generation",
            config_overrides={
                "agent_mission": "docs",
                "watch_dirs": ["src", "lib"],
                "working_set_dir": "docs/working_set",
                "watch_extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".md"],
                "code_tool": "goose",
                "goose_timeout": 180,
                "claude_timeout": 300
            }
        ),
        
        "full_stack": SDKProfile(
            name="full_stack",
            description="Monitor both frontend and backend code",
            config_overrides={
                "agent_mission": "testing",
                "watch_dirs": ["src", "frontend", "backend", "api"],
                "test_dir": "tests",
                "working_set_dir": "tests/working_set",
                "watch_extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java"],
                "code_tool": "goose",
                "goose_timeout": 180,
                "claude_timeout": 300
            }
        ),
        
        "demo": SDKProfile(
            name="demo",
            description="Demo mode with mock agents",
            config_overrides={
                "agent_mission": "testing",
                "watch_dirs": ["src"],
                "test_dir": "tests",
                "working_set_dir": "tests/working_set",
                "watch_extensions": [".py"],
                "code_tool": "goose",
                "goose_timeout": 60,
                "claude_timeout": 60
            }
        ),
        
        "minimal": SDKProfile(
            name="minimal",
            description="Minimal configuration for small projects",
            config_overrides={
                "agent_mission": "testing",
                "watch_dirs": ["src"],
                "test_dir": "tests",
                "working_set_dir": "tests/working_set",
                "watch_extensions": [".py"],
                "code_tool": "goose",
                "goose_timeout": 90,
                "claude_timeout": 180
            }
        )
    }
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
    def create_config_from_profile(self, profile_name: str, config_file: str = "verifier.json") -> VerifierConfig:
        """Create a configuration file from a predefined profile"""
        if profile_name not in self.PROFILES:
            raise ValueError(f"Unknown profile: {profile_name}. Available profiles: {list(self.PROFILES.keys())}")
            
        profile = self.PROFILES[profile_name]
        
        # Start with default config
        config = VerifierConfig()
        
        # Apply profile overrides
        config_dict = config.model_dump()
        config_dict.update(profile.config_overrides)
        
        # Create new config with overrides
        new_config = VerifierConfig(**config_dict)
        
        # Save to file
        config_path = self.config_dir / config_file
        new_config.to_file(str(config_path))
        
        return new_config
        
    def get_profile_info(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about available profiles"""
        if profile_name:
            if profile_name not in self.PROFILES:
                raise ValueError(f"Unknown profile: {profile_name}")
            profile = self.PROFILES[profile_name]
            return {
                "name": profile.name,
                "description": profile.description,
                "config_overrides": profile.config_overrides
            }
        else:
            return {
                profile_name: {
                    "name": profile.name,
                    "description": profile.description,
                    "config_overrides": profile.config_overrides
                }
                for profile_name, profile in self.PROFILES.items()
            }
            
    def validate_config_file(self, config_file: str) -> Dict[str, Any]:
        """Validate a configuration file thoroughly"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            return {
                "valid": False,
                "errors": [f"Configuration file not found: {config_file}"],
                "warnings": []
            }
            
        try:
            # Try to load the config
            config = VerifierConfig.from_file(config_file)
            
            errors = []
            warnings = []
            
            # Check directories
            for watch_dir in config.watch_dirs:
                if not Path(watch_dir).exists():
                    warnings.append(f"Watch directory does not exist: {watch_dir}")
                    
            # Check working set directory
            working_set_path = Path(config.working_set_dir)
            if not working_set_path.exists() and not working_set_path.parent.exists():
                errors.append(f"Working set directory parent does not exist: {working_set_path.parent}")
                
            # Check test directory
            test_path = Path(config.test_dir)
            if not test_path.exists() and not test_path.parent.exists():
                warnings.append(f"Test directory does not exist: {test_path}")
                
            # Check code tool
            if config.code_tool not in ["goose", "claude"]:
                errors.append(f"Unknown code tool: {config.code_tool}")
                
            # Check timeouts
            if config.goose_timeout < 30:
                warnings.append("Goose timeout is very short, may cause failures")
            if config.claude_timeout < 30:
                warnings.append("Claude timeout is very short, may cause failures")
                
            # Check file extensions
            if not config.watch_extensions:
                warnings.append("No file extensions configured for watching")
                
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "config": config.model_dump()
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Error loading configuration: {e}"],
                "warnings": []
            }
            
    def compare_configs(self, config1_file: str, config2_file: str) -> Dict[str, Any]:
        """Compare two configuration files"""
        try:
            config1 = VerifierConfig.from_file(config1_file)
            config2 = VerifierConfig.from_file(config2_file)
            
            dict1 = config1.model_dump()
            dict2 = config2.model_dump()
            
            differences = {}
            all_keys = set(dict1.keys()) | set(dict2.keys())
            
            for key in all_keys:
                val1 = dict1.get(key)
                val2 = dict2.get(key)
                
                if val1 != val2:
                    differences[key] = {
                        config1_file: val1,
                        config2_file: val2
                    }
                    
            return {
                "identical": len(differences) == 0,
                "differences": differences,
                "config1": config1_file,
                "config2": config2_file
            }
            
        except Exception as e:
            return {
                "error": f"Error comparing configs: {e}"
            }
            
    def backup_config(self, config_file: str) -> str:
        """Create a backup of a configuration file"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_path.stem}_backup_{timestamp}{config_path.suffix}"
        backup_path = config_path.parent / backup_name
        
        # Copy file
        import shutil
        shutil.copy2(config_path, backup_path)
        
        return str(backup_path)
        
    def restore_config(self, backup_file: str, target_file: str) -> None:
        """Restore a configuration from backup"""
        backup_path = Path(backup_file)
        target_path = Path(target_file)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
        # Validate the backup is a valid config
        validation = self.validate_config_file(backup_file)
        if not validation["valid"]:
            raise ValueError(f"Backup file is not a valid configuration: {validation['errors']}")
            
        # Copy backup to target
        import shutil
        shutil.copy2(backup_path, target_path)
        
    def migrate_config(self, old_config_file: str, new_config_file: str) -> VerifierConfig:
        """Migrate an old configuration file to a new format"""
        try:
            # Load old config
            old_config = VerifierConfig.from_file(old_config_file)
            
            # Create new config with updated defaults
            new_config = VerifierConfig()
            
            # Copy over existing values
            old_dict = old_config.model_dump()
            new_dict = new_config.model_dump()
            
            # Update with old values
            new_dict.update(old_dict)
            
            # Create final config
            final_config = VerifierConfig(**new_dict)
            
            # Save to new file
            final_config.to_file(new_config_file)
            
            return final_config
            
        except Exception as e:
            raise RuntimeError(f"Error migrating configuration: {e}")
            
    def get_config_recommendations(self, project_dir: str = ".") -> Dict[str, Any]:
        """Analyze a project and recommend configuration settings"""
        project_path = Path(project_dir)
        
        recommendations = {
            "watch_dirs": [],
            "watch_extensions": [],
            "code_tool": "goose",  # Default to goose for cost efficiency
            "agent_mission": "testing",
            "suggestions": []
        }
        
        # Analyze project structure
        common_src_dirs = ["src", "lib", "app", "backend", "frontend", "api"]
        for src_dir in common_src_dirs:
            if (project_path / src_dir).exists():
                recommendations["watch_dirs"].append(src_dir)
                
        # Analyze file types
        extensions = set()
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix:
                extensions.add(file_path.suffix)
                
        # Filter to supported extensions
        supported_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".cpp", ".c", ".h"}
        found_extensions = extensions & supported_extensions
        
        if found_extensions:
            recommendations["watch_extensions"] = sorted(list(found_extensions))
            
        # Generate suggestions
        if not recommendations["watch_dirs"]:
            recommendations["suggestions"].append("No common source directories found. Consider adding your source directories to watch_dirs.")
            
        if not recommendations["watch_extensions"]:
            recommendations["suggestions"].append("No supported file extensions found. Consider adding file extensions to watch_extensions.")
            
        if len(recommendations["watch_dirs"]) > 3:
            recommendations["suggestions"].append("Many directories to watch. Consider focusing on the most important ones for better performance.")
            
        return recommendations
        
    def create_project_config(self, project_dir: str = ".", config_file: str = "verifier.json") -> VerifierConfig:
        """Create a configuration file tailored to a specific project"""
        recommendations = self.get_config_recommendations(project_dir)
        
        # Create config with recommendations
        config = VerifierConfig()
        config_dict = config.model_dump()
        
        # Apply recommendations
        if recommendations["watch_dirs"]:
            config_dict["watch_dirs"] = recommendations["watch_dirs"]
        if recommendations["watch_extensions"]:
            config_dict["watch_extensions"] = recommendations["watch_extensions"]
            
        config_dict["code_tool"] = recommendations["code_tool"]
        config_dict["agent_mission"] = recommendations["agent_mission"]
        
        # Create final config
        final_config = VerifierConfig(**config_dict)
        
        # Save to file
        config_path = Path(project_dir) / config_file
        final_config.to_file(str(config_path))
        
        return final_config


# Convenience functions

def create_config_from_profile(profile_name: str, config_file: str = "verifier.json") -> VerifierConfig:
    """Create a configuration file from a predefined profile"""
    manager = SDKConfigManager()
    return manager.create_config_from_profile(profile_name, config_file)

def get_available_profiles() -> Dict[str, Any]:
    """Get information about all available configuration profiles"""
    manager = SDKConfigManager()
    return manager.get_profile_info()

def validate_config(config_file: str) -> Dict[str, Any]:
    """Validate a configuration file"""
    manager = SDKConfigManager()
    return manager.validate_config_file(config_file)

def create_project_config(project_dir: str = ".", config_file: str = "verifier.json") -> VerifierConfig:
    """Create a configuration file tailored to a specific project"""
    manager = SDKConfigManager()
    return manager.create_project_config(project_dir, config_file) 