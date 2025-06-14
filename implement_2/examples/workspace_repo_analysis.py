#!/usr/bin/env python3
"""
Example: Agent analyzes a GitHub repository and creates a summary file.

This demonstrates:
1. Creating a workspace with a GitHub repo and additional files
2. Checking workspace contents before agent work
3. Having the agent analyze and create a summary
4. Checking workspace contents after to verify the summary was created
"""

import tempfile
from pathlib import Path
import json

from claude_multi_agent import ShellExecutor, WorkspaceManager, setup_logging


def list_workspace_contents(workspace_path: Path, indent: str = "  ") -> None:
    """Recursively list all files in the workspace."""
    def print_tree(path: Path, prefix: str = ""):
        items = sorted(path.iterdir())
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir() and not item.name.startswith('.'):
                extension = "    " if is_last else "│   "
                print_tree(item, prefix + extension)
    
    print(f"\nWorkspace contents ({workspace_path}):")
    print_tree(workspace_path)


def main():
    """Main example function."""
    setup_logging(level="INFO")
    
    print("=== GitHub Repository Analysis Example ===\n")
    
    # Create temporary directory for our local files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create an analysis guide file
        guide_file = temp_path / "ANALYSIS_GUIDE.md"
        guide_file.write_text("""# Repository Analysis Guide

Please analyze the cloned repository and create a file called `repo-summary.md` that includes:

1. **Overview**: What is this repository about?
2. **Structure**: Main directories and their purposes
3. **Key Files**: Important files and what they do
4. **Technologies**: Languages and frameworks used
5. **Getting Started**: Basic setup instructions if available

Focus on providing a concise but comprehensive overview that would help a new developer understand the project quickly.
""")
        
        # Create a config file for the analysis
        config_file = temp_path / "analysis_config.json"
        config_file.write_text(json.dumps({
            "output_file": "repo-summary.md",
            "max_depth": 3,
            "include_code_snippets": False,
            "focus_areas": ["README", "main files", "configuration"]
        }, indent=2))
        
        # Initialize managers
        workspace_manager = WorkspaceManager()
        shell_executor = ShellExecutor()
        
        # Define resources
        files = [
            {
                "name": "ANALYSIS_GUIDE.md",
                "src_path": str(guide_file),
                "dest_path": "."
            },
            {
                "name": "analysis_config.json", 
                "src_path": str(config_file),
                "dest_path": "config"
            }
        ]
        
        # Use the specified learn repository
        repos = [
            {
                "github": "https://github.com/Polkm/learn",
                "dest_path": "learn-repo"
            }
        ]
        
        try:
            # Create workspace
            print("1. Creating workspace with GitHub repo and guide files...")
            workspace_path = workspace_manager.create_workspace(
                "repo-analysis",
                files=files,
                repos=repos,
                persistent=True  # Keep it for inspection
            )
            
            print(f"\n   Workspace created at: {workspace_path}")
            
            # Check initial contents
            print("\n2. Initial workspace contents (before agent work):")
            list_workspace_contents(workspace_path)
            
            # Verify repo-summary.md doesn't exist yet
            summary_path = workspace_path / "repo-summary.md"
            print(f"\n   repo-summary.md exists: {summary_path.exists()}")
            
            # The prompt that instructs the agent to create the summary
            analysis_prompt = """Please analyze the GitHub repository in the 'learn-repo' directory 
and create a comprehensive summary. Read the ANALYSIS_GUIDE.md file first for detailed 
instructions. The summary should be saved as 'repo-summary.md' in the workspace root.

Also check the config/analysis_config.json file for additional parameters.

After creating the summary, confirm that the file was created successfully."""
            
            # Run the agent
            print("\n3. Running agent to analyze repository...")
            print("   This may take a moment...\n")
            
            response = shell_executor.execute_claude(
                prompt=analysis_prompt,
                working_dir=workspace_path
            )
            
            print("Agent's response:")
            print("-" * 70)
            print(response["result"])
            print("-" * 70)
            
            # Check workspace contents after agent work
            print("\n4. Workspace contents after agent work:")
            list_workspace_contents(workspace_path)
            
            # Check if repo-summary.md was created
            print(f"\n5. Checking for repo-summary.md...")
            if summary_path.exists():
                print("   ✅ repo-summary.md was created!")
                print("\n   First 500 characters of the summary:")
                print("   " + "-" * 60)
                content = summary_path.read_text()
                preview = content[:500] + "..." if len(content) > 500 else content
                for line in preview.split('\n'):
                    print(f"   {line}")
                print("   " + "-" * 60)
                
                # Show file size
                size = summary_path.stat().st_size
                print(f"\n   File size: {size} bytes")
            else:
                print("   ❌ repo-summary.md was NOT created")
                
            # Continue the session to get more details
            print("\n6. Asking agent for more details...")
            response2 = shell_executor.execute_claude(
                prompt="What sections did you include in the repo-summary.md file? Also, what was the most interesting thing you found in the repository?",
                session_id=response["session_id"],
                working_dir=workspace_path
            )
            
            print("\nAgent's follow-up:")
            print("-" * 70)
            print(response2["result"])
            print("-" * 70)
            
            # Show session costs
            total_cost = response.get("total_cost_usd", 0) + response2.get("total_cost_usd", 0)
            print(f"\n7. Total cost for analysis: ${total_cost:.4f}")
            
            # Cleanup instructions
            print(f"\n8. Workspace preserved at: {workspace_path}")
            print("   To view the full summary:")
            print(f"   cat {summary_path}")
            print("\n   To clean up the workspace:")
            print(f"   rm -rf {workspace_path}")
            
        except Exception as e:
            print(f"\nError: {e}")
            print("\nNote: This example requires:")
            print("- Git to be installed")
            print("- Internet access to clone from GitHub")
            print("- Claude CLI to be properly configured")


if __name__ == "__main__":
    main()