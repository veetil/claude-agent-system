#!/usr/bin/env python3
"""
Example of using WorkspaceManager to create isolated environments for agents.

This demonstrates:
1. Creating a workspace with files and folders
2. Running Claude in that workspace
3. Cleaning up the workspace
"""

import tempfile
from pathlib import Path

from claude_multi_agent import ShellExecutor, WorkspaceManager


def create_sample_project(base_dir: Path) -> tuple[list[dict], list[dict]]:
    """Create a sample project structure for demonstration."""
    # Create a sample Python project
    project_dir = base_dir / "sample_app"
    project_dir.mkdir()
    
    # Create main.py
    (project_dir / "main.py").write_text('''
def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
''')
    
    # Create config directory
    config_dir = project_dir / "config"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text('{"debug": true, "port": 8080}')
    
    # Create data directory
    data_dir = base_dir / "sample_data"
    data_dir.mkdir()
    (data_dir / "users.txt").write_text("Alice\nBob\nCharlie")
    (data_dir / "scores.csv").write_text("name,score\nAlice,95\nBob,87\nCharlie,92")
    
    # Define file mappings
    files = [
        {
            "name": "main.py",
            "src_path": str(project_dir / "main.py"),
            "dest_path": "src"
        },
        {
            "name": "settings.json",
            "src_path": str(config_dir / "settings.json"),
            "dest_path": "config"
        }
    ]
    
    # Define folder mappings
    folders = [
        {
            "name": "data",
            "src_path": str(data_dir),
            "dest_path": "resources"
        }
    ]
    
    return files, folders


def main():
    """Main example function."""
    print("=== Workspace Manager Example ===\n")
    
    # Create temporary directory for our sample files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample project
        files, folders = create_sample_project(temp_path)
        
        # Initialize managers
        workspace_manager = WorkspaceManager()
        shell_executor = ShellExecutor()
        
        # Create workspace with files and folders
        print("1. Creating workspace with files and folders...")
        workspace_path = workspace_manager.create_workspace(
            "agent-workspace",
            files=files,
            folders=folders
        )
        
        print(f"   Workspace created at: {workspace_path}")
        
        # List workspace contents
        print("\n2. Workspace contents:")
        for item in workspace_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(workspace_path)
                print(f"   - {rel_path}")
        
        # Use Claude in the workspace
        print("\n3. Running Claude in the workspace...")
        response = shell_executor.execute_claude(
            prompt="List all files in this workspace and briefly describe what each does based on its name or content.",
            working_dir=workspace_path
        )
        
        print(f"\nClaude's response:")
        print("-" * 50)
        print(response["result"])
        print("-" * 50)
        
        # Continue the session
        print("\n4. Continuing the session...")
        response2 = shell_executor.execute_claude(
            prompt="What's in the settings.json file?",
            session_id=response["session_id"],
            working_dir=workspace_path
        )
        
        print(f"\nClaude's follow-up response:")
        print("-" * 50)
        print(response2["result"])
        print("-" * 50)
        
        # Show workspace info
        print("\n5. Active workspaces:")
        workspaces = workspace_manager.list_workspaces()
        for ws_id, info in workspaces.items():
            print(f"   - {ws_id}: {info['path']}")
            if info.get('resources'):
                print(f"     Files: {len(info['resources']['files'])}")
                print(f"     Folders: {len(info['resources']['folders'])}")
        
        # Clean up
        print("\n6. Cleaning up workspace...")
        cleaned = workspace_manager.cleanup_workspace("agent-workspace")
        if cleaned:
            print("   Workspace cleaned up successfully!")
        else:
            print("   Failed to clean up workspace")


if __name__ == "__main__":
    main()