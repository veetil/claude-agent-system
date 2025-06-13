"""Tests for core exceptions"""

import pytest
from claude_multi_agent.core.exceptions import (
    ClaudeMultiAgentError, AgentConfigurationError, SessionError,
    WorkspaceError, ExecutionError, TimeoutError, ValidationError
)


class TestClaudeMultiAgentError:
    """Test base exception class"""
    
    def test_base_exception_creation(self):
        """Test basic exception creation"""
        error = ClaudeMultiAgentError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_base_exception_inheritance(self):
        """Test that all custom exceptions inherit from base"""
        exceptions = [
            AgentConfigurationError("test"),
            SessionError("test"),
            WorkspaceError("test"),
            ExecutionError("test"),
            TimeoutError("test"),
            ValidationError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, ClaudeMultiAgentError)
            assert isinstance(exc, Exception)


class TestAgentConfigurationError:
    """Test AgentConfigurationError"""
    
    def test_agent_config_error(self):
        """Test AgentConfigurationError creation"""
        error = AgentConfigurationError("Invalid agent configuration")
        assert str(error) == "Invalid agent configuration"
        assert isinstance(error, ClaudeMultiAgentError)
    
    def test_agent_config_error_with_details(self):
        """Test AgentConfigurationError with detailed message"""
        agent_id = "test-agent"
        message = f"Agent '{agent_id}' has invalid system prompt"
        error = AgentConfigurationError(message)
        assert str(error) == message


class TestSessionError:
    """Test SessionError"""
    
    def test_session_error(self):
        """Test SessionError creation"""
        error = SessionError("Session failed to start")
        assert str(error) == "Session failed to start"
        assert isinstance(error, ClaudeMultiAgentError)
    
    def test_session_error_with_session_id(self):
        """Test SessionError with session ID"""
        session_id = "session-123"
        message = f"Failed to resume session {session_id}"
        error = SessionError(message)
        assert str(error) == message


class TestWorkspaceError:
    """Test WorkspaceError"""
    
    def test_workspace_error(self):
        """Test WorkspaceError creation"""
        error = WorkspaceError("Failed to create workspace")
        assert str(error) == "Failed to create workspace"
        assert isinstance(error, ClaudeMultiAgentError)
    
    def test_workspace_error_with_path(self):
        """Test WorkspaceError with path information"""
        path = "/tmp/invalid/path"
        message = f"Cannot access workspace at {path}"
        error = WorkspaceError(message)
        assert str(error) == message


class TestExecutionError:
    """Test ExecutionError"""
    
    def test_execution_error(self):
        """Test ExecutionError creation"""
        error = ExecutionError("Command execution failed")
        assert str(error) == "Command execution failed"
        assert isinstance(error, ClaudeMultiAgentError)
    
    def test_execution_error_with_command(self):
        """Test ExecutionError with command details"""
        command = "claude chat --session=test"
        message = f"Failed to execute: {command}"
        error = ExecutionError(message)
        assert str(error) == message


class TestTimeoutError:
    """Test TimeoutError"""
    
    def test_timeout_error(self):
        """Test TimeoutError creation"""
        error = TimeoutError("Operation timed out")
        assert str(error) == "Operation timed out"
        assert isinstance(error, ClaudeMultiAgentError)
    
    def test_timeout_error_with_duration(self):
        """Test TimeoutError with timeout duration"""
        timeout = 300
        message = f"Operation timed out after {timeout} seconds"
        error = TimeoutError(message)
        assert str(error) == message


class TestValidationError:
    """Test ValidationError"""
    
    def test_validation_error(self):
        """Test ValidationError creation"""
        error = ValidationError("Invalid input data")
        assert str(error) == "Invalid input data"
        assert isinstance(error, ClaudeMultiAgentError)
    
    def test_validation_error_with_field(self):
        """Test ValidationError with field information"""
        field = "max_turns"
        value = -1
        message = f"Invalid value for {field}: {value}"
        error = ValidationError(message)
        assert str(error) == message


class TestExceptionUsage:
    """Test exception usage patterns"""
    
    def test_raising_and_catching_custom_exceptions(self):
        """Test that custom exceptions can be raised and caught properly"""
        
        # Test raising specific exception
        with pytest.raises(AgentConfigurationError):
            raise AgentConfigurationError("Test error")
        
        # Test catching as base exception
        with pytest.raises(ClaudeMultiAgentError):
            raise SessionError("Test session error")
        
        # Test catching multiple exception types
        for ExceptionClass in [SessionError, WorkspaceError, ExecutionError]:
            with pytest.raises(ClaudeMultiAgentError):
                raise ExceptionClass("Test error")
    
    def test_exception_chaining(self):
        """Test exception chaining functionality"""
        original_error = ValueError("Original error")
        
        # Test that we can create chained exceptions
        chained_error = ExecutionError("Execution failed")
        chained_error.__cause__ = original_error
            
        assert chained_error.__cause__ == original_error
        assert "Original error" in str(original_error)
    
    def test_exception_message_formatting(self):
        """Test that exception messages are properly formatted"""
        test_cases = [
            (AgentConfigurationError, "Agent 'test' failed to initialize"),
            (SessionError, "Session 'abc123' could not be resumed"),
            (WorkspaceError, "Workspace '/tmp/test' is not accessible"),
            (ExecutionError, "Command 'claude chat' failed with exit code 1"),
            (TimeoutError, "Operation exceeded 300 second timeout"),
            (ValidationError, "Field 'system_prompt' cannot be empty")
        ]
        
        for ExceptionClass, message in test_cases:
            error = ExceptionClass(message)
            assert str(error) == message
            assert isinstance(error, ClaudeMultiAgentError)