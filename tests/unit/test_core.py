"""
Unit tests for core components
"""

import pytest
import json
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.config.models import ParallelAgentsConfig
from core.config.profiles import get_profile, list_profiles
from core.agents.factory import create_agent
from core.agents.base import BaseAgent
from core.monitoring.working_set import WorkingSetManager
from core.monitoring.delta_gate import DeltaGate


class TestParallelAgentsConfig:
    """Test the configuration model"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = ParallelAgentsConfig()
        
        assert config.code_tool == "goose"
        assert config.agent_mission == "You are a helpful AI assistant"
        assert config.log_level == "INFO"
        assert config.max_iterations == 10
        assert config.timeout == 300
        assert config.goose_timeout == 600
        assert config.goose_log_file == "goose.log"
    
    def test_config_custom_values(self):
        """Test configuration with custom values"""
        config = ParallelAgentsConfig(
            code_tool="claude_code",
            agent_mission="Test mission",
            log_level="DEBUG",
            max_iterations=5,
            timeout=120
        )
        
        assert config.code_tool == "claude_code"
        assert config.agent_mission == "Test mission"
        assert config.log_level == "DEBUG"
        assert config.max_iterations == 5
        assert config.timeout == 120
    
    def test_config_to_dict(self):
        """Test configuration serialization"""
        config = ParallelAgentsConfig(
            code_tool="goose",
            agent_mission="Testing",
            log_level="INFO"
        )
        
        result = config.to_dict()
        
        assert result["code_tool"] == "goose"
        assert result["agent_mission"] == "Testing"
        assert result["log_level"] == "INFO"
        assert isinstance(result, dict)
    
    def test_config_from_dict(self):
        """Test configuration deserialization"""
        data = {
            "code_tool": "claude_code",
            "agent_mission": "Test mission",
            "log_level": "DEBUG",
            "max_iterations": 3
        }
        
        config = ParallelAgentsConfig.from_dict(data)
        
        assert config.code_tool == "claude_code"
        assert config.agent_mission == "Test mission"
        assert config.log_level == "DEBUG"
        assert config.max_iterations == 3
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test valid code_tool
        config = ParallelAgentsConfig(code_tool="goose")
        assert config.code_tool == "goose"
        
        # Test valid log_level
        config = ParallelAgentsConfig(log_level="DEBUG")
        assert config.log_level == "DEBUG"
        
        # Test that invalid values don't break the config
        config = ParallelAgentsConfig(max_iterations=0)
        assert config.max_iterations == 0  # Should accept 0 as valid
    
    def test_config_comparison(self):
        """Test configuration comparison"""
        config1 = ParallelAgentsConfig(code_tool="goose", agent_mission="Test")
        config2 = ParallelAgentsConfig(code_tool="goose", agent_mission="Test")
        config3 = ParallelAgentsConfig(code_tool="claude_code", agent_mission="Test")
        
        assert config1 == config2
        assert config1 != config3


class TestConfigProfiles:
    """Test configuration profiles"""
    
    def test_list_profiles(self):
        """Test listing available profiles"""
        profiles = list_profiles()
        
        assert isinstance(profiles, dict)
        assert "testing" in profiles
        assert "documentation" in profiles
        assert "demo" in profiles
        assert "minimal" in profiles
        assert "full_stack" in profiles
    
    def test_get_profile_testing(self):
        """Test getting testing profile"""
        profile = get_profile("testing")
        
        assert profile is not None
        assert profile.code_tool == "goose"
        assert profile.log_level == "DEBUG"
        assert profile.max_iterations == 3
    
    def test_get_profile_documentation(self):
        """Test getting documentation profile"""
        profile = get_profile("documentation")
        
        assert profile is not None
        assert profile.code_tool == "goose"
        assert "documentation" in profile.agent_mission.lower()
    
    def test_get_profile_nonexistent(self):
        """Test getting nonexistent profile"""
        profile = get_profile("nonexistent")
        
        assert profile is None
    
    def test_profile_inheritance(self):
        """Test that profiles have proper inheritance"""
        testing_profile = get_profile("testing")
        minimal_profile = get_profile("minimal")
        
        # Both should have valid configurations
        assert testing_profile.code_tool in ["goose", "claude_code"]
        assert minimal_profile.code_tool in ["goose", "claude_code"]
        
        # Testing should have more specific settings
        assert testing_profile.max_iterations <= 5
        assert testing_profile.log_level == "DEBUG"


class TestAgentFactory:
    """Test the agent factory"""
    
    @patch('core.agents.goose.agent.BlockGooseVerifierAgent')
    @pytest.mark.skip(reason="BlockGooseVerifierAgent is abstract and needs full implementation")
    def test_create_verifier_agent_goose(self, mock_goose_agent):
        """Test creating a Goose verifier agent"""
        mock_agent = Mock()
        mock_goose_agent.return_value = mock_agent
        
        config = ParallelAgentsConfig(code_tool="goose")
        agent = create_agent(config, "verifier")
        
        assert agent is mock_agent
        mock_goose_agent.assert_called_once_with(config)
    
    @patch('core.agents.claude.agent.ClaudeCodeVerifierAgent')
    @pytest.mark.skip(reason="ClaudeCodeVerifierAgent is abstract and needs full implementation")
    def test_create_verifier_agent_claude(self, mock_claude_agent):
        """Test creating a Claude Code verifier agent"""
        mock_agent = Mock()
        mock_claude_agent.return_value = mock_agent
        
        config = ParallelAgentsConfig(code_tool="claude_code")
        agent = create_agent(config, "verifier")
        
        assert agent is mock_agent
        mock_claude_agent.assert_called_once_with(config)
    
    @patch('core.agents.mock.agent.MockVerifierAgent')
    def test_create_mock_agent(self, mock_mock_agent):
        """Test creating a mock agent"""
        mock_agent = Mock()
        mock_mock_agent.return_value = mock_agent
        
        config = ParallelAgentsConfig(code_tool="mock")
        agent = create_agent(config, "verifier")
        
        assert agent is mock_agent
        mock_mock_agent.assert_called_once_with(config)
    
    def test_create_agent_invalid_tool(self):
        """Test creating agent with invalid tool"""
        config = ParallelAgentsConfig(code_tool="invalid_tool")
        
        with pytest.raises(ValueError, match="Unknown code tool"):
            create_agent(config, "verifier")
    
    def test_create_agent_invalid_type(self):
        """Test creating agent with invalid type"""
        config = ParallelAgentsConfig(code_tool="goose")
        
        with pytest.raises(ValueError, match="Unknown agent type"):
            create_agent(config, "invalid_type")


class TestBaseAgent:
    """Test the base agent class"""
    
    def test_base_agent_abstract(self):
        """Test that BaseAgent is abstract"""
        config = ParallelAgentsConfig()
        
        with pytest.raises(TypeError):
            BaseAgent(config)
    
    def test_base_agent_interface(self):
        """Test base agent interface"""
        # Create a concrete implementation
        class TestAgent(BaseAgent):
            def process_files(self, file_changes):
                return {"success": True}

            def stop(self):
                return {"success": True}
                
            def _get_working_set_dir(self):
                return Path("test_working_set")
                
            def _get_mission_prompt(self):
                return "Test mission prompt"
                
            def _get_file_deltas_prompt(self, file_changes):
                return "Test file deltas prompt"
                
            def _get_mission_reminder(self):
                return "Test mission reminder"
                
            def _get_log_file_path(self):
                return Path("test.log")
                
            def _get_session_start_message(self):
                return "Test session started"
                
            def _get_process_success_message(self, change_count):
                return f"Processed {change_count} changes"

        config = ParallelAgentsConfig()
        agent = TestAgent(config, "test")
        
        # Test interface exists
        assert hasattr(agent, 'process_files')
        assert hasattr(agent, 'stop')
        
        # Test interface works
        result = agent.process_files([])
        assert result["success"] is True
        
        stop_result = agent.stop()
        assert stop_result["success"] is True


class TestWorkingSet:
    """Test the working set functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.working_set = WorkingSetManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_working_set_initialization(self):
        """Test working set initialization"""
        assert self.working_set.working_set_dir == Path(self.temp_dir)
        assert self.working_set.working_set_dir.exists()
    
    def test_add_file(self):
        """Test adding a file to working set"""
        test_content = "print('hello')"
        test_file = self.working_set.create_test_file("test_example", test_content)
        
        assert test_file.exists()
        assert test_file.read_text() == test_content
        assert test_file.name == "test_example.py"
    
    def test_remove_file(self):
        """Test removing a file from working set"""
        # Create a test file first
        self.working_set.create_test_file("test_example", "print('hello')")
        
        result = self.working_set.remove_test_file("test_example")
        
        assert result is True
        assert not (self.working_set.working_set_dir / "test_example.py").exists()
    
    def test_list_files(self):
        """Test listing files in working set"""
        # Create test files
        test_files = ["test_example1", "test_example2", "test_example3"]
        for test_name in test_files:
            self.working_set.create_test_file(test_name, "content")
        
        files = self.working_set.list_test_files()
        
        assert len(files) == 3
        assert all(f.name.startswith("test_") and f.name.endswith(".py") for f in files)
    
    def test_get_file_content(self):
        """Test getting file content"""
        content = "print('hello world')"
        test_file = self.working_set.create_test_file("test_example", content)
        
        # Read content directly from file
        actual_content = test_file.read_text()
        
        assert actual_content == content
    
    def test_get_file_content_nonexistent(self):
        """Test getting content of nonexistent file"""
        nonexistent_file = self.working_set.working_set_dir / "nonexistent.py"
        
        assert not nonexistent_file.exists()


class TestDeltaGate:
    """Test the delta gate functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.delta_gate = DeltaGate()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_delta_gate_initialization(self):
        """Test delta gate initialization"""
        assert hasattr(self.delta_gate, 'config')
        assert self.delta_gate.get_pending_count() == 0
    
    def test_start_watching(self):
        """Test adding changes to the gate"""
        test_file = str(Path(self.temp_dir) / "test.py")
        
        result = self.delta_gate.add_change(test_file, "created")
        
        assert result is True
        assert self.delta_gate.get_pending_count() == 1
    
    def test_stop_watching(self):
        """Test clearing pending changes"""
        test_file = str(Path(self.temp_dir) / "test.py")
        self.delta_gate.add_change(test_file, "created")
        
        self.delta_gate.clear_pending()
        
        assert self.delta_gate.get_pending_count() == 0
    
    def test_detect_changes(self):
        """Test detecting and batching file changes"""
        test_file = str(Path(self.temp_dir) / "test.py")
        
        # Add a change
        self.delta_gate.add_change(test_file, "created")
        
        # Force batch processing by waiting
        import time
        time.sleep(0.1)
        
        # Should have pending changes
        assert self.delta_gate.get_pending_count() > 0
        
        # Get the batch
        batch = self.delta_gate.get_batch()
        
        assert len(batch) > 0
        assert batch[0]["file_path"] == test_file
        assert batch[0]["action"] == "created"
    
    def test_filter_changes(self):
        """Test filtering file changes"""
        # Test files with different extensions
        test_files = [
            (str(Path(self.temp_dir) / "test.py"), "created", True),  # Should be accepted
            (str(Path(self.temp_dir) / "test.pyc"), "created", False),  # Should be ignored
            (str(Path(self.temp_dir) / "test.log"), "created", False),  # Should be ignored
            (str(Path(self.temp_dir) / ".hidden"), "created", False)  # Should be ignored
        ]
        
        for file_path, action, should_accept in test_files:
            result = self.delta_gate.add_change(file_path, action)
            if should_accept:
                assert result is True, f"Should accept {file_path}"
            else:
                assert result is False, f"Should ignore {file_path}"
    
    def test_clear_changes(self):
        """Test clearing all pending changes"""
        # Add multiple changes
        for i in range(3):
            test_file = str(Path(self.temp_dir) / f"test{i}.py")
            self.delta_gate.add_change(test_file, "created")
        
        assert self.delta_gate.get_pending_count() == 3
        
        self.delta_gate.clear_pending()
        
        assert self.delta_gate.get_pending_count() == 0


class TestAgentIntegration:
    """Test agent integration with config and monitoring"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = ParallelAgentsConfig(
            code_tool="mock",
            agent_mission="Testing integration",
            log_level="DEBUG"
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('core.agents.mock.agent.MockVerifierAgent')
    def test_agent_with_working_set(self, mock_mock_agent):
        """Test agent integration with working set"""
        mock_agent = Mock()
        mock_mock_agent.return_value = mock_agent
        
        # Create agent
        agent = create_agent(self.config, "verifier")
        
        # Create working set
        working_set = WorkingSetManager(self.temp_dir)
        
        # Add file to working set using the correct API
        test_content = "print('hello')"
        test_file = working_set.create_test_file("test_example", test_content)
        
        # Process files with agent
        file_changes = [{"file": str(test_file), "action": "created"}]
        mock_agent.process_files.return_value = {"success": True}
        
        result = agent.process_files(file_changes)
        
        assert result["success"] is True
        mock_agent.process_files.assert_called_once_with(file_changes)
    
    @patch('core.agents.mock.agent.MockVerifierAgent')
    def test_agent_with_delta_gate(self, mock_mock_agent):
        """Test agent integration with delta gate"""
        mock_agent = Mock()
        mock_mock_agent.return_value = mock_agent
        
        # Create agent
        agent = create_agent(self.config, "verifier")
        
        # Create delta gate
        delta_gate = DeltaGate()
        
        # Add changes to delta gate
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")
        
        # Add change to delta gate
        delta_gate.add_change(test_file, "created")
        
        # Get changes from delta gate
        changes = delta_gate.get_batch()
        
        # Process changes with agent
        mock_agent.process_files.return_value = {"success": True}
        result = agent.process_files(changes)
        
        assert result["success"] is True
        mock_agent.process_files.assert_called_once_with(changes)
    
    def test_config_profile_integration(self):
        """Test configuration profile integration"""
        # Test different profiles create different configurations
        testing_profile = get_profile("testing")
        documentation_profile = get_profile("documentation")
        
        assert testing_profile != documentation_profile
        assert testing_profile.code_tool == "goose"
        assert documentation_profile.code_tool == "goose"
        
        # Test that profiles have appropriate settings
        assert testing_profile.max_iterations <= 5
        assert testing_profile.log_level == "DEBUG"
    
    @patch('core.agents.mock.agent.MockVerifierAgent')
    def test_full_integration_flow(self, mock_mock_agent):
        """Test full integration flow"""
        mock_agent = Mock()
        mock_mock_agent.return_value = mock_agent
        
        # Get a profile and override to use mock agent
        config = get_profile("testing")
        config.code_tool = "mock"  # Override to use mock agent for testing
        assert config is not None
        
        # Create agent
        agent = create_agent(config, "verifier")
        
        # Create working environment
        working_set = WorkingSetManager(self.temp_dir)
        delta_gate = DeltaGate()
        
        # Simulate file changes
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")
        
        # Add change to delta gate
        delta_gate.add_change(test_file, "created")
        
        # Get changes
        changes = delta_gate.get_batch()
        
        # Process with agent
        mock_agent.process_files.return_value = {
            "success": True,
            "message": "Files processed successfully"
        }
        
        result = agent.process_files(changes)
        
        assert result["success"] is True
        assert "processed successfully" in result["message"]
        
        # Clean up
        mock_agent.stop.return_value = {"success": True}
        agent.stop() 