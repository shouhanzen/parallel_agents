"""
Unit tests for the client SDK
"""

import pytest
import json
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from client.client import ParallelAgentsClient
from client.agent import AgentProxy
from client.exceptions import ClientError, ServerError, AgentNotFoundError


class TestParallelAgentsClient:
    """Test the main client class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = ParallelAgentsClient(host="localhost", port=8000)
    
    def test_client_initialization(self):
        """Test client initialization"""
        assert self.client.host == "localhost"
        assert self.client.port == 8000
        assert self.client.base_url == "http://localhost:8000/api"
        assert self.client.websocket_url == "ws://localhost:8000/ws"
        assert self.client.timeout == 30
    
    def test_client_custom_config(self):
        """Test client with custom configuration"""
        client = ParallelAgentsClient(host="example.com", port=9000, timeout=60)
        assert client.host == "example.com"
        assert client.port == 9000
        assert client.timeout == 60
    
    @patch('client.client.requests.Session.request')
    def test_make_request_success(self, mock_request):
        """Test successful HTTP request"""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        result = self.client._make_request("GET", "/test")
        
        assert result == {"success": True, "data": "test"}
        mock_request.assert_called_once_with("GET", "http://localhost:8000/api/test")
    
    @patch('client.client.requests.Session.request')
    def test_make_request_server_error(self, mock_request):
        """Test HTTP request with server error"""
        from requests.exceptions import HTTPError
        
        mock_response = Mock()
        mock_response.json.return_value = {"detail": "Server error"}
        
        error = HTTPError()
        error.response = mock_response
        mock_request.side_effect = error
        
        with pytest.raises(ServerError, match="Server error"):
            self.client._make_request("GET", "/test")
    
    @patch('client.client.requests.Session.request')
    def test_make_request_connection_error(self, mock_request):
        """Test HTTP request with connection error"""
        from requests.exceptions import ConnectionError
        
        mock_request.side_effect = ConnectionError("Connection failed")
        
        with pytest.raises(ClientError, match="Connection error"):
            self.client._make_request("GET", "/test")
    
    @patch.object(ParallelAgentsClient, '_make_request')
    def test_health_check(self, mock_request):
        """Test health check"""
        mock_request.return_value = {"status": "healthy"}
        
        result = self.client.health_check()
        
        assert result == {"status": "healthy"}
        mock_request.assert_called_once_with("GET", "/health/")
    
    @patch.object(ParallelAgentsClient, '_make_request')
    def test_get_config_profiles(self, mock_request):
        """Test getting configuration profiles"""
        mock_request.return_value = {
            "success": True,
            "profiles": {"testing": {"description": "Test profile"}}
        }
        
        result = self.client.get_config_profiles()
        
        assert result["success"] is True
        assert "testing" in result["profiles"]
        mock_request.assert_called_once_with("GET", "/config/profiles")
    
    @patch.object(ParallelAgentsClient, '_make_request')
    def test_start_agent_success(self, mock_request):
        """Test starting an agent successfully"""
        mock_request.return_value = {
            "success": True,
            "agent_id": "test_agent",
            "agent_type": "verifier"
        }
        
        config = {"code_tool": "goose", "agent_mission": "testing"}
        agent = self.client.start_agent("test_agent", config)
        
        assert isinstance(agent, AgentProxy)
        assert agent.agent_id == "test_agent"
        assert agent.agent_type == "verifier"
        assert "test_agent" in self.client._agent_proxies
    
    @patch.object(ParallelAgentsClient, '_make_request')
    def test_start_agent_failure(self, mock_request):
        """Test starting an agent with failure"""
        mock_request.return_value = {
            "success": False,
            "message": "Agent creation failed"
        }
        
        config = {"code_tool": "goose"}
        
        with pytest.raises(ClientError, match="Failed to start agent"):
            self.client.start_agent("test_agent", config)
    
    @patch.object(ParallelAgentsClient, '_make_request')
    def test_stop_agent(self, mock_request):
        """Test stopping an agent"""
        # First create an agent proxy
        proxy = AgentProxy("test_agent", self.client)
        self.client._agent_proxies["test_agent"] = proxy
        
        mock_request.return_value = {"success": True}
        
        result = self.client.stop_agent("test_agent")
        
        assert result["success"] is True
        assert "test_agent" not in self.client._agent_proxies
    
    @patch.object(ParallelAgentsClient, '_make_request')
    def test_get_agent_existing(self, mock_request):
        """Test getting an existing agent"""
        # Create an existing agent proxy
        proxy = AgentProxy("test_agent", self.client)
        self.client._agent_proxies["test_agent"] = proxy
        
        result = self.client.get_agent("test_agent")
        
        assert result is proxy
        assert result.agent_id == "test_agent"
    
    @patch.object(ParallelAgentsClient, '_make_request')
    def test_get_agent_from_server(self, mock_request):
        """Test getting an agent from server"""
        mock_request.return_value = {
            "success": True,
            "agent_type": "documentation"
        }
        
        result = self.client.get_agent("test_agent")
        
        assert isinstance(result, AgentProxy)
        assert result.agent_id == "test_agent"
        assert result.agent_type == "documentation"
    
    @patch.object(ParallelAgentsClient, '_make_request')
    def test_get_agent_not_found(self, mock_request):
        """Test getting a non-existent agent"""
        mock_request.side_effect = ServerError("404 Not Found")
        
        with pytest.raises(AgentNotFoundError):
            self.client.get_agent("nonexistent_agent")
    
    def test_cleanup(self):
        """Test client cleanup"""
        # Add some mock resources
        mock_ws = Mock()
        self.client._websocket_connections["test"] = mock_ws
        self.client._log_callbacks["test"] = [lambda x: None]
        
        mock_proxy = Mock()
        self.client._agent_proxies["test"] = mock_proxy
        
        self.client.cleanup()
        
        assert len(self.client._websocket_connections) == 0
        assert len(self.client._log_callbacks) == 0
        assert len(self.client._agent_proxies) == 0
        mock_proxy._cleanup.assert_called_once()
    
    def test_context_manager(self):
        """Test client as context manager"""
        with patch.object(self.client, 'cleanup') as mock_cleanup:
            with self.client as client:
                assert client is self.client
            mock_cleanup.assert_called_once()


class TestAgentProxy:
    """Test the agent proxy class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=ParallelAgentsClient)
        self.proxy = AgentProxy("test_agent", self.mock_client, "verifier")
    
    def test_proxy_initialization(self):
        """Test proxy initialization"""
        assert self.proxy.agent_id == "test_agent"
        assert self.proxy.client is self.mock_client
        assert self.proxy.agent_type == "verifier"
        assert self.proxy._log_callbacks == []
    
    def test_status_property(self):
        """Test status property"""
        self.mock_client.get_agent_info.return_value = {
            "success": True,
            "status": "running"
        }
        
        status = self.proxy.status
        
        assert status["success"] is True
        assert status["status"] == "running"
        self.mock_client.get_agent_info.assert_called_once_with("test_agent")
    
    def test_config_property(self):
        """Test config property"""
        self.mock_client.get_agent_info.return_value = {
            "config": {"code_tool": "goose", "agent_mission": "testing"}
        }
        
        config = self.proxy.config
        
        assert config["code_tool"] == "goose"
        assert config["agent_mission"] == "testing"
    
    def test_process_files(self):
        """Test file processing"""
        file_changes = [{"file": "test.py", "action": "modified"}]
        self.mock_client.process_files.return_value = {"success": True}
        
        result = self.proxy.process_files(file_changes)
        
        assert result["success"] is True
        self.mock_client.process_files.assert_called_once_with("test_agent", file_changes)
    
    def test_stop(self):
        """Test stopping the agent"""
        self.mock_client.stop_agent.return_value = {"success": True}
        
        result = self.proxy.stop()
        
        assert result["success"] is True
        self.mock_client.stop_agent.assert_called_once_with("test_agent")
    
    def test_subscribe_to_logs(self):
        """Test log subscription"""
        callback = lambda x: None
        
        self.proxy.subscribe_to_logs(callback)
        
        assert callback in self.proxy._log_callbacks
        self.mock_client.subscribe_to_agent_logs.assert_called_once_with("test_agent", callback)
    
    def test_unsubscribe_from_logs(self):
        """Test log unsubscription"""
        callback = lambda x: None
        self.proxy._log_callbacks.append(callback)
        
        self.proxy.unsubscribe_from_logs(callback)
        
        assert callback not in self.proxy._log_callbacks
        self.mock_client.unsubscribe_from_agent_logs.assert_called_once_with("test_agent", callback)
    
    def test_cleanup(self):
        """Test proxy cleanup"""
        callback1 = lambda x: None
        callback2 = lambda x: None
        self.proxy._log_callbacks = [callback1, callback2]
        
        with patch.object(self.proxy, 'unsubscribe_from_logs') as mock_unsub:
            self.proxy._cleanup()
            
            assert len(self.proxy._log_callbacks) == 0
            assert mock_unsub.call_count == 2
    
    def test_repr(self):
        """Test string representation"""
        assert repr(self.proxy) == "AgentProxy(agent_id='test_agent', type='verifier')"
        assert str(self.proxy) == "Agent test_agent (verifier)" 