import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import * as path from 'path';
import * as os from 'os';

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

interface ClaudeInstance {
  id: string;
  sessionFile: string;
  process?: any;
  output: string;
  error: string;
  exitCode?: number;
  startTime: number;
  endTime?: number;
}

async function spawnClaude(
  id: string, 
  prompt: string, 
  sessionFile: string
): Promise<ClaudeInstance> {
  return new Promise((resolve, reject) => {
    const instance: ClaudeInstance = {
      id,
      sessionFile,
      output: '',
      error: '',
      startTime: Date.now()
    };
    
    const env = { ...process.env };
    delete env.ANTHROPIC_API_KEY;
    
    const args = [
      '-p',
      '--output-format', 'json',
      '--session-file', sessionFile,
      prompt
    ];
    
    const claude = spawn('claude', args, { 
      env,
      shell: true 
    });
    
    instance.process = claude;
    
    claude.stdout.on('data', (data) => {
      instance.output += data.toString();
    });
    
    claude.stderr.on('data', (data) => {
      instance.error += data.toString();
    });
    
    claude.on('close', (code) => {
      instance.exitCode = code || 0;
      instance.endTime = Date.now();
      resolve(instance);
    });
    
    claude.on('error', (err) => {
      instance.error = err.message;
      instance.exitCode = 1;
      instance.endTime = Date.now();
      resolve(instance);
    });
    
    // Timeout after 45 seconds
    setTimeout(() => {
      if (!instance.endTime) {
        claude.kill();
        instance.error = 'Process timed out';
        instance.exitCode = -1;
        instance.endTime = Date.now();
        resolve(instance);
      }
    }, 45000);
  });
}

function parseOutput(output: string): any {
  try {
    const jsonMatch = output.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      return null;
    }
    return JSON.parse(jsonMatch[0]);
  } catch (e) {
    return null;
  }
}

async function runTest(): Promise<TestResult> {
  const startTime = Date.now();
  const testName = 'Concurrent Execution';
  const sessionFiles: string[] = [];
  
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
    
    // Create session files
    for (const item of concurrentPrompts) {
      const sessionFile = path.join(os.tmpdir(), `claude-concurrent-${item.id}-${Date.now()}.json`);
      sessionFiles.push(sessionFile);
      item['sessionFile'] = sessionFile;
    }
    
    // Launch all instances concurrently
    const launchTime = Date.now();
    const instances = await Promise.all(
      concurrentPrompts.map(item => 
        spawnClaude(item.id, item.prompt, item['sessionFile'])
      )
    );
    const totalLaunchTime = Date.now() - launchTime;
    
    console.log(`All instances completed in ${totalLaunchTime}ms`);
    
    // Verify all instances succeeded
    const successfulInstances = instances.filter(i => i.exitCode === 0);
    console.log(`Successful instances: ${successfulInstances.length}/${instances.length}`);
    
    // Verify outputs are correct
    let outputsCorrect = true;
    for (let i = 0; i < instances.length; i++) {
      const instance = instances[i];
      const parsed = parseOutput(instance.output);
      const content = parsed?.result || parsed?.content || parsed?.response || '';
      
      if (i < 3) {
        // Agent identification tests
        const expectedAgent = `Agent ${i + 1}`;
        const correct = content.includes(expectedAgent);
        console.log(`${instance.id} output correct: ${correct}`);
        if (!correct) outputsCorrect = false;
      } else if (i === 3) {
        // Math test 1
        const correct = content.includes('40');
        console.log(`${instance.id} calculation correct: ${correct}`);
        if (!correct) outputsCorrect = false;
      } else if (i === 4) {
        // Math test 2
        const correct = content.includes('50');
        console.log(`${instance.id} calculation correct: ${correct}`);
        if (!correct) outputsCorrect = false;
      }
    }
    
    // Test 2: Stress test with more instances
    console.log('\nTest 2: Stress testing with 10 concurrent instances...');
    
    const stressPrompts = Array.from({ length: 10 }, (_, i) => ({
      id: `stress-${i}`,
      prompt: `Calculate ${i} * ${i}. Reply with just the number.`,
      sessionFile: path.join(os.tmpdir(), `claude-stress-${i}-${Date.now()}.json`)
    }));
    
    stressPrompts.forEach(p => sessionFiles.push(p.sessionFile));
    
    const stressStartTime = Date.now();
    const stressInstances = await Promise.all(
      stressPrompts.map(item => 
        spawnClaude(item.id, item.prompt, item.sessionFile)
      )
    );
    const stressDuration = Date.now() - stressStartTime;
    
    const stressSuccessful = stressInstances.filter(i => i.exitCode === 0);
    console.log(`Stress test: ${stressSuccessful.length}/${stressInstances.length} succeeded in ${stressDuration}ms`);
    
    // Test 3: Session isolation in concurrent execution
    console.log('\nTest 3: Testing session isolation...');
    
    // First, create sessions with different data
    const isolationTests = [
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
      const sessionFile = path.join(os.tmpdir(), `claude-iso-${test.id}-${Date.now()}.json`);
      sessionFiles.push(sessionFile);
      test['sessionFile'] = sessionFile;
      
      const instance = await spawnClaude(test.id, test.prompt1, sessionFile);
      return instance.exitCode === 0;
    });
    
    const setupResults = await Promise.all(setupPromises);
    const allSetupsSucceeded = setupResults.every(r => r);
    console.log('Session setups succeeded:', allSetupsSucceeded);
    
    // Now query both sessions concurrently
    const queryPromises = isolationTests.map(test => 
      spawnClaude(`${test.id}-query`, test.prompt2, test['sessionFile'])
    );
    
    const queryResults = await Promise.all(queryPromises);
    
    let isolationCorrect = true;
    for (let i = 0; i < isolationTests.length; i++) {
      const test = isolationTests[i];
      const result = queryResults[i];
      const parsed = parseOutput(result.output);
      const content = parsed?.result || parsed?.content || parsed?.response || '';
      const correct = content.toLowerCase().includes(test.expected);
      console.log(`${test.id} isolation correct: ${correct}`);
      if (!correct) isolationCorrect = false;
    }
    
    // Clean up session files
    for (const file of sessionFiles) {
      try {
        await fs.unlink(file);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
    
    // Calculate metrics
    const avgDuration = instances.reduce((sum, i) => 
      sum + ((i.endTime || i.startTime) - i.startTime), 0
    ) / instances.length;
    
    const maxDuration = Math.max(...instances.map(i => 
      (i.endTime || i.startTime) - i.startTime
    ));
    
    // Determine if all tests passed
    const allTestsPassed = 
      successfulInstances.length === instances.length &&
      outputsCorrect &&
      stressSuccessful.length >= stressInstances.length * 0.8 && // Allow 80% success for stress test
      allSetupsSucceeded &&
      isolationCorrect;
    
    return {
      testName,
      passed: allTestsPassed,
      duration: Date.now() - startTime,
      details: {
        concurrentSuccess: `${successfulInstances.length}/${instances.length}`,
        outputsCorrect,
        stressTestSuccess: `${stressSuccessful.length}/${stressInstances.length}`,
        sessionIsolation: isolationCorrect,
        avgInstanceDuration: Math.round(avgDuration),
        maxInstanceDuration: Math.round(maxDuration),
        totalConcurrentTime: totalLaunchTime,
        stressTestTime: stressDuration
      }
    };
    
  } catch (error) {
    // Clean up session files on error
    for (const file of sessionFiles) {
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