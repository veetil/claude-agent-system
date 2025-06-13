#!/usr/bin/env ts-node

import { ClaudeWrapper } from './src/utils/claude-wrapper';

async function test() {
  console.log('=== Testing Session ID Tracking ===\n');
  
  const claude = new ClaudeWrapper({
    outputFormat: 'json',
    timeout: 30000
  });
  
  // Step 1: Create initial session
  console.log('Step 1: Creating session with "My name is Alice"');
  const { sessionId: sessionId1, response: response1 } = await claude.createSession(
    'My name is Alice. Please remember this.'
  );
  console.log('Response:', response1.result);
  console.log('Session ID 1:', sessionId1);
  
  // Step 2: Continue with session ID 1
  console.log('\nStep 2: Continuing with session ID 1');
  const response2 = await claude.continueSession(
    sessionId1,
    'What is my name?'
  );
  if (!response2.success) {
    console.log('Error:', response2.error);
    console.log('Metadata:', response2.metadata);
  }
  console.log('Response:', response2.result);
  console.log('Session ID 2:', response2.sessionId);
  console.log('Remembers name?', response2.result?.includes('Alice'));
  
  // Step 3: Continue with the NEW session ID from step 2
  console.log('\nStep 3: Continuing with session ID 2 (the updated one)');
  const response3 = await claude.continueSession(
    response2.sessionId!,
    'Tell me again, what was the name I told you?'
  );
  console.log('Response:', response3.result);
  console.log('Session ID 3:', response3.sessionId);
  console.log('Still remembers?', response3.result?.includes('Alice'));
  
  // Step 4: Try using the OLD session ID 1 again
  console.log('\nStep 4: Using OLD session ID 1 (should only know up to first message)');
  const response4 = await claude.continueSession(
    sessionId1,
    'Do you remember me asking you what my name was?'
  );
  console.log('Response:', response4.result);
  console.log('Acknowledges previous questions?', 
    response4.result?.toLowerCase().includes('ask') || 
    response4.result?.toLowerCase().includes('no') ||
    response4.result?.toLowerCase().includes("haven't")
  );
}

test().catch(console.error);