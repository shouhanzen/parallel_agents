"""
Unit tests for the server components
"""

import pytest
import json
import sys
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from server.app import app, AgentSession, agent_sessions
from server.routes import agents, config, health, working_set
from core.config.models import ParallelAgentsConfig
from core.config.profiles import get_profile
from core.agents.factory import create_agent


class TestAgentSession:
    """Test the AgentSession class"""
    
    def test_session_initialization(self):
        """Test session initialization"""
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        
        assert session.agent_id == "test_agent"
        assert session.config == config
        assert session.agent_type == "verifier"
        assert session.agent is None
        assert session.status == "starting"
        assert session.logs == []
        assert session.websocket_connections == []
    
    def test_add_log(self):
        """Test adding a log message"""
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        
        log_message = {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "Test"}
        session.add_log(log_message)
        
        assert len(session.logs) == 1
        assert session.logs[0] == log_message
    
    def test_log_limit(self):
        """Test log limit enforcement"""
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        
        # Add more than the limit
        for i in range(1200):
            session.add_log({"message": f"Log {i}"})
        
        # Should be limited to 1000
        assert len(session.logs) == 1000
        # Should have the latest logs
        assert session.logs[-1]["message"] == "Log 1199"
    
    def test_add_websocket_connection(self):
        """Test adding websocket connection"""
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        
        mock_ws = Mock()
        session.add_websocket_connection(mock_ws)
        
        assert mock_ws in session.websocket_connections
    
    def test_remove_websocket_connection(self):
        """Test removing websocket connection"""
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        
        mock_ws = Mock()
        session.add_websocket_connection(mock_ws)
        session.remove_websocket_connection(mock_ws)
        
        assert mock_ws not in session.websocket_connections
    
    def test_to_dict(self):
        """Test session serialization"""
        config = ParallelAgentsConfig(code_tool="goose", agent_mission="testing")
        session = AgentSession("test_agent", config, "verifier")
        session.status = "running"
        
        result = session.to_dict()
        
        assert result["agent_id"] == "test_agent"
        assert result["agent_type"] == "verifier"
        assert result["status"] == "running"
        assert result["config"]["code_tool"] == "goose"
        assert result["config"]["agent_mission"] == "testing"
        assert result["logs"] == []
        assert result["websocket_connections"] == 0


class TestHealthRoute:
    """Test the health route"""
    
    def test_health_endpoint(self):
        """Test the health endpoint"""
        from server.routes.health import health
        
        result = health()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "version" in result
        assert "active_agents" in result
        assert result["active_agents"] == 0


class TestConfigRoute:
    """Test the config routes"""
    
    def test_get_profiles(self):
        """Test getting configuration profiles"""
        from server.routes.config import get_profiles
        
        result = get_profiles()
        
        assert result["success"] is True
        assert "profiles" in result
        assert "testing" in result["profiles"]
        assert "documentation" in result["profiles"]
    
    def test_get_profile_existing(self):
        """Test getting a specific profile"""
        from server.routes.config import get_profile_endpoint
        
        result = get_profile_endpoint("testing")
        
        assert result["success"] is True
        assert result["profile_name"] == "testing"
        assert "config" in result
        assert result["config"]["code_tool"] == "goose"
    
    def test_get_profile_nonexistent(self):
        """Test getting a nonexistent profile"""
        from server.routes.config import get_profile_endpoint
        
        result = get_profile_endpoint("nonexistent")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_analyze_project(self):
        """Test project analysis"""
        from server.routes.config import analyze_project
        
        with patch('server.routes.config.os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = analyze_project()
            
            assert result["success"] is True
            assert "analysis" in result
            assert "recommended_profile" in result
    
    def test_create_config(self):
        """Test config creation"""
        from server.routes.config import create_config
        
        config_data = {
            "code_tool": "goose",
            "agent_mission": "testing",
            "log_level": "INFO"
        }
        
        result = create_config(config_data)
        
        assert result["success"] is True
        assert result["config"]["code_tool"] == "goose"
        assert result["config"]["agent_mission"] == "testing"


class TestAgentsRoute:
    """Test the agents routes"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Clear any existing sessions
        agent_sessions.clear()
    
    def test_get_agents_empty(self):
        """Test getting agents when none exist"""
        from server.routes.agents import get_agents
        
        result = get_agents()
        
        assert result["success"] is True
        assert result["agents"] == []
    
    def test_get_agents_with_sessions(self):
        """Test getting agents with existing sessions"""
        from server.routes.agents import get_agents
        
        # Create a test session
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        agent_sessions["test_agent"] = session
        
        result = get_agents()
        
        assert result["success"] is True
        assert len(result["agents"]) == 1
        assert result["agents"][0]["agent_id"] == "test_agent"
    
    def test_get_agent_info_existing(self):
        """Test getting info for existing agent"""
        from server.routes.agents import get_agent_info
        
        # Create a test session
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        agent_sessions["test_agent"] = session
        
        result = get_agent_info("test_agent")
        
        assert result["success"] is True
        assert result["agent_id"] == "test_agent"
        assert result["agent_type"] == "verifier"
    
    def test_get_agent_info_nonexistent(self):
        """Test getting info for nonexistent agent"""
        from server.routes.agents import get_agent_info
        
        result = get_agent_info("nonexistent")
        
        assert result["success"] is False
        assert "error" in result
    
    @patch('server.routes.agents.create_agent')
    def test_start_agent_success(self, mock_create_agent):
        """Test starting an agent successfully"""
        from server.routes.agents import start_agent
        
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        
        config_data = {
            "code_tool": "goose",
            "agent_mission": "testing",
            "agent_type": "verifier"
        }
        
        result = start_agent("test_agent", config_data)
        
        assert result["success"] is True
        assert result["agent_id"] == "test_agent"
        assert result["agent_type"] == "verifier"
        assert "test_agent" in agent_sessions
    
    @patch('server.routes.agents.create_agent')
    def test_start_agent_already_exists(self, mock_create_agent):
        """Test starting an agent that already exists"""
        from server.routes.agents import start_agent
        
        # Create existing session
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        agent_sessions["test_agent"] = session
        
        config_data = {
            "code_tool": "goose",
            "agent_mission": "testing",
            "agent_type": "verifier"
        }
        
        result = start_agent("test_agent", config_data)
        
        assert result["success"] is False
        assert "already exists" in result["error"]
    
    def test_stop_agent_success(self):
        """Test stopping an agent successfully"""
        from server.routes.agents import stop_agent
        
        # Create a test session
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        agent_sessions["test_agent"] = session
        
        result = stop_agent("test_agent")
        
        assert result["success"] is True
        assert "test_agent" not in agent_sessions
    
    def test_stop_agent_nonexistent(self):
        """Test stopping a nonexistent agent"""
        from server.routes.agents import stop_agent
        
        result = stop_agent("nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_process_files_success(self):
        """Test processing files successfully"""
        from server.routes.agents import process_files_endpoint
        
        # Create a test session with mock agent
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        session.agent = Mock()
        session.agent.process_files.return_value = {"success": True}
        session.status = "running"
        agent_sessions["test_agent"] = session
        
        file_changes = [{"file": "test.py", "action": "modified"}]
        result = process_files_endpoint("test_agent", file_changes)
        
        assert result["success"] is True
        session.agent.process_files.assert_called_once_with(file_changes)
    
    def test_process_files_agent_not_running(self):
        """Test processing files when agent is not running"""
        from server.routes.agents import process_files_endpoint
        
        # Create a test session without running agent
        config = ParallelAgentsConfig(code_tool="goose")
        session = AgentSession("test_agent", config, "verifier")
        session.status = "stopped"
        agent_sessions["test_agent"] = session
        
        file_changes = [{"file": "test.py", "action": "modified"}]
        result = process_files_endpoint("test_agent", file_changes)
        
        assert result["success"] is False
        assert "not running" in result["error"]


class TestWorkingSetRoute:
    """Test the working set routes"""
    
    def test_get_working_set_files(self):
        """Test getting working set files"""
        from server.routes.working_set import get_working_set_files
        
        with patch('server.routes.working_set.os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('server.routes.working_set.os.listdir') as mock_listdir:
                mock_listdir.return_value = ["test.py", "README.md"]
                
                result = get_working_set_files()
                
                assert result["success"] is True
                assert len(result["files"]) == 2
    
    def test_get_working_set_files_no_directory(self):
        """Test getting working set files when directory doesn't exist"""
        from server.routes.working_set import get_working_set_files
        
        with patch('server.routes.working_set.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = get_working_set_files()
            
            assert result["success"] is True
            assert result["files"] == []
    
    def test_add_working_set_file(self):
        """Test adding a file to working set"""
        from server.routes.working_set import add_working_set_file
        
        with patch('server.routes.working_set.os.makedirs') as mock_makedirs:
            with patch('server.routes.working_set.shutil.copy2') as mock_copy:
                result = add_working_set_file("test.py")
                
                assert result["success"] is True
                mock_makedirs.assert_called_once()
                mock_copy.assert_called_once()
    
    def test_remove_working_set_file(self):
        """Test removing a file from working set"""
        from server.routes.working_set import remove_working_set_file
        
        with patch('server.routes.working_set.os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('server.routes.working_set.os.remove') as mock_remove:
                result = remove_working_set_file("test.py")
                
                assert result["success"] is True
                mock_remove.assert_called_once()
    
    def test_remove_working_set_file_not_exists(self):
        """Test removing a file that doesn't exist"""
        from server.routes.working_set import remove_working_set_file
        
        with patch('server.routes.working_set.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = remove_working_set_file("test.py")
            
            assert result["success"] is False
            assert "not found" in result["error"] 