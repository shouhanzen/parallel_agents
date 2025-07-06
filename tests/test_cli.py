#!/usr/bin/env python3
"""Unit tests for the CLI module"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from click.testing import CliRunner
from src.cli import cli, start, demo, init, status, validate
from src.config import VerifierConfig


class TestCLICommands:
    """Test CLI command functions"""
    
    def test_cli_group(self):
        """Test the main CLI group"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Verifier - Automated testing with Claude Code agents" in result.output
        
    def test_init_command_new_file(self):
        """Test init command with new configuration file"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            
            result = runner.invoke(init, ['--output', str(config_path)])
            
            assert result.exit_code == 0
            assert config_path.exists()
            assert "Created configuration file" in result.output
            
            # Verify config content
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            assert config_data['watch_dirs'] == ['src']
            assert config_data['agent_mission'] == 'testing'
            
    def test_init_command_existing_file_abort(self):
        """Test init command with existing file and abort"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "existing_config.json"
            config_path.write_text('{"test": true}')
            
            # Don't confirm overwrite
            result = runner.invoke(init, ['--output', str(config_path)], input='n\n')
            
            assert result.exit_code == 1  # Aborted
            
    def test_init_command_existing_file_overwrite(self):
        """Test init command with existing file and overwrite"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "existing_config.json"
            config_path.write_text('{"test": true}')
            
            # Confirm overwrite
            result = runner.invoke(init, ['--output', str(config_path)], input='y\n')
            
            assert result.exit_code == 0
            assert "Created configuration file" in result.output
            
            # Verify config was overwritten
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            assert 'test' not in config_data
            assert config_data['watch_dirs'] == ['src']
            
    def test_status_command_existing_config(self):
        """Test status command with existing configuration"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = VerifierConfig(watch_dirs=['custom_src'], agent_mission='docs')
            config.to_file(str(config_path))
            
            result = runner.invoke(status, ['--config', str(config_path)])
            
            assert result.exit_code == 0
            assert "Configuration from" in result.output
            assert "custom_src" in result.output
            assert "docs" in result.output
            
    def test_status_command_missing_config(self):
        """Test status command with missing configuration"""
        runner = CliRunner()
        
        result = runner.invoke(status, ['--config', 'nonexistent.json'])
        
        assert result.exit_code == 0
        assert "Configuration file not found" in result.output
        assert "verifier init" in result.output
        
    def test_validate_command_valid_config(self):
        """Test validate command with valid configuration"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create config with existing watch directory
            config = VerifierConfig(
                watch_dirs=[temp_dir],  # Use temp_dir as watch dir since it exists
                working_set_dir=str(Path(temp_dir) / "working_set")
            )
            config.to_file(str(config_path))
            
            result = runner.invoke(validate, ['--config', str(config_path)])
            
            assert result.exit_code == 0
            assert "Configuration is valid!" in result.output
            assert "Working set directory ready" in result.output
            
    def test_validate_command_missing_watch_dir(self):
        """Test validate command with missing watch directory"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create config with non-existent watch directory
            config = VerifierConfig(watch_dirs=['/nonexistent/directory'])
            config.to_file(str(config_path))
            
            result = runner.invoke(validate, ['--config', str(config_path)])
            
            assert result.exit_code == 0
            assert "Configuration is valid!" in result.output
            assert "Warning: Watch directory does not exist" in result.output
            
    def test_validate_command_missing_config(self):
        """Test validate command with missing configuration file"""
        runner = CliRunner()
        
        result = runner.invoke(validate, ['--config', 'nonexistent.json'])
        
        assert result.exit_code == 0
        assert "Configuration file not found" in result.output
        
    def test_validate_command_invalid_config(self):
        """Test validate command with invalid configuration"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create invalid JSON
            config_path.write_text('{"invalid": json}')
            
            result = runner.invoke(validate, ['--config', str(config_path)])
            
            assert result.exit_code == 0
            assert "Configuration validation failed" in result.output


class TestCLIStartCommand:
    """Test the start command specifically"""
    
    @patch('verifier.cli.asyncio.run')
    @patch('verifier.cli.Overseer')
    def test_start_command_default_config(self, mock_overseer_class, mock_asyncio_run):
        """Test start command with default configuration"""
        runner = CliRunner()
        
        mock_overseer = Mock()
        mock_overseer_class.return_value = mock_overseer
        
        result = runner.invoke(start)
        
        assert result.exit_code == 0
        assert "Using default configuration" in result.output
        mock_overseer_class.assert_called_once()
        mock_asyncio_run.assert_called_once()
        
    @patch('verifier.cli.asyncio.run')
    @patch('verifier.cli.Overseer')
    def test_start_command_existing_config(self, mock_overseer_class, mock_asyncio_run):
        """Test start command with existing configuration"""
        runner = CliRunner()
        
        mock_overseer = Mock()
        mock_overseer_class.return_value = mock_overseer
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = VerifierConfig(agent_mission='docs')
            config.to_file(str(config_path))
            
            result = runner.invoke(start, ['--config', str(config_path)])
            
            assert result.exit_code == 0
            assert f"Loaded configuration from {config_path}" in result.output
            
            # Check that overseer was called with correct config
            args, kwargs = mock_overseer_class.call_args
            config_arg = args[0]
            assert config_arg.agent_mission == 'docs'
            
    @patch('verifier.cli.asyncio.run')
    @patch('verifier.cli.Overseer')
    def test_start_command_with_overrides(self, mock_overseer_class, mock_asyncio_run):
        """Test start command with command line overrides"""
        runner = CliRunner()
        
        mock_overseer = Mock()
        mock_overseer_class.return_value = mock_overseer
        
        result = runner.invoke(start, [
            '--watch-dir', 'custom1',
            '--watch-dir', 'custom2',
            '--mission', 'tooling'
        ])
        
        assert result.exit_code == 0
        
        # Check that overseer was called with overridden config
        args, kwargs = mock_overseer_class.call_args
        config_arg = args[0]
        assert config_arg.watch_dirs == ['custom1', 'custom2']
        assert config_arg.agent_mission == 'tooling'
        
    @patch('verifier.cli.asyncio.run')
    @patch('verifier.cli.Overseer')
    def test_start_command_keyboard_interrupt(self, mock_overseer_class, mock_asyncio_run):
        """Test start command with keyboard interrupt"""
        runner = CliRunner()
        
        mock_overseer = Mock()
        mock_overseer_class.return_value = mock_overseer
        mock_asyncio_run.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(start)
        
        assert result.exit_code == 0
        assert "Shutting down..." in result.output


class TestCLIDemoCommand:
    """Test the demo command specifically"""
    
    @patch('verifier.cli.asyncio.run')
    @patch('verifier.cli.MockOverseer')
    def test_demo_command_default_config(self, mock_overseer_class, mock_asyncio_run):
        """Test demo command with default configuration"""
        runner = CliRunner()
        
        mock_overseer = Mock()
        mock_overseer_class.return_value = mock_overseer
        
        result = runner.invoke(demo)
        
        assert result.exit_code == 0
        assert "Using default configuration" in result.output
        mock_overseer_class.assert_called_once()
        mock_asyncio_run.assert_called_once()
        
    @patch('verifier.cli.asyncio.run')
    @patch('verifier.cli.MockOverseer')
    def test_demo_command_existing_config(self, mock_overseer_class, mock_asyncio_run):
        """Test demo command with existing configuration"""
        runner = CliRunner()
        
        mock_overseer = Mock()
        mock_overseer_class.return_value = mock_overseer
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config = VerifierConfig(agent_mission='docs')
            config.to_file(str(config_path))
            
            result = runner.invoke(demo, ['--config', str(config_path)])
            
            assert result.exit_code == 0
            assert f"Loaded configuration from {config_path}" in result.output
            
            # Check that mock overseer was called with correct config
            args, kwargs = mock_overseer_class.call_args
            config_arg = args[0]
            assert config_arg.agent_mission == 'docs'
            
    @patch('verifier.cli.asyncio.run')
    @patch('verifier.cli.MockOverseer')
    def test_demo_command_with_overrides(self, mock_overseer_class, mock_asyncio_run):
        """Test demo command with command line overrides"""
        runner = CliRunner()
        
        mock_overseer = Mock()
        mock_overseer_class.return_value = mock_overseer
        
        result = runner.invoke(demo, [
            '--watch-dir', 'test_src',
            '--mission', 'docs'
        ])
        
        assert result.exit_code == 0
        
        # Check that mock overseer was called with overridden config
        args, kwargs = mock_overseer_class.call_args
        config_arg = args[0]
        assert config_arg.watch_dirs == ['test_src']
        assert config_arg.agent_mission == 'docs'


class TestCLIHelp:
    """Test CLI help functionality"""
    
    def test_main_help(self):
        """Test main CLI help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Verifier - Automated testing with Claude Code agents" in result.output
        assert "start" in result.output
        assert "demo" in result.output
        assert "init" in result.output
        assert "status" in result.output
        assert "validate" in result.output
        
    def test_start_help(self):
        """Test start command help"""
        runner = CliRunner()
        result = runner.invoke(start, ['--help'])
        
        assert result.exit_code == 0
        assert "Start the verifier overseer process" in result.output
        assert "--config" in result.output
        assert "--watch-dir" in result.output
        assert "--mission" in result.output
        
    def test_demo_help(self):
        """Test demo command help"""
        runner = CliRunner()
        result = runner.invoke(demo, ['--help'])
        
        assert result.exit_code == 0
        assert "Start the verifier with mock agent" in result.output
        assert "for testing" in result.output
        
    def test_init_help(self):
        """Test init command help"""
        runner = CliRunner()
        result = runner.invoke(init, ['--help'])
        
        assert result.exit_code == 0
        assert "Initialize a new verifier configuration" in result.output
        assert "--output" in result.output
        
    def test_status_help(self):
        """Test status command help"""
        runner = CliRunner()
        result = runner.invoke(status, ['--help'])
        
        assert result.exit_code == 0
        assert "Show verifier status and configuration" in result.output
        
    def test_validate_help(self):
        """Test validate command help"""
        runner = CliRunner()
        result = runner.invoke(validate, ['--help'])
        
        assert result.exit_code == 0
        assert "Validate the verifier configuration" in result.output


class TestCLIIntegration:
    """Integration tests for CLI commands"""
    
    def test_full_config_workflow(self):
        """Test a complete configuration workflow"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "workflow_config.json"
            
            # Initialize config
            result = runner.invoke(init, ['--output', str(config_path)])
            assert result.exit_code == 0
            assert config_path.exists()
            
            # Check status
            result = runner.invoke(status, ['--config', str(config_path)])
            assert result.exit_code == 0
            assert "Configuration from" in result.output
            
            # Validate config
            result = runner.invoke(validate, ['--config', str(config_path)])
            assert result.exit_code == 0
            assert "Configuration is valid!" in result.output
            
    @patch('verifier.cli.asyncio.run')
    @patch('verifier.cli.Overseer')
    def test_config_override_precedence(self, mock_overseer_class, mock_asyncio_run):
        """Test that command line options override config file"""
        runner = CliRunner()
        
        mock_overseer = Mock()
        mock_overseer_class.return_value = mock_overseer
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create config with specific values
            config = VerifierConfig(
                watch_dirs=['config_src'],
                agent_mission='testing'
            )
            config.to_file(str(config_path))
            
            # Start with overrides
            result = runner.invoke(start, [
                '--config', str(config_path),
                '--watch-dir', 'override_src',
                '--mission', 'docs'
            ])
            
            assert result.exit_code == 0
            
            # Check that overseer was called with overridden values
            args, kwargs = mock_overseer_class.call_args
            config_arg = args[0]
            assert config_arg.watch_dirs == ['override_src']
            assert config_arg.agent_mission == 'docs'


if __name__ == '__main__':
    pytest.main([__file__])