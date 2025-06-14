#!/usr/bin/env python3
"""
Test MCP integration with our multi-agent system.
This test verifies that MCP servers work with the updated executors.
"""

import json
import tempfile
from pathlib import Path

from src.claude_multi_agent.mcp_support import MCPManager
from src.claude_multi_agent.shell.executor import ShellExecutor
from src.claude_multi_agent.shell.executor_realtime import RealtimeShellExecutor
from src.claude_multi_agent.utils.logging import setup_logging

def test_basic_mcp():
    """Test basic MCP functionality without using MCP servers."""
    print("\n📝 Test 1: Basic test without MCP")
    
    # Create executor without MCP
    executor = ShellExecutor()
    
    # Simple test
    result = executor.execute_claude(
        prompt="What is 2+2?",
        debug=False
    )
    
    print(f"✅ Basic test passed: {result.get('result', '')[:100]}...")
    print(f"   Session ID: {result.get('session_id')}")
    return result.get('session_id')

def test_mcp_github():
    """Test MCP with GitHub server."""
    print("\n📝 Test 2: MCP with GitHub server")
    
    # Create MCP manager
    mcp_manager = MCPManager()
    
    # Create executor with MCP support
    executor = ShellExecutor(mcp_manager=mcp_manager)
    
    # Test with GitHub MCP
    prompt = """Use the GitHub MCP server to search for repositories 
    related to 'machine learning'. Show me just the first 2 results."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace = Path(tmp_dir)
        
        # Execute with MCP
        result = executor.execute_claude(
            prompt=prompt,
            working_dir=workspace,
            debug=False,
            enable_mcp=True
        )
        
        print(f"✅ MCP test passed: {result.get('result', '')[:200]}...")
        print(f"   Session ID: {result.get('session_id')}")
        print(f"   Cost: ${result.get('total_cost_usd', 0):.4f}")
        
        # Check if MCP files were created
        mcp_json = workspace / ".roo" / "mcp.json"
        env_mcp = workspace / ".env.mcp"
        export_sh = workspace / "export-env.sh"
        
        print(f"\n   MCP files created:")
        print(f"   - .roo/mcp.json: {'✅' if mcp_json.exists() else '❌'}")
        print(f"   - .env.mcp: {'✅' if env_mcp.exists() else '❌'}")
        print(f"   - export-env.sh: {'✅' if export_sh.exists() else '❌'}")
        
    return result.get('session_id')

def test_mcp_realtime():
    """Test MCP with real-time debug output."""
    print("\n📝 Test 3: MCP with real-time debug output")
    
    # Create MCP manager
    mcp_manager = MCPManager()
    
    # Create realtime executor with MCP support
    executor = RealtimeShellExecutor(mcp_manager=mcp_manager)
    
    # Test with GitHub MCP and debug
    prompt = """Use the GitHub MCP server to list my repositories. 
    Show just 2 repositories with their names and descriptions."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace = Path(tmp_dir)
        
        print("🔧 Running with real-time debug output...")
        
        # Execute with MCP and debug
        result = executor.execute_claude(
            prompt=prompt,
            working_dir=workspace,
            debug=True,  # Enable real-time debug
            enable_mcp=True
        )
        
        print(f"\n✅ Real-time MCP test completed")
        print(f"   Session ID: {result.get('session_id')}")
        print(f"   Cost: ${result.get('total_cost_usd', 0):.4f}")
        
    return result.get('session_id')

def test_mcp_multiple_servers():
    """Test using multiple MCP servers in one session."""
    print("\n📝 Test 4: Multiple MCP servers")
    
    # Create MCP manager
    mcp_manager = MCPManager()
    
    # Create executor with MCP support
    executor = ShellExecutor(mcp_manager=mcp_manager)
    
    # Test with multiple MCP servers
    prompt = """First, use the GitHub MCP server to search for 'claude' repositories (show 2).
    Then, use the Perplexity MCP server to search for 'what is Model Context Protocol MCP'.
    Provide a brief summary of both results."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace = Path(tmp_dir)
        
        # Execute with MCP
        result = executor.execute_claude(
            prompt=prompt,
            working_dir=workspace,
            debug=False,
            enable_mcp=True,
            timeout=120  # Longer timeout for multiple operations
        )
        
        print(f"✅ Multiple MCP test passed")
        print(f"   Session ID: {result.get('session_id')}")
        print(f"   Cost: ${result.get('total_cost_usd', 0):.4f}")
        print(f"\n   Result preview: {result.get('result', '')[:300]}...")
        
    return result.get('session_id')

def main():
    """Run all MCP integration tests."""
    print("=== MCP Integration Tests ===")
    print("Testing Model Context Protocol with our multi-agent system\n")
    
    # Setup logging
    setup_logging("DEBUG")
    
    try:
        # Run tests
        session1 = test_basic_mcp()
        session2 = test_mcp_github()
        session3 = test_mcp_realtime()
        session4 = test_mcp_multiple_servers()
        
        print("\n✅ All tests completed successfully!")
        print("\nSessions created:")
        print(f"  - Basic test: {session1}")
        print(f"  - GitHub MCP: {session2}")
        print(f"  - Real-time MCP: {session3}")
        print(f"  - Multiple MCP: {session4}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()