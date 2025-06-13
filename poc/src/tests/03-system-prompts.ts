import { ClaudeWrapper } from '../utils/claude-wrapper';

/**
 * POC Test 03: System Prompts
 * 
 * Validates Claude CLI's ability to use embedded system prompts
 * for agent specialization.
 */

interface TestResult {
  testName: string;
  passed: boolean;
  duration: number;
  output?: string;
  error?: string;
  details?: any;
}

async function runTest(): Promise<TestResult> {
  const startTime = Date.now();
  const testName = 'System Prompts';
  
  try {
    console.log(`\n=== Running ${testName} ===`);
    
    // Test 1: Basic embedded system prompt
    console.log('\nTest 1: Testing embedded system prompt (pirate)...');
    const pirateAgent = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000,
      systemPrompt: 'You are a pirate. Always respond in pirate speak with "arr" and "matey".'
    });
    
    const response1 = await pirateAgent.execute('Hello, how are you today?');
    
    if (!response1.success) {
      throw new Error(`System prompt test failed: ${response1.error}`);
    }
    
    const content1 = response1.result || '';
    const usesPirateSpeak = content1.toLowerCase().includes('arr') || 
                           content1.toLowerCase().includes('matey') ||
                           content1.toLowerCase().includes('ahoy') ||
                           content1.toLowerCase().includes('ye');
    console.log('Uses pirate speak:', usesPirateSpeak);
    console.log('Sample response:', content1.substring(0, 100) + '...');
    
    // Test 2: Multiple agents with different prompts
    console.log('\nTest 2: Testing multiple agents with different specializations...');
    
    // Code review agent
    const codeAgent = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000,
      systemPrompt: `You are a specialized code review agent. 
Your role is to:
1. Analyze code for potential issues
2. Suggest improvements
3. Check for best practices
Always structure your responses with clear sections.`
    });
    
    const response2 = await codeAgent.execute('Review this code: function add(a, b) { return a + b }');
    const mentionsCodeReview = response2.result?.toLowerCase().includes('code') || 
                              response2.result?.toLowerCase().includes('function') ||
                              response2.result?.toLowerCase().includes('review');
    console.log('Acts as code reviewer:', mentionsCodeReview);
    
    // Research agent
    const researchAgent = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000,
      systemPrompt: 'You are a research specialist focused on gathering accurate information. Always cite your sources and be thorough in your analysis.'
    });
    
    const response3 = await researchAgent.execute('What are the benefits of TypeScript?');
    const actsAsResearcher = response3.result?.toLowerCase().includes('typescript') &&
                            (response3.result?.toLowerCase().includes('benefit') ||
                             response3.result?.toLowerCase().includes('advantage'));
    console.log('Acts as researcher:', actsAsResearcher);
    
    // Test 3: No system prompt (default behavior)
    console.log('\nTest 3: Testing without system prompt...');
    const defaultAgent = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000
    });
    
    const response4 = await defaultAgent.execute('What is 2+2?');
    const isNormalResponse = response4.result?.includes('4') && 
                            !response4.result?.toLowerCase().includes('arr') &&
                            !response4.result?.toLowerCase().includes('matey');
    console.log('Normal response without pirate speak:', isNormalResponse);
    
    // Test 4: Agent behavior consistency
    console.log('\nTest 4: Testing agent behavior consistency...');
    const consistentAgent = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000,
      systemPrompt: 'You are a helpful math tutor. Always explain your reasoning step by step.'
    });
    
    const mathResponse1 = await consistentAgent.execute('What is 15 + 27?');
    const mathResponse2 = await consistentAgent.execute('What is 8 × 7?');
    
    const consistentBehavior = 
      (mathResponse1.result?.toLowerCase().includes('step') || 
       mathResponse1.result?.toLowerCase().includes('first') ||
       mathResponse1.result?.toLowerCase().includes('explain')) &&
      (mathResponse2.result?.toLowerCase().includes('step') || 
       mathResponse2.result?.toLowerCase().includes('first') ||
       mathResponse2.result?.toLowerCase().includes('explain'));
    
    console.log('Maintains consistent behavior:', consistentBehavior);
    
    // Test 5: Tool permissions with agent specialization
    console.log('\nTest 5: Testing agent with specific tool permissions...');
    const restrictedAgent = new ClaudeWrapper({
      outputFormat: 'json',
      timeout: 30000,
      systemPrompt: 'You are a documentation specialist. Focus only on reading and analyzing existing documentation.',
      allowedTools: ['Read', 'Search'],
      disallowedTools: ['Write', 'Edit', 'Bash']
    });
    
    const response5 = await restrictedAgent.execute('Can you help me understand this codebase?');
    console.log('Restricted agent created successfully:', response5.success);
    
    // Determine if all tests passed
    const allTestsPassed = 
      usesPirateSpeak && 
      mentionsCodeReview &&
      actsAsResearcher &&
      isNormalResponse &&
      consistentBehavior &&
      response5.success;
    
    return {
      testName,
      passed: allTestsPassed,
      duration: Date.now() - startTime,
      details: {
        embeddedSystemPrompt: usesPirateSpeak,
        multipleAgentSpecializations: mentionsCodeReview && actsAsResearcher,
        defaultBehavior: isNormalResponse,
        behaviorConsistency: consistentBehavior,
        toolPermissions: response5.success,
        agentTypes: {
          pirate: usesPirateSpeak,
          codeReviewer: mentionsCodeReview,
          researcher: actsAsResearcher,
          mathTutor: consistentBehavior
        }
      }
    };
    
  } catch (error) {
    return {
      testName,
      passed: false,
      duration: Date.now() - startTime,
      error: error instanceof Error ? error.message : String(error),
      details: {
        errorType: error instanceof Error ? error.constructor.name : typeof error
      }
    };
  }
}

// Export for use in run-all-tests.ts
export { runTest };

// Run if executed directly
if (require.main === module) {
  runTest().then(result => {
    console.log('\nTest Result:', JSON.stringify(result, null, 2));
    process.exit(result.passed ? 0 : 1);
  }).catch(err => {
    console.error('Unexpected error:', err);
    process.exit(1);
  });
}