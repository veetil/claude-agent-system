#!/usr/bin/env python3
"""
Simple example of agent with file I/O.

This shows the minimal code needed to:
1. Give an agent some input files
2. Run a task
3. Get output files back
"""

from pathlib import Path
from claude_multi_agent.agent_runner import run_agent_with_io


def analyze_code_files():
    """Simple example: analyze Python files and create a report."""
    
    # Prepare input files (assuming these exist)
    project_dir = Path("./my_project")  # Your project directory
    output_dir = Path("./analysis_results")
    output_dir.mkdir(exist_ok=True)
    
    # Run agent with inputs and expected outputs
    result = run_agent_with_io(
        prompt="""Analyze the Python files in the 'code' directory and create:
1. analysis_report.md - A detailed analysis of the code
2. issues.json - A JSON file listing any issues found""",
        
        input_folders=[
            {
                "name": "my_project",
                "src_path": str(project_dir),
                "dest_path": "code"
            }
        ],
        
        output_files=[
            {
                "name": "analysis_report.md",
                "src_path": "analysis_report.md",
                "dest_path": str(output_dir)
            },
            {
                "name": "issues.json",
                "src_path": "issues.json",
                "dest_path": str(output_dir)
            }
        ]
    )
    
    # Check results
    if result.success:
        print(f"✅ Analysis complete! Cost: ${result.cost_usd:.4f}")
        print(f"\nFiles created:")
        for file in result.files_created:
            print(f"  - {file['dest_path']}")
    else:
        print(f"❌ Failed: {result.error}")


def process_data_files():
    """Example: process CSV files and generate summary."""
    
    # Create some sample data
    data_dir = Path("./sample_data")
    data_dir.mkdir(exist_ok=True)
    
    # Create sample CSV
    (data_dir / "sales.csv").write_text("""date,product,amount
2024-01-01,Widget A,100
2024-01-02,Widget B,150
2024-01-03,Widget A,200""")
    
    # Run agent
    result = run_agent_with_io(
        prompt="Analyze the CSV files and create a summary report with insights",
        
        input_files=[
            {
                "name": "sales.csv",
                "src_path": str(data_dir / "sales.csv"),
                "dest_path": "data"
            }
        ],
        
        output_files=[
            {
                "name": "sales_summary.md",
                "src_path": "sales_summary.md",
                "dest_path": str(data_dir)
            }
        ],
        
        cleanup=True  # Auto cleanup workspace
    )
    
    if result.success:
        print("✅ Summary created!")
        summary_path = Path(result.files_created[0]['dest_path'])
        print(f"\nSummary content:\n{summary_path.read_text()}")


def generate_documentation():
    """Example: generate documentation from code."""
    
    result = run_agent_with_io(
        prompt="""Generate comprehensive documentation for the Learn repository.
Create a docs folder with:
- API.md - API documentation
- TUTORIAL.md - Getting started tutorial  
- EXAMPLES.md - Code examples""",
        
        input_repos=[
            {
                "github": "https://github.com/Polkm/learn",
                "dest_path": "learn"
            }
        ],
        
        output_folders=[
            {
                "name": "docs",
                "src_path": "docs",
                "dest_path": "./generated_docs"
            }
        ]
    )
    
    if result.success:
        print("✅ Documentation generated!")
        print(f"\nFiles in docs folder:")
        docs_dir = Path("./generated_docs")
        for file in docs_dir.rglob("*.md"):
            print(f"  - {file.name}")


# Minimal example
def minimal_example():
    """Bare minimum code to run an agent and get a file back."""
    
    result = run_agent_with_io(
        prompt="Create a file called hello.txt with a greeting",
        output_files=[{
            "name": "hello.txt",
            "src_path": "hello.txt", 
            "dest_path": "./"
        }]
    )
    
    if result.success:
        print(f"Created: {result.files_created[0]['dest_path']}")
        print(f"Content: {Path('hello.txt').read_text()}")


if __name__ == "__main__":
    print("=== Simple I/O Examples ===\n")
    
    print("1. Minimal example:")
    minimal_example()
    
    print("\n2. Process data example:")
    process_data_files()
    
    # Uncomment to run other examples:
    # print("\n3. Analyze code:")
    # analyze_code_files()
    
    # print("\n4. Generate documentation:")  
    # generate_documentation()