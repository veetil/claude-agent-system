# Claude Multi-Agent System Examples

This directory contains example scripts demonstrating how to use the Claude Multi-Agent System.

## Prerequisites

Make sure you have:
1. Claude CLI installed and configured
2. The claude-multi-agent package installed (`pip install -e .` from the project root)

## Examples Overview

### Single Agent Examples

**Basic Agent Runner** (`run_agent.py`)

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

**Session Management** (`example_session.py`)

Demonstrates session continuity across multiple interactions:

```bash
python example_session.py
```

This shows:
1. Starting a new conversation
2. Claude remembering context across multiple turns
3. Session ID chaining
4. Cost tracking

Shows how to:
- Start a new conversation
- Continue with session IDs
- Maintain context across turns

### Parallel Execution Examples

**Simple Parallel Agents** (`simple_parallel.py`)

Basic example of running 5 agents concurrently:

```bash
python simple_parallel.py
```

Output shows all agents running simultaneously:
```
Launching 5 agents in parallel...

[Agent1] Starting...
[Agent2] Starting...
[Agent3] Starting...
[Agent4] Starting...
[Agent5] Starting...
[Agent3] Complete!
[Agent4] Complete!
[Agent2] Complete!
[Agent5] Complete!
[Agent1] Complete!
```

**Advanced Parallel Execution** (`parallel_agents.py`)

Comprehensive example with:
- 5 different specialized agents (poet, mathematician, historian, chef, translator)
- Timing and cost tracking
- Workspace management
- Session continuation

```bash
python parallel_agents.py
```

Features:
- Each agent gets its own isolated workspace
- Non-blocking concurrent execution
- Detailed performance metrics
- Example of continuing a conversation after parallel execution

**Parallel Timing Demo** (`parallel_timing_demo.py`)

Demonstrates the performance benefits of parallel execution:

```bash
python parallel_timing_demo.py
```

Output shows speedup comparison:
```
=== Performance Comparison ===
Sequential time: 25.43s
Parallel time: 5.21s
Speedup: 4.9x faster
Time saved: 20.22s

=== Efficiency Analysis ===
Number of agents: 5
Theoretical max speedup: 5x
Actual speedup: 4.9x
Parallel efficiency: 98.0%
```

## Key Concepts

1. **Workspace**: Each agent runs in a specific directory. Sessions are tied to this workspace.

2. **Session Management**: Each response includes a new session ID. Use this to continue the conversation.

3. **System Prompts**: Since Claude CLI doesn't have a separate system prompt flag, we prepend it to the user prompt.

4. **Cost Tracking**: Each response includes usage metrics and cost in USD.

## Code Patterns

### Running Agents in Parallel

The key to parallel execution is using `asyncio`:

```python
import asyncio
from claude_multi_agent import ShellExecutor

async def run_agent(name, prompt):
    executor = ShellExecutor()
    result = await executor.execute_claude_async(
        prompt=prompt,
        working_dir=Path(f"/tmp/{name}")
    )
    return result

async def main():
    # Create tasks for all agents
    tasks = [
        run_agent("agent1", "Task 1"),
        run_agent("agent2", "Task 2"),
        run_agent("agent3", "Task 3")
    ]
    
    # Run all concurrently (non-blocking)
    results = await asyncio.gather(*tasks)
    
    # All results available here
    for result in results:
        print(result["result"])

# Run the async main function
asyncio.run(main())
```

### Important Notes for Parallel Execution

1. **Use `execute_claude_async()`** - The async version of the executor
2. **Each agent needs its own workspace** - Sessions are tied to directories
3. **Use `asyncio.gather()`** - Runs all tasks concurrently
4. **Non-blocking** - All agents run simultaneously, not sequentially

## Advanced Usage

You can build on these examples to:
- Create agent pools with different specializations
- Implement map-reduce patterns across agents
- Build real-time collaborative agent systems
- Create web services with parallel agent processing

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