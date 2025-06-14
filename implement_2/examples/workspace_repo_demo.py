#!/usr/bin/env python3
"""
Simplified demo: Create workspace with repo, run agent, check for output file.

This demonstrates the complete workflow in a more concise way.
"""

import tempfile
from pathlib import Path

from claude_multi_agent import ShellExecutor, WorkspaceManager


def main():
    """Main demo function."""
    print("=== Workspace Repository Demo ===\n")
    
    # Create a simple instruction file
    with tempfile.TemporaryDirectory() as temp_dir:
        instruction_file = Path(temp_dir) / "instructions.txt"
        instruction_file.write_text(
            "Analyze the learn-repo directory and create repo-summary.md"
        )
        
        # Setup
        workspace_manager = WorkspaceManager()
        shell_executor = ShellExecutor()
        
        # Create workspace
        print("1. Creating workspace...")
        workspace_path = workspace_manager.create_workspace(
            "demo",
            files=[{
                "name": "instructions.txt",
                "src_path": str(instruction_file),
                "dest_path": "."
            }],
            repos=[{
                "github": "https://github.com/Polkm/learn",
                "dest_path": "learn-repo"
            }]
        )
        
        print(f"   Workspace: {workspace_path}")
        
        # Check initial contents
        print("\n2. Initial contents:")
        for item in sorted(workspace_path.rglob("*")):
            if item.is_file() and not str(item).startswith(str(workspace_path / ".git")):
                print(f"   - {item.relative_to(workspace_path)}")
        
        summary_path = workspace_path / "repo-summary.md"
        print(f"\n   repo-summary.md exists: {summary_path.exists()}")
        
        # Run agent
        print("\n3. Running agent...")
        prompt = """Analyze the learn-repo directory and create a summary file called repo-summary.md.
The summary should describe what the repository is about, list the main files, and explain what 
programming language and purpose it serves. Keep it concise but informative."""
        
        try:
            response = shell_executor.execute_claude(
                prompt=prompt,
                working_dir=workspace_path,
                timeout=60  # 60 second timeout
            )
            
            print("   Agent completed!")
            
            # Check if file was created
            print("\n4. After agent work:")
            if summary_path.exists():
                print(f"   ✅ repo-summary.md created! ({summary_path.stat().st_size} bytes)")
                print("\n   Preview:")
                print("   " + "-" * 50)
                preview = summary_path.read_text()[:300] + "..."
                print("   " + preview.replace("\n", "\n   "))
            else:
                print("   ❌ repo-summary.md not found")
                
            # List all files again
            print("\n5. Final contents:")
            for item in sorted(workspace_path.rglob("*")):
                if item.is_file() and not str(item).startswith(str(workspace_path / ".git")):
                    print(f"   - {item.relative_to(workspace_path)}")
                    
        except Exception as e:
            print(f"   Error: {e}")
            
        # Cleanup
        if workspace_manager.cleanup_workspace("demo"):
            print("\n6. Workspace cleaned up!")
        else:
            print(f"\n6. Workspace at: {workspace_path}")


if __name__ == "__main__":
    main()