# Claude Code SDK Issues and Limitations

## Summary
This document outlines the issues discovered during POC validation of Claude Code SDK for building a multi-agent system.

## Critical Issues

### 1. Session Persistence Problem
**Issue**: Session IDs from `--print` mode cannot be resumed with `-r` flag
- **Symptom**: "No conversation found with session ID" error when trying to resume
- **Impact**: Cannot maintain conversation context across separate CLI invocations
- **Test Evidence**: 
  ```bash
  claude -p "My name is Alice" --output-format json
  # Returns session_id: "abc123"
  
  claude -p "What is my name?" --output-format json -r abc123
  # Error: No conversation found with session ID: abc123
  ```

### 2. Python SDK Code Generation Failures
**Issue**: Code generation requests often return errors or incomplete responses
- **Symptom**: "unhandled errors in a TaskGroup" exceptions
- **Impact**: Only 20% test success rate for code generation tasks
- **Test Evidence**: Basic functionality test failed, concurrent agents had 80% failure rate

### 3. Multi-turn Conversation Limitations
**Issue**: Multi-turn conversations don't maintain context properly
- **Symptom**: Later turns don't build on previous responses
- **Impact**: Cannot create complex, iterative solutions
- **Test Evidence**: Calculator class example only showed basic structure, didn't add methods or error handling

### 4. JSON Parsing Errors in Python SDK
**Issue**: CLIJSONDecodeError when processing responses
- **Symptom**: "Extra data: line 2 column 1" JSON decode errors
- **Impact**: Intermittent failures in message processing
- **Test Evidence**: Multiple TaskGroup exceptions during testing

## Moderate Issues

### 5. No Session ID Tracking in Python SDK
**Issue**: Python SDK doesn't expose session IDs for conversation continuation
- **Symptom**: No `session_id` attribute in response messages
- **Impact**: Must use `continue_conversation` flag, limiting flexibility
- **Test Evidence**: Had to modify ClaudeCodeAgent to use boolean flag instead of session IDs

### 6. Tool Use Response Parsing
**Issue**: Responses containing tool use (file writes) aren't easily extractable as text
- **Symptom**: Assistant messages contain ToolUseBlock objects instead of text
- **Impact**: Complex parsing required to extract actual content
- **Test Evidence**: Had to check for TextBlock within content blocks

### 7. Concurrent Execution Reliability
**Issue**: Concurrent agents have inconsistent success rates
- **Symptom**: Same prompts succeed/fail randomly when run concurrently
- **Impact**: Unpredictable behavior in multi-agent scenarios
- **Test Evidence**: 1/5 success rate in concurrent test, varying each run

## Minor Issues

### 8. Output Format Inconsistency
**Issue**: Different output structure between CLI and Python SDK
- **Symptom**: CLI returns flat JSON, Python SDK returns nested message objects
- **Impact**: Need different parsing logic for each SDK

### 9. System Prompt Limitations
**Issue**: System prompts must be embedded in first message for CLI
- **Symptom**: No `--system-prompt` flag in print mode
- **Impact**: Less clean separation of concerns

### 10. Cost Tracking Differences
**Issue**: Cost information format differs between SDKs
- **Symptom**: CLI has `total_cost_usd`, Python SDK doesn't expose costs directly
- **Impact**: Harder to track usage costs in Python SDK

## Root Causes (Research Findings)

### 1. Session Persistence is By Design
**Finding**: Print/headless mode (`-p` flag) intentionally does NOT persist sessions between invocations
- This is an architectural decision for CI/CD and automation use cases
- Sessions only persist in interactive mode for up to 48 hours
- The `-r` flag works only for interactive sessions, not print mode sessions

### 2. JSON Parsing Errors - NDJSON Format
**Finding**: Claude Code SDK streams responses in NDJSON (newline-delimited JSON) format
- Multiple JSON objects separated by newlines
- Standard JSON parser expects single object
- Need to split by newlines and parse each line separately

### 3. TaskGroup Exception Handling
**Finding**: AsyncIO TaskGroup cancels all tasks when one fails
- Exceptions are collected into ExceptionGroup
- Need to wrap individual tasks with try-except
- Use `except*` syntax for handling ExceptionGroups

### 4. Permission and Tool Use Issues
**Finding**: Code generation failures often due to:
- Missing npm global permissions
- SDK permission_mode not configured
- Working directory not writable
- Tool use responses parsed differently than text responses

## Solutions

### Solution 1: Custom Session Management
```python
# Since SDK doesn't persist sessions, implement our own
class SessionManager:
    def __init__(self):
        self.conversations = {}
    
    def save_context(self, agent_id, prompt, response):
        if agent_id not in self.conversations:
            self.conversations[agent_id] = []
        self.conversations[agent_id].append({
            'prompt': prompt,
            'response': response
        })
    
    def get_context(self, agent_id):
        return self.conversations.get(agent_id, [])
```

### Solution 2: NDJSON Parser
```python
def parse_ndjson(text):
    results = []
    for line in text.strip().split('\n'):
        if line.strip():
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return results
```

### Solution 3: Safe Async Wrapper
```python
async def safe_query(prompt, options):
    try:
        messages = []
        async for message in query(prompt=prompt, options=options):
            messages.append(message)
        return messages
    except CLIJSONDecodeError as e:
        # Handle NDJSON format
        return parse_ndjson(str(e))
    except Exception as e:
        return None
```

### Solution 4: Proper SDK Configuration
```python
options = ClaudeCodeOptions(
    max_turns=3,
    system_prompt="Your role here",
    permission_mode="acceptEdits",  # Auto-accept file operations
    allowed_tools=["Read", "Write"],
    cwd=Path.cwd()  # Set working directory
)
```

## Final Solution: Use Claude's Built-in Session System

### Key Discovery
Sessions work perfectly with Claude CLI:
1. Sessions are tied to the folder where CLI is launched
2. Each `-r` creates a new session file but maintains full conversation history
3. Simply update the session ID with each interaction
4. Claude manages all conversation context internally

### Why This is THE Solution
- We CANNOT directly input message history to Claude
- There's no API or parameter to inject conversation context
- Claude's session system is the ONLY way to maintain conversation history
- External state management is unnecessary and inferior

### Simple Implementation
```python
class ClaudeAgent:
    def __init__(self, agent_id, working_dir):
        self.working_dir = Path(working_dir)  # Critical: consistent folder
        self.current_session_id = None
        
    async def ask(self, prompt):
        cmd = ['claude', '-p', prompt, '--output-format', 'json']
        
        if self.current_session_id:
            cmd.extend(['-r', self.current_session_id])
            
        result = subprocess.run(cmd, cwd=self.working_dir)
        response = json.loads(result.stdout)
        
        # Update for next call
        self.current_session_id = response['session_id']
        return response
```

### Best Practices for Multi-Agent System
1. **Use Claude CLI**: It's the only way to maintain conversation history
2. **Consistent Folders**: Each agent runs from its own dedicated folder
3. **Track Session IDs**: Update after each interaction
4. **Let Claude Manage History**: Don't try to manage conversation externally
5. **System Prompts**: Include in first message only