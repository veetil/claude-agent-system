"""Core module for Claude Multi-Agent System"""

from .types import (
    AgentConfig, TaskInput, AgentResponse, FileMapping, FolderMapping, 
    OrchestrationResult, ExecutionStrategy
)
from .exceptions import (
    ClaudeMultiAgentError, AgentConfigurationError, SessionError,
    WorkspaceError, ExecutionError, TimeoutError, ValidationError
)

__all__ = [
    # Types
    "AgentConfig", "TaskInput", "AgentResponse", "FileMapping", 
    "FolderMapping", "OrchestrationResult", "ExecutionStrategy",
    
    # Exceptions
    "ClaudeMultiAgentError", "AgentConfigurationError", "SessionError",
    "WorkspaceError", "ExecutionError", "TimeoutError", "ValidationError",
]