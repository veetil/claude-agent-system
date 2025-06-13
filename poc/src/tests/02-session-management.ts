import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import * as path from 'path';
import * as os from 'os';

/**
 * POC Test 02: Session Management
 * 
 * Validates Claude CLI session creation, continuation, and resumption
 * using --continue and --resume flags.
 */

interface TestResult {
  testName: string;
  passed: boolean;
  duration: number;
  output?: string;
  error?: string;
  details?: any;
}

interface ClaudeResponse {
  session_id?: string;
  result?: string;
  content?: string;
  response?: string;
  [key: string]: any;
}

async function executeClaudeCommand(args: string[]): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve, reject) => {
    let stdout = '';
    let stderr = '';
    
    const env = { ...process.env };
    delete env.ANTHROPIC_API_KEY;
    
    const claude = spawn('claude', args, { 
      env,
      shell: true 
    });
    
    claude.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    claude.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    claude.on('close', (code) => {
      resolve({ stdout, stderr, exitCode: code || 0 });
    });
    
    claude.on('error', (err) => {
      reject(err);
    });
    
    // Timeout after 30 seconds
    setTimeout(() => {
      claude.kill();
      reject(new Error('Claude process timed out'));
    }, 30000);
  });
}

function parseClaudeOutput(output: string): ClaudeResponse {
  // Try to find JSON in the output
  const jsonMatch = output.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error('No JSON found in output');
  }
  return JSON.parse(jsonMatch[0]);
}

async function runTest(): Promise<TestResult> {
  const startTime = Date.now();
  const testName = 'Session Management';
  let sessionId: string | undefined;
  const sessionFile = path.join(os.tmpdir(), `claude-test-session-${Date.now()}.json`);
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Test 1: Create initial session
    console.log('\nTest 1: Creating initial session...');
    const result1 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--session-file', sessionFile,
      'Hello! Please remember that my favorite color is blue. What is my favorite color?'
    ]);
    
    if (result1.exitCode !== 0) {
      throw new Error(`Initial session creation failed: ${result1.stderr}`);
    }
    
    const response1 = parseClaudeOutput(result1.stdout);
    const content1 = response1.result || response1.content || response1.response || '';
    
    // Extract session ID if available
    sessionId = response1.session_id;
    console.log('Session ID:', sessionId || 'Not provided in response');
    console.log('Response mentions blue:', content1.toLowerCase().includes('blue'));
    
    // Test 2: Continue session with --continue
    console.log('\nTest 2: Continuing session...');
    const result2 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--continue',
      '--session-file', sessionFile,
      'What was my favorite color that I mentioned earlier?'
    ]);
    
    if (result2.exitCode !== 0) {
      throw new Error(`Session continuation failed: ${result2.stderr}`);
    }
    
    const response2 = parseClaudeOutput(result2.stdout);
    const content2 = response2.result || response2.content || response2.response || '';
    const remembersColor = content2.toLowerCase().includes('blue');
    console.log('Continues session correctly:', remembersColor);
    
    // Test 3: Start new conversation, then resume
    console.log('\nTest 3: Starting new conversation...');
    const newSessionFile = path.join(os.tmpdir(), `claude-test-session-new-${Date.now()}.json`);
    const result3 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--session-file', newSessionFile,
      'My favorite number is 42. Remember this.'
    ]);
    
    if (result3.exitCode !== 0) {
      throw new Error(`New session creation failed: ${result3.stderr}`);
    }
    
    // Test 4: Resume original session
    console.log('\nTest 4: Resuming original session...');
    const result4 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--resume', sessionFile,
      'Do you still remember my favorite color?'
    ]);
    
    if (result4.exitCode !== 0) {
      throw new Error(`Session resumption failed: ${result4.stderr}`);
    }
    
    const response4 = parseClaudeOutput(result4.stdout);
    const content4 = response4.result || response4.content || response4.response || '';
    const stillRemembersColor = content4.toLowerCase().includes('blue');
    console.log('Resumes session correctly:', stillRemembersColor);
    
    // Test 5: Test session isolation
    console.log('\nTest 5: Testing session isolation...');
    const result5 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--resume', newSessionFile,
      'What was my favorite number?'
    ]);
    
    if (result5.exitCode !== 0) {
      throw new Error(`Session isolation test failed: ${result5.stderr}`);
    }
    
    const response5 = parseClaudeOutput(result5.stdout);
    const content5 = response5.result || response5.content || response5.response || '';
    const remembersNumber = content5.includes('42');
    const mentionsColor = content5.toLowerCase().includes('blue');
    console.log('Remembers number from correct session:', remembersNumber);
    console.log('Does not mention color from other session:', !mentionsColor);
    
    // Clean up session files
    try {
      await fs.unlink(sessionFile);
      await fs.unlink(newSessionFile);
    } catch (e) {
      // Ignore cleanup errors
    }
    
    // Determine if all tests passed
    const allTestsPassed = 
      remembersColor && 
      stillRemembersColor && 
      remembersNumber && 
      !mentionsColor;
    
    return {
      testName,
      passed: allTestsPassed,
      duration: Date.now() - startTime,
      details: {
        sessionCreated: !!sessionId || !!sessionFile,
        continuationWorks: remembersColor,
        resumptionWorks: stillRemembersColor,
        sessionIsolation: remembersNumber && !mentionsColor,
        sessionFile: sessionFile
      }
    };
    
  } catch (error) {
    // Clean up session files on error
    try {
      if (sessionFile) await fs.unlink(sessionFile);
    } catch (e) {
      // Ignore cleanup errors
    }
    
    return {
      testName,
      passed: false,
      duration: Date.now() - startTime,
      error: error instanceof Error ? error.message : String(error),
      details: {
        errorType: error instanceof Error ? error.constructor.name : typeof error,
        sessionId
      }
    };
  }
}

// Export for use in run-all-tests.ts
export { runTest };

// Run if executed directly
if (require.main === module) {
  runTest().then(result => {
    console.log('\nTest Result:', JSON.stringify(result, null, 2));
    process.exit(result.passed ? 0 : 1);
  }).catch(err => {
    console.error('Unexpected error:', err);
    process.exit(1);
  });
}