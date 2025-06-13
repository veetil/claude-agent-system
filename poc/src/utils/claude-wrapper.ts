import { spawn, ChildProcess } from 'child_process';
import { EventEmitter } from 'events';

/**
 * Claude CLI Wrapper Utility
 * 
 * Updated to work with actual Claude CLI behavior:
 * - Uses stdin/stdout for communication
 * - Tracks session IDs from responses
 * - Embeds system prompts in messages
 */

export interface ClaudeOptions {
  outputFormat?: 'text' | 'json' | 'stream-json';
  sessionId?: string;
  continueLastSession?: boolean;
  model?: string;
  allowedTools?: string[];
  disallowedTools?: string[];
  addDirs?: string[];
  timeout?: number;
  systemPrompt?: string; // Will be embedded in the message
}

export interface ClaudeResponse {
  success: boolean;
  result?: any;
  error?: string;
  sessionId?: string;
  metadata?: {
    duration: number;
    exitCode: number;
    stdout: string;
    stderr: string;
    cost?: number;
    usage?: {
      input_tokens: number;
      output_tokens: number;
    };
  };
}

interface RawClaudeResponse {
  type: string;
  subtype: string;
  is_error: boolean;
  result?: string;
  session_id?: string;
  total_cost_usd?: number;
  duration_ms?: number;
  usage?: {
    input_tokens: number;
    output_tokens: number;
  };
}

export class ClaudeWrapper extends EventEmitter {
  private defaultTimeout = 30000;
  private sessionIds: Map<string, string> = new Map();
  
  constructor(private defaultOptions?: ClaudeOptions) {
    super();
  }
  
  /**
   * Execute a Claude command with the given prompt and options
   */
  async execute(prompt: string, options?: ClaudeOptions): Promise<ClaudeResponse> {
    const startTime = Date.now();
    const opts = { ...this.defaultOptions, ...options };
    
    // Embed system prompt if provided
    const finalPrompt = opts.systemPrompt 
      ? `${opts.systemPrompt}\n\n${prompt}`
      : prompt;
    
    try {
      const args = this.buildArgs(opts);
      const result = await this.runCommand(finalPrompt, args, opts);
      
      // Parse response if JSON format
      if (opts.outputFormat === 'json') {
        try {
          const parsed = JSON.parse(result.stdout) as RawClaudeResponse;
          
          // Store session ID if present
          if (parsed.session_id) {
            this.sessionIds.set('last', parsed.session_id);
          }
          
          return {
            success: !parsed.is_error,
            result: parsed.result,
            sessionId: parsed.session_id,
            error: parsed.is_error ? result.stderr : undefined,
            metadata: {
              duration: Date.now() - startTime,
              exitCode: result.exitCode,
              stdout: result.stdout,
              stderr: result.stderr,
              cost: parsed.total_cost_usd,
              usage: parsed.usage
            }
          };
        } catch (e) {
          // If JSON parsing fails, return raw output
          return {
            success: result.exitCode === 0,
            result: result.stdout,
            error: result.exitCode !== 0 ? result.stderr : undefined,
            metadata: {
              duration: Date.now() - startTime,
              exitCode: result.exitCode,
              stdout: result.stdout,
              stderr: result.stderr
            }
          };
        }
      }
      
      // For non-JSON output
      return {
        success: result.exitCode === 0,
        result: result.stdout,
        error: result.exitCode !== 0 ? result.stderr : undefined,
        metadata: {
          duration: Date.now() - startTime,
          ...result
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        metadata: {
          duration: Date.now() - startTime,
          exitCode: -1,
          stdout: '',
          stderr: error instanceof Error ? error.message : String(error)
        }
      };
    }
  }
  
  /**
   * Create a new session and return the session ID
   */
  async createSession(
    initialPrompt: string,
    options?: ClaudeOptions
  ): Promise<{ sessionId: string; response: ClaudeResponse }> {
    const response = await this.execute(initialPrompt, {
      ...options,
      outputFormat: 'json' // Force JSON to get session ID
    });
    
    const sessionId = response.sessionId || 'unknown';
    if (sessionId !== 'unknown') {
      this.sessionIds.set(sessionId, sessionId);
      this.sessionIds.set('last', sessionId);
    }
    
    return {
      sessionId,
      response
    };
  }
  
  /**
   * Continue an existing session
   * Note: This returns a new session ID that must be used for subsequent calls
   */
  async continueSession(
    sessionId: string,
    prompt: string,
    options?: ClaudeOptions
  ): Promise<ClaudeResponse> {
    const response = await this.execute(prompt, {
      ...options,
      sessionId
    });
    
    // Update our stored session ID if we got a new one
    if (response.sessionId && response.success) {
      this.sessionIds.set(sessionId, response.sessionId);
      this.sessionIds.set('last', response.sessionId);
    }
    
    return response;
  }
  
  /**
   * Continue the last session
   */
  async continueLastSession(
    prompt: string,
    options?: ClaudeOptions
  ): Promise<ClaudeResponse> {
    return this.execute(prompt, {
      ...options,
      continueLastSession: true
    });
  }
  
  /**
   * Execute multiple prompts in sequence with the same session
   */
  async executeSequence(
    prompts: string[],
    options?: ClaudeOptions
  ): Promise<ClaudeResponse[]> {
    const results: ClaudeResponse[] = [];
    
    // First prompt creates the session
    const first = await this.execute(prompts[0], {
      ...options,
      outputFormat: 'json'
    });
    results.push(first);
    
    // Get session ID from first response
    const sessionId = first.sessionId;
    
    // Continue with subsequent prompts
    for (let i = 1; i < prompts.length; i++) {
      const result = await this.execute(prompts[i], {
        ...options,
        sessionId,
        outputFormat: 'json'
      });
      results.push(result);
    }
    
    return results;
  }
  
  /**
   * Execute multiple prompts concurrently with separate sessions
   */
  async executeConcurrent(
    prompts: Array<{ id: string; prompt: string; options?: ClaudeOptions }>
  ): Promise<Map<string, ClaudeResponse>> {
    const results = new Map<string, ClaudeResponse>();
    
    const promises = prompts.map(async ({ id, prompt, options }) => {
      const response = await this.execute(prompt, options);
      results.set(id, response);
    });
    
    await Promise.all(promises);
    return results;
  }
  
  /**
   * Get the last session ID
   */
  getLastSessionId(): string | undefined {
    return this.sessionIds.get('last');
  }
  
  /**
   * Build command line arguments from options
   */
  private buildArgs(options: ClaudeOptions): string[] {
    const args: string[] = ['--print']; // Always use print mode for SDK
    
    if (options.outputFormat) {
      args.push('--output-format', options.outputFormat);
    }
    
    if (options.sessionId) {
      args.push('-r', options.sessionId);
    } else if (options.continueLastSession) {
      args.push('-c');
    }
    
    if (options.model) {
      args.push('--model', options.model);
    }
    
    if (options.allowedTools && options.allowedTools.length > 0) {
      args.push('--allowedTools', options.allowedTools.join(','));
    }
    
    if (options.disallowedTools && options.disallowedTools.length > 0) {
      args.push('--disallowedTools', options.disallowedTools.join(','));
    }
    
    if (options.addDirs && options.addDirs.length > 0) {
      options.addDirs.forEach(dir => {
        args.push('--add-dir', dir);
      });
    }
    
    return args;
  }
  
  /**
   * Run the Claude command and capture output
   */
  private runCommand(
    prompt: string,
    args: string[],
    options: ClaudeOptions
  ): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    return new Promise((resolve, reject) => {
      let stdout = '';
      let stderr = '';
      
      // Prepare environment
      const env = { ...process.env };
      // Don't delete ANTHROPIC_API_KEY - it might be needed for session storage
      
      const claude = spawn('claude', args, {
        env,
        shell: false
      });
      
      // Emit process started event
      this.emit('processStarted', { pid: claude.pid, args });
      
      claude.stdout.on('data', (data) => {
        const chunk = data.toString();
        stdout += chunk;
        this.emit('stdout', chunk);
      });
      
      claude.stderr.on('data', (data) => {
        const chunk = data.toString();
        stderr += chunk;
        this.emit('stderr', chunk);
      });
      
      claude.on('close', (code) => {
        this.emit('processEnded', { pid: claude.pid, exitCode: code });
        resolve({ stdout, stderr, exitCode: code || 0 });
      });
      
      claude.on('error', (err) => {
        this.emit('processError', { pid: claude.pid, error: err });
        reject(err);
      });
      
      // Send prompt via stdin
      claude.stdin.write(prompt);
      claude.stdin.end();
      
      // Handle timeout
      const timeout = options.timeout || this.defaultTimeout;
      const timer = setTimeout(() => {
        claude.kill();
        reject(new Error(`Claude process timed out after ${timeout}ms`));
      }, timeout);
      
      // Clear timeout if process ends normally
      claude.on('exit', () => clearTimeout(timer));
    });
  }
}

/**
 * Convenience function to create a new Claude wrapper instance
 */
export function createClaudeWrapper(options?: ClaudeOptions): ClaudeWrapper {
  return new ClaudeWrapper(options);
}

/**
 * Simple one-shot execution
 */
export async function claudeExecute(
  prompt: string,
  options?: ClaudeOptions
): Promise<ClaudeResponse> {
  const wrapper = new ClaudeWrapper(options);
  return wrapper.execute(prompt, options);
}

// Export types
export type { ChildProcess };