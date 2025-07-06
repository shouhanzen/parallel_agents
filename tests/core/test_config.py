#!/usr/bin/env python3
"""Unit tests for the configuration module"""

import pytest
import tempfile
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config.models import ParallelAgentsConfig
from core.config.profiles import get_profile, list_profiles


class TestParallelAgentsConfig:
    """Test the ParallelAgentsConfig class"""
    
    def test_default_config_creation(self):
        """Test creating a default configuration"""
        config = ParallelAgentsConfig()
        
        assert config.code_tool == "goose"
        assert config.agent_mission == "You are a helpful AI assistant"
        assert config.log_level == "INFO"
        assert config.max_iterations == 10
        assert config.timeout == 300
        assert config.goose_timeout == 600
        assert config.goose_log_file == "goose.log"
        
    def test_config_with_custom_values(self):
        """Test creating config with custom values"""
        config = ParallelAgentsConfig(
            code_tool="claude_code",
            agent_mission="Generate documentation",
            log_level="DEBUG",
            max_iterations=5,
            timeout=600
        )
        
        assert config.code_tool == "claude_code"
        assert config.agent_mission == "Generate documentation"
        assert config.log_level == "DEBUG"
        assert config.max_iterations == 5
        assert config.timeout == 600
        
    def test_config_serialization(self):
        """Test configuration serialization to dict"""
        config = ParallelAgentsConfig(
            code_tool="mock",
            agent_mission="Testing serialization",
            log_level="DEBUG",
            max_iterations=3
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["code_tool"] == "mock"
        assert config_dict["agent_mission"] == "Testing serialization"
        assert config_dict["log_level"] == "DEBUG"
        assert config_dict["max_iterations"] == 3
        
    def test_config_from_dict(self):
        """Test creating config from dictionary"""
        config_data = {
            "code_tool": "goose",
            "agent_mission": "Test from dict",
            "log_level": "WARNING",
            "max_iterations": 7,
            "timeout": 180
        }
        
        config = ParallelAgentsConfig.from_dict(config_data)
        
        assert config.code_tool == "goose"
        assert config.agent_mission == "Test from dict"
        assert config.log_level == "WARNING"
        assert config.max_iterations == 7
        assert config.timeout == 180
        
    def test_config_save_and_load_json(self):
        """Test saving and loading configuration from JSON"""
        config = ParallelAgentsConfig(
            code_tool="mock",
            agent_mission="Test save and load",
            log_level="DEBUG",
            max_iterations=5
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'test_config.json'
            
            # Save config to JSON file
            with open(config_path, 'w') as f:
                json.dump(config.to_dict(), f)
            
            # Load config from JSON file
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            loaded_config = ParallelAgentsConfig.from_dict(config_data)
            
            assert loaded_config.code_tool == config.code_tool
            assert loaded_config.agent_mission == config.agent_mission
            assert loaded_config.log_level == config.log_level
            assert loaded_config.max_iterations == config.max_iterations
            
    def test_config_equality(self):
        """Test configuration equality comparison"""
        config1 = ParallelAgentsConfig(
            code_tool="goose",
            agent_mission="Testing",
            log_level="INFO"
        )
        
        config2 = ParallelAgentsConfig(
            code_tool="goose",
            agent_mission="Testing",
            log_level="INFO"
        )
        
        config3 = ParallelAgentsConfig(
            code_tool="claude_code",
            agent_mission="Testing",
            log_level="INFO"
        )
        
        assert config1 == config2
        assert config1 != config3


class TestConfigProfiles:
    """Test configuration profiles functionality"""
    
    def test_list_profiles(self):
        """Test listing available profiles"""
        profiles = list_profiles()
        
        assert isinstance(profiles, dict)
        assert "testing" in profiles
        assert "documentation" in profiles
        assert "demo" in profiles
        assert "minimal" in profiles
        assert "full_stack" in profiles
        
    def test_get_testing_profile(self):
        """Test getting the testing profile"""
        config = get_profile("testing")
        
        assert config is not None
        assert config.code_tool == "goose"
        assert config.log_level == "DEBUG"
        assert config.max_iterations == 3
        
    def test_get_documentation_profile(self):
        """Test getting the documentation profile"""
        config = get_profile("documentation")
        
        assert config is not None
        assert config.code_tool == "goose"
        assert "documentation" in config.agent_mission.lower()
        
    def test_get_demo_profile(self):
        """Test getting the demo profile"""
        config = get_profile("demo")
        
        assert config is not None
        assert config.code_tool == "mock"
        
    def test_get_nonexistent_profile(self):
        """Test getting a profile that doesn't exist"""
        config = get_profile("nonexistent_profile")
        
        assert config is None
        
    def test_profile_inheritance(self):
        """Test that profiles have proper default values"""
        testing_config = get_profile("testing")
        minimal_config = get_profile("minimal")
        
        # Both should be valid configurations
        assert testing_config.code_tool in ["goose", "claude_code", "mock"]
        assert minimal_config.code_tool in ["goose", "claude_code", "mock"]
        
        # Testing profile should have specific settings
        assert testing_config.log_level == "DEBUG"
        assert testing_config.max_iterations <= 5


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_valid_code_tools(self):
        """Test that valid code tools are accepted"""
        valid_tools = ["goose", "claude_code", "mock"]
        
        for tool in valid_tools:
            config = ParallelAgentsConfig(code_tool=tool)
            assert config.code_tool == tool
            
    def test_valid_log_levels(self):
        """Test that valid log levels are accepted"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            config = ParallelAgentsConfig(log_level=level)
            assert config.log_level == level
            
    def test_mission_values(self):
        """Test different mission values"""
        missions = [
            "Code verification and testing",
            "Documentation generation",
            "Code review and analysis",
            "General AI assistance"
        ]
        
        for mission in missions:
            config = ParallelAgentsConfig(agent_mission=mission)
            assert config.agent_mission == mission
            
    def test_timeout_values(self):
        """Test different timeout values"""
        timeouts = [30, 60, 120, 300, 600, 1800]
        
        for timeout in timeouts:
            config = ParallelAgentsConfig(timeout=timeout)
            assert config.timeout == timeout
            
    def test_max_iterations_values(self):
        """Test different max iteration values"""
        iterations = [1, 3, 5, 10, 20]
        
        for max_iter in iterations:
            config = ParallelAgentsConfig(max_iterations=max_iter)
            assert config.max_iterations == max_iter


class TestConfigIntegration:
    """Test configuration integration scenarios"""
    
    def test_profile_customization(self):
        """Test customizing a profile"""
        base_config = get_profile("testing")
        
        # Create a customized version
        custom_config = ParallelAgentsConfig(
            code_tool=base_config.code_tool,
            agent_mission="Custom testing mission",
            log_level=base_config.log_level,
            max_iterations=base_config.max_iterations,
            timeout=120  # Custom timeout
        )
        
        assert custom_config.code_tool == base_config.code_tool
        assert custom_config.agent_mission == "Custom testing mission"
        assert custom_config.log_level == base_config.log_level
        assert custom_config.timeout == 120
        
    def test_config_merge_behavior(self):
        """Test configuration merging behavior"""
        config1 = ParallelAgentsConfig(
            code_tool="goose",
            agent_mission="Original mission"
        )
        
        # Override specific fields
        config2 = ParallelAgentsConfig(
            code_tool=config1.code_tool,
            agent_mission="Updated mission",
            log_level="WARNING",
            max_iterations=config1.max_iterations
        )
        
        assert config2.code_tool == config1.code_tool
        assert config2.agent_mission == "Updated mission"
        assert config2.log_level == "WARNING"
        assert config2.max_iterations == config1.max_iterations
        
    def test_config_copy_behavior(self):
        """Test configuration copying behavior"""
        original = ParallelAgentsConfig(
            code_tool="goose",
            agent_mission="Original",
            log_level="DEBUG"
        )
        
        # Create a copy with modifications
        copy_data = original.to_dict()
        copy_data["agent_mission"] = "Modified"
        
        modified = ParallelAgentsConfig.from_dict(copy_data)
        
        assert modified.code_tool == original.code_tool
        assert modified.agent_mission == "Modified"
        assert modified.log_level == original.log_level
        assert original.agent_mission == "Original"  # Original unchanged


if __name__ == '__main__':
    pytest.main([__file__])