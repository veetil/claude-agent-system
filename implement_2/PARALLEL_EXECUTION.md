# Parallel Agent Execution

The Claude Multi-Agent System now supports parallel execution of multiple agents without blocking. This allows you to run 5, 10, or more agents simultaneously, achieving near-linear speedup.

## Quick Example

```python
import asyncio
from pathlib import Path
from claude_multi_agent import ShellExecutor

async def run_parallel_agents():
    # Define tasks for 5 agents
    tasks = []
    for i in range(5):
        executor = ShellExecutor()
        workspace = Path(f"/tmp/agent_{i}")
        task = executor.execute_claude_async(
            prompt=f"Task for agent {i}",
            working_dir=workspace
        )
        tasks.append(task)
    
    # Run all agents concurrently (non-blocking)
    results = await asyncio.gather(*tasks)
    
    # All results available immediately
    return results

# Execute
results = asyncio.run(run_parallel_agents())
```

## Performance Benefits

Testing shows significant speedup with parallel execution:

- **5 agents sequential**: ~25 seconds
- **5 agents parallel**: ~5 seconds  
- **Speedup**: 4.9x faster
- **Efficiency**: 98% (near-perfect parallelization)

## Key Requirements

1. **Use async methods**: Call `execute_claude_async()` instead of `execute_claude()`
2. **Unique workspaces**: Each agent needs its own directory for session isolation
3. **asyncio.gather()**: Runs all tasks concurrently
4. **Python 3.9+**: For modern asyncio support

## Examples Provided

### 1. Simple Parallel (`examples/simple_parallel.py`)
- Basic demonstration with 5 agents
- Each performing a different simple task
- Shows concurrent execution pattern

### 2. Advanced Parallel (`examples/parallel_agents.py`)
- 5 specialized agents (poet, mathematician, historian, chef, translator)
- Timing and cost tracking
- Session continuation after parallel execution
- Detailed performance metrics

### 3. Timing Demo (`examples/parallel_timing_demo.py`)
- Compares sequential vs parallel execution
- Measures actual speedup
- Calculates parallel efficiency

## Use Cases

Parallel agents are perfect for:

1. **Data Processing**: Each agent processes a different dataset
2. **Multi-perspective Analysis**: Get insights from different viewpoints simultaneously
3. **Task Decomposition**: Break complex problems into parallel subtasks
4. **A/B Testing**: Test multiple approaches concurrently
5. **Report Generation**: Generate multiple sections in parallel

## Architecture Notes

The current implementation:
- Uses Python's asyncio for concurrency
- Each ShellExecutor instance is independent
- Claude CLI handles session isolation via working directories
- No shared state between agents (fully isolated)

## Future Enhancements

With the Orchestrator (Step 4), we'll add:
- Agent pools with automatic task distribution
- Result aggregation and synthesis
- Inter-agent communication patterns
- Dynamic agent spawning based on workload

For now, the parallel execution capability provides a solid foundation for building sophisticated multi-agent applications.