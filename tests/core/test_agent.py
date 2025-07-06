#!/usr/bin/env python3
"""Unit tests for the agent module"""

import pytest
import tempfile
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.agents.factory import create_verifier_agent
from core.config.models import ParallelAgentsConfig as VerifierConfig
from src.agent import VerifierAgent


class TestVerifierAgent:
    """Test the VerifierAgent class"""
    
    def test_verifier_agent_creation(self):
        """Test creating a VerifierAgent instance"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        assert agent.config == config
        assert agent.working_set_dir == Path(config.working_set_dir)
        assert agent.conversation_history == []
        assert agent.session_active is False
        
    def test_verifier_agent_creates_working_dir(self):
        """Test that VerifierAgent creates working directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(working_set_dir=temp_dir)
            agent = VerifierAgent(config)
            
            assert Path(temp_dir).exists()
            
    def test_get_mission_prompt(self):
        """Test getting the mission prompt"""
        config = VerifierConfig(
            agent_mission="testing",
            working_set_dir="/test/working",
            error_report_file="/test/errors.jsonl"
        )
        agent = VerifierAgent(config)
        
        prompt = agent._get_mission_prompt()
        
        assert "testing" in prompt
        assert "/test/working" in prompt
        assert "/test/errors.jsonl" in prompt
        assert "verifier agent" in prompt.lower()
        assert "background mode" in prompt.lower()
        
    def test_get_mission_prompt_different_missions(self):
        """Test mission prompt with different missions"""
        missions = ["testing", "docs", "tooling"]
        
        for mission in missions:
            config = VerifierConfig(agent_mission=mission)
            agent = VerifierAgent(config)
            prompt = agent._get_mission_prompt()
            assert mission in prompt
            
    def test_get_file_deltas_prompt(self):
        """Test getting file deltas prompt"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        file_changes = [
            {
                "action": "created",
                "file_path": "/test/new_file.py",
                "content": "def test_function(): pass"
            },
            {
                "action": "modified", 
                "file_path": "/test/existing_file.py",
                "content": "def updated_function(): return True"
            }
        ]
        
        prompt = agent._get_file_deltas_prompt(file_changes)
        
        assert "FILE CHANGES DETECTED" in prompt
        assert "created: /test/new_file.py" in prompt
        assert "modified: /test/existing_file.py" in prompt
        assert "def test_function()" in prompt
        assert "def updated_function()" in prompt
        
    def test_get_file_deltas_prompt_no_content(self):
        """Test file deltas prompt when changes have no content"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        file_changes = [
            {
                "action": "deleted",
                "file_path": "/test/deleted_file.py"
            }
        ]
        
        prompt = agent._get_file_deltas_prompt(file_changes)
        
        assert "deleted: /test/deleted_file.py" in prompt
        assert "Content preview" not in prompt
        
    def test_read_file_content_existing(self):
        """Test reading existing file content"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_function(): pass")
            temp_file = f.name
            
        try:
            content = agent._read_file_content(temp_file)
            assert content == "def test_function(): pass"
        finally:
            Path(temp_file).unlink()
            
    def test_read_file_content_nonexistent(self):
        """Test reading non-existent file content"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        content = agent._read_file_content("/nonexistent/file.py")
        assert "Error reading file" in content
        
    def test_read_file_content_unicode(self):
        """Test reading file with unicode content"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        unicode_content = "def test_unicode(): return '你好世界'"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(unicode_content)
            temp_file = f.name
            
        try:
            content = agent._read_file_content(temp_file)
            assert content == unicode_content
        finally:
            Path(temp_file).unlink()
            
    @patch('asyncio.create_subprocess_exec')
    @pytest.mark.asyncio
    async def test_run_claude_code_success(self, mock_subprocess):
        """Test running Claude Code successfully"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        # Mock process
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"Success output", b""))
        mock_subprocess.return_value = mock_process
        
        result = await agent._run_claude_code("test prompt")
        
        assert result == "Success output"
        mock_subprocess.assert_called_once()
        
    @patch('asyncio.create_subprocess_exec')
    @pytest.mark.asyncio
    async def test_run_claude_code_failure(self, mock_subprocess):
        """Test running Claude Code with failure"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        # Mock process with error
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"Error occurred"))
        mock_subprocess.return_value = mock_process
        
        with pytest.raises(RuntimeError, match="Claude Code failed"):
            await agent._run_claude_code("test prompt")
            
    @patch('asyncio.create_subprocess_exec')
    @pytest.mark.asyncio
    async def test_run_claude_code_timeout(self, mock_subprocess):
        """Test running Claude Code with timeout"""
        config = VerifierConfig(claude_timeout=0.1)
        agent = VerifierAgent(config)
        
        # Mock process that hangs
        mock_process = Mock()
        async def slow_communicate():
            await asyncio.sleep(1.0)  # Longer than timeout
            return (b"", b"")
        mock_process.communicate = slow_communicate
        mock_subprocess.return_value = mock_process
        
        with pytest.raises(RuntimeError, match="Claude Code timed out"):
            await agent._run_claude_code("test prompt")
            
    @patch.object(VerifierAgent, '_run_claude_code')
    @pytest.mark.asyncio
    async def test_start_session_success(self, mock_run_claude):
        """Test starting a verifier session successfully"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        mock_run_claude.return_value = "Session started successfully"
        
        await agent.start_session()
        
        assert agent.session_active is True
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0]["type"] == "mission"
        mock_run_claude.assert_called_once()
        
    @patch.object(VerifierAgent, '_run_claude_code')
    @pytest.mark.asyncio
    async def test_start_session_already_active(self, mock_run_claude):
        """Test starting session when already active"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        agent.session_active = True
        
        await agent.start_session()
        
        # Should not call Claude Code again
        mock_run_claude.assert_not_called()
        
    @patch.object(VerifierAgent, '_run_claude_code')
    @pytest.mark.asyncio
    async def test_start_session_failure(self, mock_run_claude):
        """Test starting session with failure"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        mock_run_claude.side_effect = RuntimeError("Connection failed")
        
        await agent.start_session()
        
        assert agent.session_active is False
        assert len(agent.conversation_history) == 0
        
    @patch.object(VerifierAgent, '_run_claude_code')
    @patch.object(VerifierAgent, 'start_session')
    @pytest.mark.asyncio
    async def test_process_file_changes_session_inactive(self, mock_start_session, mock_run_claude):
        """Test processing file changes when session is inactive"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        mock_run_claude.return_value = "Changes processed"
        
        file_changes = [
            {"action": "created", "file_path": "/test/file.py"}
        ]
        
        await agent.process_file_changes(file_changes)
        
        mock_start_session.assert_called_once()
        mock_run_claude.assert_called_once()
        
    @patch.object(VerifierAgent, '_run_claude_code')
    @patch.object(VerifierAgent, '_read_file_content')
    @pytest.mark.asyncio
    async def test_process_file_changes_with_content(self, mock_read_file, mock_run_claude):
        """Test processing file changes with content reading"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        agent.session_active = True
        
        mock_read_file.return_value = "def test(): pass"
        mock_run_claude.return_value = "Changes processed"
        
        file_changes = [
            {"action": "created", "file_path": "/test/file.py"},
            {"action": "modified", "file_path": "/test/other.py"}
        ]
        
        await agent.process_file_changes(file_changes)
        
        # Should read content for created and modified files
        assert mock_read_file.call_count == 2
        mock_run_claude.assert_called_once()
        
        # Check conversation history
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0]["type"] == "file_changes"
        assert len(agent.conversation_history[0]["changes"]) == 2
        
    @patch.object(VerifierAgent, '_run_claude_code')
    @patch.object(VerifierAgent, '_read_file_content')
    @pytest.mark.asyncio
    async def test_process_file_changes_deleted_no_content(self, mock_read_file, mock_run_claude):
        """Test processing deleted file changes (no content reading)"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        agent.session_active = True
        
        mock_run_claude.return_value = "Changes processed"
        
        file_changes = [
            {"action": "deleted", "file_path": "/test/file.py"}
        ]
        
        await agent.process_file_changes(file_changes)
        
        # Should not read content for deleted files
        mock_read_file.assert_not_called()
        mock_run_claude.assert_called_once()
        
    @patch.object(VerifierAgent, '_run_claude_code')
    @pytest.mark.asyncio
    async def test_process_file_changes_failure(self, mock_run_claude):
        """Test processing file changes with failure"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        agent.session_active = True
        
        mock_run_claude.side_effect = RuntimeError("Processing failed")
        
        file_changes = [
            {"action": "created", "file_path": "/test/file.py"}
        ]
        
        # Should not raise exception, just handle gracefully
        await agent.process_file_changes(file_changes)
        
        mock_run_claude.assert_called_once()
        
    def test_get_conversation_history(self):
        """Test getting conversation history"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        # Add some history
        agent.conversation_history = [
            {"type": "mission", "content": "test"},
            {"type": "file_changes", "changes": []}
        ]
        
        history = agent.get_conversation_history()
        
        # Should return a copy
        assert history == agent.conversation_history
        assert history is not agent.conversation_history
        
    def test_stop_session(self):
        """Test stopping the verifier session"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        agent.session_active = True
        
        agent.stop_session()
        
        assert agent.session_active is False


class TestVerifierAgentIntegration:
    """Integration tests for VerifierAgent"""
    
    @patch.object(VerifierAgent, '_run_claude_code')
    @pytest.mark.asyncio
    async def test_complete_workflow(self, mock_run_claude):
        """Test a complete agent workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VerifierConfig(working_set_dir=temp_dir)
            agent = VerifierAgent(config)
            
            mock_run_claude.return_value = "Operation successful"
            
            # Start session
            await agent.start_session()
            assert agent.session_active is True
            
            # Process some file changes
            file_changes = [
                {"action": "created", "file_path": "/test/new_file.py"},
                {"action": "modified", "file_path": "/test/existing_file.py"},
                {"action": "deleted", "file_path": "/test/old_file.py"}
            ]
            
            await agent.process_file_changes(file_changes)
            
            # Check conversation history
            history = agent.get_conversation_history()
            assert len(history) == 2  # Mission + file changes
            assert history[0]["type"] == "mission"
            assert history[1]["type"] == "file_changes"
            assert len(history[1]["changes"]) == 3
            
            # Stop session
            agent.stop_session()
            assert agent.session_active is False
            
    @patch.object(VerifierAgent, '_run_claude_code')
    @pytest.mark.asyncio
    async def test_multiple_file_change_batches(self, mock_run_claude):
        """Test processing multiple batches of file changes"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        agent.session_active = True
        
        mock_run_claude.return_value = "Batch processed"
        
        # Process multiple batches
        for i in range(3):
            file_changes = [
                {"action": "modified", "file_path": f"/test/file_{i}.py"}
            ]
            await agent.process_file_changes(file_changes)
            
        # Should have 3 file change entries in history
        history = agent.get_conversation_history()
        file_change_entries = [h for h in history if h["type"] == "file_changes"]
        assert len(file_change_entries) == 3
        
        # Each should have mission reminder
        for entry in file_change_entries:
            assert config.agent_mission in entry["content"]
            
    @patch.object(VerifierAgent, '_run_claude_code')
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_run_claude):
        """Test concurrent agent operations"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        mock_run_claude.return_value = "Operation completed"
        
        # Start session and process changes concurrently
        tasks = []
        
        # Start session
        tasks.append(agent.start_session())
        
        # Process file changes
        for i in range(3):
            file_changes = [{"action": "created", "file_path": f"/test/file_{i}.py"}]
            tasks.append(agent.process_file_changes(file_changes))
            
        # Wait for all operations to complete
        await asyncio.gather(*tasks)
        
        # Session should be active
        assert agent.session_active is True
        
        # Should have processed all changes
        history = agent.get_conversation_history()
        assert len(history) >= 3  # At least mission + some file changes


class TestVerifierAgentPrompts:
    """Test agent prompt generation"""
    
    def test_mission_prompt_contains_key_elements(self):
        """Test that mission prompt contains all key elements"""
        config = VerifierConfig(
            agent_mission="testing",
            working_set_dir="/test/working",
            error_report_file="/test/errors.jsonl"
        )
        agent = VerifierAgent(config)
        
        prompt = agent._get_mission_prompt()
        
        # Should contain key instructions
        assert "verifier agent" in prompt.lower()
        assert "background mode" in prompt.lower()
        assert "monitoring source code changes" in prompt.lower()
        assert "automatically generating tests" in prompt.lower()
        
        # Should contain configuration details
        assert config.working_set_dir in prompt
        assert config.error_report_file in prompt
        assert config.agent_mission in prompt
        
        # Should contain error report format
        assert "ERROR REPORT FORMAT" in prompt
        assert "timestamp" in prompt
        assert "severity" in prompt
        
    def test_file_deltas_prompt_formatting(self):
        """Test file deltas prompt formatting"""
        config = VerifierConfig()
        agent = VerifierAgent(config)
        
        file_changes = [
            {
                "action": "created",
                "file_path": "/src/calculator.py",
                "content": "def add(a, b): return a + b\ndef subtract(a, b): return a - b"
            },
            {
                "action": "modified",
                "file_path": "/src/utils.py",
                "content": "x" * 300  # Long content
            },
            {
                "action": "deleted",
                "file_path": "/src/old_module.py"
            }
        ]
        
        prompt = agent._get_file_deltas_prompt(file_changes)
        
        # Should list all changes
        assert "created: /src/calculator.py" in prompt
        assert "modified: /src/utils.py" in prompt
        assert "deleted: /src/old_module.py" in prompt
        
        # Should include content preview for files with content
        assert "def add(a, b)" in prompt
        
        # Should truncate long content
        long_content_lines = [line for line in prompt.split('\n') if 'x' * 200 in line]
        assert any('...' in line for line in long_content_lines)
        
        # Should include instructions
        assert "analyze these changes" in prompt.lower()
        assert "generate appropriate tests" in prompt.lower()
        assert "run the tests" in prompt.lower()


if __name__ == '__main__':
    pytest.main([__file__])