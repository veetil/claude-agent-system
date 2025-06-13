#!/usr/bin/env ts-node

import { promises as fs } from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

/**
 * POC Test Runner
 * 
 * Runs all POC tests and generates a comprehensive validation report.
 */

interface TestResult {
  testName: string;
  passed: boolean;
  duration: number;
  output?: string;
  error?: string;
  details?: any;
}

interface TestModule {
  runTest: () => Promise<TestResult>;
}

// ANSI color codes for console output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  gray: '\x1b[90m'
};

async function checkClaudeCLI(): Promise<boolean> {
  return new Promise((resolve) => {
    const claude = spawn('claude', ['--version'], { shell: true });
    
    claude.on('close', (code) => {
      resolve(code === 0);
    });
    
    claude.on('error', () => {
      resolve(false);
    });
    
    setTimeout(() => {
      claude.kill();
      resolve(false);
    }, 5000);
  });
}

async function runAllTests(): Promise<void> {
  console.log(`${colors.blue}═══════════════════════════════════════════════════════════════${colors.reset}`);
  console.log(`${colors.blue}           Claude CLI POC Validation Test Suite                 ${colors.reset}`);
  console.log(`${colors.blue}═══════════════════════════════════════════════════════════════${colors.reset}\n`);
  
  // Check if Claude CLI is available
  console.log('Checking Claude CLI availability...');
  const claudeAvailable = await checkClaudeCLI();
  
  if (!claudeAvailable) {
    console.error(`${colors.red}✗ Claude CLI is not available or not in PATH${colors.reset}`);
    console.error('Please ensure Claude CLI is installed and accessible.\n');
    process.exit(1);
  }
  
  console.log(`${colors.green}✓ Claude CLI is available${colors.reset}\n`);
  
  // Check ANTHROPIC_API_KEY is not set
  if (process.env.ANTHROPIC_API_KEY) {
    console.warn(`${colors.yellow}⚠ Warning: ANTHROPIC_API_KEY is set. Unsetting for tests...${colors.reset}`);
    delete process.env.ANTHROPIC_API_KEY;
  }
  
  // Test files in order
  const testFiles = [
    '01-basic-sdk-mode.ts',
    '02-session-management.ts',
    '03-system-prompts.ts',
    '04-concurrent-execution.ts',
    '05-error-handling.ts',
    '06-performance.ts'
  ];
  
  const results: TestResult[] = [];
  const startTime = Date.now();
  
  // Run each test
  for (const testFile of testFiles) {
    const testPath = path.join(__dirname, 'tests', testFile);
    
    try {
      console.log(`${colors.blue}Running ${testFile}...${colors.reset}`);
      
      // Import and run the test
      const testModule: TestModule = await import(testPath);
      const result = await testModule.runTest();
      
      results.push(result);
      
      if (result.passed) {
        console.log(`${colors.green}✓ ${result.testName} - PASSED (${result.duration}ms)${colors.reset}`);
      } else {
        console.log(`${colors.red}✗ ${result.testName} - FAILED (${result.duration}ms)${colors.reset}`);
        if (result.error) {
          console.log(`  ${colors.gray}Error: ${result.error}${colors.reset}`);
        }
      }
      
      // Show test details
      if (result.details) {
        console.log(`  ${colors.gray}Details:${colors.reset}`);
        Object.entries(result.details).forEach(([key, value]) => {
          console.log(`    ${colors.gray}${key}: ${JSON.stringify(value)}${colors.reset}`);
        });
      }
      
      console.log(''); // Empty line between tests
      
    } catch (error) {
      console.error(`${colors.red}✗ Failed to run ${testFile}: ${error}${colors.reset}\n`);
      results.push({
        testName: testFile,
        passed: false,
        duration: 0,
        error: error instanceof Error ? error.message : String(error)
      });
    }
  }
  
  const totalDuration = Date.now() - startTime;
  
  // Generate summary
  console.log(`${colors.blue}═══════════════════════════════════════════════════════════════${colors.reset}`);
  console.log(`${colors.blue}                        Test Summary                            ${colors.reset}`);
  console.log(`${colors.blue}═══════════════════════════════════════════════════════════════${colors.reset}\n`);
  
  const passedTests = results.filter(r => r.passed).length;
  const failedTests = results.filter(r => !r.passed).length;
  const passRate = (passedTests / results.length) * 100;
  
  console.log(`Total Tests: ${results.length}`);
  console.log(`${colors.green}Passed: ${passedTests}${colors.reset}`);
  console.log(`${colors.red}Failed: ${failedTests}${colors.reset}`);
  console.log(`Pass Rate: ${passRate.toFixed(1)}%`);
  console.log(`Total Duration: ${(totalDuration / 1000).toFixed(2)} seconds\n`);
  
  // Generate detailed report
  const report = {
    timestamp: new Date().toISOString(),
    duration: totalDuration,
    summary: {
      total: results.length,
      passed: passedTests,
      failed: failedTests,
      passRate: `${passRate.toFixed(1)}%`
    },
    environment: {
      node: process.version,
      platform: process.platform,
      arch: process.arch,
      claudeAvailable
    },
    results: results.map(r => ({
      ...r,
      output: r.output ? r.output.substring(0, 500) + '...' : undefined // Truncate long outputs
    })),
    recommendations: generateRecommendations(results)
  };
  
  // Save report
  const reportPath = path.join(__dirname, '..', 'results', 'validation-report.json');
  await fs.mkdir(path.dirname(reportPath), { recursive: true });
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  console.log(`${colors.blue}Full report saved to: ${reportPath}${colors.reset}\n`);
  
  // Generate markdown report
  const markdownReport = generateMarkdownReport(report);
  const mdReportPath = path.join(__dirname, '..', 'results', 'validation-report.md');
  await fs.writeFile(mdReportPath, markdownReport);
  console.log(`${colors.blue}Markdown report saved to: ${mdReportPath}${colors.reset}\n`);
  
  // Exit with appropriate code
  if (failedTests > 0) {
    console.log(`${colors.red}❌ POC validation failed with ${failedTests} test(s) failing.${colors.reset}`);
    process.exit(1);
  } else {
    console.log(`${colors.green}✅ POC validation passed! All tests successful.${colors.reset}`);
    console.log(`${colors.green}   Claude CLI is ready for multi-agent system implementation.${colors.reset}`);
    process.exit(0);
  }
}

function generateRecommendations(results: TestResult[]): string[] {
  const recommendations: string[] = [];
  
  // Check each test result for specific issues
  results.forEach(result => {
    if (!result.passed) {
      switch (result.testName) {
        case 'Basic SDK Mode (-p flag)':
          recommendations.push('Verify Claude CLI is properly installed and the -p flag is supported');
          break;
        case 'Session Management':
          recommendations.push('Check session file permissions and --continue/--resume flag support');
          break;
        case 'System Prompts':
          recommendations.push('Ensure system prompt files are readable and properly formatted');
          break;
        case 'Concurrent Execution':
          recommendations.push('Consider implementing connection pooling or rate limiting for concurrent operations');
          break;
        case 'Error Handling':
          recommendations.push('Implement robust error recovery mechanisms in the agent system');
          break;
        case 'Performance Testing':
          recommendations.push('Monitor and optimize Claude CLI startup time and response latency');
          break;
      }
    }
  });
  
  // General recommendations based on results
  const performanceTest = results.find(r => r.testName === 'Performance Testing');
  if (performanceTest?.details?.avgStartupTime > 3000) {
    recommendations.push('Consider implementing session caching to reduce startup overhead');
  }
  
  if (results.filter(r => !r.passed).length > results.length / 2) {
    recommendations.push('Critical: Multiple test failures indicate fundamental compatibility issues');
  }
  
  if (recommendations.length === 0) {
    recommendations.push('All tests passed - system is ready for production implementation');
    recommendations.push('Consider implementing monitoring and alerting for production deployment');
  }
  
  return recommendations;
}

function generateMarkdownReport(report: any): string {
  const md: string[] = [];
  
  md.push('# Claude CLI POC Validation Report');
  md.push(`\nGenerated: ${new Date(report.timestamp).toLocaleString()}`);
  md.push(`\nDuration: ${(report.duration / 1000).toFixed(2)} seconds`);
  
  md.push('\n## Summary');
  md.push(`- **Total Tests**: ${report.summary.total}`);
  md.push(`- **Passed**: ${report.summary.passed}`);
  md.push(`- **Failed**: ${report.summary.failed}`);
  md.push(`- **Pass Rate**: ${report.summary.passRate}`);
  
  md.push('\n## Environment');
  md.push(`- **Node.js**: ${report.environment.node}`);
  md.push(`- **Platform**: ${report.environment.platform}`);
  md.push(`- **Architecture**: ${report.environment.arch}`);
  md.push(`- **Claude CLI Available**: ${report.environment.claudeAvailable ? 'Yes' : 'No'}`);
  
  md.push('\n## Test Results');
  
  report.results.forEach((result: TestResult) => {
    md.push(`\n### ${result.testName}`);
    md.push(`- **Status**: ${result.passed ? '✅ PASSED' : '❌ FAILED'}`);
    md.push(`- **Duration**: ${result.duration}ms`);
    
    if (result.error) {
      md.push(`- **Error**: ${result.error}`);
    }
    
    if (result.details) {
      md.push('\n**Details:**');
      Object.entries(result.details).forEach(([key, value]) => {
        md.push(`- ${key}: \`${JSON.stringify(value)}\``);
      });
    }
  });
  
  md.push('\n## Recommendations');
  report.recommendations.forEach((rec: string, i: number) => {
    md.push(`${i + 1}. ${rec}`);
  });
  
  md.push('\n## Conclusion');
  if (report.summary.failed === 0) {
    md.push('All POC tests passed successfully. The Claude CLI is validated and ready for the multi-agent system implementation.');
    md.push('\n### Next Steps:');
    md.push('1. Proceed with Step 1: TDD Infrastructure Setup');
    md.push('2. Implement core types and interfaces');
    md.push('3. Build the CLI Process Manager');
    md.push('4. Continue with remaining implementation steps');
  } else {
    md.push(`${report.summary.failed} test(s) failed. Please address the issues identified above before proceeding with implementation.`);
  }
  
  return md.join('\n');
}

// Run tests if executed directly
if (require.main === module) {
  runAllTests().catch(err => {
    console.error(`${colors.red}Unexpected error: ${err}${colors.reset}`);
    process.exit(1);
  });
}

// Export for potential reuse
export { runAllTests, TestResult };