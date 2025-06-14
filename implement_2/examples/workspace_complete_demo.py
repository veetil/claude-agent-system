#!/usr/bin/env python3
"""
Complete workspace demo showing all features.

This example demonstrates:
1. Creating a workspace with files, folders, and a git repo
2. Listing workspace contents before agent execution
3. Running an agent in the workspace
4. Checking workspace contents after execution
5. Verifying any files created by the agent
"""

import tempfile
from pathlib import Path
import json

from claude_multi_agent import ShellExecutor, WorkspaceManager, setup_logging


def create_demo_files(temp_dir: Path) -> tuple[list[dict], list[dict]]:
    """Create demo files and folders."""
    # Create a project structure
    project_dir = temp_dir / "demo_project"
    project_dir.mkdir()
    
    # Create some Python files
    (project_dir / "main.py").write_text("""
def analyze_repo(repo_path):
    '''Analyze a repository and generate summary.'''
    print(f"Analyzing {repo_path}")
    # Implementation would go here
    
if __name__ == "__main__":
    analyze_repo("./learn-repo")
""")
    
    (project_dir / "utils.py").write_text("""
import os
from pathlib import Path

def count_files_by_extension(directory):
    '''Count files by their extensions.'''
    extensions = {}
    for file_path in Path(directory).rglob("*"):
        if file_path.is_file():
            ext = file_path.suffix or "no_extension"
            extensions[ext] = extensions.get(ext, 0) + 1
    return extensions
""")
    
    # Create a data folder
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    (data_dir / "config.json").write_text(json.dumps({
        "analysis": {
            "include_readme": True,
            "max_file_size": 10000,
            "output_format": "markdown"
        }
    }, indent=2))
    
    # Create instructions
    instructions = temp_dir / "INSTRUCTIONS.md"
    instructions.write_text("""# Workspace Demo Instructions

This workspace contains:
1. A cloned repository in `learn-repo/`
2. Python analysis tools in `src/`
3. Configuration in `data/`

Your task:
- Explore the learn-repo directory
- Use the Python tools if helpful
- Create a summary of your findings
""")
    
    # Define mappings
    files = [
        {
            "name": "INSTRUCTIONS.md",
            "src_path": str(instructions),
            "dest_path": "."
        }
    ]
    
    folders = [
        {
            "name": "demo_project", 
            "src_path": str(project_dir),
            "dest_path": "src"
        },
        {
            "name": "data",
            "src_path": str(data_dir),
            "dest_path": "."
        }
    ]
    
    return files, folders


def print_workspace_tree(workspace_path: Path, max_depth: int = 3) -> None:
    """Print workspace directory tree."""
    def print_tree(path: Path, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return
            
        items = sorted(path.iterdir())
        for i, item in enumerate(items):
            if item.name.startswith('.') and item.name != '.workspace_metadata.json':
                continue
                
            is_last = i == len(items) - 1
            current = "└── " if is_last else "├── "
            print(f"{prefix}{current}{item.name}")
            
            if item.is_dir() and depth < max_depth:
                extension = "    " if is_last else "│   "
                print_tree(item, prefix + extension, depth + 1)
    
    print(f"\nWorkspace structure ({workspace_path.name}):")
    print_tree(workspace_path)


def main():
    """Main demo function."""
    setup_logging(level="INFO")
    
    print("=== Complete Workspace Demo ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create demo files
        files, folders = create_demo_files(temp_path)
        
        # Initialize managers
        workspace_manager = WorkspaceManager()
        shell_executor = ShellExecutor()
        
        # Define git repo
        repos = [{
            "github": "https://github.com/Polkm/learn",
            "dest_path": "learn-repo"
        }]
        
        try:
            # Step 1: Create workspace
            print("1. Creating workspace with all resources...")
            workspace_path = workspace_manager.create_workspace(
                "complete-demo",
                files=files,
                folders=folders,
                repos=repos
            )
            
            print(f"   ✓ Workspace created: {workspace_path}")
            
            # Step 2: Show initial state
            print("\n2. Initial workspace contents:")
            print_workspace_tree(workspace_path)
            
            # Count files
            file_count = sum(1 for _ in workspace_path.rglob("*") if _.is_file())
            print(f"\n   Total files: {file_count}")
            
            # Step 3: Run agent
            print("\n3. Running agent to analyze workspace...")
            
            # First, have agent explore
            response1 = shell_executor.execute_claude(
                prompt="""Please explore this workspace:
1. Read the INSTRUCTIONS.md file
2. List what's in the learn-repo directory
3. Check what Python tools are available in src/
4. Look at the configuration in data/config.json

Summarize what you find.""",
                working_dir=workspace_path
            )
            
            print("\n   Agent's exploration:")
            print("   " + "-" * 60)
            for line in response1["result"][:400].split('\n'):
                print(f"   {line}")
            if len(response1["result"]) > 400:
                print("   ...")
            print("   " + "-" * 60)
            
            # Step 4: Ask agent to create a summary file
            print("\n4. Asking agent to document findings...")
            
            response2 = shell_executor.execute_claude(
                prompt="""Based on your exploration, please create a file called 
'workspace-analysis.md' that documents:
1. The structure of this workspace
2. What the learn-repo contains (language, purpose)
3. Available tools and configuration
4. Your overall assessment

Just describe what you would write - don't actually create the file.""",
                session_id=response1["session_id"],
                working_dir=workspace_path
            )
            
            print("\n   Agent's planned summary:")
            print("   " + "-" * 60)
            for line in response2["result"][:400].split('\n'):
                print(f"   {line}")
            if len(response2["result"]) > 400:
                print("   ...")
            print("   " + "-" * 60)
            
            # Step 5: Final state
            print("\n5. Final workspace state:")
            print_workspace_tree(workspace_path)
            
            # Show session cost
            total_cost = response1.get("total_cost_usd", 0) + response2.get("total_cost_usd", 0)
            print(f"\n6. Session cost: ${total_cost:.4f}")
            
            # Step 6: Demonstrate file creation (programmatically)
            print("\n7. Creating summary file programmatically...")
            summary_content = f"""# Workspace Analysis

Generated after agent exploration.

## Workspace Structure
- **learn-repo/**: Cloned GitHub repository
- **src/**: Python analysis tools
- **data/**: Configuration files
- **INSTRUCTIONS.md**: Task instructions

## Learn Repository
Based on agent analysis: {response1["result"][:100]}...

## Session Information
- Session ID: {response2["session_id"]}
- Total cost: ${total_cost:.4f}
"""
            
            summary_path = workspace_path / "workspace-analysis.md"
            workspace_manager.file_handler.write_file(
                workspace_path,
                "workspace-analysis.md",
                summary_content
            )
            
            print(f"   ✓ Created: {summary_path}")
            print(f"   File size: {summary_path.stat().st_size} bytes")
            
            # Cleanup
            print("\n8. Cleaning up...")
            if workspace_manager.cleanup_workspace("complete-demo"):
                print("   ✓ Workspace cleaned up successfully!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()