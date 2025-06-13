#!/usr/bin/env python3
"""
Simple example of running multiple Claude agents in parallel

Shows the basic pattern for concurrent agent execution without blocking.
"""

import asyncio
import tempfile
from pathlib import Path

from claude_multi_agent import ShellExecutor


async def run_agent(name: str, prompt: str) -> dict:
    """Run a single agent asynchronously"""
    # Create a unique workspace for this agent
    workspace = Path(tempfile.mkdtemp(prefix=f"agent_{name}_"))
    
    # Create executor and run
    executor = ShellExecutor()
    print(f"[{name}] Starting...")
    
    result = await executor.execute_claude_async(
        prompt=prompt,
        working_dir=workspace
    )
    
    print(f"[{name}] Complete!")
    return {
        "name": name,
        "result": result["result"],
        "session_id": result["session_id"]
    }


async def main():
    """Run 5 agents in parallel"""
    
    # Define our 5 agents and their tasks
    agents = [
        ("Agent1", "Count from 1 to 5"),
        ("Agent2", "Name 3 colors"),
        ("Agent3", "What is 10 + 20?"),
        ("Agent4", "Say hello in 3 languages"),
        ("Agent5", "Name 3 animals")
    ]
    
    print("Launching 5 agents in parallel...\n")
    
    # Create tasks for all agents
    tasks = [run_agent(name, prompt) for name, prompt in agents]
    
    # Run all agents concurrently (non-blocking)
    results = await asyncio.gather(*tasks)
    
    # Print all results
    print("\n=== All Results ===")
    for result in results:
        print(f"\n{result['name']}:")
        print(f"  Result: {result['result']}")
        print(f"  Session: {result['session_id']}")


if __name__ == "__main__":
    asyncio.run(main())