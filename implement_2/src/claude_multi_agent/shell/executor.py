"""Shell Executor for Claude CLI Integration"""

import os
import subprocess
import json
import shlex
import asyncio
from typing import Dict, Optional, Any, List
from pathlib import Path
import logging

from ..core.exceptions import ExecutionError, SessionError, ValidationError
from ..utils.json_parser import RobustJSONParser
from ..utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class ShellExecutor:
    """Executes Claude CLI commands via interactive shell
    
    This is the critical component that properly invokes Claude CLI through
    an interactive shell to ensure aliases and functions are loaded.
    """
    
    def __init__(self, shell: Optional[str] = None):
        """Initialize shell executor
        
        Args:
            shell: Path to shell executable. Defaults to $SHELL or /bin/bash
        """
        self.shell = shell or os.environ.get("SHELL", "/bin/bash")
        self._validate_shell()
        logger.info(f"Initialized ShellExecutor with shell: {self.shell}")
        
    def _validate_shell(self):
        """Ensure shell is available and executable"""
        if not Path(self.shell).exists():
            raise ExecutionError(f"Shell not found: {self.shell}")
    
    def _build_claude_command(
        self, 
        prompt: str, 
        session_id: Optional[str] = None,
        output_format: str = "json",
        debug: bool = False
    ) -> List[str]:
        """Build Claude CLI command arguments
        
        Args:
            prompt: The prompt to send to Claude
            session_id: Optional session ID to resume
            output_format: Output format (default: json)
            debug: Enable Claude CLI debug mode
            
        Returns:
            List of command arguments
        """
        args = [
            "claude", 
            "--dangerously-skip-permissions",  # Enable autonomous operation
            "-p", prompt, 
            "--output-format", output_format
        ]
        
        if debug:
            args.append("--debug")
            
        if session_id:
            args.extend(["-r", session_id])
            
        return args
    
    def _sanitize_output(self, output: str) -> str:
        """Remove shell artifacts and find JSON content
        
        Args:
            output: Raw shell output
            
        Returns:
            Clean JSON string
            
        Raises:
            ExecutionError: If no valid JSON found
        """
        lines = output.strip().split('\n')
        
        # Find first line that starts with '{'
        json_start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start_idx = i
                break
                
        if json_start_idx is None:
            raise ExecutionError("No JSON found in output")
            
        # Extract JSON lines using brace counting
        json_lines = []
        brace_count = 0
        
        for line in lines[json_start_idx:]:
            json_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                break
                
        return '\n'.join(json_lines)
    
    def _handle_error(self, stderr: str, session_id: Optional[str]):
        """Parse and handle specific errors from Claude CLI
        
        Args:
            stderr: Error output from command
            session_id: Session ID if resuming
            
        Raises:
            SessionError: If session not found
            ExecutionError: For other errors
        """
        error_lower = stderr.lower()
        
        if "no conversation found with session id" in error_lower:
            raise SessionError(f"Session not found: {session_id}")
        elif "not a valid uuid" in error_lower:
            # Handle invalid UUID format as session error
            raise SessionError(f"Invalid session ID format: {session_id}")
        elif "rate limit" in error_lower:
            raise ExecutionError("Rate limit exceeded")
        else:
            raise ExecutionError(f"Claude CLI error: {stderr}")
    
    @retry_with_backoff(max_attempts=3, exceptions=(ExecutionError,))
    def execute_claude(
        self, 
        prompt: str, 
        session_id: Optional[str] = None,
        working_dir: Optional[Path] = None,
        timeout: int = 300,
        debug: bool = False
    ) -> Dict[str, Any]:
        """Execute Claude CLI command and return parsed response
        
        Args:
            prompt: The prompt to send to Claude
            session_id: Optional session ID to resume
            working_dir: Working directory for command execution
            timeout: Command timeout in seconds
            debug: Enable Claude CLI debug mode
            
        Returns:
            Parsed JSON response with session_id and result
            
        Raises:
            ExecutionError: If command fails or timeout
            SessionError: If session not found
        """
        # Build command
        args = self._build_claude_command(prompt, session_id, debug=debug)
        shell_cmd = " ".join(shlex.quote(arg) for arg in args)
        
        # Set working directory
        cwd = str(working_dir) if working_dir else os.getcwd()
        
        logger.debug(f"Executing: {shell_cmd} in {cwd}")
        
        try:
            # Execute via interactive shell - THIS IS CRITICAL!
            # The -ic flags ensure shell loads aliases/functions
            proc = subprocess.run(
                [self.shell, "-ic", shell_cmd],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Log debug output if enabled
            if debug:
                logger.info("=== Claude CLI Debug Output ===")
                if proc.stderr:
                    logger.info(f"STDERR:\n{proc.stderr}")
                logger.info(f"STDOUT:\n{proc.stdout}")
                logger.info("=== End Debug Output ===")
            
            if proc.returncode != 0:
                self._handle_error(proc.stderr, session_id)
                
            # Parse response
            clean_output = self._sanitize_output(proc.stdout)
            response = json.loads(clean_output)
            
            logger.debug(f"Response: {response}")
            return response
            
        except subprocess.TimeoutExpired:
            raise ExecutionError(f"Command timed out after {timeout}s")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Raw output: {proc.stdout if 'proc' in locals() else 'N/A'}")
            raise ExecutionError(f"Failed to parse Claude response: {e}")
        except SessionError:
            # Re-raise session errors as-is
            raise
        except ExecutionError:
            # Re-raise execution errors as-is  
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ExecutionError(f"Command execution failed: {e}")
    
    async def execute_claude_async(
        self, 
        prompt: str, 
        session_id: Optional[str] = None,
        working_dir: Optional[Path] = None,
        timeout: int = 300,
        debug: bool = False
    ) -> Dict[str, Any]:
        """Async version of execute_claude
        
        Args:
            prompt: The prompt to send to Claude
            session_id: Optional session ID to resume
            working_dir: Working directory for command execution
            timeout: Command timeout in seconds
            debug: Enable Claude CLI debug mode
            
        Returns:
            Parsed JSON response with session_id and result
        """
        return await asyncio.to_thread(
            self.execute_claude,
            prompt,
            session_id,
            working_dir,
            timeout,
            debug
        )