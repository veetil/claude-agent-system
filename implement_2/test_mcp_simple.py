#!/usr/bin/env python3
"""
Simple test to verify MCP (Model Context Protocol) integration with Claude CLI.
This test will check if we can use MCP servers through Claude.
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
import tempfile

def setup_mcp_environment(workspace_dir: Path):
    """Set up MCP configuration in the workspace."""
    
    # Copy MCP configuration
    mcp_config_src = Path("/Users/mi/Projects/claude-sdk/.roo/mcp.json")
    mcp_config_dst = workspace_dir / ".roo" / "mcp.json"
    mcp_config_dst.parent.mkdir(exist_ok=True)
    shutil.copy2(mcp_config_src, mcp_config_dst)
    
    # Create a modified export-env.sh that uses .env.mcp
    export_env_script = workspace_dir / "export-env.sh"
    export_env_script.write_text("""#!/bin/bash

# Load .env.mcp file and export variables
while IFS= read -r line || [ -n "$line" ]; do
  # Skip comments and empty lines
  if [[ $line =~ ^[[:space:]]*$ || $line =~ ^[[:space:]]*# ]]; then
    continue
  fi
  
  # Remove leading/trailing whitespace
  line=$(echo "$line" | xargs)
  
  # Export the variable
  export "$line"
  
  # Extract variable name for display
  var_name=$(echo "$line" | cut -d= -f1)
  echo "Exported: $var_name"
done < .env.mcp
""")
    export_env_script.chmod(0o755)
    
    # Copy .env.mcp
    env_mcp_src = Path("/Users/mi/Projects/claude-sdk/.env.mcp")
    env_mcp_dst = workspace_dir / ".env.mcp"
    shutil.copy2(env_mcp_src, env_mcp_dst)
    
    print(f"✅ MCP environment set up in {workspace_dir}")
    print(f"   - .roo/mcp.json copied")
    print(f"   - export-env.sh created")
    print(f"   - .env.mcp copied")

def test_mcp_with_claude():
    """Test MCP integration with Claude CLI."""
    
    # Create a temporary workspace
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace = Path(tmp_dir)
        print(f"\n🔧 Setting up test workspace: {workspace}")
        
        # Set up MCP environment
        setup_mcp_environment(workspace)
        
        # Test 1: Simple prompt without MCP
        print("\n📝 Test 1: Simple prompt without MCP")
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "-p", "What is 2+2?",
            "--output-format", "json"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                response = json.loads(result.stdout)
                print(f"✅ Success: {response.get('result', 'No result')[:100]}...")
            else:
                print(f"❌ Failed: {result.stderr}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Test with MCP - List GitHub repositories
        print("\n📝 Test 2: Using MCP to search GitHub")
        
        # First, export environment variables
        export_cmd = f"source {workspace}/export-env.sh && env"
        env_result = subprocess.run(
            ["bash", "-c", export_cmd],
            cwd=str(workspace),
            capture_output=True,
            text=True
        )
        
        # Parse environment variables
        env_vars = {}
        for line in env_result.stdout.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
        
        # Update current environment with MCP variables
        mcp_env = os.environ.copy()
        mcp_env.update(env_vars)
        
        # Now test Claude with MCP
        prompt = """Use the GitHub MCP server to search for repositories related to 'machine learning'.
Show me the first 3 results with their names and descriptions."""
        
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "-p", prompt,
            "--output-format", "json"
        ]
        
        print(f"Running Claude with MCP support...")
        print(f"Environment includes: GITHUB_TOKEN={mcp_env.get('GITHUB_TOKEN', 'Not set')[:20]}...")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(workspace),
                env=mcp_env,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                response = json.loads(result.stdout)
                print(f"✅ Success: {response.get('result', 'No result')[:200]}...")
                print(f"   Cost: ${response.get('total_cost_usd', 0):.4f}")
            else:
                print(f"❌ Failed: {result.stderr}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Test MCP with streaming output
        print("\n📝 Test 3: MCP with streaming output")
        
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "-p", "Use the GitHub MCP to list my repositories (just show 2)",
            "--output-format", "stream-json",
            "--debug"
        ]
        
        print("Running with stream-json format...")
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(workspace),
                env=mcp_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Read output
            stdout, stderr = process.communicate(timeout=60)
            
            if process.returncode == 0:
                print("✅ Streaming output received:")
                # Parse streaming JSON objects
                lines = stdout.strip().split('\n')
                json_count = 0
                for line in lines:
                    if line.strip().startswith('{'):
                        try:
                            obj = json.loads(line)
                            json_count += 1
                            if obj.get('type') == 'tool_use':
                                print(f"   🔧 Tool: {obj.get('name', 'unknown')}")
                            elif obj.get('type') == 'text':
                                print(f"   💬 Text: {obj.get('text', '')[:100]}...")
                        except:
                            pass
                print(f"   Total JSON objects: {json_count}")
            else:
                print(f"❌ Failed: {stderr}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=== MCP Integration Test ===")
    print("Testing Model Context Protocol with Claude CLI\n")
    
    # Check if Claude CLI is available
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
        print("✅ Claude CLI is available")
    except:
        print("❌ Claude CLI not found. Please install it first.")
        exit(1)
    
    # Run tests
    test_mcp_with_claude()
    
    print("\n✅ MCP test completed!")