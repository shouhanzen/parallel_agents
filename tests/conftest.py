#!/usr/bin/env python3
"""Pytest configuration and fixtures for the verifier tests"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from src.config import VerifierConfig
from src.working_set import WorkingSetManager
from src.reporter import ErrorReporter
from src.agent import VerifierAgent


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Provide a test configuration"""
    return VerifierConfig(
        watch_dirs=[str(temp_dir / "src")],
        test_dir=str(temp_dir / "test"),
        working_set_dir=str(temp_dir / "working_set"),
        error_report_file=str(temp_dir / "errors.jsonl"),
        agent_mission="testing",
        claude_timeout=60
    )


@pytest.fixture
def working_set_manager(test_config):
    """Provide a working set manager"""
    manager = WorkingSetManager(test_config.working_set_dir)
    manager.ensure_directory_structure()
    return manager


@pytest.fixture
def error_reporter(test_config):
    """Provide an error reporter"""
    return ErrorReporter(test_config.error_report_file)


@pytest.fixture
def mock_agent(test_config):
    """Provide a mock verifier agent"""
    with patch.object(VerifierAgent, '_run_claude_code') as mock_run:
        mock_run.return_value = "Mock response"
        agent = VerifierAgent(test_config)
        yield agent


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
    config = VerifierConfig(
        watch_dirs=[str(temp_dir / "src")],
        working_set_dir=str(temp_dir / "working_set"),
        agent_mission="testing"
    )
    config.to_file(str(config_file))
    return config_file


@pytest.fixture
def file_changes_sample():
    """Provide sample file changes for testing"""
    return [
        {
            "action": "created",
            "file_path": "/test/new_module.py",
            "timestamp": 1234567890.0,
            "content": "def new_function(): pass"
        },
        {
            "action": "modified", 
            "file_path": "/test/existing_module.py",
            "timestamp": 1234567891.0,
            "content": "def updated_function(): return True"
        },
        {
            "action": "deleted",
            "file_path": "/test/old_module.py",
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


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names/paths"""
    for item in items:
        # Mark integration tests
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            
        # Mark e2e tests
        if "test_e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            
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


def pytest_runtest_setup(item):
    """Skip tests based on custom options"""
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("need --run-slow option to run")
        
    if "integration" in item.keywords and not item.config.getoption("--run-integration"):
        pytest.skip("need --run-integration option to run")
        
    if "e2e" in item.keywords and not item.config.getoption("--run-e2e"):
        pytest.skip("need --run-e2e option to run")