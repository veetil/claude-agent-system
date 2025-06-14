#!/usr/bin/env python3
"""
Advanced agent runner that reads task configuration from JSON file.

Usage:
    python run_agent_advanced.py --task task.json
    python run_agent_advanced.py --task task.json --verbose
    python run_agent_advanced.py --task task.json --output-dir ./results
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from claude_multi_agent import run_agent_with_io, verify_outputs, setup_logging
from claude_multi_agent.agent_runner import AgentRunResult


def load_task_config(task_file: Path) -> Dict[str, Any]:
    """Load and validate task configuration from JSON file."""
    if not task_file.exists():
        raise FileNotFoundError(f"Task file not found: {task_file}")
    
    try:
        with open(task_file, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in task file: {e}")
    
    # Validate required fields
    required_fields = ['prompt']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    # Set defaults
    defaults = {
        'input_files': [],
        'input_folders': [],
        'input_repos': [],
        'output_files': [],
        'output_folders': [],
        'system_prompt': None,
        'workspace_id': None,
        'cleanup': True,
        'timeout': 300,
        'debug': False,
        'realtime_debug': False,
        'enable_mcp': False,
        'mcp_config_path': None,
        'mcp_env_file': None
    }
    
    for key, default_value in defaults.items():
        config.setdefault(key, default_value)
    
    return config


def print_task_summary(config: Dict[str, Any]) -> None:
    """Print a summary of the task configuration."""
    print("=" * 60)
    print("TASK CONFIGURATION")
    print("=" * 60)
    
    print(f"\nPrompt: {config['prompt'][:100]}..." if len(config['prompt']) > 100 else f"\nPrompt: {config['prompt']}")
    
    if config.get('system_prompt'):
        print(f"\nSystem Prompt: {config['system_prompt'][:100]}..." 
              if len(config['system_prompt']) > 100 else f"\nSystem Prompt: {config['system_prompt']}")
    
    print(f"\nWorkspace ID: {config.get('workspace_id', 'auto-generated')}")
    print(f"Timeout: {config['timeout']} seconds")
    print(f"Cleanup: {config['cleanup']}")
    print(f"Debug: {config.get('debug', False)}")
    print(f"MCP Enabled: {config.get('enable_mcp', False)}")
    
    # Input summary
    print("\nINPUTS:")
    print(f"  Files: {len(config['input_files'])}")
    for f in config['input_files']:
        print(f"    - {f['name']} -> {f['dest_path']}")
    
    print(f"  Folders: {len(config['input_folders'])}")
    for f in config['input_folders']:
        print(f"    - {f['name']} -> {f['dest_path']}")
    
    print(f"  Repositories: {len(config['input_repos'])}")
    for r in config['input_repos']:
        if 'github' in r:
            print(f"    - {r['github']} -> {r['dest_path']}")
        elif 'git' in r:
            print(f"    - {r['git']} -> {r['dest_path']}")
    
    # Output summary
    print("\nEXPECTED OUTPUTS:")
    print(f"  Files: {len(config['output_files'])}")
    for f in config['output_files']:
        print(f"    - {f['name']} ({f['src_path']} -> {f['dest_path']})")
    
    print(f"  Folders: {len(config['output_folders'])}")
    for f in config['output_folders']:
        print(f"    - {f['name']} ({f['src_path']} -> {f['dest_path']})")
    
    print("=" * 60)


def print_execution_result(result: AgentRunResult, verbose: bool = False) -> None:
    """Print the execution result."""
    print("\n" + "=" * 60)
    print("EXECUTION RESULT")
    print("=" * 60)
    
    status = "✅ SUCCESS" if result.success else "❌ FAILED"
    print(f"\nStatus: {status}")
    print(f"Session ID: {result.session_id}")
    print(f"Cost: ${result.cost_usd:.4f}")
    print(f"Workspace: {result.workspace_path}")
    
    if result.error:
        print(f"\nError: {result.error}")
    
    if verbose and result.text_output:
        print("\nAgent Output:")
        print("-" * 40)
        print(result.text_output[:1000])
        if len(result.text_output) > 1000:
            print("... (truncated)")
        print("-" * 40)
    
    # Files created
    if result.files_created:
        print(f"\nFiles Created: {len(result.files_created)}")
        for f in result.files_created:
            dest_path = Path(f['dest_path'])
            if dest_path.exists():
                size = dest_path.stat().st_size
                print(f"  ✅ {f['name']} ({size} bytes)")
            else:
                print(f"  ❌ {f['name']} (not found)")
    
    # Folders created
    if result.folders_created:
        print(f"\nFolders Created: {len(result.folders_created)}")
        for f in result.folders_created:
            dest_path = Path(f['dest_path'])
            if dest_path.exists():
                # Count files in folder
                file_count = sum(1 for _ in dest_path.rglob('*') if _.is_file())
                print(f"  ✅ {f['name']} ({file_count} files)")
            else:
                print(f"  ❌ {f['name']} (not found)")


def verify_all_outputs(result: AgentRunResult, config: Dict[str, Any]) -> bool:
    """Verify all expected outputs were created."""
    print("\n" + "=" * 60)
    print("OUTPUT VERIFICATION")
    print("=" * 60)
    
    # Get expected file and folder names
    expected_files = [f['name'] for f in config['output_files']]
    expected_folders = [f['name'] for f in config['output_folders']]
    
    # Use the verify_outputs utility
    all_found, missing = verify_outputs(result, expected_files, expected_folders)
    
    if all_found:
        print("\n✅ All expected outputs were created successfully!")
    else:
        print("\n❌ Missing outputs:")
        for item in missing:
            print(f"  - {item}")
    
    # Additional verification: check actual file presence
    print("\nFile System Verification:")
    
    for file_config in config['output_files']:
        dest_path = Path(file_config['dest_path']) / file_config['name']
        if dest_path.exists():
            print(f"  ✅ {dest_path} (exists)")
        else:
            print(f"  ❌ {dest_path} (missing)")
    
    for folder_config in config['output_folders']:
        dest_path = Path(folder_config['dest_path']) / folder_config['name']
        if dest_path.exists() and dest_path.is_dir():
            print(f"  ✅ {dest_path} (exists)")
        else:
            print(f"  ❌ {dest_path} (missing)")
    
    return all_found


def main():
    parser = argparse.ArgumentParser(
        description="Run Claude agent with task configuration from JSON file"
    )
    parser.add_argument(
        "--task",
        type=Path,
        required=True,
        help="Path to task JSON file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output including agent responses"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Override output directory for all outputs"
    )
    parser.add_argument(
        "--log-level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help="Set logging level"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Display confirmation prompt"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable Claude CLI debug mode and show debug output"
    )
    parser.add_argument(
        "--realtime-debug",
        action="store_true",
        help="Enable real-time streaming debug output (shows logs as they happen)"
    )
    parser.add_argument(
        "--enable-mcp",
        action="store_true",
        help="Enable Model Context Protocol (MCP) support"
    )
    parser.add_argument(
        "--mcp-config",
        type=Path,
        help="Path to MCP configuration file (defaults to .roo/mcp.json)"
    )
    parser.add_argument(
        "--mcp-env",
        type=Path,
        help="Path to MCP environment file (defaults to .env.mcp)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Print header
    print("\n" + "=" * 60)
    print("CLAUDE AGENT ADVANCED RUNNER")
    print("=" * 60)
    print(f"Task File: {args.task}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load task configuration
        config = load_task_config(args.task)
        
        # Override output directory if specified
        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            # Update all output paths
            for output in config['output_files']:
                output['dest_path'] = str(args.output_dir)
            for output in config['output_folders']:
                output['dest_path'] = str(args.output_dir)
        
        # Print task summary
        print_task_summary(config)
        
        # Confirm before running
        if args.confirm:
            print("\nPress Enter to start execution (Ctrl+C to cancel)...")
            try:
                input()
            except KeyboardInterrupt:
                print("\nCancelled by user")
                return 1
        
        # Run the agent
        print("\nExecuting agent...")
        
        # Debug mode from either command line or JSON
        debug_enabled = args.debug or config.get('debug', False)
        realtime_debug = args.realtime_debug or config.get('realtime_debug', False)
        
        # MCP settings from command line or JSON
        enable_mcp = args.enable_mcp or config.get('enable_mcp', False)
        mcp_config_path = args.mcp_config or config.get('mcp_config_path')
        mcp_env_file = args.mcp_env or config.get('mcp_env_file')
        
        if realtime_debug:
            print("🔍 Real-time debug mode enabled - streaming output as it happens")
        elif debug_enabled:
            print("🔍 Debug mode enabled - Claude CLI will show verbose output")
        
        if enable_mcp:
            print("🔌 MCP support enabled")
            if mcp_config_path:
                print(f"   Config: {mcp_config_path}")
            if mcp_env_file:
                print(f"   Env file: {mcp_env_file}")
        
        result = run_agent_with_io(
            prompt=config['prompt'],
            input_files=config['input_files'],
            input_folders=config['input_folders'],
            input_repos=config['input_repos'],
            output_files=config['output_files'],
            output_folders=config['output_folders'],
            system_prompt=config['system_prompt'],
            workspace_id=config['workspace_id'],
            cleanup=config['cleanup'],
            timeout=config['timeout'],
            debug=debug_enabled,
            realtime_debug=realtime_debug,
            enable_mcp=enable_mcp,
            mcp_config_path=mcp_config_path,
            mcp_env_file=mcp_env_file
        )
        
        # Print result
        print_execution_result(result, args.verbose)
        
        # Verify outputs
        all_outputs_found = verify_all_outputs(result, config)
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Cost: ${result.cost_usd:.4f}")
        print(f"Success: {result.success and all_outputs_found}")
        
        if not config['cleanup']:
            print(f"\nWorkspace preserved at: {result.workspace_path}")
            print("To clean up manually:")
            print(f"  rm -rf {result.workspace_path}")
        
        # Return appropriate exit code
        return 0 if result.success and all_outputs_found else 1
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())