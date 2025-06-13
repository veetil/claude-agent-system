import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import * as path from 'path';
import * as os from 'os';

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

interface PerformanceMetrics {
  startupTime: number;
  responseTime: number;
  totalTime: number;
  memoryUsage?: number;
  cpuTime?: number;
}

async function measureClaudePerformance(
  args: string[],
  prompt?: string
): Promise<PerformanceMetrics & { stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve, reject) => {
    const metrics: PerformanceMetrics = {
      startupTime: 0,
      responseTime: 0,
      totalTime: 0
    };
    
    let stdout = '';
    let stderr = '';
    let firstDataTime: number | null = null;
    
    const env = { ...process.env };
    delete env.ANTHROPIC_API_KEY;
    
    const startTime = process.hrtime.bigint();
    const startCpu = process.cpuUsage();
    
    const claude = spawn('claude', args, { 
      env,
      shell: true 
    });
    
    claude.stdout.on('data', (data) => {
      if (!firstDataTime) {
        firstDataTime = Date.now();
        metrics.startupTime = Number(process.hrtime.bigint() - startTime) / 1_000_000; // Convert to ms
      }
      stdout += data.toString();
    });
    
    claude.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    claude.on('close', (code) => {
      const endTime = process.hrtime.bigint();
      const endCpu = process.cpuUsage(startCpu);
      
      metrics.totalTime = Number(endTime - startTime) / 1_000_000; // Convert to ms
      metrics.responseTime = metrics.totalTime - metrics.startupTime;
      metrics.cpuTime = (endCpu.user + endCpu.system) / 1000; // Convert to ms
      
      // Try to get memory usage from process (approximation)
      if (claude.pid) {
        try {
          const memUsage = process.memoryUsage();
          metrics.memoryUsage = memUsage.heapUsed / 1024 / 1024; // Convert to MB
        } catch (e) {
          // Ignore memory measurement errors
        }
      }
      
      resolve({
        ...metrics,
        stdout,
        stderr,
        exitCode: code || 0
      });
    });
    
    claude.on('error', (err) => {
      reject(err);
    });
    
    // Timeout after 60 seconds for performance tests
    setTimeout(() => {
      claude.kill();
      reject(new Error('Performance test timed out'));
    }, 60000);
  });
}

async function runTest(): Promise<TestResult> {
  const startTime = Date.now();
  const testName = 'Performance Testing';
  const performanceMetrics: any[] = [];
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Test 1: Basic startup performance
    console.log('\nTest 1: Measuring basic startup time...');
    const startupRuns = 5;
    const startupTimes: number[] = [];
    
    for (let i = 0; i < startupRuns; i++) {
      const result = await measureClaudePerformance([
        '-p',
        '--output-format', 'json',
        'Reply with just "OK"'
      ]);
      
      if (result.exitCode === 0) {
        startupTimes.push(result.startupTime);
        console.log(`Run ${i + 1}: Startup ${result.startupTime.toFixed(2)}ms, Total ${result.totalTime.toFixed(2)}ms`);
      }
    }
    
    const avgStartup = startupTimes.reduce((a, b) => a + b, 0) / startupTimes.length;
    console.log(`Average startup time: ${avgStartup.toFixed(2)}ms`);
    
    // Test 2: Response time for different prompt sizes
    console.log('\nTest 2: Testing response times for different prompt sizes...');
    const promptSizes = [
      { size: 10, prompt: 'Count to 5' },
      { size: 100, prompt: 'Explain quantum computing in one sentence. Be brief.' },
      { size: 500, prompt: 'Write a haiku about artificial intelligence. ' + 'Context: '.repeat(50) },
      { size: 1000, prompt: 'Summarize this: ' + 'The quick brown fox jumps over the lazy dog. '.repeat(20) }
    ];
    
    const responseTimes: any[] = [];
    for (const test of promptSizes) {
      const result = await measureClaudePerformance([
        '-p',
        '--output-format', 'json',
        test.prompt
      ]);
      
      if (result.exitCode === 0) {
        responseTimes.push({
          size: test.size,
          responseTime: result.responseTime,
          totalTime: result.totalTime
        });
        console.log(`Prompt size ~${test.size} chars: Response ${result.responseTime.toFixed(2)}ms`);
      }
    }
    
    // Test 3: Session creation overhead
    console.log('\nTest 3: Measuring session creation overhead...');
    const sessionFile = path.join(os.tmpdir(), `perf-session-${Date.now()}.json`);
    
    // First run with new session
    const newSessionResult = await measureClaudePerformance([
      '-p',
      '--output-format', 'json',
      '--session-file', sessionFile,
      'Starting new session'
    ]);
    
    // Second run continuing session
    const continueSessionResult = await measureClaudePerformance([
      '-p',
      '--output-format', 'json',
      '--continue',
      '--session-file', sessionFile,
      'Continuing session'
    ]);
    
    const sessionOverhead = newSessionResult.totalTime - continueSessionResult.totalTime;
    console.log(`New session time: ${newSessionResult.totalTime.toFixed(2)}ms`);
    console.log(`Continue session time: ${continueSessionResult.totalTime.toFixed(2)}ms`);
    console.log(`Session creation overhead: ~${Math.abs(sessionOverhead).toFixed(2)}ms`);
    
    // Test 4: Concurrent performance degradation
    console.log('\nTest 4: Testing concurrent performance...');
    const concurrentCounts = [1, 3, 5];
    const concurrentResults: any[] = [];
    
    for (const count of concurrentCounts) {
      const promises = Array(count).fill(0).map((_, i) => 
        measureClaudePerformance([
          '-p',
          '--output-format', 'json',
          `Instance ${i + 1}: What is ${i + 1} + ${i + 1}?`
        ])
      );
      
      const startConcurrent = Date.now();
      const results = await Promise.all(promises);
      const concurrentDuration = Date.now() - startConcurrent;
      
      const avgTime = results.reduce((sum, r) => sum + r.totalTime, 0) / results.length;
      concurrentResults.push({
        count,
        avgTime,
        totalDuration: concurrentDuration
      });
      
      console.log(`${count} concurrent: Avg ${avgTime.toFixed(2)}ms, Total ${concurrentDuration}ms`);
    }
    
    // Test 5: Memory efficiency
    console.log('\nTest 5: Testing memory efficiency...');
    const memoryTest = await measureClaudePerformance([
      '-p',
      '--output-format', 'json',
      'Process this and report: ' + 'Lorem ipsum '.repeat(100)
    ]);
    
    if (memoryTest.memoryUsage) {
      console.log(`Memory usage: ~${memoryTest.memoryUsage.toFixed(2)} MB`);
    }
    if (memoryTest.cpuTime) {
      console.log(`CPU time: ${memoryTest.cpuTime.toFixed(2)}ms`);
    }
    
    // Test 6: Stress test - rapid sequential calls
    console.log('\nTest 6: Rapid sequential calls...');
    const rapidCalls = 10;
    const rapidStart = Date.now();
    let successfulCalls = 0;
    
    for (let i = 0; i < rapidCalls; i++) {
      try {
        const result = await measureClaudePerformance([
          '-p',
          '--output-format', 'json',
          `Quick call ${i + 1}`
        ]);
        if (result.exitCode === 0) successfulCalls++;
      } catch (e) {
        console.log(`Rapid call ${i + 1} failed:`, e);
      }
    }
    
    const rapidDuration = Date.now() - rapidStart;
    const avgRapidTime = rapidDuration / rapidCalls;
    console.log(`Rapid calls: ${successfulCalls}/${rapidCalls} succeeded`);
    console.log(`Average time per call: ${avgRapidTime.toFixed(2)}ms`);
    
    // Clean up
    try {
      await fs.unlink(sessionFile);
    } catch (e) {
      // Ignore cleanup errors
    }
    
    // Performance criteria
    const performanceCriteria = {
      startupTime: avgStartup < 5000, // Less than 5 seconds
      responseScaling: responseTimes.length === promptSizes.length,
      sessionEfficiency: continueSessionResult.exitCode === 0,
      concurrentScaling: concurrentResults.length === concurrentCounts.length,
      stressTest: successfulCalls >= rapidCalls * 0.8 // 80% success rate
    };
    
    const meetsPerformanceCriteria = Object.values(performanceCriteria).every(v => v);
    
    return {
      testName,
      passed: meetsPerformanceCriteria,
      duration: Date.now() - startTime,
      details: {
        avgStartupTime: avgStartup.toFixed(2),
        responseTimes,
        sessionOverhead: sessionOverhead.toFixed(2),
        concurrentResults,
        memoryUsage: memoryTest.memoryUsage?.toFixed(2),
        cpuTime: memoryTest.cpuTime?.toFixed(2),
        rapidCallsPerSecond: (1000 / avgRapidTime).toFixed(2),
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