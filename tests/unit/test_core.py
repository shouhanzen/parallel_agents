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
from core.monitoring.working_set import WorkingSet
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
    
    @patch('core.agents.factory.GooseAgent')
    def test_create_verifier_agent_goose(self, mock_goose_agent):
        """Test creating a Goose verifier agent"""
        mock_agent = Mock()
        mock_goose_agent.return_value = mock_agent
        
        config = ParallelAgentsConfig(code_tool="goose")
        agent = create_agent(config, "verifier")
        
        assert agent is mock_agent
        mock_goose_agent.assert_called_once_with(config)
    
    @patch('core.agents.factory.ClaudeCodeAgent')
    def test_create_verifier_agent_claude(self, mock_claude_agent):
        """Test creating a Claude Code verifier agent"""
        mock_agent = Mock()
        mock_claude_agent.return_value = mock_agent
        
        config = ParallelAgentsConfig(code_tool="claude_code")
        agent = create_agent(config, "verifier")
        
        assert agent is mock_agent
        mock_claude_agent.assert_called_once_with(config)
    
    @patch('core.agents.factory.MockAgent')
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
        
        with pytest.raises(ValueError, match="Unsupported code tool"):
            create_agent(config, "verifier")
    
    def test_create_agent_invalid_type(self):
        """Test creating agent with invalid type"""
        config = ParallelAgentsConfig(code_tool="goose")
        
        with pytest.raises(ValueError, match="Unsupported agent type"):
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
        
        config = ParallelAgentsConfig()
        agent = TestAgent(config)
        
        assert agent.config == config
        assert hasattr(agent, 'process_files')
        assert hasattr(agent, 'stop')
        
        # Test method calls
        result = agent.process_files([])
        assert result["success"] is True
        
        result = agent.stop()
        assert result["success"] is True


class TestWorkingSet:
    """Test the working set functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.working_set = WorkingSet(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_working_set_initialization(self):
        """Test working set initialization"""
        assert self.working_set.working_dir == self.temp_dir
        assert os.path.exists(self.temp_dir)
    
    def test_add_file(self):
        """Test adding a file to working set"""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")
        
        result = self.working_set.add_file("test.py")
        
        assert result["success"] is True
        assert os.path.exists(os.path.join(self.temp_dir, "test.py"))
    
    def test_remove_file(self):
        """Test removing a file from working set"""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")
        
        result = self.working_set.remove_file("test.py")
        
        assert result["success"] is True
        assert not os.path.exists(test_file)
    
    def test_list_files(self):
        """Test listing files in working set"""
        # Create test files
        files = ["test1.py", "test2.py", "README.md"]
        for file in files:
            with open(os.path.join(self.temp_dir, file), 'w') as f:
                f.write("content")
        
        result = self.working_set.list_files()
        
        assert result["success"] is True
        assert len(result["files"]) == 3
        assert all(file in result["files"] for file in files)
    
    def test_get_file_content(self):
        """Test getting file content"""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.py")
        content = "print('hello world')"
        with open(test_file, 'w') as f:
            f.write(content)
        
        result = self.working_set.get_file_content("test.py")
        
        assert result["success"] is True
        assert result["content"] == content
    
    def test_get_file_content_nonexistent(self):
        """Test getting content of nonexistent file"""
        result = self.working_set.get_file_content("nonexistent.py")
        
        assert result["success"] is False
        assert "not found" in result["error"]


class TestDeltaGate:
    """Test the delta gate functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.delta_gate = DeltaGate(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_delta_gate_initialization(self):
        """Test delta gate initialization"""
        assert self.delta_gate.watch_dir == self.temp_dir
        assert self.delta_gate.is_watching is False
    
    def test_start_watching(self):
        """Test starting file watching"""
        self.delta_gate.start_watching()
        
        assert self.delta_gate.is_watching is True
    
    def test_stop_watching(self):
        """Test stopping file watching"""
        self.delta_gate.start_watching()
        self.delta_gate.stop_watching()
        
        assert self.delta_gate.is_watching is False
    
    def test_detect_changes(self):
        """Test detecting file changes"""
        self.delta_gate.start_watching()
        
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")
        
        # Give it a moment to detect the change
        import time
        time.sleep(0.1)
        
        changes = self.delta_gate.get_changes()
        
        assert len(changes) > 0
        assert any(change["file"].endswith("test.py") for change in changes)
    
    def test_filter_changes(self):
        """Test filtering file changes"""
        self.delta_gate.start_watching()
        
        # Create files with different extensions
        test_files = [
            ("test.py", "print('hello')"),
            ("test.txt", "text content"),
            ("test.log", "log content"),
            (".hidden", "hidden content")
        ]
        
        for filename, content in test_files:
            with open(os.path.join(self.temp_dir, filename), 'w') as f:
                f.write(content)
        
        # Give it a moment to detect changes
        import time
        time.sleep(0.1)
        
        changes = self.delta_gate.get_changes()
        
        # Should filter out .log and .hidden files
        filtered_changes = [
            change for change in changes
            if not change["file"].endswith((".log", ".hidden"))
        ]
        
        assert len(filtered_changes) >= 2  # .py and .txt files
    
    def test_clear_changes(self):
        """Test clearing detected changes"""
        self.delta_gate.start_watching()
        
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")
        
        # Give it a moment to detect the change
        import time
        time.sleep(0.1)
        
        changes = self.delta_gate.get_changes()
        assert len(changes) > 0
        
        self.delta_gate.clear_changes()
        changes = self.delta_gate.get_changes()
        assert len(changes) == 0


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
    
    @patch('core.agents.factory.MockAgent')
    def test_agent_with_working_set(self, mock_mock_agent):
        """Test agent integration with working set"""
        mock_agent = Mock()
        mock_mock_agent.return_value = mock_agent
        
        # Create agent
        agent = create_agent(self.config, "verifier")
        
        # Create working set
        working_set = WorkingSet(self.temp_dir)
        
        # Add file to working set
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")
        
        working_set.add_file("test.py")
        
        # Process files with agent
        file_changes = [{"file": "test.py", "action": "created"}]
        mock_agent.process_files.return_value = {"success": True}
        
        result = agent.process_files(file_changes)
        
        assert result["success"] is True
        mock_agent.process_files.assert_called_once_with(file_changes)
    
    @patch('core.agents.factory.MockAgent')
    def test_agent_with_delta_gate(self, mock_mock_agent):
        """Test agent integration with delta gate"""
        mock_agent = Mock()
        mock_mock_agent.return_value = mock_agent
        
        # Create agent
        agent = create_agent(self.config, "verifier")
        
        # Create delta gate
        delta_gate = DeltaGate(self.temp_dir)
        delta_gate.start_watching()
        
        # Create a file change
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")
        
        # Give it a moment to detect the change
        import time
        time.sleep(0.1)
        
        changes = delta_gate.get_changes()
        
        # Process changes with agent
        mock_agent.process_files.return_value = {"success": True}
        result = agent.process_files(changes)
        
        assert result["success"] is True
        mock_agent.process_files.assert_called_once_with(changes)
        
        delta_gate.stop_watching()
    
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
    
    def test_full_integration_flow(self):
        """Test full integration flow"""
        # Get a profile
        config = get_profile("testing")
        assert config is not None
        
        # Create agent (mock to avoid external dependencies)
        with patch('core.agents.factory.MockAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            agent = create_agent(config, "verifier")
            
            # Create working environment
            working_set = WorkingSet(self.temp_dir)
            delta_gate = DeltaGate(self.temp_dir)
            
            # Start monitoring
            delta_gate.start_watching()
            
            # Simulate file changes
            test_file = os.path.join(self.temp_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("print('hello')")
            
            # Give it a moment to detect changes
            import time
            time.sleep(0.1)
            
            changes = delta_gate.get_changes()
            
            # Process with agent
            mock_agent.process_files.return_value = {
                "success": True,
                "message": "Files processed successfully"
            }
            
            result = agent.process_files(changes)
            
            assert result["success"] is True
            assert "processed successfully" in result["message"]
            
            # Clean up
            delta_gate.stop_watching()
            agent.stop() 