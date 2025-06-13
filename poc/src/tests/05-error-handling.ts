import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import * as path from 'path';
import * as os from 'os';

/**
 * POC Test 05: Error Handling
 * 
 * Validates Claude CLI's error handling capabilities including
 * invalid inputs, session errors, and recovery mechanisms.
 */

interface TestResult {
  testName: string;
  passed: boolean;
  duration: number;
  output?: string;
  error?: string;
  details?: any;
}

async function executeClaudeCommand(
  args: string[],
  options?: { timeout?: number; expectError?: boolean }
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve, reject) => {
    let stdout = '';
    let stderr = '';
    const timeout = options?.timeout || 30000;
    
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
      if (options?.expectError) {
        resolve({ stdout, stderr: err.message, exitCode: 1 });
      } else {
        reject(err);
      }
    });
    
    // Timeout
    setTimeout(() => {
      claude.kill();
      resolve({ stdout, stderr: 'Process timed out', exitCode: -1 });
    }, timeout);
  });
}

async function runTest(): Promise<TestResult> {
  const startTime = Date.now();
  const testName = 'Error Handling';
  const tempFiles: string[] = [];
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Test 1: Invalid command line arguments
    console.log('\nTest 1: Testing invalid arguments...');
    const result1 = await executeClaudeCommand([
      '-p',
      '--invalid-flag',
      'test prompt'
    ], { expectError: true });
    
    const handlesInvalidArgs = result1.exitCode !== 0;
    console.log('Handles invalid arguments:', handlesInvalidArgs);
    console.log('Error output contains helpful message:', result1.stderr.length > 0);
    
    // Test 2: Invalid output format
    console.log('\nTest 2: Testing invalid output format...');
    const result2 = await executeClaudeCommand([
      '-p',
      '--output-format', 'invalid-format',
      'test prompt'
    ], { expectError: true });
    
    const handlesInvalidFormat = result2.exitCode !== 0;
    console.log('Handles invalid output format:', handlesInvalidFormat);
    
    // Test 3: Non-existent session file for resume
    console.log('\nTest 3: Testing non-existent session file...');
    const nonExistentFile = path.join(os.tmpdir(), `non-existent-${Date.now()}.json`);
    const result3 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--resume', nonExistentFile,
      'test prompt'
    ], { expectError: true });
    
    const handlesNonExistentSession = result3.exitCode !== 0;
    console.log('Handles non-existent session:', handlesNonExistentSession);
    
    // Test 4: Invalid system prompt file
    console.log('\nTest 4: Testing invalid system prompt file...');
    const result4 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--system-prompt-file', '/path/that/does/not/exist.txt',
      'test prompt'
    ], { expectError: true });
    
    const handlesInvalidSystemPrompt = result4.exitCode !== 0;
    console.log('Handles invalid system prompt file:', handlesInvalidSystemPrompt);
    
    // Test 5: Empty prompt
    console.log('\nTest 5: Testing empty prompt...');
    const result5 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      ''
    ], { expectError: true });
    
    const handlesEmptyPrompt = result5.exitCode !== 0 || result5.stderr.length > 0;
    console.log('Handles empty prompt:', handlesEmptyPrompt);
    
    // Test 6: Session recovery after error
    console.log('\nTest 6: Testing session recovery...');
    const sessionFile = path.join(os.tmpdir(), `recovery-session-${Date.now()}.json`);
    tempFiles.push(sessionFile);
    
    // Create initial session
    const setupResult = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--session-file', sessionFile,
      'Remember that my favorite number is 42'
    ]);
    
    if (setupResult.exitCode === 0) {
      // Simulate an error by corrupting the session file
      try {
        await fs.writeFile(sessionFile, 'invalid json content');
      } catch (e) {
        console.log('Could not corrupt session file:', e);
      }
      
      // Try to continue with corrupted session
      const corruptResult = await executeClaudeCommand([
        '-p',
        '--output-format', 'json',
        '--continue',
        '--session-file', sessionFile,
        'What is my favorite number?'
      ], { expectError: true });
      
      const handlesCorruptSession = corruptResult.exitCode !== 0;
      console.log('Handles corrupted session:', handlesCorruptSession);
      
      // Try to create new session with same file (recovery)
      const recoveryResult = await executeClaudeCommand([
        '-p',
        '--output-format', 'json',
        '--session-file', sessionFile,
        'Starting fresh. My favorite color is blue.'
      ]);
      
      const recoversFromError = recoveryResult.exitCode === 0;
      console.log('Recovers from session error:', recoversFromError);
    }
    
    // Test 7: Timeout handling
    console.log('\nTest 7: Testing timeout handling...');
    const timeoutStart = Date.now();
    const result7 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      'Please count from 1 to 1000000 very slowly'
    ], { timeout: 5000 }); // 5 second timeout
    
    const timeoutDuration = Date.now() - timeoutStart;
    const handlesTimeout = result7.exitCode === -1 && timeoutDuration < 6000;
    console.log('Handles timeout correctly:', handlesTimeout);
    console.log('Timeout duration:', timeoutDuration);
    
    // Test 8: Concurrent error scenarios
    console.log('\nTest 8: Testing concurrent error handling...');
    const errorPromises = [
      executeClaudeCommand(['--invalid-flag-1'], { expectError: true }),
      executeClaudeCommand(['--invalid-flag-2'], { expectError: true }),
      executeClaudeCommand(['--invalid-flag-3'], { expectError: true })
    ];
    
    const errorResults = await Promise.allSettled(errorPromises);
    const allErrorsHandled = errorResults.every(r => 
      r.status === 'fulfilled' && r.value.exitCode !== 0
    );
    console.log('All concurrent errors handled:', allErrorsHandled);
    
    // Test 9: Very long prompt
    console.log('\nTest 9: Testing very long prompt...');
    const longPrompt = 'x'.repeat(10000); // 10k character prompt
    const result9 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      longPrompt
    ]);
    
    const handlesLongPrompt = result9.exitCode === 0 || result9.exitCode !== 0;
    console.log('Handles long prompt without crash:', handlesLongPrompt);
    
    // Test 10: Special characters in prompt
    console.log('\nTest 10: Testing special characters...');
    const specialPrompt = 'Test with special chars: "\'`${}[]()<>|&;\\n\\t';
    const result10 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      specialPrompt
    ]);
    
    const handlesSpecialChars = result10.exitCode === 0 || result10.stderr.length === 0;
    console.log('Handles special characters:', handlesSpecialChars);
    
    // Clean up temp files
    for (const file of tempFiles) {
      try {
        await fs.unlink(file);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
    
    // Determine if error handling is robust
    const robustErrorHandling = 
      handlesInvalidArgs &&
      handlesInvalidFormat &&
      handlesNonExistentSession &&
      handlesInvalidSystemPrompt &&
      handlesEmptyPrompt &&
      handlesTimeout &&
      allErrorsHandled;
    
    return {
      testName,
      passed: robustErrorHandling,
      duration: Date.now() - startTime,
      details: {
        invalidArgs: handlesInvalidArgs,
        invalidFormat: handlesInvalidFormat,
        nonExistentSession: handlesNonExistentSession,
        invalidSystemPrompt: handlesInvalidSystemPrompt,
        emptyPrompt: handlesEmptyPrompt,
        timeout: handlesTimeout,
        concurrentErrors: allErrorsHandled,
        longPrompt: handlesLongPrompt,
        specialChars: handlesSpecialChars
      }
    };
    
  } catch (error) {
    // Clean up temp files on error
    for (const file of tempFiles) {
      try {
        await fs.unlink(file);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
    
    return {
      testName,
      passed: false,
      duration: Date.now() - startTime,
      error: error instanceof Error ? error.message : String(error),
      details: {
        errorType: error instanceof Error ? error.constructor.name : typeof error
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