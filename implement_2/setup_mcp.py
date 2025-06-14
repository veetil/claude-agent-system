#!/usr/bin/env python3
"""
Setup MCP servers for Claude CLI based on .roo/mcp.json configuration.
"""

import json
import subprocess
import os
from pathlib import Path

def load_mcp_config():
    """Load MCP configuration from .roo/mcp.json"""
    mcp_config_path = Path("/Users/mi/Projects/claude-sdk/.roo/mcp.json")
    with open(mcp_config_path, 'r') as f:
        return json.load(f)

def load_env_vars():
    """Load environment variables from .env.mcp"""
    env_vars = {}
    env_file = Path("/Users/mi/Projects/claude-sdk/.env.mcp")
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
    
    return env_vars

def setup_mcp_servers():
    """Set up MCP servers in Claude CLI."""
    
    # Load configurations
    mcp_config = load_mcp_config()
    env_vars = load_env_vars()
    
    # Get current environment and add MCP variables
    env = os.environ.copy()
    env.update(env_vars)
    
    print("🔧 Setting up MCP servers...\n")
    
    # First, list current servers
    result = subprocess.run(["claude", "mcp", "list"], capture_output=True, text=True)
    print("Current MCP servers:")
    print(result.stdout)
    
    # Add each server from mcp.json
    for server_name, server_config in mcp_config.get("mcpServers", {}).items():
        print(f"\n📦 Adding MCP server: {server_name}")
        
        # Build the command
        cmd = ["claude", "mcp", "add", server_name]
        
        # Add command and args
        cmd.append(server_config["command"])
        cmd.extend(server_config.get("args", []))
        
        # Handle environment variables for this server
        if "env" in server_config:
            # We need to pass env vars differently
            # For now, let's show what would be configured
            print(f"   Command: {server_config['command']}")
            print(f"   Args: {server_config.get('args', [])}")
            print(f"   Env vars: {list(server_config.get('env', {}).keys())}")
        
        # Try to add the server
        try:
            # For servers that use "source ./export-env.sh", we need to handle specially
            if "source ./export-env.sh" in str(server_config.get("args", [])):
                print(f"   ⚠️  Server {server_name} requires environment setup")
                print(f"   Available env vars: GITHUB_TOKEN, SUPABASE_ACCESS_TOKEN, etc.")
            
            # Actually add the server
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode == 0:
                print(f"   ✅ Added successfully")
            else:
                print(f"   ❌ Failed: {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # List servers again to confirm
    print("\n\n📋 Final MCP server list:")
    result = subprocess.run(["claude", "mcp", "list"], capture_output=True, text=True)
    print(result.stdout)

def test_mcp_server(server_name: str):
    """Test a specific MCP server."""
    print(f"\n🧪 Testing MCP server: {server_name}")
    
    # Simple test prompts for each server
    test_prompts = {
        "github": "Use the GitHub MCP server to list my repositories (show just 2)",
        "puppeteer": "Use Puppeteer MCP to navigate to https://example.com and take a screenshot",
        "perplexityai": "Use Perplexity MCP to search for 'what is MCP protocol'",
        "supabase": "Use Supabase MCP to list available organizations",
        "firecrawl": "Use Firecrawl MCP to scrape the title from https://example.com"
    }
    
    prompt = test_prompts.get(server_name, f"Test the {server_name} MCP server")
    
    cmd = [
        "claude",
        "--dangerously-skip-permissions",
        "-p", prompt,
        "--output-format", "json",
        "--debug"
    ]
    
    # Load environment variables
    env = os.environ.copy()
    env.update(load_env_vars())
    
    try:
        print(f"Running: {' '.join(cmd[:4])}...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            print(f"✅ Success: {response.get('result', '')[:200]}...")
        else:
            print(f"❌ Failed: {result.stderr[:200]}...")
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  Timeout after 30 seconds")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("=== MCP Server Setup for Claude CLI ===\n")
    
    # Check if Claude CLI is available
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
        print("✅ Claude CLI is available\n")
    except:
        print("❌ Claude CLI not found. Please install it first.")
        return
    
    # Setup MCP servers
    setup_mcp_servers()
    
    # Optional: Test servers
    print("\n\n🧪 Would you like to test the MCP servers? (y/n): ", end="")
    if input().lower() == 'y':
        mcp_config = load_mcp_config()
        for server_name in mcp_config.get("mcpServers", {}).keys():
            test_mcp_server(server_name)
    
    print("\n\n✅ MCP setup completed!")
    print("\nTo use MCP servers in your prompts:")
    print("1. Make sure environment variables are set (.env.mcp)")
    print("2. Use prompts that reference the MCP servers")
    print("3. Example: 'Use GitHub MCP to search for repositories'")

if __name__ == "__main__":
    main()