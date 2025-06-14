#!/usr/bin/env python3
"""
Test the agent I/O functionality with a real example.
"""

import tempfile
from pathlib import Path

from claude_multi_agent import run_agent_with_io, verify_outputs, setup_logging


def test_repo_analysis():
    """Test analyzing a repo and getting outputs."""
    setup_logging(level="INFO")
    
    print("=== Testing Agent I/O with Repository Analysis ===\n")
    
    # Create output directory
    output_dir = Path("./test_outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Create a task file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Repository Analysis Task

Please analyze the learn repository and create two files:

1. **repo-overview.md** - A comprehensive overview of the repository including:
   - What the project does
   - Main components
   - How to use it

2. **file-list.txt** - A simple text file listing all Lua files in the repository, one per line
""")
        task_file = Path(f.name)
    
    try:
        # Run the agent
        print("Running agent to analyze repository...")
        result = run_agent_with_io(
            prompt="""Read the task file and analyze the learn-repo directory.
Create the two requested files: repo-overview.md and file-list.txt""",
            
            input_files=[
                {
                    "name": "task.md",
                    "src_path": str(task_file),
                    "dest_path": "."
                }
            ],
            
            input_repos=[
                {
                    "github": "https://github.com/Polkm/learn",
                    "dest_path": "learn-repo"
                }
            ],
            
            output_files=[
                {
                    "name": "repo-overview.md",
                    "src_path": "repo-overview.md",
                    "dest_path": str(output_dir)
                },
                {
                    "name": "file-list.txt",
                    "src_path": "file-list.txt",
                    "dest_path": str(output_dir)
                }
            ],
            
            workspace_id="test_analysis",
            cleanup=False,  # Keep for debugging
            timeout=60
        )
        
        # Show results
        print(f"\nSuccess: {result.success}")
        print(f"Cost: ${result.cost_usd:.4f}")
        print(f"Session ID: {result.session_id}")
        
        if result.error:
            print(f"Error: {result.error}")
            return
            
        # Agent output
        print(f"\nAgent said:")
        print("-" * 60)
        print(result.text_output[:400])
        if len(result.text_output) > 400:
            print("...")
        print("-" * 60)
        
        # Check what was created
        print(f"\nFiles created: {len(result.files_created)}")
        for file_info in result.files_created:
            dest_path = Path(file_info['dest_path'])
            if dest_path.exists():
                size = dest_path.stat().st_size
                print(f"✅ {file_info['name']} ({size} bytes) -> {dest_path}")
            else:
                print(f"❌ {file_info['name']} -> File not found at {dest_path}")
                
        # Verify outputs
        expected_files = ["repo-overview.md", "file-list.txt"]
        all_found, missing = verify_outputs(result, expected_files, [])
        
        print(f"\nVerification: {'PASSED' if all_found else 'FAILED'}")
        if missing:
            print("Missing items:")
            for item in missing:
                print(f"  - {item}")
                
        # Show content samples
        if result.files_created:
            print("\n=== Output Samples ===")
            
            # Show overview
            overview_path = output_dir / "repo-overview.md"
            if overview_path.exists():
                print("\nrepo-overview.md (first 300 chars):")
                print(overview_path.read_text()[:300] + "...")
                
            # Show file list
            file_list_path = output_dir / "file-list.txt"
            if file_list_path.exists():
                print("\nfile-list.txt:")
                print(file_list_path.read_text())
                
        # Workspace info
        print(f"\nWorkspace: {result.workspace_path}")
        print("To inspect: cd " + str(result.workspace_path))
        print("To cleanup: rm -rf " + str(result.workspace_path))
        
    finally:
        # Cleanup task file
        task_file.unlink()


def test_file_generation():
    """Test generating multiple files."""
    print("\n\n=== Testing Multiple File Generation ===\n")
    
    output_dir = Path("./test_outputs")
    output_dir.mkdir(exist_ok=True)
    
    result = run_agent_with_io(
        prompt="""Create three files:
1. config.json - A JSON configuration file with at least 3 settings
2. readme.txt - A short readme explaining the config
3. example.py - A Python script that loads and uses the config""",
        
        output_files=[
            {
                "name": "config.json",
                "src_path": "config.json",
                "dest_path": str(output_dir)
            },
            {
                "name": "readme.txt",
                "src_path": "readme.txt",
                "dest_path": str(output_dir)
            },
            {
                "name": "example.py",
                "src_path": "example.py",
                "dest_path": str(output_dir)
            }
        ],
        
        cleanup=True,
        timeout=30
    )
    
    print(f"Success: {result.success}")
    print(f"Files created: {len(result.files_created)}")
    
    for file_info in result.files_created:
        print(f"  ✅ {file_info['name']}")
        
    # Verify
    expected = ["config.json", "readme.txt", "example.py"]
    all_found, _ = verify_outputs(result, expected, [])
    print(f"\nAll files created: {'YES' if all_found else 'NO'}")


if __name__ == "__main__":
    # Test 1: Repository analysis with outputs
    test_repo_analysis()
    
    # Test 2: Multiple file generation
    test_file_generation()