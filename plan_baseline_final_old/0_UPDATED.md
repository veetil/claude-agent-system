# Step 0: Feasibility Validation and POC (UPDATED with CLI Documentation)

## Objective
Validate that Claude CLI can be reliably spawned and controlled programmatically before committing to the full implementation.

## Key Insights from Claude CLI Documentation

### 1. SDK Print Mode (`-p` flag)
The CLI provides a non-interactive print mode specifically designed for programmatic usage:
- Use `claude -p "query"` for single-shot execution
- Supports JSON output format with `--output-format json`
- Streaming JSON available with `--output-format stream-json`
- Returns structured data including session IDs for conversation continuity

### 2. Session Management
Claude CLI supports sophisticated session management:
- `--continue` flag to continue most recent conversation
- `--resume <session-id>` to resume specific sessions
- Sessions maintain context across multiple interactions

### 3. System Prompt Customization
- `--system-prompt` to override default prompts (only with `-p`)
- `--append-system-prompt` to add to existing prompts
- Critical for agent specialization

### 4. Tool Permission Management
- `--allowedTools` and `--disallowedTools` for fine-grained control
- `--dangerously-skip-permissions` for automated environments
- MCP tools follow pattern: `mcp__<serverName>__<toolName>`

### 5. Resource and Turn Limits
- `--max-turns` to limit agent iterations
- Built-in timeout handling
- Verbose logging with `--verbose` for debugging

## Updated Validation Tests

### 0.1 CLI SDK Mode Test
```typescript
// poc/test-cli-sdk-mode.ts
import { spawn } from 'child_process';
import { v4 as uuidv4 } from 'uuid';

interface ClaudeResponse {
  type: 'result';
  subtype: 'success' | 'error_max_turns';
  cost_usd: number;
  duration_ms: number;
  duration_api_ms: number;
  is_error: boolean;
  num_turns: number;
  result?: string;
  session_id: string;
}

async function testSDKMode(): Promise<{
  success: boolean;
  sessionId: string;
  response: ClaudeResponse;
}> {
  return new Promise((resolve, reject) => {
    const claude = spawn('claude', [
      '-p',
      'Respond with exactly "CLAUDE_SDK_TEST_SUCCESS"',
      '--output-format', 'json',
      '--max-turns', '1'
    ], {
      env: {
        ...process.env,
        ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY
      }
    });

    let output = '';

    claude.stdout.on('data', (data) => {
      output += data.toString();
    });

    claude.on('close', (code) => {
      if (code === 0) {
        try {
          const response = JSON.parse(output) as ClaudeResponse;
          resolve({
            success: response.subtype === 'success',
            sessionId: response.session_id,
            response
          });
        } catch (e) {
          reject(new Error(`Failed to parse JSON: ${e.message}`));
        }
      } else {
        reject(new Error(`Claude exited with code ${code}`));
      }
    });

    claude.on('error', reject);
  });
}
```

### 0.2 Session Continuation Test
```typescript
// poc/test-session-continuation.ts
async function testSessionContinuation(): Promise<boolean> {
  // First command - establish context
  const firstResult = await runClaudeCommand([
    '-p',
    'Remember this number: 42. I will ask about it later.',
    '--output-format', 'json'
  ]);

  if (!firstResult.success) return false;

  const sessionId = firstResult.session_id;

  // Continue session with follow-up
  const secondResult = await runClaudeCommand([
    '-p',
    'What number did I ask you to remember?',
    '--resume', sessionId,
    '--output-format', 'json'
  ]);

  return secondResult.success && 
         secondResult.result.includes('42');
}
```

### 0.3 Custom System Prompt Test
```typescript
// poc/test-system-prompts.ts
async function testSystemPrompts(): Promise<boolean> {
  const customPrompt = 'You are a specialized test agent. Always prefix responses with "[TEST]".';
  
  const result = await runClaudeCommand([
    '-p',
    'Say hello',
    '--system-prompt', customPrompt,
    '--output-format', 'json'
  ]);

  return result.success && 
         result.result.startsWith('[TEST]');
}
```

### 0.4 Tool Permission Test
```typescript
// poc/test-tool-permissions.ts
async function testToolPermissions(): Promise<{
  withPermissions: boolean;
  withoutPermissions: boolean;
  skipPermissions: boolean;
}> {
  // Test with allowed tools
  const allowedResult = await runClaudeCommand([
    '-p',
    'List files in current directory',
    '--allowedTools', 'Bash(ls:*)',
    '--output-format', 'json'
  ]);

  // Test with disallowed tools
  const disallowedResult = await runClaudeCommand([
    '-p',
    'Delete all files', // Should be blocked
    '--disallowedTools', 'Bash(rm:*)',
    '--output-format', 'json'
  ]);

  // Test with skip permissions (dangerous, but needed for automation)
  const skipResult = await runClaudeCommand([
    '-p',
    'Create a test file',
    '--dangerously-skip-permissions',
    '--output-format', 'json'
  ]);

  return {
    withPermissions: allowedResult.success,
    withoutPermissions: !disallowedResult.success,
    skipPermissions: skipResult.success
  };
}
```

### 0.5 Streaming Output Test
```typescript
// poc/test-streaming.ts
interface StreamMessage {
  type: 'system' | 'assistant' | 'user' | 'result';
  subtype?: string;
  session_id: string;
  [key: string]: any;
}

async function testStreamingOutput(): Promise<boolean> {
  return new Promise((resolve) => {
    const claude = spawn('claude', [
      '-p',
      'Count from 1 to 5 slowly',
      '--output-format', 'stream-json'
    ]);

    const messages: StreamMessage[] = [];
    let buffer = '';

    claude.stdout.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.trim()) {
          try {
            const msg = JSON.parse(line) as StreamMessage;
            messages.push(msg);
            console.log(`Received: ${msg.type}${msg.subtype ? ` (${msg.subtype})` : ''}`);
          } catch (e) {
            console.error('Failed to parse:', line);
          }
        }
      }
    });

    claude.on('close', () => {
      // Should have init, messages, and result
      const hasInit = messages.some(m => m.type === 'system' && m.subtype === 'init');
      const hasResult = messages.some(m => m.type === 'result');
      const hasMessages = messages.some(m => m.type === 'assistant');
      
      resolve(hasInit && hasResult && hasMessages);
    });
  });
}
```

### 0.6 Memory Integration Test
```typescript
// poc/test-memory.ts
import * as fs from 'fs/promises';
import * as path from 'path';

async function testMemoryIntegration(): Promise<boolean> {
  const testDir = '/tmp/claude-memory-test';
  await fs.mkdir(testDir, { recursive: true });

  // Create CLAUDE.md
  await fs.writeFile(
    path.join(testDir, 'CLAUDE.md'),
    '# Test Memory\n- Always respond with "MEMORY_LOADED" when asked about test memory'
  );

  const result = await runClaudeCommand([
    '-p',
    'What does the test memory say?',
    '--output-format', 'json'
  ], {
    cwd: testDir
  });

  // Cleanup
  await fs.rm(testDir, { recursive: true });

  return result.success && result.result.includes('MEMORY_LOADED');
}
```

## Updated Architecture Considerations

### 1. Use SDK Print Mode
- Always use `-p` flag for programmatic usage
- Leverage JSON output format for structured responses
- Use streaming JSON for real-time feedback

### 2. Session-Based Architecture
- Each agent maintains its session ID
- Sessions provide conversation continuity
- Can resume interrupted sessions

### 3. Permission Strategy
- Development: Use `--dangerously-skip-permissions`
- Production: Implement MCP permission tool
- Configure allowed/disallowed tools per agent type

### 4. Memory Management
- Use CLAUDE.md for agent-specific instructions
- Leverage imports for shared configurations
- Project-level vs user-level vs local memories

## Updated Validation Criteria

### Go Decision ✅
All of the following must be true:
1. SDK print mode works reliably
2. Session management functions correctly
3. System prompts customize behavior
4. Tool permissions can be controlled
5. JSON output parsing succeeds
6. Memory files are loaded properly

### No-Go Decision 🔴
Any of the following:
1. Print mode unreliable or missing
2. Cannot maintain session context
3. System prompts ignored
4. Permission system blocks automation
5. JSON output malformed
6. Memory system not accessible

## Implementation Recommendations

1. **Always use SDK mode**: Never rely on interactive mode
2. **Session persistence**: Store session IDs for continuity
3. **Structured output**: Always use JSON format
4. **Permission automation**: Use `--dangerously-skip-permissions` with caution
5. **Memory architecture**: Design clear memory hierarchy
6. **Error handling**: Parse JSON errors properly

## Updated POC Timeline

### Day 1
1. Validate SDK print mode
2. Test session management
3. Verify JSON output formats
4. Test permission controls

### Day 2
1. Test memory integration
2. Validate streaming output
3. Stress test with concurrent sessions
4. Document all findings

## Success Metrics
- SDK mode reliability >99%
- Session continuity maintained
- JSON parsing 100% successful
- Permission system controllable
- Memory loading verified

This updated plan incorporates the specific Claude CLI features documented, providing a more robust foundation for the multi-agent system.