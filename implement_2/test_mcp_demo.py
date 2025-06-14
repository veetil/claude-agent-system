#!/usr/bin/env python3
"""
Demonstration of MCP integration with Claude Multi-Agent System.
Shows how to use MCP servers with the agent runner.
"""

import json
from pathlib import Path
from claude_multi_agent import run_agent_with_io, setup_logging

def demo_github_mcp():
    """Demo: Use GitHub MCP to search repositories."""
    print("\n🔍 Demo 1: GitHub MCP - Search for Claude repositories")
    
    result = run_agent_with_io(
        prompt="""Use the GitHub MCP server to search for repositories 
        with 'claude' in the name. Show me the top 3 results with:
        - Repository name
        - Description
        - Star count
        
        Just display the results, don't save to a file.""",
        system_prompt="You have access to MCP servers. Be concise.",
        workspace_id="demo_github",
        cleanup=True,
        timeout=60,
        enable_mcp=True
    )
    
    if result.success:
        print(f"✅ Success! Cost: ${result.cost_usd:.4f}")
        print(f"\nResult:\n{result.text_output}")
    else:
        print(f"❌ Failed: {result.error}")
    
    return result.session_id

def demo_perplexity_mcp():
    """Demo: Use Perplexity MCP for web search."""
    print("\n🔍 Demo 2: Perplexity MCP - Web search")
    
    result = run_agent_with_io(
        prompt="""Use the Perplexity MCP server to search for:
        'What is Model Context Protocol (MCP) by Anthropic?'
        
        Provide a brief 2-3 sentence summary.""",
        system_prompt="You have access to MCP servers. Be very concise.",
        workspace_id="demo_perplexity",
        cleanup=True,
        timeout=60,
        enable_mcp=True
    )
    
    if result.success:
        print(f"✅ Success! Cost: ${result.cost_usd:.4f}")
        print(f"\nResult:\n{result.text_output}")
    else:
        print(f"❌ Failed: {result.error}")
    
    return result.session_id

def demo_multi_mcp_with_file():
    """Demo: Use multiple MCP servers and save output."""
    print("\n🔍 Demo 3: Multiple MCP servers with file output")
    
    result = run_agent_with_io(
        prompt="""Do the following:
        1. Use GitHub MCP to find info about 'anthropics/anthropic-sdk-python'
        2. Use Perplexity MCP to search 'Claude AI features 2025'
        3. Create a brief report (5-6 lines) combining both findings
        4. Save it as 'mcp_demo_report.txt'""",
        output_files=[{
            "name": "mcp_demo_report.txt",
            "src_path": "mcp_demo_report.txt",
            "dest_path": "./outputs"
        }],
        workspace_id="demo_multi",
        cleanup=False,  # Keep workspace to check file
        timeout=90,
        enable_mcp=True,
        realtime_debug=True  # Show real-time output
    )
    
    if result.success:
        print(f"\n✅ Success! Cost: ${result.cost_usd:.4f}")
        print(f"Files created: {len(result.files_created)}")
        for f in result.files_created:
            print(f"  - {f['name']} -> {f['dest_path']}")
    else:
        print(f"❌ Failed: {result.error}")
    
    return result.session_id

def main():
    """Run MCP demonstrations."""
    print("=== MCP Integration Demo ===")
    print("Demonstrating Model Context Protocol with Claude Multi-Agent System\n")
    
    # Setup logging
    setup_logging("INFO")
    
    # Create output directory
    Path("./outputs").mkdir(exist_ok=True)
    
    try:
        # Run demos
        session1 = demo_github_mcp()
        print("\n" + "="*60)
        
        session2 = demo_perplexity_mcp()
        print("\n" + "="*60)
        
        session3 = demo_multi_mcp_with_file()
        
        print("\n\n✅ All demos completed!")
        print("\nSessions created:")
        print(f"  - GitHub search: {session1}")
        print(f"  - Perplexity search: {session2}")
        print(f"  - Multi-MCP with file: {session3}")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()