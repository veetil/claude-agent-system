"""Claude Multi-Agent System

A sophisticated multi-agent orchestration framework built on Claude Code CLI.
"""

__version__ = "0.1.0"

# Core exports
from .core.types import (
    AgentConfig, TaskInput, AgentResponse, 
    FileMapping, FolderMapping, OrchestrationResult, ExecutionStrategy
)
from .core.exceptions import (
    ClaudeMultiAgentError, AgentConfigurationError, SessionError,
    WorkspaceError, ExecutionError, TimeoutError, ValidationError
)

# Shell executor
from .shell.executor import ShellExecutor

# Workspace manager
from .workspace.manager import WorkspaceManager

# Utilities
from .utils.logging import setup_logging, get_logger
from .utils.retry import retry_with_backoff
from .utils.json_parser import RobustJSONParser

__all__ = [
    # Version
    "__version__",
    
    # Core types
    "AgentConfig", "TaskInput", "AgentResponse",
    "FileMapping", "FolderMapping", "OrchestrationResult", "ExecutionStrategy",
    
    # Exceptions
    "ClaudeMultiAgentError", "AgentConfigurationError", "SessionError",
    "WorkspaceError", "ExecutionError", "TimeoutError", "ValidationError",
    
    # Shell executor
    "ShellExecutor",
    
    # Workspace manager
    "WorkspaceManager",
    
    # Utilities
    "setup_logging", "get_logger", "retry_with_backoff", "RobustJSONParser",
]