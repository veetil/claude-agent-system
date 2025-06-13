import { ClaudeWrapper } from '../utils/claude-wrapper';

/**
 * POC Test 02: Session Management
 * 
 * Validates Claude CLI session creation, continuation, and resumption
 * using session IDs from responses.
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
  const testName = 'Session Management';
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Create wrapper instance
    const claude = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000
    });
    
    // Test 1: Create initial session
    console.log('\nTest 1: Creating initial session...');
    const { sessionId, response: response1 } = await claude.createSession(
      'Hello! Please remember that my favorite color is blue. What is my favorite color?'
    );
    
    console.log('Session ID:', sessionId);
    console.log('Response mentions blue:', response1.result?.toLowerCase().includes('blue'));
    
    if (!response1.success) {
      throw new Error(`Initial session creation failed: ${response1.error}`);
    }
    
    // Test 2: Continue session with session ID
    console.log('\nTest 2: Continuing session with session ID...');
    const response2 = await claude.continueSession(
      sessionId,
      'What was my favorite color that I mentioned earlier?'
    );
    
    if (!response2.success) {
      console.log('Error continuing session:', response2.error);
      console.log('Full response:', JSON.stringify(response2, null, 2));
    }
    
    const remembersColor = response2.result?.toLowerCase().includes('blue');
    console.log('Continues session correctly:', remembersColor);
    console.log('Response received:', response2.success);
    console.log('New session ID:', response2.sessionId);
    console.log('Original session ID:', sessionId);
    
    // Update sessionId for next continuation
    const currentSessionId = response2.sessionId || sessionId;
    
    // Test 3: Start new conversation
    console.log('\nTest 3: Starting new conversation...');
    const { sessionId: newSessionId } = await claude.createSession(
      'My favorite number is 42. Remember this.'
    );
    
    console.log('New session ID:', newSessionId);
    console.log('Different from first session:', newSessionId !== sessionId);
    
    // Test 4: Continue new session
    console.log('\nTest 4: Continuing new session...');
    const response4 = await claude.continueSession(
      newSessionId,
      'What was my favorite number?'
    );
    
    const remembersNumber = response4.result?.includes('42');
    console.log('Remembers number from correct session:', remembersNumber);
    
    // Update session ID for the new conversation
    const currentNewSessionId = response4.sessionId || newSessionId;
    
    // Test 5: Test session isolation
    console.log('\nTest 5: Testing session isolation...');
    // Try to ask about color in the number session (using the updated session ID)
    const response5 = await claude.continueSession(
      currentNewSessionId,
      'What was my favorite color?'
    );
    
    const mentionsBlue = response5.result?.toLowerCase().includes('blue');
    const admitsNotKnowing = response5.result?.toLowerCase().includes("don't") || 
                            response5.result?.toLowerCase().includes("didn't") ||
                            response5.result?.toLowerCase().includes("not");
    console.log('Does not mention blue from other session:', !mentionsBlue || admitsNotKnowing);
    
    // Test 6: Continue last session
    console.log('\nTest 6: Testing continue last session...');
    const response6 = await claude.continueLastSession(
      'Can you remind me what we were just talking about?'
    );
    
    console.log('Continues last session:', response6.success);
    console.log('References recent context:', response6.result?.includes('color') || response6.result?.includes('number'));
    
    // Determine if all tests passed
    // Note: Claude returns a new session_id for each response, even with -r flag
    const allTestsPassed = 
      response1.success && 
      remembersColor && 
      remembersNumber && 
      (!mentionsBlue || admitsNotKnowing) &&
      response6.success;
    
    return {
      testName,
      passed: allTestsPassed,
      duration: Date.now() - startTime,
      details: {
        sessionCreated: !!sessionId,
        sessionContinuation: remembersColor,
        newSessionCreated: !!newSessionId,
        sessionIsolation: !mentionsBlue || admitsNotKnowing,
        continueLastWorks: response6.success,
        sessionMemory: {
          remembersColor,
          remembersNumber,
          isolation: !mentionsBlue || admitsNotKnowing
        }
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