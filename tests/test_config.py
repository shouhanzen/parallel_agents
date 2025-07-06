#!/usr/bin/env python3
"""Unit tests for the configuration module"""

import pytest
import tempfile
import json
from pathlib import Path
from src.config import VerifierConfig, get_default_config


class TestVerifierConfig:
    """Test the VerifierConfig class"""
    
    def test_default_config_creation(self):
        """Test creating a default configuration"""
        config = VerifierConfig()
        
        assert config.watch_dirs == ['src']
        assert config.test_dir == 'tests'
        assert config.working_set_dir == 'tests/working_set'
        assert config.agent_mission == 'testing'
        assert config.claude_timeout == 300
        assert '.py' in config.watch_extensions
        assert '.js' in config.watch_extensions
        
    def test_config_with_custom_values(self):
        """Test creating config with custom values"""
        config = VerifierConfig(
            watch_dirs=['custom_src', 'lib'],
            test_dir='custom_test',
            agent_mission='docs',
            claude_timeout=600
        )
        
        assert config.watch_dirs == ['custom_src', 'lib']
        assert config.test_dir == 'custom_test'
        assert config.agent_mission == 'docs'
        assert config.claude_timeout == 600
        
    def test_config_save_and_load_json(self):
        """Test saving and loading configuration from JSON"""
        config = VerifierConfig(
            watch_dirs=['src', 'lib'],
            test_dir='tests',
            agent_mission='tooling',
            claude_timeout=120
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'test_config.json'
            
            # Save config
            config.to_file(str(config_path))
            assert config_path.exists()
            
            # Load config
            loaded_config = VerifierConfig.from_file(str(config_path))
            
            assert loaded_config.watch_dirs == config.watch_dirs
            assert loaded_config.test_dir == config.test_dir
            assert loaded_config.agent_mission == config.agent_mission
            assert loaded_config.claude_timeout == config.claude_timeout
            
    def test_config_load_nonexistent_file(self):
        """Test loading config from non-existent file returns default"""
        config = VerifierConfig.from_file('nonexistent.json')
        default_config = VerifierConfig()
        
        assert config.model_dump() == default_config.model_dump()
        
    def test_config_unsupported_format(self):
        """Test that unsupported file formats raise ValueError"""
        config = VerifierConfig()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.yaml'
            
            with pytest.raises(ValueError, match="Unsupported config file format"):
                config.to_file(str(config_path))
                
    def test_config_from_json_dict(self):
        """Test loading config from JSON dictionary"""
        test_data = {
            'watch_dirs': ['custom'],
            'test_dir': 'my_tests',
            'agent_mission': 'docs',
            'claude_timeout': 180
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'config.json'
            
            with open(config_path, 'w') as f:
                json.dump(test_data, f)
                
            config = VerifierConfig.from_file(str(config_path))
            
            assert config.watch_dirs == ['custom']
            assert config.test_dir == 'my_tests'
            assert config.agent_mission == 'docs'
            assert config.claude_timeout == 180
            
    def test_config_directory_creation(self):
        """Test that config file directory is created if it doesn't exist"""
        config = VerifierConfig()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / 'nested' / 'config.json'
            
            config.to_file(str(nested_path))
            assert nested_path.exists()
            assert nested_path.parent.exists()
            
    def test_get_default_config(self):
        """Test the get_default_config function"""
        config = get_default_config()
        
        assert isinstance(config, VerifierConfig)
        assert config.watch_dirs == ['src']
        assert config.agent_mission == 'testing'


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_valid_watch_extensions(self):
        """Test that watch extensions are properly set"""
        config = VerifierConfig()
        
        expected_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c', '.h'}
        assert set(config.watch_extensions) == expected_extensions
        
    def test_custom_watch_extensions(self):
        """Test setting custom watch extensions"""
        config = VerifierConfig(watch_extensions=['.py', '.md'])
        
        assert config.watch_extensions == ['.py', '.md']
        
    def test_mission_values(self):
        """Test different mission values"""
        for mission in ['testing', 'docs', 'tooling']:
            config = VerifierConfig(agent_mission=mission)
            assert config.agent_mission == mission
            
    def test_timeout_values(self):
        """Test different timeout values"""
        config = VerifierConfig(claude_timeout=60)
        assert config.claude_timeout == 60
        
        config = VerifierConfig(claude_timeout=3600)
        assert config.claude_timeout == 3600


if __name__ == '__main__':
    pytest.main([__file__])