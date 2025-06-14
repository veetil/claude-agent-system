#!/usr/bin/env python3
"""
Production example of running an agent with input/output file management.

This demonstrates:
1. Providing input files and repositories to an agent
2. Running the agent with a specific task
3. Extracting output files from the agent's workspace
4. Verifying all expected outputs were created
"""

import tempfile
from pathlib import Path
import json

from claude_multi_agent.agent_runner import run_agent_with_io, verify_outputs
from claude_multi_agent import setup_logging


def main():
    """Run a production agent example."""
    setup_logging(level="INFO")
    
    print("=== Production Agent Example ===\n")
    
    # Create a temporary directory for our outputs
    output_dir = Path("./agent_outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Prepare some input files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create an analysis configuration
        config_file = temp_path / "analysis_config.json"
        config_file.write_text(json.dumps({
            "analysis_type": "repository",
            "output_format": "markdown",
            "include_metrics": True,
            "max_file_size": 10000
        }, indent=2))
        
        # Create task instructions
        instructions_file = temp_path / "TASK.md"
        instructions_file.write_text("""# Analysis Task

Please analyze the Python repository in the 'repo' directory and create the following outputs:

1. **summary.md** - A comprehensive summary of the repository
2. **metrics.json** - JSON file with code metrics (file count, total lines, etc.)
3. **recommendations.md** - Suggestions for improvements

Focus on:
- Code organization and structure
- Documentation quality
- Testing coverage
- Potential improvements
""")
        
        # Define inputs
        input_files = [
            {
                "name": "analysis_config.json",
                "src_path": str(config_file),
                "dest_path": "config"
            },
            {
                "name": "TASK.md",
                "src_path": str(instructions_file),
                "dest_path": "."
            }
        ]
        
        input_repos = [
            {
                "github": "https://github.com/Polkm/learn",
                "dest_path": "repo"
            }
        ]
        
        # Define expected outputs
        output_files = [
            {
                "name": "summary.md",
                "src_path": "summary.md",
                "dest_path": str(output_dir)
            },
            {
                "name": "metrics.json",
                "src_path": "metrics.json", 
                "dest_path": str(output_dir)
            },
            {
                "name": "recommendations.md",
                "src_path": "recommendations.md",
                "dest_path": str(output_dir)
            }
        ]
        
        # System prompt
        system_prompt = """You are a code analysis expert. You have access to a repository and configuration files.
Your task is to analyze the code and create the requested output files. Make sure to create all three files:
summary.md, metrics.json, and recommendations.md."""
        
        # Main prompt
        main_prompt = """Read the TASK.md file for your instructions, then analyze the repository in the 'repo' directory.
Use the configuration from config/analysis_config.json to guide your analysis.

Create all the requested output files in the workspace root."""
        
        print("Running agent with:")
        print(f"- Input files: {len(input_files)}")
        print(f"- Input repos: {len(input_repos)}")
        print(f"- Expected outputs: {len(output_files)}")
        print()
        
        # Run the agent
        print("Executing agent...")
        result = run_agent_with_io(
            prompt=main_prompt,
            input_files=input_files,
            input_repos=input_repos,
            output_files=output_files,
            system_prompt=system_prompt,
            workspace_id="analysis_agent",
            cleanup=False,  # Keep workspace for inspection
            timeout=120
        )
        
        # Check results
        print("\n=== Results ===")
        print(f"Success: {result.success}")
        print(f"Session ID: {result.session_id}")
        print(f"Cost: ${result.cost_usd:.4f}")
        print(f"Workspace: {result.workspace_path}")
        
        if result.error:
            print(f"Error: {result.error}")
            return
            
        # Show agent's text output
        print("\nAgent output (first 500 chars):")
        print("-" * 60)
        print(result.text_output[:500])
        if len(result.text_output) > 500:
            print("...")
        print("-" * 60)
        
        # Show created files
        print(f"\nFiles created: {len(result.files_created)}")
        for file_info in result.files_created:
            print(f"  - {file_info['name']}")
            print(f"    From: {file_info['src_path']}")
            print(f"    To: {file_info['dest_path']}")
            
            # Show file size
            dest_file = Path(file_info['dest_path'])
            if dest_file.exists():
                size = dest_file.stat().st_size
                print(f"    Size: {size} bytes")
                
        # Verify all expected outputs
        print("\n=== Verification ===")
        expected_files = ["summary.md", "metrics.json", "recommendations.md"]
        all_found, missing = verify_outputs(result, expected_files, [])
        
        if all_found:
            print("✅ All expected files were created!")
        else:
            print("❌ Missing outputs:")
            for item in missing:
                print(f"  - {item}")
                
        # Show content previews
        if result.files_created:
            print("\n=== Content Previews ===")
            
            for file_info in result.files_created:
                dest_path = Path(file_info['dest_path'])
                if dest_path.exists():
                    print(f"\n{file_info['name']}:")
                    print("-" * 40)
                    
                    content = dest_path.read_text()
                    if file_info['name'].endswith('.json'):
                        # Pretty print JSON
                        try:
                            data = json.loads(content)
                            print(json.dumps(data, indent=2)[:300])
                        except:
                            print(content[:300])
                    else:
                        # Show first 300 chars
                        print(content[:300])
                        
                    if len(content) > 300:
                        print("...")
                        
        # Cleanup instructions
        print(f"\n=== Cleanup ===")
        print(f"Workspace preserved at: {result.workspace_path}")
        print("To inspect the workspace:")
        print(f"  cd {result.workspace_path}")
        print(f"  ls -la")
        print("\nTo clean up:")
        print(f"  rm -rf {result.workspace_path}")
        print(f"\nOutput files saved to: {output_dir}/")
        
        # Example of continuing the session
        print("\n=== Session Continuation Example ===")
        print(f"To continue this session, use session_id: {result.session_id}")
        print(f"Example:")
        print(f'  response = executor.execute_claude(')
        print(f'      prompt="What other analyses could we add?",')
        print(f'      session_id="{result.session_id}",')
        print(f'      working_dir=Path("{result.workspace_path}")')
        print(f'  )')


if __name__ == "__main__":
    main()