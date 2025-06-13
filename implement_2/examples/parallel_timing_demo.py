#!/usr/bin/env python3
"""
Demonstrates parallel speedup by comparing sequential vs parallel execution
"""

import asyncio
import tempfile
import time
from pathlib import Path

from claude_multi_agent import ShellExecutor, setup_logging


async def timed_agent(name: str, prompt: str) -> dict:
    """Run an agent and track timing"""
    workspace = Path(tempfile.mkdtemp(prefix=f"agent_{name}_"))
    executor = ShellExecutor()
    
    start = time.time()
    result = await executor.execute_claude_async(
        prompt=prompt,
        working_dir=workspace
    )
    duration = time.time() - start
    
    return {
        "name": name,
        "duration": duration,
        "result": result["result"][:50] + "..." if len(result["result"]) > 50 else result["result"]
    }


async def run_sequential():
    """Run agents one after another"""
    prompts = [
        "Write a haiku",
        "List prime numbers under 20", 
        "Name 5 programming languages",
        "What is machine learning in one sentence?",
        "Convert 100°F to Celsius"
    ]
    
    print("Running 5 agents SEQUENTIALLY...")
    start = time.time()
    
    results = []
    for i, prompt in enumerate(prompts):
        result = await timed_agent(f"Seq{i+1}", prompt)
        print(f"  {result['name']} completed in {result['duration']:.2f}s")
        results.append(result)
    
    total_time = time.time() - start
    print(f"Sequential total time: {total_time:.2f}s\n")
    print("*********\nResults\n")
    for r in results:
        print(r)
    print("*********\nEnd Results\n")

    return results, total_time


async def run_parallel():
    """Run all agents at the same time"""
    prompts = [
        "Write a haiku",
        "List prime numbers under 20",
        "Name 5 programming languages", 
        "What is machine learning in one sentence?",
        "Convert 100°F to Celsius"
    ]
    
    print("Running 5 agents in PARALLEL...")
    start = time.time()
    
    # Launch all agents concurrently
    tasks = [timed_agent(f"Par{i+1}", prompt) for i, prompt in enumerate(prompts)]
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start
    
    for result in results:
        print(f"  {result['name']} completed in {result['duration']:.2f}s")
        print("Result\n")
        print(result)
        print("End Result\n\n")
    
    print(f"Parallel total time: {total_time:.2f}s\n")
    
    return results, total_time


async def main():
    """Compare sequential vs parallel execution"""
    setup_logging(level="WARNING")  # Reduce logging noise
    
    print("=== Parallel Execution Demo ===\n")
    
    # Run sequential
    seq_results, seq_time = await run_sequential()
    
    # Run parallel
    par_results, par_time = await run_parallel()
    
    # Show speedup
    speedup = seq_time / par_time
    print(f"=== Performance Comparison ===")
    print(f"Sequential time: {seq_time:.2f}s")
    print(f"Parallel time: {par_time:.2f}s")
    print(f"Speedup: {speedup:.1f}x faster")
    print(f"Time saved: {seq_time - par_time:.2f}s")
    
    # Calculate theoretical vs actual speedup
    avg_task_time = sum(r['duration'] for r in par_results) / len(par_results)
    theoretical_speedup = (avg_task_time * len(par_results)) / par_time
    efficiency = (speedup / len(par_results)) * 100
    
    print(f"\n=== Efficiency Analysis ===")
    print(f"Number of agents: {len(par_results)}")
    print(f"Theoretical max speedup: {len(par_results)}x")
    print(f"Actual speedup: {speedup:.1f}x")
    print(f"Parallel efficiency: {efficiency:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())