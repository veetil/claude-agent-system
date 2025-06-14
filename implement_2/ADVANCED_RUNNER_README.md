# Claude Agent Advanced Runner

The `run_agent_advanced.py` script provides a production-ready interface for running Claude agents with complex input/output requirements defined in JSON configuration files.

## Features

- **JSON Task Configuration**: Define all agent parameters in a structured JSON file
- **Multiple Input Types**: Support for files, folders, and Git repositories
- **Output Management**: Automatic extraction and verification of expected outputs
- **Session Management**: Workspace persistence and session continuation support
- **Comprehensive Logging**: Detailed execution logs and progress tracking
- **Cost Tracking**: Monitor API usage costs for each execution
- **Automatic Verification**: Validates all expected outputs were created

## Usage

```bash
# Basic usage
python run_agent_advanced.py --task task.json

# With verbose output
python run_agent_advanced.py --task task.json --verbose

# Skip confirmation prompt
python run_agent_advanced.py --task task.json --no-confirm

# Override output directory
python run_agent_advanced.py --task task.json --output-dir ./results

# Set logging level
python run_agent_advanced.py --task task.json --log-level DEBUG

# Enable Claude CLI debug mode
python run_agent_advanced.py --task task.json --debug
```

## Task JSON Format

```json
{
  "prompt": "Main instruction for the agent",
  "system_prompt": "Optional system prompt to set agent behavior",
  "input_files": [
    {
      "name": "config.json",
      "src_path": "/path/to/source/file",
      "dest_path": "relative/path/in/workspace"
    }
  ],
  "input_folders": [
    {
      "name": "templates",
      "src_path": "/path/to/source/folder",
      "dest_path": "relative/path/in/workspace"
    }
  ],
  "input_repos": [
    {
      "github": "https://github.com/owner/repo",
      "dest_path": "relative/path/in/workspace"
    }
  ],
  "output_files": [
    {
      "name": "result.txt",
      "src_path": "relative/path/in/workspace",
      "dest_path": "/path/to/save/on/host"
    }
  ],
  "output_folders": [
    {
      "name": "processed",
      "src_path": "relative/path/in/workspace",
      "dest_path": "/path/to/save/on/host"
    }
  ],
  "workspace_id": "optional_persistent_workspace_name",
  "timeout": 300,
  "cleanup": true,
  "debug": false
}
```

## Field Descriptions

### Required Fields
- `prompt`: The main instruction/task for the agent

### Optional Fields
- `system_prompt`: System-level instructions to guide agent behavior
- `input_files`: List of files to copy into the agent's workspace
- `input_folders`: List of folders to copy into the workspace
- `input_repos`: Git repositories to clone (supports `github` or `git` URLs)
- `output_files`: Expected files to extract after execution
- `output_folders`: Expected folders to extract after execution
- `workspace_id`: Persistent workspace ID (auto-generated if not provided)
- `timeout`: Maximum execution time in seconds (default: 300)
- `cleanup`: Whether to clean up workspace after execution (default: true)
- `debug`: Enable Claude CLI debug mode for verbose output (default: false)

## Examples

### 1. Simple File Generation
```json
{
  "prompt": "Create a Python script that calculates prime numbers",
  "output_files": [
    {
      "name": "primes.py",
      "src_path": "primes.py",
      "dest_path": "./outputs"
    }
  ]
}
```

### 2. Repository Analysis
```json
{
  "prompt": "Analyze the repository and create documentation",
  "input_repos": [
    {
      "github": "https://github.com/user/project",
      "dest_path": "repo"
    }
  ],
  "output_files": [
    {
      "name": "analysis.md",
      "src_path": "analysis.md",
      "dest_path": "./reports"
    }
  ]
}
```

### 3. Data Processing Pipeline
```json
{
  "prompt": "Process CSV files and generate visualizations",
  "input_folders": [
    {
      "name": "raw_data",
      "src_path": "./data/raw",
      "dest_path": "input"
    }
  ],
  "output_folders": [
    {
      "name": "processed",
      "src_path": "output",
      "dest_path": "./data/processed"
    }
  ],
  "output_files": [
    {
      "name": "report.pdf",
      "src_path": "report.pdf",
      "dest_path": "./reports"
    }
  ]
}
```

## Output Verification

The script automatically verifies that all expected outputs were created:

1. **File Verification**: Checks each expected file exists at the destination
2. **Folder Verification**: Validates folders exist and reports file count
3. **Exit Codes**: Returns 0 on success, 1 on failure

## Session Continuation

When `cleanup: false` is set, the workspace is preserved and you can continue the session:

```python
from claude_multi_agent import ShellExecutor
from pathlib import Path

executor = ShellExecutor()
response = executor.execute_claude(
    prompt="What files did you create?",
    session_id="<session_id_from_output>",
    working_dir=Path("<workspace_path_from_output>")
)
```

## Best Practices

1. **Be Specific**: Provide clear, detailed prompts for better results
2. **Use System Prompts**: Guide agent behavior with system-level instructions
3. **Verify Paths**: Ensure all input file/folder paths exist before running
4. **Monitor Costs**: Check the cost output to track API usage
5. **Preserve Workspaces**: Use `cleanup: false` for debugging or session continuation
6. **Set Appropriate Timeouts**: Adjust timeout based on task complexity

## Error Handling

The script provides detailed error messages for common issues:

- Missing or invalid task JSON file
- Missing required fields in configuration
- Input files/folders not found
- Agent execution failures
- Output verification failures

## Advanced Features

### Override Output Directory
```bash
python run_agent_advanced.py --task task.json --output-dir ./today_results
```

This overrides all output destinations in the task JSON to use the specified directory.

### Debug Mode
```bash
# Enable both application logging and Claude CLI debug output
python run_agent_advanced.py --task task.json --log-level DEBUG --debug --verbose
```

This provides:
- Maximum application logging detail (--log-level DEBUG)
- Claude CLI debug output including stderr/stdout (--debug)
- Full agent responses in the output (--verbose)

You can also enable debug mode in the task JSON:
```json
{
  "prompt": "...",
  "debug": true,
  // other fields...
}
```

When debug mode is enabled, you'll see:
- Claude CLI command being executed
- Full stdout and stderr from Claude CLI
- Detailed execution logs
- Any error messages or warnings from the CLI

### Batch Processing
Create multiple task JSON files and process them:
```bash
for task in tasks/*.json; do
    python run_agent_advanced.py --task "$task" --no-confirm
done
```