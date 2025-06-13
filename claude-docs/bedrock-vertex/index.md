# Overview

Claude Code can integrate with various third-party services and infrastructure to meet enterprise requirements. This page provides an overview of available integration options and helps you choose the right configuration for your organization.

## Provider comparison

| Feature | Anthropic | Amazon Bedrock | Google Vertex AI |
| --- | --- | --- | --- |
| Regions | Supported [countries](https://www.anthropic.com/supported-countries) | Multiple AWS [regions](https://docs.aws.amazon.com/bedrock/latest/userguide/models-regions.html) | Multiple GCP [regions](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations) |
| Prompt caching | Enabled by default | Contact AWS for enablement | Contact Google for enablement |
| Authentication | API key | AWS credentials (IAM) | GCP credentials (OAuth/Service Account) |
| Cost tracking | Dashboard | AWS Cost Explorer | GCP Billing |
| Enterprise features | Teams, usage monitoring | IAM policies, CloudTrail | IAM roles, Cloud Audit Logs |

## Integration options

### Cloud providers

[**Amazon Bedrock** \\
\\
Use Claude models through AWS infrastructure with IAM-based authentication and AWS-native monitoring](https://docs.anthropic.com/en/docs/claude-code/amazon-bedrock) [**Google Vertex AI** \\
\\
Access Claude models via Google Cloud Platform with enterprise-grade security and compliance](https://docs.anthropic.com/en/docs/claude-code/google-vertex-ai)

### Corporate infrastructure

[**Corporate Proxy** \\
\\
Configure Claude Code to work with your organization's proxy servers and SSL/TLS requirements](https://docs.anthropic.com/en/docs/claude-code/corporate-proxy) [**LLM Gateway** \\
\\
Deploy centralized model access with usage tracking, budgeting, and audit logging](https://docs.anthropic.com/en/docs/claude-code/llm-gateway)

## Mixing and matching settings

Claude Code supports flexible configuration options that allow you to combine different providers and infrastructure:

Understand the difference between:

- **Corporate proxy**: An HTTP/HTTPS proxy for routing traffic (set via `HTTPS_PROXY` or `HTTP_PROXY`)
- **LLM Gateway**: A service that handles authentication and provides provider-compatible endpoints (set via `ANTHROPIC_BASE_URL`, `ANTHROPIC_BEDROCK_BASE_URL`, or `ANTHROPIC_VERTEX_BASE_URL`)

Both configurations can be used in tandem.

### Using Bedrock with corporate proxy

Route Bedrock traffic through a corporate HTTP/HTTPS proxy:

```bash
# Enable Bedrock
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION=us-east-1

# Configure corporate proxy
export HTTPS_PROXY='https://proxy.example.com:8080'
```

### Using Bedrock with LLM Gateway

Use a gateway service that provides Bedrock-compatible endpoints:

```bash
# Enable Bedrock
export CLAUDE_CODE_USE_BEDROCK=1

# Configure LLM gateway
export ANTHROPIC_BEDROCK_BASE_URL='https://your-llm-gateway.com/bedrock'
export CLAUDE_CODE_SKIP_BEDROCK_AUTH=1  # If gateway handles AWS auth
```

### Using Vertex AI with corporate proxy

Route Vertex AI traffic through a corporate HTTP/HTTPS proxy:

```bash
# Enable Vertex
export CLAUDE_CODE_USE_VERTEX=1
export CLOUD_ML_REGION=us-east5
export ANTHROPIC_VERTEX_PROJECT_ID=your-project-id

# Configure corporate proxy
export HTTPS_PROXY='https://proxy.example.com:8080'
```

### Using Vertex AI with LLM Gateway

Combine Google Vertex AI models with an LLM gateway for centralized management:

```bash
# Enable Vertex
export CLAUDE_CODE_USE_VERTEX=1

# Configure LLM gateway
export ANTHROPIC_VERTEX_BASE_URL='https://your-llm-gateway.com/vertex'
export CLAUDE_CODE_SKIP_VERTEX_AUTH=1  # If gateway handles GCP auth
```

### Authentication configuration

Claude Code uses the `ANTHROPIC_AUTH_TOKEN` for both `Authorization` and `Proxy-Authorization` headers when needed. The `SKIP_AUTH` flags ( `CLAUDE_CODE_SKIP_BEDROCK_AUTH`, `CLAUDE_CODE_SKIP_VERTEX_AUTH`) are used in LLM gateway scenarios where the gateway handles provider authentication.

## Choosing the right integration

Consider these factors when selecting your integration approach:

### Direct provider access

Best for organizations that:

- Want the simplest setup
- Have existing AWS or GCP infrastructure
- Need provider-native monitoring and compliance

### Corporate proxy

Best for organizations that:

- Have existing corporate proxy requirements
- Need traffic monitoring and compliance
- Must route all traffic through specific network paths

### LLM Gateway

Best for organizations that:

- Need usage tracking across teams
- Want to dynamically switch between models
- Require custom rate limiting or budgets
- Need centralized authentication management

## Debugging

When debugging your third-party integration configuration:

- Use the `claude /status` [slash command](https://docs.anthropic.com/en/docs/claude-code/cli-usage#slash-command). This command provides observability into any applied authentication, proxy, and URL settings.
- Set environment variable `export ANTHROPIC_LOG=debug` to log requests.

## Next steps

- [Set up Amazon Bedrock](https://docs.anthropic.com/en/docs/claude-code/amazon-bedrock) for AWS-native integration
- [Configure Google Vertex AI](https://docs.anthropic.com/en/docs/claude-code/google-vertex-ai) for GCP deployment
- [Implement Corporate Proxy](https://docs.anthropic.com/en/docs/claude-code/corporate-proxy) for network requirements
- [Deploy LLM Gateway](https://docs.anthropic.com/en/docs/claude-code/llm-gateway) for enterprise management
- [Settings](https://docs.anthropic.com/en/docs/claude-code/settings) for configuration options and environment variables