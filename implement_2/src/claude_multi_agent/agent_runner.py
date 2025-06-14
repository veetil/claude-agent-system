"""Agent runner with input/output file management."""

import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .shell import ShellExecutor
from .workspace import WorkspaceManager

logger = logging.getLogger(__name__)


@dataclass
class AgentRunResult:
    """Result from running an agent."""
    success: bool
    session_id: str
    text_output: str
    cost_usd: float
    files_created: List[Dict[str, str]]  # List of {name, src_path, dest_path}
    folders_created: List[Dict[str, str]]  # List of {name, src_path, dest_path}
    workspace_path: Path
    error: Optional[str] = None


def run_agent_with_io(
    prompt: str,
    input_files: Optional[List[Dict[str, str]]] = None,
    input_folders: Optional[List[Dict[str, str]]] = None,
    input_repos: Optional[List[Dict[str, Any]]] = None,
    output_files: Optional[List[Dict[str, str]]] = None,
    output_folders: Optional[List[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
    workspace_id: Optional[str] = None,
    cleanup: bool = True,
    timeout: int = 300,
    debug: bool = False
) -> AgentRunResult:
    """Run an agent with specified inputs and capture outputs.
    
    Args:
        prompt: The main prompt for the agent
        input_files: Files to copy TO the agent workspace
            Format: [{"name": "file.txt", "src_path": "/host/path/file.txt", "dest_path": "agent/path"}]
        input_folders: Folders to copy TO the agent workspace
            Format: [{"name": "folder", "src_path": "/host/path/folder", "dest_path": "agent/path"}]
        input_repos: Git repositories to clone
            Format: [{"github": "https://github.com/...", "dest_path": "path"}]
        output_files: Files to copy FROM the agent workspace to host
            Format: [{"name": "result.txt", "src_path": "agent/path/result.txt", "dest_path": "/host/path"}]
        output_folders: Folders to copy FROM the agent workspace to host
            Format: [{"name": "output", "src_path": "agent/path/output", "dest_path": "/host/path"}]
        system_prompt: Optional system prompt to prepend
        workspace_id: Optional workspace ID (auto-generated if not provided)
        cleanup: Whether to cleanup workspace after execution
        timeout: Timeout in seconds for agent execution
        debug: Enable Claude CLI debug mode
        
    Returns:
        AgentRunResult with success status, output text, and file/folder creation info
        
    Example:
        result = run_agent_with_io(
            prompt="Analyze the repository and create a summary",
            input_repos=[{"github": "https://github.com/user/repo", "dest_path": "repo"}],
            output_files=[{"name": "summary.md", "src_path": "summary.md", "dest_path": "./outputs/"}]
        )
    """
    workspace_manager = WorkspaceManager()
    shell_executor = ShellExecutor()
    
    # Generate workspace ID if not provided
    if not workspace_id:
        import uuid
        workspace_id = f"agent_{uuid.uuid4().hex[:8]}"
    
    files_created = []
    folders_created = []
    workspace_path = None
    
    try:
        # Create workspace with inputs
        logger.info(f"Creating workspace '{workspace_id}' with inputs")
        workspace_path = workspace_manager.create_workspace(
            workspace_id,
            files=input_files,
            folders=input_folders,
            repos=input_repos,
            persistent=not cleanup
        )
        
        # Prepare the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
        # Run the agent
        logger.info(f"Running agent in workspace: {workspace_path}")
        response = shell_executor.execute_claude(
            prompt=full_prompt,
            working_dir=workspace_path,
            timeout=timeout,
            debug=debug
        )
        
        # Extract outputs
        logger.info("Extracting outputs from workspace")
        
        # Copy output files
        if output_files:
            for file_spec in output_files:
                src_in_workspace = workspace_path / file_spec["src_path"]
                dest_on_host = Path(file_spec["dest_path"])
                
                if src_in_workspace.exists():
                    # Ensure destination directory exists
                    if dest_on_host.is_dir():
                        dest_file = dest_on_host / file_spec["name"]
                    else:
                        dest_file = dest_on_host
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(src_in_workspace, dest_file)
                    logger.info(f"Copied file: {src_in_workspace} -> {dest_file}")
                    
                    files_created.append({
                        "name": file_spec["name"],
                        "src_path": str(src_in_workspace.relative_to(workspace_path)),
                        "dest_path": str(dest_file)
                    })
                else:
                    logger.warning(f"Expected output file not found: {src_in_workspace}")
                    
        # Copy output folders
        if output_folders:
            for folder_spec in output_folders:
                src_in_workspace = workspace_path / folder_spec["src_path"]
                dest_on_host = Path(folder_spec["dest_path"])
                
                if src_in_workspace.exists() and src_in_workspace.is_dir():
                    # Ensure destination exists
                    if dest_on_host.exists() and dest_on_host.is_dir():
                        dest_folder = dest_on_host / folder_spec["name"]
                    else:
                        dest_folder = dest_on_host
                        
                    # Copy the folder
                    if dest_folder.exists():
                        shutil.rmtree(dest_folder)
                    shutil.copytree(src_in_workspace, dest_folder)
                    logger.info(f"Copied folder: {src_in_workspace} -> {dest_folder}")
                    
                    folders_created.append({
                        "name": folder_spec["name"],
                        "src_path": str(src_in_workspace.relative_to(workspace_path)),
                        "dest_path": str(dest_folder)
                    })
                else:
                    logger.warning(f"Expected output folder not found: {src_in_workspace}")
        
        # Create result
        result = AgentRunResult(
            success=True,
            session_id=response["session_id"],
            text_output=response["result"],
            cost_usd=response.get("total_cost_usd", 0.0),
            files_created=files_created,
            folders_created=folders_created,
            workspace_path=workspace_path
        )
        
        # Cleanup if requested
        if cleanup:
            logger.info(f"Cleaning up workspace: {workspace_id}")
            workspace_manager.cleanup_workspace(workspace_id)
            
        return result
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        
        # Cleanup on error if requested
        if cleanup and workspace_path:
            try:
                workspace_manager.cleanup_workspace(workspace_id)
            except:
                pass
                
        return AgentRunResult(
            success=False,
            session_id="",
            text_output="",
            cost_usd=0.0,
            files_created=[],
            folders_created=[],
            workspace_path=workspace_path or Path("/tmp"),
            error=str(e)
        )


def verify_outputs(result: AgentRunResult, expected_files: List[str], expected_folders: List[str]) -> Tuple[bool, List[str]]:
    """Verify that expected outputs were created.
    
    Args:
        result: The AgentRunResult from run_agent_with_io
        expected_files: List of file names that should have been created
        expected_folders: List of folder names that should have been created
        
    Returns:
        Tuple of (all_found: bool, missing: List[str])
    """
    missing = []
    
    # Check files
    created_file_names = {f["name"] for f in result.files_created}
    for expected_file in expected_files:
        if expected_file not in created_file_names:
            missing.append(f"file: {expected_file}")
            
    # Check folders
    created_folder_names = {f["name"] for f in result.folders_created}
    for expected_folder in expected_folders:
        if expected_folder not in created_folder_names:
            missing.append(f"folder: {expected_folder}")
            
    # Also verify files exist at destination
    for file_info in result.files_created:
        dest_path = Path(file_info["dest_path"])
        if not dest_path.exists():
            missing.append(f"file at destination: {dest_path}")
            
    # Verify folders exist at destination
    for folder_info in result.folders_created:
        dest_path = Path(folder_info["dest_path"])
        if not dest_path.exists():
            missing.append(f"folder at destination: {dest_path}")
            
    all_found = len(missing) == 0
    return all_found, missing