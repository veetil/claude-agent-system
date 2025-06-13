#!/usr/bin/env python3
"""
Example of using WorkspaceManager with Git repositories.

This demonstrates:
1. Creating a workspace with a cloned repository
2. Adding local files to work alongside the repo
3. Using Claude to analyze the combined workspace
"""

import tempfile
from pathlib import Path

from claude_multi_agent import ShellExecutor, WorkspaceManager


def main():
    """Main example function."""
    print("=== Workspace Manager with Git Example ===\n")
    
    # Create temporary directory for local files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a local analysis script
        analysis_script = temp_path / "analyze.py"
        analysis_script.write_text('''
#!/usr/bin/env python3
"""Script to analyze a repository structure."""

import os
from pathlib import Path

def count_files_by_extension(directory):
    """Count files by their extensions."""
    extensions = {}
    
    for file_path in Path(directory).rglob("*"):
        if file_path.is_file():
            ext = file_path.suffix or "no_extension"
            extensions[ext] = extensions.get(ext, 0) + 1
    
    return extensions

if __name__ == "__main__":
    # Analyze the hello-world repo
    if Path("hello-world").exists():
        print("File count by extension in hello-world repo:")
        counts = count_files_by_extension("hello-world")
        for ext, count in sorted(counts.items()):
            print(f"  {ext}: {count}")
''')
        
        # Create a README for our workspace
        readme = temp_path / "WORKSPACE_README.md"
        readme.write_text('''
# Agent Workspace

This workspace contains:
1. The Hello-World repository (cloned from GitHub)
2. An analysis script (analyze.py) to examine the repository

## Tasks
- Explore the cloned repository
- Run the analysis script
- Create a summary of findings
''')
        
        # Initialize managers
        workspace_manager = WorkspaceManager()
        shell_executor = ShellExecutor()
        
        # Define resources
        files = [
            {
                "name": "analyze.py",
                "src_path": str(analysis_script),
                "dest_path": "scripts"
            },
            {
                "name": "WORKSPACE_README.md",
                "src_path": str(readme),
                "dest_path": "."
            }
        ]
        
        repos = [
            {
                "github": "https://github.com/octocat/Hello-World",
                "dest_path": "hello-world"
            }
        ]
        
        try:
            # Create workspace
            print("1. Creating workspace with repository and files...")
            workspace_path = workspace_manager.create_workspace(
                "git-analysis-workspace",
                files=files,
                repos=repos,
                persistent=True  # Keep it around for inspection
            )
            
            print(f"   Workspace created at: {workspace_path}")
            
            # List workspace contents
            print("\n2. Workspace structure:")
            for item in sorted(workspace_path.rglob("*"))[:20]:  # Limit output
                if item.is_file():
                    rel_path = item.relative_to(workspace_path)
                    print(f"   - {rel_path}")
            
            # Use Claude to explore
            print("\n3. Having Claude explore the workspace...")
            response = shell_executor.execute_claude(
                prompt="""Look at the WORKSPACE_README.md file first, then explore the hello-world 
                repository. What kind of project is it? List the main files you find.""",
                working_dir=workspace_path
            )
            
            print(f"\nClaude's exploration:")
            print("-" * 50)
            print(response["result"])
            print("-" * 50)
            
            # Have Claude run the analysis
            print("\n4. Having Claude run the analysis script...")
            response2 = shell_executor.execute_claude(
                prompt="Run the Python script in the scripts directory and tell me what it finds.",
                session_id=response["session_id"],
                working_dir=workspace_path
            )
            
            print(f"\nClaude's analysis:")
            print("-" * 50)
            print(response2["result"])
            print("-" * 50)
            
            # Show cost
            total_cost = response.get("total_cost_usd", 0) + response2.get("total_cost_usd", 0)
            print(f"\n5. Total cost: ${total_cost:.4f}")
            
            # Cleanup decision
            print(f"\n6. Workspace is persistent at: {workspace_path}")
            print("   To clean it up, run:")
            print(f"   rm -rf {workspace_path}")
            
        except Exception as e:
            print(f"\nError: {e}")
            print("\nNote: This example requires git to be installed.")
            print("It also requires internet access to clone from GitHub.")


if __name__ == "__main__":
    main()