"""Custom exception classes for Claude Multi-Agent System"""


class ClaudeMultiAgentError(Exception):
    """Base exception for Claude Multi-Agent System"""
    pass


class AgentConfigurationError(ClaudeMultiAgentError):
    """Raised when agent configuration is invalid"""
    pass


class SessionError(ClaudeMultiAgentError):
    """Raised when session operations fail"""
    pass


class WorkspaceError(ClaudeMultiAgentError):
    """Raised when workspace operations fail"""
    pass


class ExecutionError(ClaudeMultiAgentError):
    """Raised when command execution fails"""
    pass


class TimeoutError(ClaudeMultiAgentError):
    """Raised when operations timeout"""
    pass


class ValidationError(ClaudeMultiAgentError):
    """Raised when data validation fails"""
    pass