import { ClaudeWrapper } from '../utils/claude-wrapper';

/**
 * POC Test 01: Basic SDK Mode (--print flag)
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
  const testName = 'Basic SDK Mode (--print flag)';
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Create wrapper instance
    const claude = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000
    });
    
    // Test 1: Launch Claude with --print flag and simple prompt
    console.log('\nTest 1: Basic print mode with JSON output...');
    const response1 = await claude.execute('Say "Hello from SDK mode" and nothing else');
    
    console.log('Success:', response1.success);
    console.log('Result:', response1.result);
    console.log('Session ID:', response1.sessionId);
    
    // Validate response
    if (!response1.success) {
      throw new Error(`Claude execution failed: ${response1.error}`);
    }
    
    // Test 2: Verify we got a result
    const hasResult = !!response1.result;
    const hasSessionId = !!response1.sessionId;
    
    // Test 3: Check response content
    const responseText = response1.result || '';
    const containsExpectedText = responseText.toLowerCase().includes('hello') && 
                                responseText.toLowerCase().includes('sdk');
    
    if (!containsExpectedText) {
      console.warn('Response does not contain expected text:', responseText);
    }
    
    // Test 4: Multiple prompts in sequence
    console.log('\nTest 4: Testing sequential prompts...');
    const prompts = [
      'What is 2+2? Reply with just the number.',
      'What color is the sky? Reply with just one word.',
      'Is TypeScript a programming language? Reply with just yes or no.'
    ];
    
    const sequentialResults = await claude.executeSequence(prompts);
    
    const allSequentialPassed = sequentialResults.every(r => r.success);
    console.log(`Sequential tests: ${sequentialResults.filter(r => r.success).length}/${sequentialResults.length} passed`);
    
    // Test 5: Test metadata collection
    console.log('\nTest 5: Testing metadata collection...');
    const hasMetadata = response1.metadata && 
                       typeof response1.metadata.duration === 'number' &&
                       response1.metadata.exitCode === 0;
    
    const hasUsageData = response1.metadata?.usage && 
                        typeof response1.metadata.usage.input_tokens === 'number';
    
    console.log('Has metadata:', hasMetadata);
    console.log('Has usage data:', hasUsageData);
    
    return {
      testName,
      passed: response1.success && hasResult && hasSessionId && allSequentialPassed,
      duration: Date.now() - startTime,
      output: JSON.stringify({
        result: response1.result,
        sessionId: response1.sessionId,
        cost: response1.metadata?.cost
      }, null, 2),
      details: {
        hasResult,
        hasSessionId,
        containsExpectedText,
        sequentialResults: sequentialResults.map(r => ({
          success: r.success,
          result: r.result?.substring(0, 50)
        })),
        hasMetadata,
        hasUsageData,
        tokensUsed: response1.metadata?.usage
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