import { ClaudeWrapper } from '../utils/claude-wrapper';

/**
 * POC Test 04: Concurrent Execution
 * 
 * Validates that multiple Claude CLI instances can run concurrently
 * with separate sessions and without interference.
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
  const testName = 'Concurrent Execution';
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Test 1: Launch multiple Claude instances concurrently
    console.log('\nTest 1: Launching 5 concurrent Claude instances...');
    
    const concurrentPrompts = [
      { id: 'agent-1', prompt: 'You are Agent 1. What is your agent number? Reply with just "Agent 1".' },
      { id: 'agent-2', prompt: 'You are Agent 2. What is your agent number? Reply with just "Agent 2".' },
      { id: 'agent-3', prompt: 'You are Agent 3. What is your agent number? Reply with just "Agent 3".' },
      { id: 'agent-4', prompt: 'You are Agent 4. Calculate 10 * 4. Reply with just the number.' },
      { id: 'agent-5', prompt: 'You are Agent 5. Calculate 25 + 25. Reply with just the number.' }
    ];
    
    const wrapper = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000
    });
    
    // Launch all instances concurrently
    const launchTime = Date.now();
    const results = await wrapper.executeConcurrent(concurrentPrompts);
    const totalLaunchTime = Date.now() - launchTime;
    
    console.log(`All instances completed in ${totalLaunchTime}ms`);
    
    // Verify all instances succeeded
    const successfulInstances = Array.from(results.values()).filter(r => r.success);
    console.log(`Successful instances: ${successfulInstances.length}/${results.size}`);
    
    // Verify outputs are correct
    let outputsCorrect = true;
    let i = 0;
    for (const [id, response] of results) {
      const content = response.result || '';
      
      if (i < 3) {
        // Agent identification tests
        const expectedAgent = `Agent ${i + 1}`;
        const correct = content.includes(expectedAgent);
        console.log(`${id} output correct: ${correct}`);
        if (!correct) outputsCorrect = false;
      } else if (i === 3) {
        // Math test 1
        const correct = content.includes('40');
        console.log(`${id} calculation correct: ${correct}`);
        if (!correct) outputsCorrect = false;
      } else if (i === 4) {
        // Math test 2
        const correct = content.includes('50');
        console.log(`${id} calculation correct: ${correct}`);
        if (!correct) outputsCorrect = false;
      }
      i++;
    }
    
    // Test 2: Stress test with more instances
    console.log('\nTest 2: Stress testing with 10 concurrent instances...');
    
    const stressPrompts = Array.from({ length: 10 }, (_, i) => ({
      id: `stress-${i}`,
      prompt: `Calculate ${i} * ${i}. Reply with just the number.`
    }));
    
    const stressStartTime = Date.now();
    const stressResults = await wrapper.executeConcurrent(stressPrompts);
    const stressDuration = Date.now() - stressStartTime;
    
    const stressSuccessful = Array.from(stressResults.values()).filter(r => r.success);
    console.log(`Stress test: ${stressSuccessful.length}/${stressResults.size} succeeded in ${stressDuration}ms`);
    
    // Test 3: Session isolation in concurrent execution
    console.log('\nTest 3: Testing session isolation...');
    
    // First, create sessions with different data
    interface IsolationTest {
      id: string;
      sessionId?: string;
      prompt1: string;
      prompt2: string;
      expected: string;
    }
    
    const isolationTests: IsolationTest[] = [
      { 
        id: 'iso-1', 
        prompt1: 'My favorite animal is a cat. Remember this.',
        prompt2: 'What is my favorite animal?',
        expected: 'cat'
      },
      { 
        id: 'iso-2', 
        prompt1: 'My favorite animal is a dog. Remember this.',
        prompt2: 'What is my favorite animal?',
        expected: 'dog'
      }
    ];
    
    // Create initial sessions
    const setupPromises = isolationTests.map(async (test) => {
      const { sessionId } = await wrapper.createSession(test.prompt1);
      test.sessionId = sessionId;
      return sessionId !== 'unknown';
    });
    
    const setupResults = await Promise.all(setupPromises);
    const allSetupsSucceeded = setupResults.every(r => r);
    console.log('Session setups succeeded:', allSetupsSucceeded);
    
    // Now query both sessions concurrently
    const queryPromises = isolationTests.map(test => ({
      id: `${test.id}-query`,
      prompt: test.prompt2,
      options: { sessionId: test.sessionId }
    }));
    
    const queryResults = await wrapper.executeConcurrent(queryPromises);
    
    let isolationCorrect = true;
    for (let i = 0; i < isolationTests.length; i++) {
      const test = isolationTests[i];
      const result = queryResults.get(`${test.id}-query`);
      const content = result?.result || '';
      const correct = content.toLowerCase().includes(test.expected);
      console.log(`${test.id} isolation correct: ${correct}`);
      if (!correct) isolationCorrect = false;
    }
    
    // Test 4: Different agent types running concurrently
    console.log('\nTest 4: Testing different agent types concurrently...');
    
    const agentPrompts = [
      {
        id: 'researcher',
        prompt: 'What are the key features of TypeScript? Be brief.',
        options: {
          systemPrompt: 'You are a research specialist. Provide concise, factual information.'
        }
      },
      {
        id: 'coder',
        prompt: 'Write a TypeScript function to add two numbers.',
        options: {
          systemPrompt: 'You are a code specialist. Write clean, simple code.'
        }
      },
      {
        id: 'reviewer',
        prompt: 'Review this code: const x = 5; What could be improved?',
        options: {
          systemPrompt: 'You are a code reviewer. Focus on best practices.'
        }
      }
    ];
    
    const agentResults = await wrapper.executeConcurrent(agentPrompts);
    const allAgentsSucceeded = Array.from(agentResults.values()).every(r => r.success);
    console.log('All specialized agents succeeded:', allAgentsSucceeded);
    
    // Calculate metrics
    const avgDuration = successfulInstances.reduce((sum, r) => 
      sum + (r.metadata?.duration || 0), 0
    ) / successfulInstances.length;
    
    // Determine if all tests passed
    const allTestsPassed = 
      successfulInstances.length === results.size &&
      outputsCorrect &&
      stressSuccessful.length >= stressResults.size * 0.8 && // Allow 80% success for stress test
      allSetupsSucceeded &&
      isolationCorrect &&
      allAgentsSucceeded;
    
    return {
      testName,
      passed: allTestsPassed,
      duration: Date.now() - startTime,
      details: {
        concurrentSuccess: `${successfulInstances.length}/${results.size}`,
        outputsCorrect,
        stressTestSuccess: `${stressSuccessful.length}/${stressResults.size}`,
        sessionIsolation: isolationCorrect,
        avgInstanceDuration: Math.round(avgDuration),
        totalConcurrentTime: totalLaunchTime,
        stressTestTime: stressDuration,
        specializedAgents: allAgentsSucceeded
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