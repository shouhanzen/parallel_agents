"""
End-to-end tests for client-server integration
"""

import pytest
import asyncio
import json
import sys
import time
import subprocess
import requests
from pathlib import Path
from unittest.mock import patch
import platform
import tempfile
import os
import signal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from client.client import ParallelAgentsClient
from client.exceptions import ClientError, ServerError
from core.config.models import ParallelAgentsConfig


class TestClientServerIntegration:
    """Test client-server integration"""
    
    @classmethod
    def setup_class(cls):
        """Set up server for testing"""
        cls.server_process = None
        cls.start_server()
        
        # Wait for server to start
        time.sleep(2)
        
        # Verify server is running
        try:
            response = requests.get("http://localhost:8000/api/health/")
            assert response.status_code == 200
        except requests.ConnectionError:
            pytest.fail("Server failed to start")
    
    @classmethod
    def teardown_class(cls):
        """Stop server after testing"""
        cls.stop_server()
    
    @classmethod
    def start_server(cls):
        """Start the server in background"""
        import os
        server_path = Path(__file__).parent.parent.parent / "src" / "server" / "app.py"
        
        # Start server with uvicorn
        cls.server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "server.app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], cwd=str(Path(__file__).parent.parent.parent / "src"))
    
    @classmethod
    def stop_server(cls):
        """Stop the server"""
        if cls.server_process:
            if platform.system() == "Windows":
                cls.server_process.terminate()
            else:
                cls.server_process.send_signal(signal.SIGTERM)
            cls.server_process.wait(timeout=5)
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = ParallelAgentsClient(host="localhost", port=8000)
        # Clean up any existing agents
        self.cleanup_agents()
    
    def teardown_method(self):
        """Clean up after tests"""
        self.cleanup_agents()
        self.client.cleanup()
    
    def cleanup_agents(self):
        """Clean up any running agents"""
        try:
            agents = self.client.list_agents()
            for agent in agents.get("agents", []):
                self.client.stop_agent(agent["agent_id"])
        except Exception:
            pass  # Ignore cleanup errors
    
    def test_server_health_check(self):
        """Test server health check"""
        result = self.client.health_check()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "version" in result
        assert "active_agents" in result
    
    def test_configuration_profiles(self):
        """Test configuration profile management"""
        # Get all profiles
        profiles = self.client.get_config_profiles()
        
        assert profiles["success"] is True
        assert "profiles" in profiles
        assert "testing" in profiles["profiles"]
        assert "documentation" in profiles["profiles"]
        
        # Get specific profile
        testing_profile = self.client.get_config_profile("testing")
        
        assert testing_profile["success"] is True
        assert testing_profile["profile_name"] == "testing"
        assert testing_profile["config"]["code_tool"] == "goose"
        assert testing_profile["config"]["log_level"] == "DEBUG"
    
    def test_agent_lifecycle(self):
        """Test complete agent lifecycle"""
        # Start an agent
        config = {
            "code_tool": "mock",
            "agent_mission": "Testing E2E integration",
            "log_level": "DEBUG",
            "max_iterations": 3
        }
        
        agent = self.client.start_agent("test_agent", config)
        
        assert agent is not None
        assert agent.agent_id == "test_agent"
        
        # Check agent status
        status = agent.status
        assert status["success"] is True
        assert status["agent_id"] == "test_agent"
        
        # List agents
        agents = self.client.list_agents()
        assert agents["success"] is True
        assert len(agents["agents"]) == 1
        assert agents["agents"][0]["agent_id"] == "test_agent"
        
        # Stop agent
        result = agent.stop()
        assert result["success"] is True
        
        # Verify agent is stopped
        agents = self.client.list_agents()
        assert len(agents["agents"]) == 0
    
    def test_file_processing(self):
        """Test file processing through the system"""
        # Start a mock agent
        config = {
            "code_tool": "mock",
            "agent_mission": "Testing file processing",
            "log_level": "DEBUG"
        }
        
        agent = self.client.start_agent("file_processor", config)
        
        # Process some files
        file_changes = [
            {"file": "test.py", "action": "created", "content": "print('hello')"},
            {"file": "README.md", "action": "modified", "content": "# Test Project"}
        ]
        
        result = agent.process_files(file_changes)
        
        assert result["success"] is True
        
        # Stop agent
        agent.stop()
    
    def test_multiple_agents(self):
        """Test running multiple agents simultaneously"""
        # Start multiple agents
        agents = []
        for i in range(3):
            config = {
                "code_tool": "mock",
                "agent_mission": f"Agent {i}",
                "log_level": "INFO"
            }
            agent = self.client.start_agent(f"agent_{i}", config)
            agents.append(agent)
        
        # Verify all agents are running
        agent_list = self.client.list_agents()
        assert len(agent_list["agents"]) == 3
        
        # Stop all agents
        for agent in agents:
            result = agent.stop()
            assert result["success"] is True
        
        # Verify all agents are stopped
        agent_list = self.client.list_agents()
        assert len(agent_list["agents"]) == 0
    
    def test_agent_error_handling(self):
        """Test error handling in agent operations"""
        # Try to start agent with invalid config
        invalid_config = {
            "code_tool": "invalid_tool",
            "agent_mission": "This should fail"
        }
        
        with pytest.raises(ClientError):
            self.client.start_agent("invalid_agent", invalid_config)
        
        # Try to get non-existent agent
        with pytest.raises(Exception):
            self.client.get_agent("nonexistent_agent")
        
        # Try to stop non-existent agent
        result = self.client.stop_agent("nonexistent_agent")
        assert result["success"] is False
    
    def test_working_set_management(self):
        """Test working set file management"""
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write("print('test')")
        temp_file.close()
        
        try:
            # Add file to working set
            result = self.client.add_working_set_file(temp_file.name)
            assert result["success"] is True
            
            # List working set files
            files = self.client.get_working_set_files()
            assert files["success"] is True
            assert len(files["files"]) > 0
            
            # Remove file from working set
            basename = os.path.basename(temp_file.name)
            result = self.client.remove_working_set_file(basename)
            assert result["success"] is True
            
        finally:
            # Clean up
            os.unlink(temp_file.name)
    
    def test_log_streaming(self):
        """Test log streaming via WebSocket"""
        # Start an agent
        config = {
            "code_tool": "mock",
            "agent_mission": "Testing log streaming",
            "log_level": "DEBUG"
        }
        
        agent = self.client.start_agent("log_test", config)
        
        # Set up log collection
        received_logs = []
        
        def log_callback(log_message):
            received_logs.append(log_message)
        
        # Subscribe to logs
        agent.subscribe_to_logs(log_callback)
        
        # Process files to generate logs
        file_changes = [{"file": "test.py", "action": "created"}]
        agent.process_files(file_changes)
        
        # Wait for logs
        time.sleep(1)
        
        # Unsubscribe from logs
        agent.unsubscribe_from_logs(log_callback)
        
        # Stop agent
        agent.stop()
        
        # Verify logs were received
        assert len(received_logs) > 0
    
    def test_concurrent_operations(self):
        """Test concurrent operations"""
        import threading
        
        results = []
        
        def start_agent_task(agent_id):
            try:
                config = {
                    "code_tool": "mock",
                    "agent_mission": f"Concurrent agent {agent_id}",
                    "log_level": "INFO"
                }
                agent = self.client.start_agent(f"concurrent_{agent_id}", config)
                results.append(("success", agent_id))
                # Stop agent after a short delay
                time.sleep(0.5)
                agent.stop()
            except Exception as e:
                results.append(("error", agent_id, str(e)))
        
        # Start multiple agents concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=start_agent_task, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        success_count = sum(1 for result in results if result[0] == "success")
        assert success_count == 3
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test valid configuration
        valid_config = {
            "code_tool": "mock",
            "agent_mission": "Valid configuration",
            "log_level": "INFO",
            "max_iterations": 5
        }
        
        result = self.client.validate_config(valid_config)
        assert result["success"] is True
        
        # Test configuration with missing fields (should use defaults)
        minimal_config = {
            "code_tool": "mock"
        }
        
        result = self.client.validate_config(minimal_config)
        assert result["success"] is True
    
    def test_project_analysis(self):
        """Test project analysis functionality"""
        result = self.client.analyze_project()
        
        assert result["success"] is True
        assert "analysis" in result
        assert "recommended_profile" in result
        
        # The analysis should detect this is a Python project
        assert "python" in result["analysis"]["project_type"].lower()


class TestAgentTypes:
    """Test different agent types"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = ParallelAgentsClient(host="localhost", port=8000)
        # Clean up any existing agents
        self.cleanup_agents()
    
    def teardown_method(self):
        """Clean up after tests"""
        self.cleanup_agents()
        self.client.cleanup()
    
    def cleanup_agents(self):
        """Clean up any running agents"""
        try:
            agents = self.client.list_agents()
            for agent in agents.get("agents", []):
                self.client.stop_agent(agent["agent_id"])
        except Exception:
            pass  # Ignore cleanup errors
    
    def test_verifier_agent(self):
        """Test verifier agent functionality"""
        config = {
            "code_tool": "mock",
            "agent_mission": "Code verification and testing",
            "log_level": "DEBUG"
        }
        
        agent = self.client.start_agent("verifier", config, agent_type="verifier")
        
        assert agent.agent_type == "verifier"
        
        # Test file processing
        file_changes = [
            {"file": "test.py", "action": "created", "content": "def test(): pass"}
        ]
        
        result = agent.process_files(file_changes)
        assert result["success"] is True
        
        agent.stop()
    
    def test_documentation_agent(self):
        """Test documentation agent functionality"""
        config = {
            "code_tool": "mock",
            "agent_mission": "Documentation generation and maintenance",
            "log_level": "INFO"
        }
        
        agent = self.client.start_agent("doc_agent", config, agent_type="documentation")
        
        assert agent.agent_type == "documentation"
        
        # Test documentation generation
        file_changes = [
            {"file": "module.py", "action": "created", "content": "class TestClass: pass"}
        ]
        
        result = agent.process_files(file_changes)
        assert result["success"] is True
        
        agent.stop()
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Claude Code not supported on Windows")
    def test_claude_code_agent(self):
        """Test Claude Code agent functionality"""
        config = {
            "code_tool": "claude_code",
            "agent_mission": "Code analysis using Claude Code",
            "log_level": "DEBUG"
        }
        
        try:
            agent = self.client.start_agent("claude_agent", config)
            
            # Test basic functionality
            file_changes = [
                {"file": "example.py", "action": "modified", "content": "print('hello')"}
            ]
            
            result = agent.process_files(file_changes)
            # May succeed or fail depending on Claude Code availability
            assert "success" in result
            
            agent.stop()
            
        except ClientError as e:
            # Expected if Claude Code is not available
            assert "claude_code" in str(e).lower()
    
    def test_goose_agent(self):
        """Test Goose agent functionality"""
        config = {
            "code_tool": "goose",
            "agent_mission": "Code analysis using Block Goose",
            "log_level": "DEBUG",
            "goose_timeout": 30
        }
        
        try:
            agent = self.client.start_agent("goose_agent", config)
            
            # Test basic functionality
            file_changes = [
                {"file": "example.py", "action": "modified", "content": "print('hello')"}
            ]
            
            result = agent.process_files(file_changes)
            # May succeed or fail depending on Goose availability
            assert "success" in result
            
            agent.stop()
            
        except ClientError as e:
            # Expected if Goose is not available
            assert "goose" in str(e).lower()


class TestErrorScenarios:
    """Test error scenarios and edge cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = ParallelAgentsClient(host="localhost", port=8000)
    
    def teardown_method(self):
        """Clean up after tests"""
        self.client.cleanup()
    
    def test_server_connection_error(self):
        """Test handling of server connection errors"""
        # Create client pointing to non-existent server
        bad_client = ParallelAgentsClient(host="localhost", port=9999)
        
        with pytest.raises(ClientError):
            bad_client.health_check()
    
    def test_malformed_requests(self):
        """Test handling of malformed requests"""
        # Try to start agent with no config
        with pytest.raises(Exception):
            self.client.start_agent("bad_agent", {})
    
    def test_agent_name_conflicts(self):
        """Test handling of agent name conflicts"""
        config = {
            "code_tool": "mock",
            "agent_mission": "Testing name conflicts"
        }
        
        # Start first agent
        agent1 = self.client.start_agent("duplicate_name", config)
        
        # Try to start second agent with same name
        with pytest.raises(ClientError):
            self.client.start_agent("duplicate_name", config)
        
        # Clean up
        agent1.stop()
    
    def test_resource_cleanup(self):
        """Test proper resource cleanup"""
        # Start multiple agents
        agents = []
        for i in range(3):
            config = {
                "code_tool": "mock",
                "agent_mission": f"Cleanup test {i}"
            }
            agent = self.client.start_agent(f"cleanup_{i}", config)
            agents.append(agent)
        
        # Force cleanup
        self.client.cleanup()
        
        # Verify all agents are cleaned up
        agent_list = self.client.list_agents()
        assert len(agent_list["agents"]) == 0
    
    def test_websocket_connection_handling(self):
        """Test WebSocket connection handling"""
        config = {
            "code_tool": "mock",
            "agent_mission": "WebSocket test"
        }
        
        agent = self.client.start_agent("ws_test", config)
        
        # Subscribe to logs
        logs = []
        def log_callback(log):
            logs.append(log)
        
        agent.subscribe_to_logs(log_callback)
        
        # Process files to generate logs
        file_changes = [{"file": "test.py", "action": "created"}]
        agent.process_files(file_changes)
        
        # Wait for logs
        time.sleep(1)
        
        # Unsubscribe
        agent.unsubscribe_from_logs(log_callback)
        
        # Stop agent
        agent.stop()
        
        # Verify logs were received
        assert len(logs) > 0 