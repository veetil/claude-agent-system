"""Core type definitions for Claude Multi-Agent System"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from .constants import DEFAULT_MAX_TURNS, DEFAULT_TIMEOUT_SECONDS
from .exceptions import ValidationError


class ExecutionStrategy(Enum):
    """Execution strategy for orchestrating multiple agents"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    HIERARCHICAL = "hierarchical"


@dataclass
class FileMapping:
    """Mapping for file import into agent workspace"""
    name: str
    src_path: str
    dest_path: str


@dataclass
class FolderMapping:
    """Mapping for folder import into agent workspace"""
    src_path: str
    dest_path: str
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None


@dataclass
class AgentConfig:
    """Configuration for creating an agent"""
    id: str
    system_prompt: str
    working_dir: Path
    allowed_tools: List[str] = field(default_factory=list)
    max_turns: int = DEFAULT_MAX_TURNS
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    environment_vars: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.max_turns <= 0:
            raise ValidationError("max_turns must be positive")
        if self.timeout_seconds <= 0:
            raise ValidationError("timeout_seconds must be positive")


@dataclass
class TaskInput:
    """Input for agent task execution"""
    prompt: str
    text_input: Optional[str] = None
    files: List[FileMapping] = field(default_factory=list)
    folders: List[FolderMapping] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Response from agent execution"""
    agent_id: str
    result: str
    session_id: str
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    """Result from orchestrating multiple agents"""
    responses: List[AgentResponse] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)