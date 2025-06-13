#!/usr/bin/env ts-node

import { spawn } from 'child_process';

async function runCommandNoStdin(args: string[]): Promise<any> {
  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';
    
    const claude = spawn('claude', args, { shell: false });
    
    claude.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    claude.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    claude.on('close', (code) => {
      if (code === 0 && stdout) {
        try {
          const parsed = JSON.parse(stdout);
          resolve(parsed);
        } catch (e) {
          resolve({ stdout, stderr, code });
        }
      } else {
        resolve({ stdout, stderr, code, error: true });
      }
    });
  });
}

async function test() {
  console.log('=== Testing without stdin ===\n');
  
  // Step 1: Create session by passing prompt as argument
  console.log('Step 1: Create session');
  const response1 = await runCommandNoStdin([
    '-p', 'my favorite animal is cat', '--output-format', 'json'
  ]);
  console.log('Result:', response1.result);
  console.log('Session ID:', response1.session_id);
  
  // Step 2: Continue with -r
  console.log('\nStep 2: Continue with -r');
  const response2 = await runCommandNoStdin([
    '-p', 'what is my favorite animal?', '--output-format', 'json', 
    '-r', response1.session_id
  ]);
  
  if (response2.error) {
    console.log('Error:', response2.stderr);
  } else {
    console.log('Result:', response2.result);
    console.log('New Session ID:', response2.session_id);
    console.log('Remembers?', response2.result?.includes('cat'));
  }
}

test().catch(console.error);