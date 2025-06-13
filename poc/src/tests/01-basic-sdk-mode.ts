import { spawn } from 'child_process';

/**
 * POC Test 01: Basic SDK Mode (-p flag)
 * 
 * Validates that Claude CLI can be launched in SDK/print mode
 * and returns machine-readable JSON output.
 */

interface TestResult {
  testName: string;
  passed: boolean;
  duration: number;
  output?: string;
  error?: string;
  details?: any;
}

async function runTest(): Promise<TestResult> {
  const startTime = Date.now();
  const testName = 'Basic SDK Mode (-p flag)';
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Test 1: Launch Claude with -p flag and simple prompt
    const result1 = await new Promise<{ stdout: string; stderr: string; exitCode: number }>((resolve, reject) => {
      let stdout = '';
      let stderr = '';
      
      // Ensure ANTHROPIC_API_KEY is not set
      const env = { ...process.env };
      delete env.ANTHROPIC_API_KEY;
      
      const claude = spawn('claude', [
        '-p',
        '--output-format', 'json',
        'Say "Hello from SDK mode" and nothing else'
      ], { 
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
    
    console.log('Exit code:', result1.exitCode);
    console.log('Stdout length:', result1.stdout.length);
    console.log('Stderr length:', result1.stderr.length);
    
    // Validate result
    if (result1.exitCode !== 0) {
      throw new Error(`Claude exited with code ${result1.exitCode}: ${result1.stderr}`);
    }
    
    // Parse JSON output
    let parsedOutput: any;
    try {
      // The output might have multiple JSON objects, try to find the main response
      const jsonMatch = result1.stdout.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No JSON found in output');
      }
      parsedOutput = JSON.parse(jsonMatch[0]);
    } catch (e) {
      console.error('Failed to parse JSON:', e);
      console.error('Raw output:', result1.stdout);
      throw new Error(`Failed to parse JSON output: ${e}`);
    }
    
    // Test 2: Verify JSON structure
    const hasExpectedFields = 
      parsedOutput.hasOwnProperty('result') || 
      parsedOutput.hasOwnProperty('content') ||
      parsedOutput.hasOwnProperty('response');
    
    if (!hasExpectedFields) {
      throw new Error('JSON output missing expected fields');
    }
    
    // Test 3: Check for response content
    const responseText = parsedOutput.result || parsedOutput.content || parsedOutput.response || '';
    const containsExpectedText = responseText.toLowerCase().includes('hello') && 
                                responseText.toLowerCase().includes('sdk');
    
    if (!containsExpectedText) {
      console.warn('Response does not contain expected text:', responseText);
    }
    
    // Test 4: Multiple prompts in sequence
    console.log('\nTesting sequential prompts...');
    const prompts = [
      'What is 2+2? Reply with just the number.',
      'What color is the sky? Reply with just one word.',
      'Is TypeScript a programming language? Reply with just yes or no.'
    ];
    
    const sequentialResults = [];
    for (const prompt of prompts) {
      const result = await new Promise<{ stdout: string; exitCode: number }>((resolve, reject) => {
        let stdout = '';
        
        const env = { ...process.env };
        delete env.ANTHROPIC_API_KEY;
        
        const claude = spawn('claude', [
          '-p',
          '--output-format', 'json',
          prompt
        ], { 
          env,
          shell: true 
        });
        
        claude.stdout.on('data', (data) => {
          stdout += data.toString();
        });
        
        claude.on('close', (code) => {
          resolve({ stdout, exitCode: code || 0 });
        });
        
        setTimeout(() => {
          claude.kill();
          reject(new Error('Timeout'));
        }, 30000);
      });
      
      if (result.exitCode === 0) {
        sequentialResults.push({ prompt, success: true });
      } else {
        sequentialResults.push({ prompt, success: false });
      }
    }
    
    const allSequentialPassed = sequentialResults.every(r => r.success);
    console.log(`Sequential tests: ${sequentialResults.filter(r => r.success).length}/${sequentialResults.length} passed`);
    
    return {
      testName,
      passed: hasExpectedFields && allSequentialPassed,
      duration: Date.now() - startTime,
      output: JSON.stringify(parsedOutput, null, 2),
      details: {
        jsonParsed: true,
        hasExpectedFields,
        containsExpectedText,
        sequentialResults,
        outputStructure: Object.keys(parsedOutput)
      }
    };
    
  } catch (error) {
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