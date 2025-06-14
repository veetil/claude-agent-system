#!/usr/bin/env python3
"""
Test script to compare different debug output approaches.
"""

import sys
from pathlib import Path

# Test with the realtime executor
def test_realtime_executor():
    print("=== Testing Realtime Executor ===")
    from claude_multi_agent.shell.executor_realtime import RealtimeShellExecutor
    from claude_multi_agent import setup_logging
    
    setup_logging(level="INFO")
    
    executor = RealtimeShellExecutor()
    workspace = Path("/tmp/test_debug")
    workspace.mkdir(exist_ok=True)
    
    try:
        response = executor.execute_claude(
            prompt="Create a simple hello.txt file with 'Debug test'",
            working_dir=workspace,
            timeout=30,
            debug=True
        )
        print(f"\nSuccess! Cost: ${response.get('total_cost_usd', 0):.4f}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Cleanup
        import shutil
        if workspace.exists():
            shutil.rmtree(workspace)


# Test with original executor with enhanced debug
def test_original_with_debug():
    print("\n\n=== Testing Original Executor with Debug ===")
    from claude_multi_agent.shell.executor import ShellExecutor
    from claude_multi_agent import setup_logging
    
    setup_logging(level="INFO")
    
    executor = ShellExecutor()
    workspace = Path("/tmp/test_debug2")
    workspace.mkdir(exist_ok=True)
    
    try:
        response = executor.execute_claude(
            prompt="Create a simple world.txt file with 'Original debug test'",
            working_dir=workspace,
            timeout=30,
            debug=True
        )
        print(f"\nSuccess! Cost: ${response.get('total_cost_usd', 0):.4f}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Cleanup
        import shutil
        if workspace.exists():
            shutil.rmtree(workspace)


if __name__ == "__main__":
    # Test which approach to use
    if len(sys.argv) > 1 and sys.argv[1] == "realtime":
        test_realtime_executor()
    elif len(sys.argv) > 1 and sys.argv[1] == "original":
        test_original_with_debug()
    else:
        print("Usage: python test_debug_streaming.py [realtime|original]")
        print("\nTesting both approaches...")
        test_realtime_executor()
        test_original_with_debug()