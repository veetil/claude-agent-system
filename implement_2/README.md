# Claude Multi-Agent System

A sophisticated multi-agent orchestration framework built on Claude Code CLI, enabling session management, workspace isolation, and flexible workflow patterns.

## Current Status

✅ **Step 0: Foundation** - Complete  
✅ **Step 1: Shell Executor** - Complete  
✅ **Step 2: Workspace Manager** - Complete  
⏳ **Step 3: Agent Implementation** - Not started  
⏳ **Step 4: Orchestrator** - Not started  

## Quick Start

### Installation

```bash
cd implement_2
pip install -e .
```

### Basic Usage

The system is currently capable of running single agents with session management:

```bash
# Simple prompt
python examples/run_agent.py "Write a hello world function"

# With system prompt
python examples/run_agent.py "Explain quantum computing" --system "You are a physics teacher"

# With specific workspace (for session persistence)
python examples/run_agent.py "Continue our discussion" --workspace /tmp/my_session
```

### Session Management Example

```python
from claude_multi_agent import ShellExecutor
from pathlib import Path

executor = ShellExecutor()
workspace = Path("/tmp/my_agent")

# Start conversation
response1 = executor.execute_claude(
    prompt="Remember the number 42",
    working_dir=workspace
)

# Continue with context
response2 = executor.execute_claude(
    prompt="What number did I ask you to remember?",
    session_id=response1["session_id"],
    working_dir=workspace
)

print(response2["result"])  # "42"
```

## Architecture

### Current Components

1. **Core Types** (`src/claude_multi_agent/core/types.py`)
   - `AgentConfig`: Agent configuration with validation
   - `TaskInput`: Input specification for tasks
   - `AgentResponse`: Response from agent execution
   - `ExecutionStrategy`: Orchestration patterns (sequential, parallel, etc.)

2. **Shell Executor** (`src/claude_multi_agent/shell/executor.py`)
   - Executes Claude CLI via interactive shell (`$SHELL -ic`)
   - Handles session management and continuity
   - Robust JSON parsing from mixed output
   - Retry logic with exponential backoff

3. **Utilities**
   - JSON Parser: Handles various Claude CLI output formats
   - Retry Decorator: Configurable retry logic
   - Logging: Centralized logging configuration

### Test Coverage

- **94 unit tests** for core functionality
- **21 integration tests** with real Claude CLI
- All tests pass with actual Claude CLI (no mocks)

## Features

### ✅ Implemented
- Claude CLI integration via interactive shell
- Session management with directory-based isolation
- Workspace creation with file/folder/git repo imports
- Parallel agent execution (up to 5x speedup)
- Robust error handling and retry logic
- JSON response parsing
- Comprehensive logging and configuration
- Example scripts for common use cases

### 🚧 Coming Next (Step 3-4)
- Full Agent class with lifecycle management
- Multi-agent orchestrator with communication patterns
- Advanced workflow patterns (pipeline, hierarchical)
- Agent pools and dynamic scaling

## Examples

See the `examples/` directory for:
- `run_agent.py` - Simple CLI interface for single agents
- `example_session.py` - Demonstrates session continuity
- `workspace_example.py` - Workspace creation with files/folders
- `workspace_git_example.py` - Workspace with cloned repositories
- `simple_parallel.py` - Basic parallel agent execution
- `parallel_agents.py` - Advanced parallel execution with metrics
- `parallel_timing_demo.py` - Performance comparison sequential vs parallel
- `README.md` - Detailed documentation

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# With real Claude CLI integration
pytest tests/shell/test_executor_integration.py -v -s

# Unit tests only
pytest tests/ -v -k "not integration"
```

### Project Structure

```
implement_2/
├── src/claude_multi_agent/    # Main package
│   ├── core/                  # Core types and exceptions
│   ├── shell/                 # Shell executor
│   └── utils/                 # Utilities
├── tests/                     # Test suite
├── examples/                  # Example scripts
├── 0.md                      # Step 0 documentation
├── 1.md                      # Step 1 documentation
└── setup.py                  # Package setup
```

## Requirements

- Python 3.9+
- Claude CLI installed and configured
- Unix-like system (bash/zsh shell)

## License

[Add your license here]

## Contributing

[Add contribution guidelines]