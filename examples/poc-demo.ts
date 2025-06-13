#!/usr/bin/env ts-node

/**
 * POC Demo - Simple example showing how to use Claude CLI in SDK mode
 * 
 * This demonstrates the basic capabilities that will power our multi-agent system.
 */

import { ClaudeWrapper } from '../poc/src/utils/claude-wrapper';

async function runDemo() {
  console.log('=== Claude Agent System - POC Demo ===\n');
  
  // Create a Claude wrapper instance
  const claude = new ClaudeWrapper({
    outputFormat: 'json',
    timeout: 30000
  });
  
  // Example 1: Simple execution
  console.log('1. Simple Execution:');
  const result1 = await claude.execute('What is 2+2? Reply with just the number.');
  console.log(`Result: ${result1.result}`);
  console.log(`Success: ${result1.success}\n`);
  
  // Example 2: Session management
  console.log('2. Session Management:');
  const { sessionId, response: session1 } = await claude.createSession(
    'Remember that my favorite color is blue.',
    { outputFormat: 'json' }
  );
  console.log(`Session created: ${sessionId}`);
  
  const session2 = await claude.continueSession(
    sessionId,
    'What is my favorite color?',
    { outputFormat: 'json' }
  );
  console.log(`Claude remembers: ${session2.result}\n`);
  
  // Example 3: Agent specialization with system prompts
  console.log('3. Agent Specialization:');
  const codeAgent = new ClaudeWrapper({
    outputFormat: 'json',
    systemPrompt: 'You are a code review specialist. Analyze code for quality and suggest improvements.'
  });
  
  const codeReview = await codeAgent.execute(
    'Review this: function add(a, b) { return a + b }'
  );
  console.log(`Code Review: ${codeReview.result}\n`);
  
  // Example 4: Concurrent agents
  console.log('4. Concurrent Agents:');
  const agents = [
    { id: 'researcher', prompt: 'What are the benefits of TypeScript? Be brief.' },
    { id: 'coder', prompt: 'Write a TypeScript interface for a User object.' },
    { id: 'tester', prompt: 'What should we test in a login function?' }
  ];
  
  const results = await claude.executeConcurrent(agents);
  
  results.forEach((result, id) => {
    console.log(`${id}: ${result.success ? '✓' : '✗'}`);
  });
  
  console.log('\n=== Demo Complete ===');
  console.log('This POC demonstrates all the key features needed for our multi-agent system:');
  console.log('- SDK mode with JSON output');
  console.log('- Session management for conversation continuity');
  console.log('- System prompts for agent specialization');
  console.log('- Concurrent execution for multiple agents');
}

// Note: This demo requires Claude CLI to be installed and accessible
if (require.main === module) {
  console.log('Note: This demo requires Claude CLI to be installed and accessible.\n');
  
  runDemo().catch(err => {
    console.error('Demo failed:', err.message);
    console.error('\nMake sure:');
    console.error('1. Claude CLI is installed');
    console.error('2. You are authenticated');
    console.error('3. ANTHROPIC_API_KEY is not set');
  });
}

export { runDemo };