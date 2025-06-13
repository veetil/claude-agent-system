import { ClaudeWrapper } from '../utils/claude-wrapper';

/**
 * POC Test 06: Performance Testing
 * 
 * Measures performance characteristics of Claude CLI including
 * startup time, response latency, and resource usage.
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
  const testName = 'Performance Testing';
  const performanceMetrics: any[] = [];
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Test 1: Basic startup performance
    console.log('\nTest 1: Measuring basic startup time...');
    const startupRuns = 3; // Reduced for faster testing
    const startupTimes: number[] = [];
    const responseTimes: number[] = [];
    
    for (let i = 0; i < startupRuns; i++) {
      const runStart = Date.now();
      const wrapper = new ClaudeWrapper({
        outputFormat: 'json',
        timeout: 30000
      });
      
      const result = await wrapper.execute('Reply with just "OK"');
      const runEnd = Date.now();
      const totalTime = runEnd - runStart;
      
      if (result.success) {
        startupTimes.push(totalTime);
        
        // Calculate approximate response time from metadata if available
        const responseTime = result.metadata?.duration || totalTime;
        responseTimes.push(responseTime);
        
        console.log(`Run ${i + 1}: Total ${totalTime}ms, Response ${responseTime}ms`);
      }
    }
    
    const avgStartup = startupTimes.reduce((a, b) => a + b, 0) / startupTimes.length;
    const avgResponse = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    console.log(`Average total time: ${avgStartup.toFixed(2)}ms`);
    console.log(`Average response time: ${avgResponse.toFixed(2)}ms`);
    
    // Test 2: Response time for different prompt sizes
    console.log('\nTest 2: Testing response times for different prompt sizes...');
    const promptSizes = [
      { size: 'small', prompt: 'Count to 5' },
      { size: 'medium', prompt: 'Explain quantum computing in one sentence. Be brief.' },
      { size: 'large', prompt: 'Write a haiku about artificial intelligence.' },
      { size: 'xlarge', prompt: 'Summarize this: ' + 'The quick brown fox jumps over the lazy dog. '.repeat(10) }
    ];
    
    const sizeMetrics: any[] = [];
    const wrapper = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000
    });
    
    for (const test of promptSizes) {
      const testStart = Date.now();
      const result = await wrapper.execute(test.prompt);
      const testDuration = Date.now() - testStart;
      
      if (result.success) {
        sizeMetrics.push({
          size: test.size,
          promptLength: test.prompt.length,
          responseTime: testDuration,
          tokenCount: result.metadata?.usage ? 
            (result.metadata.usage.input_tokens + result.metadata.usage.output_tokens) : 0
        });
        console.log(`Prompt ${test.size} (~${test.prompt.length} chars): ${testDuration}ms`);
      }
    }
    
    // Test 3: Session overhead
    console.log('\nTest 3: Measuring session overhead...');
    
    // First call creates a new session
    const sessionStart1 = Date.now();
    const { sessionId, response: sessionResp1 } = await wrapper.createSession(
      'Remember: My favorite number is 42.'
    );
    const sessionTime1 = Date.now() - sessionStart1;
    
    // Second call continues the session
    const sessionStart2 = Date.now();
    const sessionResp2 = await wrapper.continueSession(
      sessionId,
      'What is my favorite number?'
    );
    const sessionTime2 = Date.now() - sessionStart2;
    
    console.log(`New session time: ${sessionTime1}ms`);
    console.log(`Continue session time: ${sessionTime2}ms`);
    console.log(`Session continuation is ${sessionTime1 > sessionTime2 ? 'faster' : 'slower'}`);
    
    // Test 4: Concurrent performance
    console.log('\nTest 4: Testing concurrent performance...');
    const concurrentCounts = [1, 3, 5];
    const concurrentResults: any[] = [];
    
    for (const count of concurrentCounts) {
      const prompts = Array(count).fill(0).map((_, i) => ({
        id: `concurrent-${i}`,
        prompt: `Instance ${i + 1}: What is ${i + 1} + ${i + 1}?`
      }));
      
      const concurrentStart = Date.now();
      const results = await wrapper.executeConcurrent(prompts);
      const concurrentDuration = Date.now() - concurrentStart;
      
      const successCount = Array.from(results.values()).filter(r => r.success).length;
      const avgTimePerRequest = concurrentDuration / count;
      
      concurrentResults.push({
        count,
        duration: concurrentDuration,
        avgTimePerRequest,
        successRate: (successCount / count) * 100
      });
      
      console.log(`${count} concurrent: Total ${concurrentDuration}ms, Avg ${avgTimePerRequest.toFixed(2)}ms/req, Success ${successCount}/${count}`);
    }
    
    // Test 5: Memory efficiency (approximation)
    console.log('\nTest 5: Testing with large content...');
    const largeContent = 'Lorem ipsum dolor sit amet. '.repeat(100);
    const memStart = process.memoryUsage().heapUsed / 1024 / 1024;
    
    const largeResult = await wrapper.execute(`Process this text: ${largeContent}`);
    
    const memEnd = process.memoryUsage().heapUsed / 1024 / 1024;
    const memDelta = memEnd - memStart;
    
    console.log(`Memory delta: ~${memDelta.toFixed(2)} MB`);
    console.log(`Large content processed: ${largeResult.success}`);
    
    // Test 6: Rapid sequential calls
    console.log('\nTest 6: Rapid sequential calls...');
    const rapidCalls = 5; // Reduced for faster testing
    const rapidStart = Date.now();
    let successfulCalls = 0;
    
    for (let i = 0; i < rapidCalls; i++) {
      const result = await wrapper.execute(`Quick call ${i + 1}: What is ${i}?`);
      if (result.success) successfulCalls++;
    }
    
    const rapidDuration = Date.now() - rapidStart;
    const avgRapidTime = rapidDuration / rapidCalls;
    console.log(`Rapid calls: ${successfulCalls}/${rapidCalls} succeeded`);
    console.log(`Average time per call: ${avgRapidTime.toFixed(2)}ms`);
    console.log(`Throughput: ${(1000 / avgRapidTime).toFixed(2)} calls/second`);
    
    // Performance criteria
    const performanceCriteria = {
      startupTime: avgStartup < 10000, // Less than 10 seconds
      responseScaling: sizeMetrics.length === promptSizes.length,
      sessionWorks: sessionResp1.success && sessionResp2.success,
      concurrentScaling: concurrentResults.every(r => r.successRate >= 80),
      stressTest: successfulCalls >= rapidCalls * 0.8 // 80% success rate
    };
    
    const meetsPerformanceCriteria = Object.values(performanceCriteria).every(v => v);
    
    return {
      testName,
      passed: meetsPerformanceCriteria,
      duration: Date.now() - startTime,
      details: {
        avgTotalTime: avgStartup.toFixed(2),
        avgResponseTime: avgResponse.toFixed(2),
        promptSizeMetrics: sizeMetrics,
        sessionOverhead: {
          newSession: sessionTime1,
          continueSession: sessionTime2,
          faster: sessionTime1 > sessionTime2
        },
        concurrentResults,
        memoryDelta: memDelta.toFixed(2),
        throughput: (1000 / avgRapidTime).toFixed(2),
        performanceCriteria
      }
    };
    
  } catch (error) {
    return {
      testName,
      passed: false,
      duration: Date.now() - startTime,
      error: error instanceof Error ? error.message : String(error),
      details: {
        errorType: error instanceof Error ? error.constructor.name : typeof error,
        performanceMetrics
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