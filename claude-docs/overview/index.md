# Claude Code overview

Claude Code is an agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster through natural language commands. By integrating directly with your development environment, Claude Code streamlines your workflow without requiring additional servers or complex setup.

```bash
npm install -g @anthropic-ai/claude-code
```

Claude Code's key capabilities include:

- Editing files and fixing bugs across your codebase
- Answering questions about your code's architecture and logic
- Executing and fixing tests, linting, and other commands
- Searching through git history, resolving merge conflicts, and creating commits and PRs
- Browsing documentation and resources from the internet using web search
- Works with [Amazon Bedrock and Google Vertex AI](https://docs.anthropic.com/en/docs/claude-code/bedrock-vertex-proxies) for enterprise deployments

## Why Claude Code?

Claude Code operates directly in your terminal, understanding your project context and taking real actions. No need to manually add files to context - Claude will explore your codebase as needed.

### Enterprise integration

Claude Code seamlessly integrates with enterprise AI platforms. You can connect to [Amazon Bedrock or Google Vertex AI](https://docs.anthropic.com/en/docs/claude-code/bedrock-vertex-proxies) for secure, compliant deployments that meet your organization's requirements.

### Security and privacy by design

Your code's security is paramount. Claude Code's architecture ensures:

- **Direct API connection**: Your queries go straight to Anthropic's API without intermediate servers
- **Works where you work**: Operates directly in your terminal
- **Understands context**: Maintains awareness of your entire project structure
- **Takes action**: Performs real operations like editing files and creating commits

## Getting started

To get started with Claude Code, follow our [installation guide](https://docs.anthropic.com/en/docs/claude-code/getting-started) which covers system requirements, installation steps, and authentication process.

## Quick tour

Here's what you can accomplish with Claude Code:

### From questions to solutions in seconds

```bash
# Ask questions about your codebase
claude
> how does our authentication system work?

# Create a commit with one command
claude commit

# Fix issues across multiple files
claude "fix the type errors in the auth module"
```

### Understand unfamiliar code

```
> what does the payment processing system do?
> find where user permissions are checked
> explain how the caching layer works
```

### Automate Git operations

```
> commit my changes
> create a pr
> which commit added tests for markdown back in December?
> rebase on main and resolve any merge conflicts
```

## Next steps

- **Getting started**: Install Claude Code and get up and running
- **Core features**: Explore what Claude Code can do for you
- **Commands**: Learn about CLI commands and controls
- **Configuration**: Customize Claude Code for your workflow

## Additional resources

- **Claude Code tutorials**: Step-by-step guides for common tasks
- **Troubleshooting**: Solutions for common issues with Claude Code
- **Bedrock & Vertex integrations**: Configure Claude Code with Amazon Bedrock or Google Vertex AI
- **Reference implementation**: Clone our development container reference implementation.

## License and data usage

Claude Code is provided under Anthropic's [Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms).

### How we use your data

We aim to be fully transparent about how we use your data. We may use feedback to improve our products and services, but we will not train generative models using your feedback from Claude Code. Given their potentially sensitive nature, we store user feedback transcripts for only 30 days.

#### Feedback transcripts

If you choose to send us feedback about Claude Code, such as transcripts of your usage, Anthropic may use that feedback to debug related issues and improve Claude Code's functionality (e.g., to reduce the risk of similar bugs occurring in the future). We will not train generative models using this feedback.

### Privacy safeguards

We have implemented several safeguards to protect your data, including limited retention periods for sensitive information, restricted access to user session data, and clear policies against using feedback for model training.

For full details, please review our [Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms) and [Privacy Policy](https://www.anthropic.com/legal/privacy).

### License

© Anthropic PBC. All rights reserved. Use is subject to Anthropic's [Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms).