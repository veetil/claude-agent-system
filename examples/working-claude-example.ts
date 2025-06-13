#!/usr/bin/env ts-node

/**
 * Working example of Claude CLI usage based on actual behavior
 */

import { spawn } from 'child_process';

interface ClaudeResponse {
  type: string;
  subtype: string;
  is_error: boolean;
  result: string;
  session_id: string;
  total_cost_usd: number;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

async function callClaude(prompt: string, sessionId?: string): Promise<ClaudeResponse> {
  return new Promise((resolve, reject) => {
    const args = ['--print', '--output-format', 'json'];
    
    // Add session resumption if provided
    if (sessionId) {
      args.push('-r', sessionId);
    }
    
    const claude = spawn('claude', args, {
      shell: true,
      env: { ...process.env, ANTHROPIC_API_KEY: undefined }
    });
    
    let output = '';
    let error = '';
    
    claude.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    claude.stderr.on('data', (data) => {
      error += data.toString();
    });
    
    claude.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Claude exited with code ${code}: ${error}`));
        return;
      }
      
      try {
        const response = JSON.parse(output) as ClaudeResponse;
        resolve(response);
      } catch (e) {
        reject(new Error(`Failed to parse Claude response: ${e}`));
      }
    });
    
    // Send the prompt via stdin
    claude.stdin.write(prompt);
    claude.stdin.end();
    
    // Timeout after 30 seconds
    setTimeout(() => {
      claude.kill();
      reject(new Error('Claude request timed out'));
    }, 30000);
  });
}

async function runDemo() {
  try {
    console.log('=== Claude CLI Working Example ===\n');
    
    // Test 1: Simple question
    console.log('1. Simple question:');
    const response1 = await callClaude('What is 2+2? Reply with just the number.');
    console.log(`Result: ${response1.result}`);
    console.log(`Session ID: ${response1.session_id}`);
    console.log(`Cost: $${response1.total_cost_usd?.toFixed(6) || 'N/A'}\n`);
    
    // Test 2: Continue conversation
    console.log('2. Continuing conversation:');
    const response2 = await callClaude(
      'What was my previous question about?',
      response1.session_id
    );
    console.log(`Result: ${response2.result}`);
    console.log(`Same session: ${response2.session_id === response1.session_id}\n`);
    
    // Test 3: Agent-like behavior with embedded system prompt
    console.log('3. Agent with embedded system prompt:');
    const agentPrompt = `You are a code review specialist. Your responses should be brief and focused on code quality.

Review this function:
function add(a, b) { return a + b }

Provide one suggestion for improvement.`;
    
    const response3 = await callClaude(agentPrompt);
    console.log(`Code Review: ${response3.result}`);
    console.log(`Tokens used: ${response3.usage.input_tokens} in, ${response3.usage.output_tokens} out\n`);
    
    console.log('=== Demo Complete ===');
    
  } catch (error) {
    console.error('Demo failed:', error);
  }
}

// Run the demo
if (require.main === module) {
  runDemo();
}

export { callClaude, ClaudeResponse };