#!/usr/bin/env python3
"""
Example of session management with Claude Multi-Agent System

This demonstrates:
1. Starting a new session
2. Continuing a conversation with context
3. Using the same workspace for persistence
"""

from pathlib import Path
import tempfile

from claude_multi_agent import ShellExecutor, setup_logging


def main():
    # Set up logging
    setup_logging(level="INFO")
    
    # Create a workspace
    workspace = Path(tempfile.mkdtemp(prefix="claude_session_"))
    print(f"Using workspace: {workspace}\n")
    
    # Initialize shell executor
    executor = ShellExecutor()
    
    # Step 1: Start a conversation
    print("=== Starting new conversation ===")
    response1 = executor.execute_claude(
        prompt="I'm going to teach you a secret word. The word is 'RAINBOW'. Please confirm you've learned it.",
        working_dir=workspace
    )
    
    print(f"Response: {response1['result']}")
    print(f"Session ID: {response1['session_id']}\n")
    
    # Step 2: Continue the conversation
    print("=== Continuing conversation ===")
    response2 = executor.execute_claude(
        prompt="What was the secret word I taught you?",
        session_id=response1['session_id'],
        working_dir=workspace
    )
    
    print(f"Response: {response2['result']}")
    print(f"New Session ID: {response2['session_id']}\n")
    
    # Step 3: Further continuation
    print("=== Testing context retention ===")
    response3 = executor.execute_claude(
        prompt="Spell the secret word backwards",
        session_id=response2['session_id'],
        working_dir=workspace
    )
    
    print(f"Response: {response3['result']}")
    print(f"Final Session ID: {response3['session_id']}\n")
    
    # Show cost summary
    total_cost = sum(r.get('total_cost_usd', 0) for r in [response1, response2, response3])
    print(f"=== Cost Summary ===")
    print(f"Total cost for conversation: ${total_cost:.4f}")
    print(f"Workspace preserved at: {workspace}")
    print("\nYou can continue this conversation by using the last session ID:")
    print(f"  Session ID: {response3['session_id']}")
    print(f"  Workspace: {workspace}")


if __name__ == "__main__":
    main()