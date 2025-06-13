#!/usr/bin/env ts-node

/**
 * Quick test to verify actual Claude CLI behavior
 */

import { spawn } from 'child_process';

async function testClaude() {
  console.log('Testing Claude CLI with actual flags...\n');
  
  // Test 1: Basic print mode
  console.log('Test 1: Basic print mode with JSON output');
  const test1 = spawn('claude', [
    '--print',
    '--output-format', 'json',
    'Say "Hello from Claude" and nothing else'
  ], { 
    shell: true,
    env: { ...process.env, ANTHROPIC_API_KEY: undefined }
  });
  
  let output1 = '';
  test1.stdout.on('data', (data) => {
    output1 += data.toString();
  });
  
  test1.stderr.on('data', (data) => {
    console.error('Error:', data.toString());
  });
  
  test1.on('close', (code) => {
    console.log('Exit code:', code);
    console.log('Output:', output1.substring(0, 200) + '...');
    console.log('');
    
    // Test 2: Check if output is JSON
    try {
      const parsed = JSON.parse(output1);
      console.log('JSON parsing successful!');
      console.log('Keys:', Object.keys(parsed));
    } catch (e) {
      console.log('Failed to parse JSON:', e instanceof Error ? e.message : String(e));
    }
  });
  
  // Give it 10 seconds max
  setTimeout(() => {
    test1.kill();
    console.log('Test timed out');
  }, 10000);
}

testClaude().catch(console.error);