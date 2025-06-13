# Claude CLI Actual Behavior Documentation

## Verified Working Commands

### 1. Basic Print Mode with JSON
```bash
echo "What is 2+2?" | claude --print --output-format json
```

**Output Structure:**
```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 3995,
  "duration_api_ms": 6157,
  "num_turns": 1,
  "result": "4",
  "session_id": "cb19781e-6740-41dd-a154-fd097875a253",
  "total_cost_usd": 0.27519645,
  "usage": {
    "input_tokens": 3,
    "cache_creation_input_tokens": 14631,
    "cache_read_input_tokens": 0,
    "output_tokens": 7,
    "server_tool_use": {
      "web_search_requests": 0
    }
  }
}
```

### 2. Key Differences from Expected Behavior

1. **Session Management**: 
   - Sessions are tracked via `session_id` in the response
   - Use `-r <session_id>` to resume a specific session
   - Use `-c` to continue the most recent session

2. **Input Method**:
   - Claude CLI reads from stdin when using `--print`
   - Prompts should be piped in or provided via stdin

3. **Output Format**:
   - JSON output includes metadata (cost, usage, duration)
   - The actual response is in the `result` field

4. **System Prompts**:
   - No dedicated system prompt file option found
   - May need to embed in the initial message

## Updated Implementation Strategy

1. **Session Management**: 
   - Parse `session_id` from JSON responses
   - Store session IDs for each agent
   - Use `-r <session_id>` to continue conversations

2. **Process Spawning**:
   - Use stdin to provide prompts
   - Parse JSON output to extract results
   - Handle the metadata for monitoring

3. **Agent Specialization**:
   - Embed system prompts in initial messages
   - Use `--allowedTools` to control agent capabilities
   - Use `--add-dir` for workspace isolation

## Next Steps

1. Update the POC tests to use the correct CLI interface
2. Modify the ClaudeWrapper to handle stdin/stdout properly
3. Implement session ID tracking
4. Test concurrent execution with the actual CLI behavior