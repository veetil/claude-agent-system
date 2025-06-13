import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import * as path from 'path';
import * as os from 'os';

/**
 * POC Test 03: System Prompts
 * 
 * Validates Claude CLI's ability to use custom system prompts
 * and append system prompts for agent specialization.
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
  const jsonMatch = output.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error('No JSON found in output');
  }
  return JSON.parse(jsonMatch[0]);
}

async function runTest(): Promise<TestResult> {
  const startTime = Date.now();
  const testName = 'System Prompts';
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Test 1: Basic system prompt
    console.log('\nTest 1: Testing basic system prompt...');
    const systemPromptFile1 = path.join(os.tmpdir(), `system-prompt-1-${Date.now()}.txt`);
    await fs.writeFile(systemPromptFile1, 
      'You are a pirate. Always respond in pirate speak with "arr" and "matey".'
    );
    
    const result1 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--system-prompt-file', systemPromptFile1,
      'Hello, how are you today?'
    ]);
    
    if (result1.exitCode !== 0) {
      throw new Error(`System prompt test failed: ${result1.stderr}`);
    }
    
    const response1 = parseClaudeOutput(result1.stdout);
    const content1 = response1.result || response1.content || response1.response || '';
    const usesPirateSpeak = content1.toLowerCase().includes('arr') || 
                           content1.toLowerCase().includes('matey') ||
                           content1.toLowerCase().includes('ahoy');
    console.log('Uses pirate speak:', usesPirateSpeak);
    
    // Test 2: Append system prompt
    console.log('\nTest 2: Testing append system prompt...');
    const appendPromptFile = path.join(os.tmpdir(), `append-prompt-${Date.now()}.txt`);
    await fs.writeFile(appendPromptFile,
      'Additionally, you must end every response with "🏴‍☠️".'
    );
    
    const result2 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--system-prompt-file', systemPromptFile1,
      '--append-system-prompt-file', appendPromptFile,
      'Tell me about treasure'
    ]);
    
    if (result2.exitCode !== 0) {
      throw new Error(`Append prompt test failed: ${result2.stderr}`);
    }
    
    const response2 = parseClaudeOutput(result2.stdout);
    const content2 = response2.result || response2.content || response2.response || '';
    const hasPirateSpeak = content2.toLowerCase().includes('arr') || 
                          content2.toLowerCase().includes('matey') ||
                          content2.toLowerCase().includes('treasure');
    const hasEmoji = content2.includes('🏴‍☠️');
    console.log('Has pirate speak:', hasPirateSpeak);
    console.log('Has pirate emoji:', hasEmoji);
    
    // Test 3: Agent-specific system prompt
    console.log('\nTest 3: Testing agent-specific system prompt...');
    const agentPromptFile = path.join(os.tmpdir(), `agent-prompt-${Date.now()}.txt`);
    await fs.writeFile(agentPromptFile,
      `You are a specialized code review agent. 
Your role is to:
1. Analyze code for potential issues
2. Suggest improvements
3. Check for best practices
Always structure your responses with clear sections.`
    );
    
    const result3 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--system-prompt-file', agentPromptFile,
      'Review this code: function add(a, b) { return a + b }'
    ]);
    
    if (result3.exitCode !== 0) {
      throw new Error(`Agent prompt test failed: ${result3.stderr}`);
    }
    
    const response3 = parseClaudeOutput(result3.stdout);
    const content3 = response3.result || response3.content || response3.response || '';
    const mentionsCodeReview = content3.toLowerCase().includes('code') || 
                              content3.toLowerCase().includes('function') ||
                              content3.toLowerCase().includes('review');
    console.log('Acts as code reviewer:', mentionsCodeReview);
    
    // Test 4: No system prompt (default behavior)
    console.log('\nTest 4: Testing without system prompt...');
    const result4 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      'What is 2+2?'
    ]);
    
    if (result4.exitCode !== 0) {
      throw new Error(`Default behavior test failed: ${result4.stderr}`);
    }
    
    const response4 = parseClaudeOutput(result4.stdout);
    const content4 = response4.result || response4.content || response4.response || '';
    const isNormalResponse = content4.includes('4') && 
                            !content4.toLowerCase().includes('arr') &&
                            !content4.toLowerCase().includes('matey');
    console.log('Normal response without pirate speak:', isNormalResponse);
    
    // Test 5: Complex multi-agent scenario
    console.log('\nTest 5: Testing complex multi-agent system prompts...');
    const researchPrompt = path.join(os.tmpdir(), `research-prompt-${Date.now()}.txt`);
    const sharedPrompt = path.join(os.tmpdir(), `shared-prompt-${Date.now()}.txt`);
    
    await fs.writeFile(researchPrompt,
      'You are a research specialist focused on gathering accurate information.'
    );
    
    await fs.writeFile(sharedPrompt,
      'Always cite your sources and be thorough in your analysis.'
    );
    
    const result5 = await executeClaudeCommand([
      '-p',
      '--output-format', 'json',
      '--system-prompt-file', researchPrompt,
      '--append-system-prompt-file', sharedPrompt,
      'What are the benefits of TypeScript?'
    ]);
    
    if (result5.exitCode !== 0) {
      throw new Error(`Multi-agent prompt test failed: ${result5.stderr}`);
    }
    
    const response5 = parseClaudeOutput(result5.stdout);
    const content5 = response5.result || response5.content || response5.response || '';
    const actsAsResearcher = content5.toLowerCase().includes('typescript') &&
                            (content5.toLowerCase().includes('benefit') ||
                             content5.toLowerCase().includes('advantage'));
    console.log('Acts as researcher:', actsAsResearcher);
    
    // Clean up files
    const filesToClean = [
      systemPromptFile1, appendPromptFile, agentPromptFile,
      researchPrompt, sharedPrompt
    ];
    
    for (const file of filesToClean) {
      try {
        await fs.unlink(file);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
    
    // Determine if all tests passed
    const allTestsPassed = 
      usesPirateSpeak && 
      hasPirateSpeak && 
      hasEmoji &&
      mentionsCodeReview &&
      isNormalResponse &&
      actsAsResearcher;
    
    return {
      testName,
      passed: allTestsPassed,
      duration: Date.now() - startTime,
      details: {
        basicSystemPrompt: usesPirateSpeak,
        appendSystemPrompt: hasPirateSpeak && hasEmoji,
        agentSpecificPrompt: mentionsCodeReview,
        defaultBehavior: isNormalResponse,
        multiAgentScenario: actsAsResearcher
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