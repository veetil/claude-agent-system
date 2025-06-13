#!/usr/bin/env ts-node

/**
 * Claude CLI SDK - Using Claude CLI in print mode as an SDK
 * Based on the documentation at https://docs.anthropic.com/en/docs/claude-code/sdk
 */

import { spawn } from 'child_process';
import { EventEmitter } from 'events';

interface ClaudeResponse {
  type: string;
  subtype: string;
  is_error: boolean;
  duration_ms: number;
  result: string;
  session_id: string;
  total_cost_usd: number;
  usage: {
    input_tokens: number;
    output_tokens: number;
    cache_creation_input_tokens?: number;
    cache_read_input_tokens?: number;
  };
}

class ClaudeSDK extends EventEmitter {
  private sessions: Map<string, string> = new Map();
  
  /**
   * Execute a single prompt using Claude CLI in print mode
   */
  async query(prompt: string, options?: {
    outputFormat?: 'json' | 'stream-json';
    sessionId?: string;
    systemPrompt?: string;
  }): Promise<ClaudeResponse> {
    const args = ['-p', prompt];
    
    if (options?.outputFormat) {
      args.push('--output-format', options.outputFormat);
    }
    
    if (options?.sessionId) {
      args.push('-r', options.sessionId);
    }
    
    return new Promise((resolve, reject) => {
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
            const response = JSON.parse(stdout);
            // Track session IDs
            if (response.session_id) {
              this.sessions.set('last', response.session_id);
              if (options?.sessionId) {
                this.sessions.set(options.sessionId, response.session_id);
              }
            }
            resolve(response);
          } catch (e) {
            reject(new Error(`Failed to parse response: ${stdout}`));
          }
        } else {
          reject(new Error(stderr || `Process exited with code ${code}`));
        }
      });
    });
  }
  
  /**
   * Execute a prompt with a system prompt embedded
   */
  async queryWithSystem(systemPrompt: string, userPrompt: string, options?: {
    outputFormat?: 'json' | 'stream-json';
    sessionId?: string;
  }): Promise<ClaudeResponse> {
    // Embed system prompt in the user message
    const combinedPrompt = `${systemPrompt}\n\nUser: ${userPrompt}`;
    return this.query(combinedPrompt, options);
  }
  
  /**
   * Continue a conversation using the most recent session ID
   */
  async continueConversation(prompt: string, sessionId: string): Promise<ClaudeResponse> {
    return this.query(prompt, { 
      outputFormat: 'json',
      sessionId 
    });
  }
  
  /**
   * Get the current session ID (updated after each call)
   */
  getCurrentSessionId(originalId?: string): string | undefined {
    if (originalId && this.sessions.has(originalId)) {
      return this.sessions.get(originalId);
    }
    return this.sessions.get('last');
  }
}

// Test the SDK
async function testClaudeSDK() {
  console.log('=== Testing Claude CLI SDK ===\n');
  
  const sdk = new ClaudeSDK();
  
  try {
    // Test 1: Basic query
    console.log('Test 1: Basic Query');
    const response1 = await sdk.query('Say hello and tell me the current date', {
      outputFormat: 'json'
    });
    console.log('Response:', response1.result);
    console.log('Session ID:', response1.session_id);
    console.log('Cost:', response1.total_cost_usd);
    
    // Test 2: Continue conversation
    console.log('\nTest 2: Continue Conversation');
    const response2 = await sdk.continueConversation(
      'What did I just ask you?',
      response1.session_id
    );
    console.log('Response:', response2.result);
    console.log('New Session ID:', response2.session_id);
    console.log('References previous:', response2.result.toLowerCase().includes('hello') || response2.result.toLowerCase().includes('date'));
    
    // Test 3: System prompt
    console.log('\nTest 3: System Prompt (Pirate)');
    const response3 = await sdk.queryWithSystem(
      'You are a helpful pirate. Always respond in pirate speak.',
      'How do I write a for loop in Python?',
      { outputFormat: 'json' }
    );
    console.log('Response:', response3.result);
    console.log('Uses pirate speak:', response3.result.toLowerCase().includes('arr') || response3.result.toLowerCase().includes('matey'));
    
  } catch (error) {
    console.error('Error:', error);
  }
}

// Export the SDK
export { ClaudeSDK, ClaudeResponse };

// Run test if executed directly
if (require.main === module) {
  testClaudeSDK();
}