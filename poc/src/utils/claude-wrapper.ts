import { spawn, ChildProcess } from 'child_process';
import { EventEmitter } from 'events';

/**
 * Claude CLI Wrapper Utility
 * 
 * Provides a simplified interface for interacting with Claude CLI
 * in SDK mode with proper error handling and session management.
 */

export interface ClaudeOptions {
  outputFormat?: 'json' | 'text';
  sessionFile?: string;
  systemPrompt?: string;
  systemPromptFile?: string;
  appendSystemPrompt?: string;
  appendSystemPromptFile?: string;
  maxTurns?: number;
  maxTokens?: number;
  temperature?: number;
  workingDirectory?: string;
  env?: Record<string, string>;
  timeout?: number;
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
  };
}

export class ClaudeWrapper extends EventEmitter {
  private defaultTimeout = 30000;
  
  constructor(private defaultOptions?: ClaudeOptions) {
    super();
  }
  
  /**
   * Execute a Claude command with the given prompt and options
   */
  async execute(prompt: string, options?: ClaudeOptions): Promise<ClaudeResponse> {
    const startTime = Date.now();
    const opts = { ...this.defaultOptions, ...options };
    
    try {
      const args = this.buildArgs(prompt, opts);
      const result = await this.runCommand(args, opts);
      
      return {
        success: result.exitCode === 0,
        result: this.parseOutput(result.stdout, opts.outputFormat),
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
    const sessionFile = options?.sessionFile || `/tmp/claude-session-${Date.now()}.json`;
    const response = await this.execute(initialPrompt, {
      ...options,
      sessionFile
    });
    
    return {
      sessionId: sessionFile,
      response
    };
  }
  
  /**
   * Continue an existing session
   */
  async continueSession(
    sessionId: string,
    prompt: string,
    options?: ClaudeOptions
  ): Promise<ClaudeResponse> {
    return this.execute(prompt, {
      ...options,
      sessionFile: sessionId
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
    const { sessionId } = await this.createSession(prompts[0], options);
    
    results.push(await this.continueSession(sessionId, prompts[0], options));
    
    for (let i = 1; i < prompts.length; i++) {
      results.push(await this.continueSession(sessionId, prompts[i], options));
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
   * Build command line arguments from options
   */
  private buildArgs(prompt: string, options: ClaudeOptions): string[] {
    const args: string[] = ['-p']; // SDK mode
    
    if (options.outputFormat) {
      args.push('--output-format', options.outputFormat);
    }
    
    if (options.sessionFile) {
      // Check if this is a continuation or new session
      if (prompt !== '') {
        args.push('--continue');
      }
      args.push('--session-file', options.sessionFile);
    }
    
    if (options.systemPrompt) {
      args.push('--system-prompt', options.systemPrompt);
    }
    
    if (options.systemPromptFile) {
      args.push('--system-prompt-file', options.systemPromptFile);
    }
    
    if (options.appendSystemPrompt) {
      args.push('--append-system-prompt', options.appendSystemPrompt);
    }
    
    if (options.appendSystemPromptFile) {
      args.push('--append-system-prompt-file', options.appendSystemPromptFile);
    }
    
    if (options.maxTurns !== undefined) {
      args.push('--max-turns', options.maxTurns.toString());
    }
    
    if (options.maxTokens !== undefined) {
      args.push('--max-tokens', options.maxTokens.toString());
    }
    
    if (options.temperature !== undefined) {
      args.push('--temperature', options.temperature.toString());
    }
    
    // Add the prompt last
    args.push(prompt);
    
    return args;
  }
  
  /**
   * Run the Claude command and capture output
   */
  private runCommand(
    args: string[],
    options: ClaudeOptions
  ): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    return new Promise((resolve, reject) => {
      let stdout = '';
      let stderr = '';
      
      // Prepare environment
      const env = { ...process.env, ...options.env };
      delete env.ANTHROPIC_API_KEY; // Required for this setup
      
      const spawnOptions: any = {
        env,
        shell: true
      };
      
      if (options.workingDirectory) {
        spawnOptions.cwd = options.workingDirectory;
      }
      
      const claude = spawn('claude', args, spawnOptions);
      
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
  
  /**
   * Parse output based on format
   */
  private parseOutput(output: string, format?: string): any {
    if (format === 'json') {
      try {
        // Find JSON in output
        const jsonMatch = output.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          return parsed.result || parsed.content || parsed.response || parsed;
        }
      } catch (e) {
        // If JSON parsing fails, return raw output
        return output;
      }
    }
    
    return output;
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