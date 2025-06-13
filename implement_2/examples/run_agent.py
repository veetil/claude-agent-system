#!/usr/bin/env python3
"""
Simple agent runner using Claude Multi-Agent System

Usage:
    python run_agent.py "Your prompt here"
    python run_agent.py "Your prompt" --system "Custom system prompt"
    python run_agent.py "Your prompt" --workspace /path/to/workspace
"""

import argparse
import json
import sys
from pathlib import Path
import tempfile

from claude_multi_agent import ShellExecutor, setup_logging


def run_agent(prompt: str, system_prompt: str = None, workspace: Path = None):
    """Run a single agent with the given prompt
    
    Args:
        prompt: The user prompt to send
        system_prompt: Optional system prompt (currently Claude CLI doesn't support this directly)
        workspace: Working directory for the agent (defaults to temp dir)
        
    Returns:
        dict: The JSON response from Claude
    """
    # Set up logging
    setup_logging(level="INFO")
    
    # Create workspace if not provided
    if workspace is None:
        workspace = Path(tempfile.mkdtemp(prefix="claude_agent_"))
        print(f"Created temporary workspace: {workspace}")
    else:
        workspace = Path(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
    
    # Initialize shell executor
    executor = ShellExecutor()
    
    # Combine system prompt with user prompt if provided
    # Note: Claude CLI doesn't have a separate system prompt flag,
    # so we prepend it to the user prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    else:
        full_prompt = prompt
    
    print(f"\n=== Running Agent ===")
    print(f"Workspace: {workspace}")
    print(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")
    if system_prompt:
        print(f"System prompt: {system_prompt[:100]}..." if len(system_prompt) > 100 else f"System prompt: {system_prompt}")
    print()
    
    try:
        # Execute with Claude CLI
        result = executor.execute_claude(
            prompt=full_prompt,
            working_dir=workspace
        )
        
        # Print results
        print(f"=== Response ===")
        print(f"Session ID: {result['session_id']}")
        print(f"Result: {result['result']}")
        
        if 'usage' in result:
            usage = result['usage']
            print(f"\n=== Usage ===")
            print(f"Input tokens: {usage.get('input_tokens', 'N/A')}")
            print(f"Output tokens: {usage.get('output_tokens', 'N/A')}")
            if 'total_cost_usd' in result:
                print(f"Cost: ${result['total_cost_usd']:.4f}")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Run a Claude agent with a single prompt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_agent.py "Write a hello world function in Python"
    python run_agent.py "Explain recursion" --system "You are a teacher. Be concise."
    python run_agent.py "Continue our discussion" --workspace /tmp/my_agent
        """
    )
    
    parser.add_argument(
        "prompt",
        help="The prompt to send to Claude"
    )
    
    parser.add_argument(
        "--system", "-s",
        help="System prompt to prepend (optional)",
        default=None
    )
    
    parser.add_argument(
        "--workspace", "-w",
        help="Workspace directory (defaults to temp dir)",
        type=Path,
        default=None
    )
    
    parser.add_argument(
        "--json", "-j",
        help="Output full JSON response",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Run the agent
    result = run_agent(
        prompt=args.prompt,
        system_prompt=args.system,
        workspace=args.workspace
    )
    
    # Output JSON if requested
    if args.json:
        print("\n=== Full JSON Response ===")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()