#!/usr/bin/env python3
"""
Quick test of agent I/O functionality.
"""

from pathlib import Path
from claude_multi_agent import run_agent_with_io


def main():
    print("=== Quick Agent I/O Test ===\n")
    
    # Simple test: create a file and get it back
    output_dir = Path("./quick_test_output")
    output_dir.mkdir(exist_ok=True)
    
    print("Test 1: Simple file creation")
    result = run_agent_with_io(
        prompt="Create a file called test.md with the text 'Hello from the agent!'",
        output_files=[{
            "name": "test.md",
            "src_path": "test.md",
            "dest_path": str(output_dir)
        }],
        timeout=30,
        cleanup=True
    )
    
    if result.success:
        print(f"✅ Success! Cost: ${result.cost_usd:.4f}")
        if result.files_created:
            output_file = Path(result.files_created[0]['dest_path'])
            print(f"Created: {output_file}")
            print(f"Content: {output_file.read_text()}")
    else:
        print(f"❌ Failed: {result.error}")
        
    # Test 2: Create multiple files
    print("\n\nTest 2: Multiple file creation")
    result = run_agent_with_io(
        prompt="""Create two files:
1. info.json with {"name": "test", "version": "1.0"}
2. notes.txt with "This is a test note"
""",
        output_files=[
            {
                "name": "info.json",
                "src_path": "info.json",
                "dest_path": str(output_dir)
            },
            {
                "name": "notes.txt",
                "src_path": "notes.txt", 
                "dest_path": str(output_dir)
            }
        ],
        timeout=30,
        cleanup=True
    )
    
    print(f"Success: {result.success}")
    print(f"Files created: {len(result.files_created)}")
    for f in result.files_created:
        print(f"  - {f['name']}")
        
    # Test 3: With input file
    print("\n\nTest 3: Process input file")
    
    # Create input
    input_file = output_dir / "input.txt"
    input_file.write_text("Process this text and make it uppercase")
    
    result = run_agent_with_io(
        prompt="Read input.txt and create output.txt with the content in uppercase",
        input_files=[{
            "name": "input.txt",
            "src_path": str(input_file),
            "dest_path": "."
        }],
        output_files=[{
            "name": "output.txt",
            "src_path": "output.txt",
            "dest_path": str(output_dir)
        }],
        timeout=30,
        cleanup=True
    )
    
    if result.success and result.files_created:
        output_file = Path(result.files_created[0]['dest_path'])
        print(f"✅ Created: {output_file}")
        print(f"Content: {output_file.read_text()}")
        
    print(f"\n✅ All tests complete! Check {output_dir}/ for outputs")


if __name__ == "__main__":
    main()