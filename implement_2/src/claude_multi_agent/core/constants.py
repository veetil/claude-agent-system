"""System constants for Claude Multi-Agent System"""

import os
from pathlib import Path

# Default paths
DEFAULT_BASE_DIR = Path("/tmp/claude-agents")
DEFAULT_CONFIG_PATHS = [
    Path.cwd() / "claude-agents.yaml",
    Path.cwd() / "claude-agents.json", 
    Path.home() / ".claude-agents" / "config.yaml",
    Path.home() / ".claude-agents" / "config.json",
    Path("/etc/claude-agents/config.yaml"),
    Path("/etc/claude-agents/config.json")
]

# Shell configuration
DEFAULT_SHELL = os.environ.get("SHELL", "/bin/bash")

# Claude CLI defaults
DEFAULT_TIMEOUT = 300
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_MAX_TURNS = 10
DEFAULT_MAX_RETRIES = 3

# Session management
SESSION_PERSISTENCE_DIR = Path.home() / ".claude-agent" / "sessions"
CLAUDE_SESSION_DIR = Path.home() / ".claude" / "projects"

# Resource limits
DEFAULT_MAX_AGENTS = 10
DEFAULT_WORKSPACE_TTL_HOURS = 24
DEFAULT_CLEANUP_INTERVAL_MINUTES = 60

# Logging
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Security
FORBIDDEN_PATHS = [
    "/etc", "/usr", "/bin", "/sbin", "/root",
    "/System", "/Library", "/Applications"
]