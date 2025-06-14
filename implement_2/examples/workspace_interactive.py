#!/usr/bin/env python3
"""
Interactive workspace demo with step-by-step execution.
"""

from pathlib import Path
import time

from claude_multi_agent import ShellExecutor, WorkspaceManager, setup_logging


def show_files(workspace_path: Path, exclude_git: bool = True) -> None:
    """Show non-git files in the workspace."""
    print("\nCurrent files in workspace:")
    files = []
    for item in sorted(workspace_path.rglob("*")):
        if item.is_file():
            rel_path = item.relative_to(workspace_path)
            if exclude_git and ".git" in str(rel_path):
                continue
            files.append(rel_path)
    
    for f in files:
        size = (workspace_path / f).stat().st_size
        print(f"  - {f} ({size} bytes)")
    
    if not files:
        print("  (no files yet)")


def main():
    """Main interactive demo."""
    setup_logging(level="WARNING")  # Less verbose
    
    print("=== Interactive Workspace Demo ===\n")
    
    # Setup
    workspace_manager = WorkspaceManager()
    shell_executor = ShellExecutor()
    
    # Create workspace with repo
    print("Step 1: Creating workspace with Polkm/learn repository...")
    workspace_path = workspace_manager.create_workspace(
        "interactive-demo",
        repos=[{
            "github": "https://github.com/Polkm/learn",
            "dest_path": "learn-repo"
        }],
        persistent=True  # Keep for manual inspection
    )
    
    print(f"✓ Workspace created at: {workspace_path}")
    
    # Show initial state
    show_files(workspace_path)
    
    # First prompt - explore
    print("\nStep 2: Having agent explore the repository...")
    response1 = shell_executor.execute_claude(
        prompt="List the files in the learn-repo directory and tell me what type of project this is.",
        working_dir=workspace_path
    )
    
    print("\nAgent's exploration:")
    print("-" * 70)
    print(response1["result"][:500] + "..." if len(response1["result"]) > 500 else response1["result"])
    print("-" * 70)
    
    # Check if anything changed
    show_files(workspace_path)
    
    # Second prompt - create summary
    print("\nStep 3: Asking agent to create repo-summary.md...")
    response2 = shell_executor.execute_claude(
        prompt="""Based on your exploration of the learn-repo directory, please create a file called 
repo-summary.md in the current directory (not inside learn-repo). The summary should include:
- What the repository is about
- The main programming language used
- Key files and their purposes
- How to use the library (if clear from the README)

Make sure to save it as repo-summary.md in the workspace root.""",
        session_id=response1["session_id"],
        working_dir=workspace_path
    )
    
    print("\nAgent's response:")
    print("-" * 70) 
    print(response2["result"][:500] + "..." if len(response2["result"]) > 500 else response2["result"])
    print("-" * 70)
    
    # Final check
    print("\nStep 4: Checking final workspace state...")
    show_files(workspace_path)
    
    # Check if repo-summary.md exists
    summary_path = workspace_path / "repo-summary.md"
    if summary_path.exists():
        print(f"\n✅ SUCCESS: repo-summary.md was created!")
        print("\nContent preview:")
        print("=" * 70)
        content = summary_path.read_text()
        print(content[:800] + "\n..." if len(content) > 800 else content)
        print("=" * 70)
    else:
        print(f"\n❌ repo-summary.md was not created")
        
    # Show costs
    total_cost = response1.get("total_cost_usd", 0) + response2.get("total_cost_usd", 0)
    print(f"\nTotal cost: ${total_cost:.4f}")
    
    # Cleanup options
    print(f"\nWorkspace preserved at: {workspace_path}")
    print("\nTo manually inspect:")
    print(f"  cd {workspace_path}")
    print(f"  ls -la")
    print("\nTo clean up:")
    print(f"  rm -rf {workspace_path}")
    
    # Ask user
    cleanup = input("\nClean up workspace now? (y/n): ").lower().strip() == 'y'
    if cleanup:
        workspace_manager.cleanup_workspace("interactive-demo", force=True)
        print("✓ Workspace cleaned up!")
    else:
        print("✓ Workspace preserved for inspection")


if __name__ == "__main__":
    main()