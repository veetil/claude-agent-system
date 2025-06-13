# Tutorials

This guide provides step-by-step tutorials for common workflows with Claude Code. Each tutorial includes clear instructions, example commands, and best practices to help you get the most from Claude Code.

## Table of contents

- [Resume previous conversations](https://docs.anthropic.com/en/docs/claude-code/tutorials#resume-previous-conversations)
- [Understand new codebases](https://docs.anthropic.com/en/docs/claude-code/tutorials#understand-new-codebases)
- [Fix bugs efficiently](https://docs.anthropic.com/en/docs/claude-code/tutorials#fix-bugs-efficiently)
- [Refactor code](https://docs.anthropic.com/en/docs/claude-code/tutorials#refactor-code)
- [Work with tests](https://docs.anthropic.com/en/docs/claude-code/tutorials#work-with-tests)
- [Create pull requests](https://docs.anthropic.com/en/docs/claude-code/tutorials#create-pull-requests)
- [Handle documentation](https://docs.anthropic.com/en/docs/claude-code/tutorials#handle-documentation)
- [Work with images](https://docs.anthropic.com/en/docs/claude-code/tutorials#work-with-images)
- [Use extended thinking](https://docs.anthropic.com/en/docs/claude-code/tutorials#use-extended-thinking)
- [Set up project memory](https://docs.anthropic.com/en/docs/claude-code/tutorials#set-up-project-memory)
- [Set up Model Context Protocol (MCP)](https://docs.anthropic.com/en/docs/claude-code/tutorials#set-up-model-context-protocol-mcp)
- [Use Claude as a unix-style utility](https://docs.anthropic.com/en/docs/claude-code/tutorials#use-claude-as-a-unix-style-utility)
- [Create custom slash commands](https://docs.anthropic.com/en/docs/claude-code/tutorials#create-custom-slash-commands)
- [Run parallel Claude Code sessions with Git worktrees](https://docs.anthropic.com/en/docs/claude-code/tutorials#run-parallel-claude-code-sessions-with-git-worktrees)

## Resume previous conversations

### Continue your work seamlessly

**When to use:** You've been working on a task with Claude Code and need to continue where you left off in a later session.

Claude Code provides two options for resuming previous conversations:

- `--continue` to automatically continue the most recent conversation
- `--resume` to display a conversation picker

1

Continue the most recent conversation

```bash
claude --continue
```

This immediately resumes your most recent conversation without any prompts.

2

Continue in non-interactive mode

```bash
claude --continue --print "Continue with my task"
```

Use `--print` with `--continue` to resume the most recent conversation in non-interactive mode, perfect for scripts or automation.

3

Show conversation picker

```bash
claude --resume
```

This displays an interactive conversation selector showing:

- Conversation start time
- Initial prompt or conversation summary
- Message count

Use arrow keys to navigate and press Enter to select a conversation.

**How it works:**

1. **Conversation Storage**: All conversations are automatically saved locally with their full message history
2. **Message Deserialization**: When resuming, the entire message history is restored to maintain context
3. **Tool State**: Tool usage and results from the previous conversation are preserved
4. **Context Restoration**: The conversation resumes with all previous context intact

**Tips:**

- Conversation history is stored locally on your machine
- Use `--continue` for quick access to your most recent conversation
- Use `--resume` when you need to select a specific past conversation
- When resuming, you'll see the entire conversation history before continuing
- The resumed conversation starts with the same model and configuration as the original

**Examples:**

```bash
# Continue most recent conversation
claude --continue

# Continue most recent conversation with a specific prompt
claude --continue --print "Show me our progress"

# Show conversation picker
claude --resume

# Continue most recent conversation in non-interactive mode
claude --continue --print "Run the tests again"
```

## Understand new codebases

### Get a quick codebase overview

**When to use:** You've just joined a new project and need to understand its structure quickly.

1

Navigate to the project root directory

```bash
cd /path/to/project
```

2

Start Claude Code

```bash
claude
```

3

Ask for a high-level overview

```
> give me an overview of this codebase
```

4

Dive deeper into specific components

```
> explain the main architecture patterns used here
```

```
> what are the key data models?
```

```
> how is authentication handled?
```

**Tips:**

- Start with broad questions, then narrow down to specific areas
- Ask about coding conventions and patterns used in the project
- Request a glossary of project-specific terms

### Find relevant code

**When to use:** You need to locate code related to a specific feature or functionality.

1

Ask Claude to find relevant files

```
> find the files that handle user authentication
```

2

Get context on how components interact

```
> how do these authentication files work together?
```

3

Understand the execution flow

```
> trace the login process from front-end to database
```

**Tips:**

- Be specific about what you're looking for
- Use domain language from the project

* * *

## Fix bugs efficiently

### Diagnose error messages

**When to use:** You've encountered an error message and need to find and fix its source.

1

Share the error with Claude

```
> I'm seeing an error when I run npm test
```

2

Ask for fix recommendations

```
> suggest a few ways to fix the @ts-ignore in user.ts
```

3

Apply the fix

```
> update user.ts to add the null check you suggested
```

**Tips:**

- Tell Claude the command to reproduce the issue and get a stack trace
- Mention any steps to reproduce the error
- Let Claude know if the error is intermittent or consistent

* * *

## Refactor code

### Modernize legacy code

**When to use:** You need to update old code to use modern patterns and practices.

1

Identify legacy code for refactoring

```
> find deprecated API usage in our codebase
```

2

Get refactoring recommendations

```
> suggest how to refactor utils.js to use modern JavaScript features
```

3

Apply the changes safely

```
> refactor utils.js to use ES2024 features while maintaining the same behavior
```

4

Verify the refactoring

```
> run tests for the refactored code
```

**Tips:**

- Ask Claude to explain the benefits of the modern approach
- Request that changes maintain backward compatibility when needed
- Do refactoring in small, testable increments

* * *

## Work with tests

### Add test coverage

**When to use:** You need to add tests for uncovered code.

1

Identify untested code

```
> find functions in NotificationsService.swift that are not covered by tests
```

2

Generate test scaffolding

```
> add tests for the notification service
```

3

Add meaningful test cases

```
> add test cases for edge conditions in the notification service
```

4

Run and verify tests

```
> run the new tests and fix any failures
```

**Tips:**

- Ask for tests that cover edge cases and error conditions
- Request both unit and integration tests when appropriate
- Have Claude explain the testing strategy

* * *

## Create pull requests

### Generate comprehensive PRs

**When to use:** You need to create a well-documented pull request for your changes.

1

Summarize your changes

```
> summarize the changes I've made to the authentication module
```

2

Generate a PR with Claude

```
> create a pr
```

3

Review and refine

```
> enhance the PR description with more context about the security improvements
```

4

Add testing details

```
> add information about how these changes were tested
```

**Tips:**

- Ask Claude directly to make a PR for you
- Review Claude's generated PR before submitting
- Ask Claude to highlight potential risks or considerations

## Handle documentation

### Generate code documentation

**When to use:** You need to add or update documentation for your code.

1

Identify undocumented code

```
> find functions without proper JSDoc comments in the auth module
```

2

Generate documentation

```
> add JSDoc comments to the undocumented functions in auth.js
```

3

Review and enhance

```
> improve the generated documentation with more context and examples
```

4

Verify documentation

```
> check if the documentation follows our project standards
```

**Tips:**

- Specify the documentation style you want (JSDoc, docstrings, etc.)
- Ask for examples in the documentation
- Request documentation for public APIs, interfaces, and complex logic

## Work with images

### Analyze images and screenshots

**When to use:** You need to work with images in your codebase or get Claude's help analyzing image content.

1

Add an image to the conversation

You can use any of these methods:

1. Drag and drop an image into the Claude Code window
2. Copy an image and paste it into the CLI with cmd+v (on Mac)
3. Provide an image path claude "Analyze this image: /path/to/your/image.png"

2

Ask Claude to analyze the image

```
> What does this image show?
> Describe the UI elements in this screenshot
> Are there any problematic elements in this diagram?
```

3

Use images for context

```
> Here's a screenshot of the error. What's causing it?
> This is our current database schema. How should we modify it for the new feature?
```

4

Get code suggestions from visual content

```
> Generate CSS to match this design mockup
> What HTML structure would recreate this component?
```

**Tips:**

- Use images when text descriptions would be unclear or cumbersome
- Include screenshots of errors, UI designs, or diagrams for better context
- You can work with multiple images in a conversation
- Image analysis works with diagrams, screenshots, mockups, and more

* * *

## Use extended thinking

### Leverage Claude's extended thinking for complex tasks

**When to use:** When working on complex architectural decisions, challenging bugs, or planning multi-step implementations that require deep reasoning.

1

Provide context and ask Claude to think

```
> I need to implement a new authentication system using OAuth2 for our API. Think deeply about the best approach for implementing this in our codebase.
```

Claude will gather relevant information from your codebase and
use extended thinking, which will be visible in the interface.

2

Refine the thinking with follow-up prompts

```
> think about potential security vulnerabilities in this approach
> think harder about edge cases we should handle
```

**Tips to get the most value out of extended thinking:**

Extended thinking is most valuable for complex tasks such as:

- Planning complex architectural changes
- Debugging intricate issues
- Creating implementation plans for new features
- Understanding complex codebases
- Evaluating tradeoffs between different approaches

The way you prompt for thinking results in varying levels of thinking depth:

- "think" triggers basic extended thinking
- intensifying phrases such as "think more", "think a lot", "think harder", or "think longer" triggers deeper thinking

For more extended thinking prompting tips, see [Extended thinking tips](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/extended-thinking-tips).

Claude will display its thinking process as italic gray text above the
response.

* * *

## Set up project memory

### Create an effective CLAUDE.md file

**When to use:** You want to set up a CLAUDE.md file to store important project information, conventions, and frequently used commands.

1

Bootstrap a CLAUDE.md for your codebase

```
> /init
```

**Tips:**

- Include frequently used commands (build, test, lint) to avoid repeated searches
- Document code style preferences and naming conventions
- Add important architectural patterns specific to your project
- CLAUDE.md memories can be used for both instructions shared with your team and for your individual preferences.

* * *

## Set up Model Context Protocol (MCP)

### Configure MCP servers for enhanced capabilities

**When to use:** You want to extend Claude Code with additional tools and capabilities through MCP servers.

1

Install the MCP server you want to use

```bash
# Example: Install the filesystem MCP server
npm install -g @modelcontextprotocol/server-filesystem
```

2

Configure Claude Code to use the MCP server

```bash
claude mcp
```

This will guide you through configuring MCP servers for Claude Code.

3

Create a `.mcp.json` file in your project (optional)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    }
  }
}
```

4

Use MCP tools in your Claude Code session

```
> mcp__filesystem__read_file /path/to/file.txt
```

**Available MCP servers:**

- **Filesystem**: Read/write files with granular permissions
- **GitHub**: Interact with GitHub repositories, issues, and PRs
- **Database**: Query and modify databases
- **Web scraping**: Extract data from websites
- **Custom servers**: Build your own MCP servers for specific needs

**Tips:**

- MCP servers run as separate processes and communicate with Claude Code
- Configure permissions carefully to maintain security
- Check MCP server logs if tools aren't working as expected
- Share `.mcp.json` files with your team for consistent tooling

* * *

## Use Claude as a unix-style utility

### Add Claude to your verification process

**When to use:** You want to use Claude Code as a linter or code reviewer.

**Steps:**

1

Add Claude to your build script

```json
// package.json
{
    ...
    "scripts": {
        ...
        "lint:claude": "claude -p 'you are a linter. please look at the changes vs. main and report any issues related to typos. report the filename and line number on one line, and a description of the issue on the second line. do not return any other text.'"
    }
}
```

### Pipe in, pipe out

**When to use:** You want to pipe data into Claude, and get back data in a structured format.

1

Pipe data through Claude

```bash
cat build-error.txt | claude -p 'concisely explain the root cause of this build error' > output.txt
```

### Control output format

**When to use:** You need Claude's output in a specific format, especially when integrating Claude Code into scripts or other tools.

1

Use text format (default)

```bash
cat data.txt | claude -p 'summarize this data' --output-format text > summary.txt
```

This outputs just Claude's plain text response (default behavior).

2

Use JSON format

```bash
cat code.py | claude -p 'analyze this code for bugs' --output-format json > analysis.json
```

This outputs a JSON array of messages with metadata including cost and duration.

3

Use streaming JSON format

```bash
cat log.txt | claude -p 'parse this log file for errors' --output-format stream-json
```

This outputs a series of JSON objects in real-time as Claude processes the request. Each message is a valid JSON object, but the entire output is not valid JSON if concatenated.

**Tips:**

- Use `--output-format text` for simple integrations where you just need Claude's response
- Use `--output-format json` when you need the full conversation log
- Use `--output-format stream-json` for real-time output of each conversation turn

* * *

## Create custom slash commands

Claude Code supports custom slash commands that you can create to quickly execute specific prompts or tasks.

### Create project-specific commands

**When to use:** You want to create reusable slash commands for your project that all team members can use.

1

Create a commands directory in your project

```bash
mkdir -p .claude/commands
```

2

Create a Markdown file for each command

```bash
echo "Analyze the performance of this code and suggest three specific optimizations:" > .claude/commands/optimize.md
```

3

Use your custom command in Claude Code

```bash
claude > /project:optimize
```

**Tips:**

- Command names are derived from the filename (e.g., `optimize.md` becomes `/project:optimize`)
- You can organize commands in subdirectories (e.g., `.claude/commands/frontend/component.md` becomes `/project:frontend:component`)
- Project commands are available to everyone who clones the repository
- The Markdown file content becomes the prompt sent to Claude when the command is invoked

### Add command arguments with $ARGUMENTS

**When to use:** You want to create flexible slash commands that can accept additional input from users.

1

Create a command file with the $ARGUMENTS placeholder

```bash
echo "Find and fix issue #$ARGUMENTS. Follow these steps: 1.
Understand the issue described in the ticket 2. Locate the relevant code in
our codebase 3. Implement a solution that addresses the root cause 4. Add
appropriate tests 5. Prepare a concise PR description" >
.claude/commands/fix-issue.md
```

2

Use the command with an issue number

```bash
claude > /project:fix-issue 123
```

This will replace $ARGUMENTS with "123" in the prompt.

**Tips:**

- The $ARGUMENTS placeholder is replaced with any text that follows the command
- You can position $ARGUMENTS anywhere in your command template
- Other useful applications: generating test cases for specific functions, creating documentation for components, reviewing code in particular files, or translating content to specified languages

### Create personal slash commands

**When to use:** You want to create personal slash commands that work across all your projects.

1

Create a commands directory in your home folder

```bash
mkdir -p ~/.claude/commands
```

2

Create a Markdown file for each command

```bash
echo "Review this code for security vulnerabilities, focusing on:" >
~/.claude/commands/security-review.md
```

3

Use your personal custom command

```bash
claude > /user:security-review
```

**Tips:**

- Personal commands are prefixed with `/user:` instead of `/project:`
- Personal commands are only available to you and not shared with your team
- Personal commands work across all your projects
- You can use these for consistent workflows across different codebases

* * *

## Run parallel Claude Code sessions with Git worktrees

### Use worktrees for isolated coding environments

**When to use:** You need to work on multiple tasks simultaneously with complete code isolation between Claude Code instances.

1

Understand Git worktrees

Git worktrees allow you to check out multiple branches from the same
repository into separate directories. Each worktree has its own working
directory with isolated files, while sharing the same Git history. Learn
more in the [official Git worktree\\
documentation](https://git-scm.com/docs/git-worktree).

2

Create a new worktree

```bash
# Create a new worktree with a new branch
git worktree add ../project-feature-a -b feature-a

# Or create a worktree with an existing branch
git worktree add ../project-bugfix bugfix-123
```

This creates a new directory with a separate working copy of your repository.

3

Run Claude Code in each worktree

```bash
# Navigate to your worktree
cd ../project-feature-a

# Run Claude Code in this isolated environment
claude
```

4

In another terminal:

```bash
cd ../project-bugfix
claude
```

5

Manage your worktrees

```bash
# List all worktrees
git worktree list

# Remove a worktree when done
git worktree remove ../project-feature-a
```

**Tips:**

- Each worktree has its own independent file state, making it perfect for parallel Claude Code sessions
- Changes made in one worktree won't affect others, preventing Claude instances from interfering with each other
- All worktrees share the same Git history and remote connections
- For long-running tasks, you can have Claude working in one worktree while you continue development in another
- Use descriptive directory names to easily identify which task each worktree is for
- Remember to initialize your development environment in each new worktree according to your project's setup. Depending on your stack, this might include:
  - JavaScript projects: Running dependency installation ( `npm install`, `yarn`)
  - Python projects: Setting up virtual environments or installing with package managers
  - Other languages: Following your project's standard setup process

* * *

## Next steps

[**Claude Code reference implementation** \\
\\
Clone our development container reference implementation.](https://github.com/anthropics/claude-code/tree/main/.devcontainer)