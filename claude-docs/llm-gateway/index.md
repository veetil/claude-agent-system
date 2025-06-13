# LLM gateway configuration

This page covers how to configure Claude Code with LLM gateway solutions, including LiteLLM setup, authentication methods, and enterprise features like usage tracking and budget management.

## Overview

LLM gateways provide a centralized proxy layer between Claude Code and model providers, offering:

- **Centralized authentication** \- Single point for API key management
- **Usage tracking** \- Monitor usage across teams and projects
- **Cost controls** \- Implement budgets and rate limits
- **Audit logging** \- Track all model interactions for compliance
- **Model routing** \- Switch between providers without code changes

## LiteLLM configuration

LiteLLM is a third-party proxy service. Anthropic doesn't endorse, maintain, or audit LiteLLM's security or functionality. This guide is provided for informational purposes and may become outdated. Use at your own discretion.

### Prerequisites

- Claude Code updated to the latest version
- LiteLLM Proxy Server deployed and accessible
- Access to Claude models through your chosen provider

### Basic LiteLLM setup

**Configure Claude Code**:

#### Authentication methods

##### Static API key

Simplest method using a fixed API key:

```bash
# Set in environment
export ANTHROPIC_AUTH_TOKEN=sk-litellm-static-key

# Or in Claude Code settings
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key"
  }
}
```

This value will be sent as the `Authorization` and `Proxy-Authorization` headers, although `Authorization` may be overwritten (see Vertex "Client-specified credentials" below).

##### Dynamic API key with helper

For rotating keys or per-user authentication:

1. Create an API key helper script:

```bash
#!/bin/bash
# ~/bin/get-litellm-key.sh

# Example: Fetch key from vault
vault kv get -field=api_key secret/litellm/claude-code

# Example: Generate JWT token
jwt encode \
  --secret="${JWT_SECRET}" \
  --exp="+1h" \
  '{"user":"'${USER}'","team":"engineering"}'
```

2. Configure Claude Code settings to use the helper:

```json
{
  "apiKeyHelper": "~/bin/get-litellm-key.sh"
}
```

3. Set token refresh interval:

```bash
# Refresh every hour (3600000 ms)
export CLAUDE_CODE_API_KEY_HELPER_TTL_MS=3600000
```

This value will be sent as `Authorization`, `Proxy-Authorization`, and `X-Api-Key` headers, although `Authorization` may be overwritten (see [Google Vertex AI through LiteLLM](https://docs.anthropic.com/en/docs/claude-code/llm-gateway#google-vertex-ai-through-litellm)). The `apiKeyHelper` has lower precedence than `ANTHROPIC_AUTH_TOKEN` or `ANTHROPIC_API_KEY`.

#### Provider-specific configurations

##### Anthropic API through LiteLLM

Using [pass-through endpoint](https://docs.litellm.ai/docs/pass_through/anthropic_completion):

```bash
export ANTHROPIC_BASE_URL=https://litellm-server:4000/anthropic
```

##### Amazon Bedrock through LiteLLM

Using [pass-through endpoint](https://docs.litellm.ai/docs/pass_through/bedrock):

```bash
export ANTHROPIC_BEDROCK_BASE_URL=https://litellm-server:4000/bedrock
export CLAUDE_CODE_SKIP_BEDROCK_AUTH=1
export CLAUDE_CODE_USE_BEDROCK=1
```

##### Google Vertex AI through LiteLLM

Using [pass-through endpoint](https://docs.litellm.ai/docs/pass_through/vertex_ai):

**Recommended: Proxy-specified credentials**

```bash
export ANTHROPIC_VERTEX_BASE_URL=https://litellm-server:4000/vertex_ai/v1
export ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id
export CLAUDE_CODE_SKIP_VERTEX_AUTH=1
export CLAUDE_CODE_USE_VERTEX=1
export CLOUD_ML_REGION=us-east5
```

**Alternative: Client-specified credentials**

If you prefer to use local GCP credentials:

1. Authenticate with GCP locally:

```bash
gcloud auth application-default login
```

2. Set Claude Code environment:

```bash
export ANTHROPIC_VERTEX_BASE_URL=https://litellm-server:4000/vertex_ai/v1
export ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id
export CLAUDE_CODE_USE_VERTEX=1
export CLOUD_ML_REGION=us-east5
```

3. Update LiteLLM header configuration:

Ensure your LiteLLM config has `general_settings.litellm_key_header_name` set to `Proxy-Authorization`, since the pass-through GCP token will be located on the `Authorization` header.

#### Unified endpoint

Using LiteLLM's [Anthropic format endpoint](https://docs.litellm.ai/docs/anthropic_unified):

```bash
export ANTHROPIC_BASE_URL=https://litellm-server:4000
```

### Model selection

By default, the models will use those specified in [Model configuration](https://docs.anthropic.com/en/docs/claude-code/bedrock-vertex-proxies#model-configuration).

If you have configured custom model names in LiteLLM, set the aforementioned environment variables to those custom names.

For more detailed information, refer to the [LiteLLM documentation](https://docs.litellm.ai/).

## Additional resources

- [LiteLLM documentation](https://docs.litellm.ai/)
- [Claude Code settings](https://docs.anthropic.com/en/docs/claude-code/settings)
- [Corporate proxy setup](https://docs.anthropic.com/en/docs/claude-code/corporate-proxy)
- [Third-party integrations overview](https://docs.anthropic.com/en/docs/claude-code/third-party-integrations)