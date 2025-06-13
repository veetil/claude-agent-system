#!/usr/bin/env ts-node

import { query, ClaudeCodeOptions } from '@anthropic-ai/claude-code';

interface TestResult {
  name: string;
  passed: boolean;
  details?: any;
}

/**
 * Test basic Claude Code SDK functionality
 */
async function testBasicQuery(): Promise<TestResult> {
  console.log('=== Test 1: Basic Query ===\n');
  
  try {
    const messages: string[] = [];
    
    for await (const message of query({
      prompt: 'Write a simple TypeScript function that adds two numbers',
      options: { maxTurns: 1 }
    })) {
      if (message.type === 'text') {
        messages.push(message.content);
      }
    }
    
    const response = messages.join('\n');
    console.log('Response:', response);
    
    const hasFunction = response.includes('function') || response.includes('=>');
    const hasAddition = response.includes('+');
    
    return {
      name: 'Basic Query',
      passed: hasFunction && hasAddition,
      details: { hasFunction, hasAddition }
    };
  } catch (error) {
    return {
      name: 'Basic Query',
      passed: false,
      details: { error: error.message }
    };
  }
}

/**
 * Test system prompts for agent specialization
 */
async function testSystemPrompts(): Promise<TestResult> {
  console.log('\n=== Test 2: System Prompts ===\n');
  
  try {
    // Test with pirate system prompt
    const pirateMessages: string[] = [];
    
    for await (const message of query({
      prompt: 'Hello, how are you today?',
      options: {
        maxTurns: 1,
        systemPrompt: 'You are a helpful pirate. Always respond in pirate speak with "arr" and "matey".'
      }
    })) {
      if (message.type === 'text') {
        pirateMessages.push(message.content);
      }
    }
    
    const pirateResponse = pirateMessages.join('\n');
    console.log('Pirate response:', pirateResponse);
    
    const usesPirateSpeak = 
      pirateResponse.toLowerCase().includes('arr') || 
      pirateResponse.toLowerCase().includes('matey') ||
      pirateResponse.toLowerCase().includes('ahoy');
    
    return {
      name: 'System Prompts',
      passed: usesPirateSpeak,
      details: { usesPirateSpeak, response: pirateResponse.substring(0, 100) + '...' }
    };
  } catch (error) {
    return {
      name: 'System Prompts',
      passed: false,
      details: { error: error.message }
    };
  }
}

/**
 * Test multi-turn conversations
 */
async function testMultiTurn(): Promise<TestResult> {
  console.log('\n=== Test 3: Multi-turn Conversation ===\n');
  
  try {
    const turns: string[] = [];
    let turnCount = 0;
    
    for await (const message of query({
      prompt: `Create a simple calculator class in TypeScript.
First show the class structure.
Then add basic operations (add, subtract).
Finally add error handling.`,
      options: { maxTurns: 3 }
    })) {
      if (message.type === 'text') {
        turnCount++;
        turns.push(`Turn ${turnCount}: ${message.content}`);
      }
    }
    
    const fullResponse = turns.join('\n\n');
    console.log('Multi-turn response:', fullResponse.substring(0, 200) + '...');
    
    const hasClass = fullResponse.includes('class');
    const hasOperations = fullResponse.includes('add') && fullResponse.includes('subtract');
    const hasErrorHandling = fullResponse.includes('throw') || fullResponse.includes('Error');
    const hasMultipleTurns = turnCount > 1;
    
    return {
      name: 'Multi-turn Conversation',
      passed: hasClass && hasOperations && hasErrorHandling && hasMultipleTurns,
      details: { 
        turnCount, 
        hasClass, 
        hasOperations, 
        hasErrorHandling 
      }
    };
  } catch (error) {
    return {
      name: 'Multi-turn Conversation',
      passed: false,
      details: { error: error.message }
    };
  }
}

/**
 * Test concurrent agent execution
 */
async function testConcurrentAgents(): Promise<TestResult> {
  console.log('\n=== Test 4: Concurrent Agents ===\n');
  
  try {
    const agentTasks = [
      { id: 'agent-1', prompt: 'Write a function to reverse a string' },
      { id: 'agent-2', prompt: 'Write a function to check if a number is prime' },
      { id: 'agent-3', prompt: 'Write a function to calculate factorial' }
    ];
    
    const startTime = Date.now();
    
    // Run all agents concurrently
    const results = await Promise.all(
      agentTasks.map(async (task) => {
        const messages: string[] = [];
        const agentStart = Date.now();
        
        for await (const message of query({
          prompt: task.prompt,
          options: { maxTurns: 1 }
        })) {
          if (message.type === 'text') {
            messages.push(message.content);
          }
        }
        
        return {
          id: task.id,
          response: messages.join('\n'),
          duration: Date.now() - agentStart,
          success: messages.length > 0 && messages[0].includes('function')
        };
      })
    );
    
    const totalDuration = Date.now() - startTime;
    const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / results.length;
    const successCount = results.filter(r => r.success).length;
    
    console.log(`Total time: ${totalDuration}ms`);
    console.log(`Average agent time: ${avgDuration.toFixed(0)}ms`);
    console.log(`Successful agents: ${successCount}/${results.length}`);
    console.log(`Speedup: ${(avgDuration * results.length / totalDuration).toFixed(2)}x`);
    
    return {
      name: 'Concurrent Agents',
      passed: successCount === results.length,
      details: {
        totalDuration,
        avgDuration,
        successCount,
        agentCount: results.length
      }
    };
  } catch (error) {
    return {
      name: 'Concurrent Agents',
      passed: false,
      details: { error: error.message }
    };
  }
}

/**
 * Main test runner
 */
async function main() {
  console.log('Claude Code SDK Test Suite');
  console.log('=' * 50 + '\n');
  
  // Check API key
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error('ERROR: ANTHROPIC_API_KEY environment variable not set');
    process.exit(1);
  }
  
  const tests = [
    testBasicQuery,
    testSystemPrompts,
    testMultiTurn,
    testConcurrentAgents
  ];
  
  const results: TestResult[] = [];
  
  for (const test of tests) {
    try {
      const result = await test();
      results.push(result);
    } catch (error) {
      results.push({
        name: test.name,
        passed: false,
        details: { error: error.message }
      });
    }
  }
  
  // Summary
  console.log('\n' + '=' * 50);
  console.log('TEST SUMMARY');
  console.log('=' * 50 + '\n');
  
  for (const result of results) {
    const status = result.passed ? '✅ PASSED' : '❌ FAILED';
    console.log(`${result.name}: ${status}`);
    if (result.details) {
      console.log(`  Details: ${JSON.stringify(result.details)}`);
    }
  }
  
  const passedCount = results.filter(r => r.passed).length;
  console.log(`\nTotal: ${passedCount}/${results.length} passed`);
  
  // Save results
  const fs = require('fs');
  fs.writeFileSync('claude-code-sdk-results.json', JSON.stringify({
    timestamp: new Date().toISOString(),
    results,
    summary: {
      total: results.length,
      passed: passedCount,
      failed: results.length - passedCount
    }
  }, null, 2));
  
  process.exit(passedCount === results.length ? 0 : 1);
}

// Run tests
main().catch(console.error);