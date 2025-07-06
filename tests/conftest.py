#!/usr/bin/env python3
"""Pytest configuration and fixtures for the parallel agents tests"""

import pytest
import tempfile
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from core.config.models import ParallelAgentsConfig
    from core.monitoring.working_set import WorkingSet
    from core.review.reporter import Reporter
    from core.agents.mock.agent import MockAgent
except ImportError:
    # Fallback for when modules don't exist yet
    ParallelAgentsConfig = None
    WorkingSet = None
    Reporter = None
    MockAgent = None


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Provide a test configuration"""
    if ParallelAgentsConfig is None:
        pytest.skip("ParallelAgentsConfig not available")
    
    return ParallelAgentsConfig(
        code_tool="mock",
        agent_mission="testing",
        log_level="DEBUG",
        max_iterations=3,
        timeout=30
    )


@pytest.fixture
def working_set_manager(temp_dir):
    """Provide a working set manager"""
    if WorkingSet is None:
        pytest.skip("WorkingSet not available")
    
    manager = WorkingSet(str(temp_dir))
    return manager


@pytest.fixture
def error_reporter(temp_dir):
    """Provide an error reporter"""
    if Reporter is None:
        pytest.skip("Reporter not available")
    
    return Reporter(str(temp_dir / "errors.jsonl"))


@pytest.fixture
def mock_agent(test_config):
    """Provide a mock agent"""
    if MockAgent is None:
        pytest.skip("MockAgent not available")
    
    agent = MockAgent(test_config)
    return agent


@pytest.fixture
def event_loop():
    """Provide an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file for testing"""
    src_dir = temp_dir / "src"
    src_dir.mkdir(exist_ok=True)
    
    sample_file = src_dir / "sample.py"
    sample_file.write_text("""
def add(a, b):
    '''Add two numbers'''
    return a + b

def subtract(a, b):
    '''Subtract two numbers'''
    return a - b

class Calculator:
    '''Simple calculator class'''
    
    def multiply(self, a, b):
        return a * b
        
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
""")
    return sample_file


@pytest.fixture
def sample_config_file(temp_dir):
    """Create a sample configuration file for testing"""
    config_file = temp_dir / "test_config.json"
    
    if ParallelAgentsConfig is None:
        pytest.skip("ParallelAgentsConfig not available")
    
    config = ParallelAgentsConfig(
        code_tool="mock",
        agent_mission="testing",
        log_level="DEBUG"
    )
    
    # Save config to file
    import json
    with open(config_file, 'w') as f:
        json.dump(config.to_dict(), f)
    
    return config_file


@pytest.fixture
def file_changes_sample():
    """Provide sample file changes for testing"""
    return [
        {
            "action": "created",
            "file": "/test/new_module.py",
            "timestamp": 1234567890.0,
            "content": "def new_function(): pass"
        },
        {
            "action": "modified", 
            "file": "/test/existing_module.py",
            "timestamp": 1234567891.0,
            "content": "def updated_function(): return True"
        },
        {
            "action": "deleted",
            "file": "/test/old_module.py",
            "timestamp": 1234567892.0
        }
    ]


@pytest.fixture
def mock_subprocess():
    """Mock subprocess operations for CLI testing"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Mock command output",
            stderr=""
        )
        yield mock_run


@pytest.fixture
def mock_requests():
    """Mock requests for HTTP testing"""
    with patch('requests.Session') as mock_session:
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.request.return_value = mock_response
        yield mock_session


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "server: marks tests that require server"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names/paths"""
    for item in items:
        # Mark integration tests
        if "test_integration" in str(item.fspath) or "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            
        # Mark e2e tests
        if "test_e2e" in str(item.fspath) or "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            
        # Mark server tests
        if "server" in str(item.fspath) or "client" in str(item.fspath):
            item.add_marker(pytest.mark.server)
            
        # Mark slow tests
        if any(marker in item.name for marker in ["slow", "performance", "timeout"]):
            item.add_marker(pytest.mark.slow)


# Custom pytest options
def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--run-integration",
        action="store_true", 
        default=False,
        help="run integration tests"
    )
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="run end-to-end tests"
    )
    parser.addoption(
        "--run-server",
        action="store_true",
        default=False,
        help="run server tests"
    )


def pytest_runtest_setup(item):
    """Skip tests based on custom options"""
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("need --run-slow option to run")
    
    if "integration" in item.keywords and not item.config.getoption("--run-integration"):
        pytest.skip("need --run-integration option to run")
    
    if "e2e" in item.keywords and not item.config.getoption("--run-e2e"):
        pytest.skip("need --run-e2e option to run")
    
    if "server" in item.keywords and not item.config.getoption("--run-server"):
        pytest.skip("need --run-server option to run")