#!/usr/bin/env python3
"""
Simple test to verify Claude can create files with --dangerously-skip-permissions
"""

import tempfile
from pathlib import Path

from claude_multi_agent import ShellExecutor, WorkspaceManager


def main():
    print("=== File Creation Test ===\n")
    
    # Create workspace
    workspace_manager = WorkspaceManager()
    shell_executor = ShellExecutor()
    
    workspace_path = workspace_manager.create_workspace("file-test")
    print(f"Workspace: {workspace_path}")
    
    # Simple file creation test
    print("\n1. Testing file creation...")
    response = shell_executor.execute_claude(
        prompt='Create a file called "test.txt" with the content "Hello from Claude!"',
        working_dir=workspace_path,
        timeout=30
    )
    
    print(f"Response: {response['result'][:200]}...")
    
    # Check if file was created
    test_file = workspace_path / "test.txt"
    if test_file.exists():
        print(f"\n✅ SUCCESS! File created: {test_file}")
        print(f"Content: {test_file.read_text()}")
    else:
        print(f"\n❌ FAILED! File not created")
        
    # Test creating a more complex file
    print("\n2. Testing markdown file creation...")
    response2 = shell_executor.execute_claude(
        prompt='Create a file called "summary.md" with a markdown list of 3 programming languages',
        session_id=response["session_id"],
        working_dir=workspace_path,
        timeout=30
    )
    
    summary_file = workspace_path / "summary.md"
    if summary_file.exists():
        print(f"\n✅ SUCCESS! Markdown file created")
        print(f"Content:\n{summary_file.read_text()}")
    else:
        print(f"\n❌ FAILED! Markdown file not created")
        
    # List all files
    print("\nAll files in workspace:")
    for f in workspace_path.rglob("*"):
        if f.is_file():
            print(f"  - {f.relative_to(workspace_path)}")
            
    # Cleanup
    workspace_manager.cleanup_workspace("file-test")
    print("\n✓ Cleaned up")


if __name__ == "__main__":
    main()