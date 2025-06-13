"""Pytest configuration and fixtures"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from claude_multi_agent.core.types import AgentConfig, TaskInput, FolderMapping, FileMapping


@pytest.fixture
def temp_workspace():
    """Provide temporary workspace for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_agent_config(temp_workspace):
    """Sample agent configuration for testing"""
    return AgentConfig(
        id="test-agent",
        system_prompt="You are a test agent",
        working_dir=temp_workspace,
        allowed_tools=["read_file", "write_file"],
        max_turns=2
    )


@pytest.fixture
def sample_task_input():
    """Sample task input for testing"""
    return TaskInput(
        prompt="Test prompt",
        text_input="Additional context",
        files=[
            FileMapping(
                name="test.txt",
                src_path="/tmp/test.txt", 
                dest_path="input/test.txt"
            )
        ]
    )


@pytest.fixture
def mock_claude_response():
    """Mock Claude CLI response"""
    return {
        "session_id": "test-session-123",
        "result": "Test response from Claude",
        "metadata": {
            "tokens_used": 25,
            "duration_ms": 1500,
            "model": "claude-opus-4"
        }
    }


@pytest.fixture
def mock_shell_executor():
    """Mock shell executor for testing"""
    executor = Mock()
    executor.execute_claude = Mock()
    executor.execute_claude_async = AsyncMock()
    return executor


@pytest.fixture
def mock_workspace_manager():
    """Mock workspace manager for testing"""
    manager = Mock()
    manager.create_workspace = AsyncMock(return_value=Path("/tmp/test-workspace"))
    manager.cleanup_workspace = AsyncMock()
    manager.import_file = AsyncMock()
    manager.import_folder = AsyncMock()
    return manager


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Configure pytest for async tests
def pytest_configure(config):
    """Configure pytest settings"""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")