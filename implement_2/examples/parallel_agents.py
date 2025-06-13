#!/usr/bin/env python3
"""
Example of running multiple agents in parallel with different tasks

This demonstrates:
1. Launching multiple agents concurrently
2. Each agent having its own workspace
3. Different tasks running simultaneously
4. Collecting all results when complete
"""

import asyncio
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any

from claude_multi_agent import ShellExecutor, setup_logging


async def run_agent_task(
    agent_id: str,
    prompt: str,
    workspace: Path
) -> Dict[str, Any]:
    """Run a single agent task asynchronously
    
    Args:
        agent_id: Unique identifier for this agent
        prompt: The task prompt
        workspace: Agent's working directory
        
    Returns:
        Dict containing agent_id, result, and timing info
    """
    executor = ShellExecutor()
    start_time = time.time()
    
    print(f"[{agent_id}] Starting task in {workspace}")
    
    try:
        # Run the agent
        response = await executor.execute_claude_async(
            prompt=prompt,
            working_dir=workspace
        )
        
        duration = time.time() - start_time
        
        return {
            "agent_id": agent_id,
            "success": True,
            "result": response["result"],
            "session_id": response["session_id"],
            "duration": duration,
            "cost": response.get("total_cost_usd", 0),
            "workspace": str(workspace)
        }
        
    except Exception as e:
        duration = time.time() - start_time
        return {
            "agent_id": agent_id,
            "success": False,
            "error": str(e),
            "duration": duration,
            "workspace": str(workspace)
        }


async def run_parallel_agents():
    """Run 5 different agents in parallel"""
    
    # Define 5 different tasks
    agent_tasks = [
        {
            "id": "poet",
            "prompt": "Write a short haiku about programming"
        },
        {
            "id": "mathematician", 
            "prompt": "What is the factorial of 7? Show your calculation"
        },
        {
            "id": "historian",
            "prompt": "In one sentence, who was Alan Turing?"
        },
        {
            "id": "chef",
            "prompt": "Give me a simple recipe for scrambled eggs in 3 steps"
        },
        {
            "id": "translator",
            "prompt": "Translate 'Hello, how are you?' to French, Spanish, and Japanese"
        }
    ]
    
    # Create temporary workspaces for each agent
    workspaces = {}
    for task in agent_tasks:
        workspace = Path(tempfile.mkdtemp(prefix=f"agent_{task['id']}_"))
        workspaces[task['id']] = workspace
    
    print(f"=== Launching {len(agent_tasks)} agents in parallel ===\n")
    
    # Create tasks for concurrent execution
    tasks = []
    for agent_task in agent_tasks:
        agent_id = agent_task['id']
        prompt = agent_task['prompt']
        workspace = workspaces[agent_id]
        
        # Create coroutine for each agent
        task = run_agent_task(agent_id, prompt, workspace)
        tasks.append(task)
    
    # Run all agents concurrently
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    total_duration = time.time() - start_time
    
    return results, total_duration


def print_results(results: List[Dict[str, Any]], total_duration: float):
    """Print the results from all agents"""
    
    print("\n=== All agents completed ===")
    print(f"Total execution time: {total_duration:.2f} seconds\n")
    
    # Print individual results
    for i, result in enumerate(results, 1):
        print(f"--- Agent {i}: {result['agent_id']} ---")
        print(f"Duration: {result['duration']:.2f}s")
        
        if result['success']:
            print(f"Session ID: {result['session_id']}")
            print(f"Cost: ${result.get('cost', 0):.4f}")
            print(f"Result: {result['result'][:200]}..." if len(result['result']) > 200 else f"Result: {result['result']}")
        else:
            print(f"ERROR: {result['error']}")
        
        print(f"Workspace: {result['workspace']}")
        print()
    
    # Summary statistics
    successful = sum(1 for r in results if r['success'])
    total_cost = sum(r.get('cost', 0) for r in results if r['success'])
    avg_duration = sum(r['duration'] for r in results) / len(results)
    
    print("=== Summary ===")
    print(f"Successful agents: {successful}/{len(results)}")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Average agent duration: {avg_duration:.2f}s")
    print(f"Parallel speedup: {avg_duration * len(results) / total_duration:.1f}x")


async def main():
    """Main entry point"""
    setup_logging(level="INFO")
    
    # Run the parallel agents
    results, duration = await run_parallel_agents()
    
    # Display results
    print_results(results, duration)
    
    # Example of continuing a conversation with one of the agents
    print("\n=== Example: Continuing conversation with mathematician ===")
    
    math_result = next(r for r in results if r['agent_id'] == 'mathematician')
    if math_result['success']:
        executor = ShellExecutor()
        continuation = await executor.execute_claude_async(
            prompt="Now calculate the factorial of 8",
            session_id=math_result['session_id'],
            working_dir=Path(math_result['workspace'])
        )
        print(f"Continuation result: {continuation['result']}")
        print(f"New session ID: {continuation['session_id']}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())