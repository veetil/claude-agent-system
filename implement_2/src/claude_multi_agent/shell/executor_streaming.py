"""
Experimental streaming version of ShellExecutor for real-time debug output.
This is a copy of executor.py with modifications to support streaming output.
"""

import os
import json
import shlex
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..utils.retry import retry_with_backoff
from ..utils.logging import get_logger
from ..core.exceptions import ExecutionError, SessionError

logger = get_logger(__name__)


class StreamingShellExecutor:
    """Execute Claude CLI commands via shell with streaming output support"""
    
    def __init__(self, shell: Optional[str] = None):
        """Initialize the executor
        
        Args:
            shell: Shell to use (defaults to $SHELL or /bin/bash)
        """
        self.shell = shell or os.environ.get("SHELL", "/bin/bash")
        logger.info(f"Initialized StreamingShellExecutor with shell: {self.shell}")
        self._validate_shell()
    
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
    def execute_claude_streaming(
        self, 
        prompt: str, 
        session_id: Optional[str] = None,
        working_dir: Optional[Path] = None,
        timeout: int = 300,
        debug: bool = False
    ) -> Dict[str, Any]:
        """Execute Claude CLI command with streaming output support
        
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
            # Execute via interactive shell with Popen for streaming
            proc = subprocess.Popen(
                [self.shell, "-ic", shell_cmd],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Collect output while streaming
            stdout_lines = []
            stderr_lines = []
            
            # Read stdout in real-time
            if debug:
                logger.info("=== Claude CLI Streaming Debug Output ===")
            
            # Use communicate with timeout
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                
                # Log output as it was received
                if debug and stdout:
                    for line in stdout.splitlines():
                        if line.strip():
                            logger.info(f"[STDOUT] {line}")
                            stdout_lines.append(line)
                else:
                    stdout_lines = stdout.splitlines() if stdout else []
                
                if debug and stderr:
                    for line in stderr.splitlines():
                        if line.strip():
                            logger.info(f"[STDERR] {line}")
                            stderr_lines.append(line)
                else:
                    stderr_lines = stderr.splitlines() if stderr else []
                    
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise ExecutionError(f"Command timed out after {timeout}s")
            
            if debug:
                logger.info("=== End Streaming Debug Output ===")
            
            # Join lines back together
            full_stdout = '\n'.join(stdout_lines)
            full_stderr = '\n'.join(stderr_lines)
            
            if proc.returncode != 0:
                self._handle_error(full_stderr, session_id)
                
            # Parse response
            clean_output = self._sanitize_output(full_stdout)
            response = json.loads(clean_output)
            
            logger.debug(f"Response: {response}")
            return response
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Raw output: {full_stdout if 'full_stdout' in locals() else 'N/A'}")
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
    
    # Keep the original method as fallback
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
        
        This is the original non-streaming version kept as fallback.
        """
        # Use streaming version if debug is enabled
        if debug:
            return self.execute_claude_streaming(
                prompt, session_id, working_dir, timeout, debug
            )
        
        # Otherwise use original implementation
        args = self._build_claude_command(prompt, session_id, debug=debug)
        shell_cmd = " ".join(shlex.quote(arg) for arg in args)
        
        cwd = str(working_dir) if working_dir else os.getcwd()
        logger.debug(f"Executing: {shell_cmd} in {cwd}")
        
        try:
            proc = subprocess.run(
                [self.shell, "-ic", shell_cmd],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if proc.returncode != 0:
                self._handle_error(proc.stderr, session_id)
                
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
            raise
        except ExecutionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ExecutionError(f"Command execution failed: {e}")