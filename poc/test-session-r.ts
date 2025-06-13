#!/usr/bin/env ts-node

import { spawn } from 'child_process';

async function runCommand(args: string[], input: string): Promise<any> {
  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';
    
    const claude = spawn('claude', args, { shell: true });
    
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
    
    claude.stdin.write(input);
    claude.stdin.end();
  });
}

async function test() {
  console.log('=== Testing -r flag with session IDs ===\n');
  
  // Step 1: Create initial session
  console.log('Step 1: Creating session with "My name is Alice"');
  const response1 = await runCommand(
    ['--print', '--output-format', 'json'],
    'My name is Alice. Please remember this.'
  );
  console.log('Response:', response1.result);
  console.log('Session ID:', response1.session_id);
  
  // Step 2: Continue with -r and the session ID
  console.log('\nStep 2: Continuing with -r', response1.session_id);
  const response2 = await runCommand(
    ['--print', '--output-format', 'json', '-r', response1.session_id],
    'What is my name?'
  );
  if (response2.error) {
    console.log('Error:', response2.stderr);
    console.log('Exit code:', response2.code);
  } else {
    console.log('Response:', response2.result);
    console.log('Session ID:', response2.session_id);
    console.log('Remembers name?', response2.result?.includes('Alice'));
  }
  
  // Step 3: Try again with the original session ID
  console.log('\nStep 3: Continuing again with original session ID');
  const response3 = await runCommand(
    ['--print', '--output-format', 'json', '-r', response1.session_id],
    'Can you remind me what name I told you?'
  );
  console.log('Response:', response3.result);
  console.log('Still remembers?', response3.result?.includes('Alice'));
  
  // Step 4: Create a new separate session
  console.log('\nStep 4: Creating new session with different name');
  const response4 = await runCommand(
    ['--print', '--output-format', 'json'],
    'My name is Bob. Please remember this.'
  );
  console.log('Response:', response4.result);
  console.log('New Session ID:', response4.session_id);
  
  // Step 5: Verify isolation - ask for name in Bob's session
  console.log('\nStep 5: Checking Bob session');
  const response5 = await runCommand(
    ['--print', '--output-format', 'json', '-r', response4.session_id],
    'What is my name?'
  );
  console.log('Response:', response5.result);
  console.log('Says Bob?', response5.result?.includes('Bob'));
  console.log('Says Alice?', response5.result?.includes('Alice'));
}

test().catch(console.error);