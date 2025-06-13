# Claude Multi-Agent System Examples

This directory contains example scripts demonstrating how to use the Claude Multi-Agent System.

## Prerequisites

Make sure you have:
1. Claude CLI installed and configured
2. The claude-multi-agent package installed (`pip install -e .` from the project root)

## Basic Agent Runner

The `run_agent.py` script provides a simple command-line interface for running a single agent:

```bash
# Simple prompt
python run_agent.py "Write a hello world function in Python"

# With system prompt
python run_agent.py "Explain recursion" --system "You are a teacher. Be concise."

# With specific workspace
python run_agent.py "Continue our discussion" --workspace /tmp/my_agent

# Get full JSON output
python run_agent.py "What is 2+2?" --json
```

### Features:
- Automatic workspace creation (or use existing)
- Optional system prompt support
- Full JSON response output
- Session ID tracking for continuation

## Session Management Example

The `example_session.py` script demonstrates session continuity:

```bash
python example_session.py
```

This shows:
1. Starting a new conversation
2. Claude remembering context across multiple turns
3. Session ID chaining
4. Cost tracking

### Example Output:
```
=== Starting new conversation ===
Response: I've learned the secret word: RAINBOW.
Session ID: c7922f98-b608-448f-90c7-07361b64fc08

=== Continuing conversation ===
Response: RAINBOW
New Session ID: 2e9bab8e-0819-458d-bb01-6657cfc47752

=== Testing context retention ===
Response: WOBNIAR
Final Session ID: 62a9d066-536d-4783-afb9-43f2f4edaf89
```

## Key Concepts

1. **Workspace**: Each agent runs in a specific directory. Sessions are tied to this workspace.

2. **Session Management**: Each response includes a new session ID. Use this to continue the conversation.

3. **System Prompts**: Since Claude CLI doesn't have a separate system prompt flag, we prepend it to the user prompt.

4. **Cost Tracking**: Each response includes usage metrics and cost in USD.

## Advanced Usage

You can build on these examples to:
- Create multiple agents with different workspaces
- Implement conversation branching
- Build interactive CLI tools
- Create web services with session persistence

## API Reference

```python
from claude_multi_agent import ShellExecutor

executor = ShellExecutor()
response = executor.execute_claude(
    prompt="Your prompt here",
    session_id="previous-session-id",  # Optional
    working_dir=Path("/your/workspace"),
    timeout=300  # seconds
)

# Response format:
{
    "session_id": "new-session-id",
    "result": "Claude's response",
    "total_cost_usd": 0.0789,
    "usage": {
        "input_tokens": 100,
        "output_tokens": 50
    }
}
```