"""
Real-time output version of ShellExecutor using threading.
This approach reads stdout/stderr in separate threads for real-time logging.
"""

import os
import json
import shlex
import subprocess
import threading
import queue
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..utils.retry import retry_with_backoff
from ..utils.logging import get_logger
from ..core.exceptions import ExecutionError, SessionError

logger = get_logger(__name__)


class RealtimeShellExecutor:
    """Execute Claude CLI commands with real-time output streaming"""
    
    def __init__(self, shell: Optional[str] = None, mcp_manager=None):
        """Initialize the executor
        
        Args:
            shell: Shell to use (defaults to $SHELL or /bin/bash)
            mcp_manager: Optional MCPManager instance for MCP support
        """
        self.shell = shell or os.environ.get("SHELL", "/bin/bash")
        self.mcp_manager = mcp_manager
        logger.info(f"Initialized RealtimeShellExecutor with shell: {self.shell}")
        if self.mcp_manager:
            logger.info("MCP support enabled")
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
        debug: bool = False,
        streaming: bool = False,
        enable_mcp: bool = True
    ) -> List[str]:
        """Build Claude CLI command arguments"""
        # Use stream-json format for real-time output
        if streaming:
            output_format = "stream-json"
        
        args = [
            "claude", 
            "--dangerously-skip-permissions",
            "-p", prompt, 
            "--output-format", output_format
        ]
        
        if debug:
            args.append("--debug")
            args.append("--verbose")  # Add verbose for more output
            
        if session_id:
            args.extend(["-r", session_id])
        
        # Add MCP support if available
        if enable_mcp and self.mcp_manager:
            args = self.mcp_manager.prepare_claude_command(args, enable_mcp=True)
            
        return args
    
    def _read_stream(self, stream, stream_name: str, output_queue: queue.Queue, debug: bool):
        """Read from a stream and log/queue output in real-time
        
        With stream-json format, we get actual streaming JSON objects.
        """
        try:
            current_json = []
            brace_count = 0
            in_json = False
            
            for line in iter(stream.readline, ''):
                if line:
                    line = line.rstrip()
                    output_queue.put(line)
                    
                    if debug and line.strip():
                        timestamp = time.strftime("%H:%M:%S")
                        
                        # Check if this is the start of a JSON object
                        if line.strip().startswith('{'):
                            in_json = True
                            current_json = [line]
                            brace_count = line.count('{') - line.count('}')
                            logger.info(f"[{timestamp}] [JSON-START] {line}")
                        elif in_json:
                            current_json.append(line)
                            brace_count += line.count('{') - line.count('}')
                            
                            if brace_count == 0:
                                # Complete JSON object
                                try:
                                    json_obj = json.loads('\n'.join(current_json))
                                    if 'type' in json_obj:
                                        if json_obj['type'] == 'text':
                                            logger.info(f"[{timestamp}] [CONTENT] {json_obj.get('text', '')[:100]}...")
                                        elif json_obj['type'] == 'tool_use':
                                            logger.info(f"[{timestamp}] [TOOL] {json_obj.get('name', 'unknown')}")
                                        elif json_obj['type'] == 'result':
                                            logger.info(f"[{timestamp}] [RESULT] Success={not json_obj.get('is_error', False)}")
                                        else:
                                            logger.info(f"[{timestamp}] [JSON-{json_obj['type'].upper()}]")
                                except:
                                    logger.info(f"[{timestamp}] [JSON-END]")
                                in_json = False
                                current_json = []
                        else:
                            # Regular output
                            logger.info(f"[{timestamp}] [{stream_name}] {line}")
        except Exception as e:
            logger.error(f"Error reading {stream_name}: {e}")
        finally:
            stream.close()
    
    def _extract_json_objects(self, output: str) -> List[str]:
        """Extract all JSON objects from output"""
        json_objects = []
        lines = output.strip().split('\n')
        current_json = []
        brace_count = 0
        in_json = False
        
        for line in lines:
            if line.strip().startswith('{'):
                in_json = True
                current_json = [line]
                brace_count = line.count('{') - line.count('}')
            elif in_json:
                current_json.append(line)
                brace_count += line.count('{') - line.count('}')
                
            if in_json and brace_count == 0:
                json_objects.append('\n'.join(current_json))
                current_json = []
                in_json = False
                
        return json_objects
    
    def _sanitize_output(self, output: str, streaming: bool = False) -> str:
        """Extract the final JSON from output"""
        if streaming:
            # With stream-json, we get multiple JSON objects
            # We need the last one for the final result
            json_objects = self._extract_json_objects(output)
            if not json_objects:
                raise ExecutionError("No JSON found in output")
            return json_objects[-1]  # Return the last JSON object
        else:
            # Standard JSON output - find and extract single JSON
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
        """Parse and handle specific errors from Claude CLI"""
        error_lower = stderr.lower()
        
        if "no conversation found with session id" in error_lower:
            raise SessionError(f"Session not found: {session_id}")
        elif "not a valid uuid" in error_lower:
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
        debug: bool = False,
        enable_mcp: bool = True
    ) -> Dict[str, Any]:
        """Execute Claude CLI command with real-time output
        
        Args:
            prompt: The prompt to send to Claude
            session_id: Optional session ID to resume
            working_dir: Working directory for command execution
            timeout: Command timeout in seconds
            debug: Enable Claude CLI debug mode and real-time output
            enable_mcp: Enable MCP support if mcp_manager is available
            
        Returns:
            Parsed JSON response with session_id and result
        """
        # Use streaming when debug is enabled for real-time output
        streaming = debug
        
        # Build command
        args = self._build_claude_command(prompt, session_id, debug=debug, streaming=streaming, enable_mcp=enable_mcp)
        shell_cmd = " ".join(shlex.quote(arg) for arg in args)
        
        # Set working directory
        cwd = str(working_dir) if working_dir else os.getcwd()
        
        # Prepare environment with MCP variables if available
        env = None
        if enable_mcp and self.mcp_manager:
            env = self.mcp_manager.get_mcp_env()
            # If MCP is available, setup workspace MCP files
            if working_dir:
                self.mcp_manager.setup_workspace_mcp(working_dir)
        
        logger.debug(f"Executing: {shell_cmd} in {cwd}")
        
        if debug:
            logger.info("=== Claude CLI Real-time Debug Output ===")
            logger.info(f"Command: {shell_cmd}")
            logger.info(f"Working dir: {cwd}")
            if env and self.mcp_manager:
                logger.info("MCP support: Enabled")
        
        try:
            # Execute via interactive shell
            proc = subprocess.Popen(
                [self.shell, "-ic", shell_cmd],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                env=env  # Use MCP environment if available
            )
            
            # Create queues for output
            stdout_queue = queue.Queue()
            stderr_queue = queue.Queue()
            
            # Start threads to read output
            stdout_thread = threading.Thread(
                target=self._read_stream,
                args=(proc.stdout, "STDOUT", stdout_queue, debug),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self._read_stream,
                args=(proc.stderr, "STDERR", stderr_queue, debug),
                daemon=True
            )
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for process with timeout
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise ExecutionError(f"Command timed out after {timeout}s")
            
            # Give threads a moment to finish reading
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            # Collect all output
            stdout_lines = []
            stderr_lines = []
            
            while not stdout_queue.empty():
                stdout_lines.append(stdout_queue.get_nowait())
            
            while not stderr_queue.empty():
                stderr_lines.append(stderr_queue.get_nowait())
            
            if debug:
                logger.info("=== End Real-time Debug Output ===")
                logger.info(f"Process exited with code: {proc.returncode}")
            
            # Join output
            full_stdout = '\n'.join(stdout_lines)
            full_stderr = '\n'.join(stderr_lines)
            
            if proc.returncode != 0:
                self._handle_error(full_stderr, session_id)
                
            # Parse response
            clean_output = self._sanitize_output(full_stdout, streaming=streaming)
            response = json.loads(clean_output)
            
            logger.debug(f"Response: {response}")
            return response
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            if 'full_stdout' in locals():
                logger.error(f"Raw output: {full_stdout}")
            raise ExecutionError(f"Failed to parse Claude response: {e}")
        except SessionError:
            raise
        except ExecutionError:
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
        debug: bool = False,
        enable_mcp: bool = True
    ) -> Dict[str, Any]:
        """Async version of execute_claude"""
        import asyncio
        return await asyncio.to_thread(
            self.execute_claude,
            prompt,
            session_id,
            working_dir,
            timeout,
            debug,
            enable_mcp
        )