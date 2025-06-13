"""Tests for Shell Executor with REAL Claude CLI"""

import pytest
import subprocess
import json
import tempfile
import os
from pathlib import Path
import time

from claude_multi_agent.shell.executor import ShellExecutor
from claude_multi_agent.core.exceptions import (
    ClaudeMultiAgentError, ExecutionError, SessionError, ValidationError
)


def claude_cli_available():
    """Check if Claude CLI is available"""
    try:
        result = subprocess.run(
            [os.environ.get("SHELL", "/bin/bash"), "-ic", "which claude"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False


@pytest.mark.skipif(not claude_cli_available(), reason="Claude CLI not available")
class TestShellExecutorWithRealClaude:
    """Test ShellExecutor with REAL Claude CLI - no mocks!"""
    
    @pytest.fixture
    def executor(self):
        """Create shell executor instance"""
        return ShellExecutor()
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_real_claude_simple_execution(self, executor, temp_workspace):
        """Test real Claude CLI execution with simple prompt"""
        print(f"\nTesting in workspace: {temp_workspace}")
        
        # Execute a simple command
        result = executor.execute_claude(
            prompt="Say 'Hello from test' and nothing else",
            working_dir=temp_workspace
        )
        
        print(f"Result: {result}")
        
        # Verify response structure
        assert "session_id" in result
        assert result["session_id"] is not None
        assert "result" in result or "message" in result
        
        # The response should contain our test message
        response_text = result.get("result") or result.get("message") or ""
        assert "Hello from test" in response_text or "hello from test" in response_text.lower()
    
    def test_real_claude_session_chaining(self, executor, temp_workspace):
        """Test real session management with Claude CLI"""
        print(f"\nTesting session chaining in: {temp_workspace}")
        
        # First call - create session
        result1 = executor.execute_claude(
            prompt="Remember the number 42. Say 'Number stored'",
            working_dir=temp_workspace
        )
        
        print(f"First result: {result1}")
        session_id_1 = result1["session_id"]
        assert session_id_1 is not None
        
        # Small delay to ensure session is saved
        time.sleep(0.5)
        
        # Second call - resume session
        result2 = executor.execute_claude(
            prompt="What number did I ask you to remember?",
            session_id=session_id_1,
            working_dir=temp_workspace
        )
        
        print(f"Second result: {result2}")
        session_id_2 = result2["session_id"]
        
        # Verify session was resumed
        response_text = result2.get("result") or result2.get("message") or ""
        assert "42" in response_text
        
        # Verify we got a new session ID
        assert session_id_2 is not None
        assert session_id_2 != session_id_1
    
    def test_real_claude_invalid_session(self, executor, temp_workspace):
        """Test real error handling with invalid session ID"""
        print(f"\nTesting invalid session in: {temp_workspace}")
        
        # Try to resume non-existent session
        with pytest.raises(SessionError) as exc_info:
            executor.execute_claude(
                prompt="Continue conversation",
                session_id="invalid-session-12345",
                working_dir=temp_workspace
            )
        
        # Either "Session not found" or "Invalid session ID" is acceptable
        error_msg = str(exc_info.value)
        assert "Session not found" in error_msg or "Invalid session ID" in error_msg
    
    def test_real_claude_multiline_response(self, executor, temp_workspace):
        """Test handling multiline responses from Claude"""
        print(f"\nTesting multiline response in: {temp_workspace}")
        
        result = executor.execute_claude(
            prompt="List three items:\n1. Apple\n2. Banana\n3. Cherry\nJust list them.",
            working_dir=temp_workspace
        )
        
        print(f"Multiline result: {result}")
        
        # Should handle multiline responses
        assert "session_id" in result
        response_text = result.get("result") or result.get("message") or ""
        
        # Check that we got some kind of list response
        assert len(response_text) > 10  # Non-trivial response
    
    def test_real_claude_json_output_parsing(self, executor, temp_workspace):
        """Test that JSON output is properly parsed"""
        print(f"\nTesting JSON parsing in: {temp_workspace}")
        
        # Claude should return JSON format
        result = executor.execute_claude(
            prompt="Say hello",
            working_dir=temp_workspace
        )
        
        # Result should be a parsed dict, not a string
        assert isinstance(result, dict)
        assert "session_id" in result
    
    def test_real_claude_timeout_handling(self, executor, temp_workspace):
        """Test timeout handling with real Claude"""
        print(f"\nTesting timeout in: {temp_workspace}")
        
        # Use very short timeout
        with pytest.raises(ExecutionError) as exc_info:
            executor.execute_claude(
                prompt="Count to 1000 slowly",
                working_dir=temp_workspace,
                timeout=0.1  # 100ms timeout - should fail
            )
        
        assert "timed out" in str(exc_info.value)
    
    def test_real_claude_different_working_dirs(self, executor):
        """Test that sessions are isolated by working directory"""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                dir1 = Path(tmpdir1)
                dir2 = Path(tmpdir2)
                
                print(f"\nTesting isolation between {dir1} and {dir2}")
                
                # Create session in first directory
                result1 = executor.execute_claude(
                    prompt="Remember the word 'ALPHA'",
                    working_dir=dir1
                )
                session1 = result1["session_id"]
                
                # Create session in second directory
                result2 = executor.execute_claude(
                    prompt="Remember the word 'BETA'",
                    working_dir=dir2
                )
                session2 = result2["session_id"]
                
                # Sessions should be different
                assert session1 != session2
                
                # Resume in first directory
                result3 = executor.execute_claude(
                    prompt="What word did I ask you to remember?",
                    session_id=session1,
                    working_dir=dir1
                )
                
                response_text = result3.get("result") or result3.get("message") or ""
                assert "ALPHA" in response_text
                assert "BETA" not in response_text


class TestShellExecutorBasics:
    """Basic tests that don't require real Claude CLI"""
    
    def test_init_default_shell(self):
        """Test initialization with default shell"""
        executor = ShellExecutor()
        assert executor.shell is not None
        assert isinstance(executor.shell, str)
    
    def test_init_custom_shell(self):
        """Test initialization with custom shell"""
        executor = ShellExecutor(shell="/bin/bash")
        assert executor.shell == "/bin/bash"
    
    def test_init_invalid_shell(self):
        """Test initialization with invalid shell"""
        with pytest.raises(ExecutionError, match="Shell not found"):
            ShellExecutor(shell="/nonexistent/shell")
    
    def test_build_claude_command_basic(self):
        """Test building basic Claude command"""
        executor = ShellExecutor()
        cmd = executor._build_claude_command("Hello Claude")
        assert cmd == ["claude", "-p", "Hello Claude", "--output-format", "json"]
    
    def test_build_claude_command_with_session(self):
        """Test building Claude command with session ID"""
        executor = ShellExecutor()
        cmd = executor._build_claude_command("Hello", session_id="session-123")
        assert cmd == ["claude", "-p", "Hello", "--output-format", "json", "-r", "session-123"]
    
    def test_sanitize_output_clean_json(self):
        """Test sanitizing clean JSON output"""
        executor = ShellExecutor()
        output = '{"session_id": "123", "result": "Success"}'
        result = executor._sanitize_output(output)
        data = json.loads(result)
        assert data["session_id"] == "123"
        assert data["result"] == "Success"
    
    def test_sanitize_output_with_shell_artifacts(self):
        """Test sanitizing output with shell artifacts"""
        executor = ShellExecutor()
        output = """
        Welcome to zsh!
        Loading environment...
        {"session_id": "123", "result": "Hello World"}
        Shell cleanup...
        """
        result = executor._sanitize_output(output)
        data = json.loads(result)
        assert data["session_id"] == "123"
        assert data["result"] == "Hello World"
    
    def test_sanitize_output_no_json(self):
        """Test sanitizing output with no JSON"""
        executor = ShellExecutor()
        output = "Just plain text output"
        with pytest.raises(ExecutionError, match="No JSON found in output"):
            executor._sanitize_output(output)