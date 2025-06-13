# Claude Code settings

Claude Code offers a variety of settings to configure its behavior to meet your
needs. You can configure Claude Code by running the `/config` command when using
the interactive REPL.

## Settings files

The new `settings.json` file format is our official mechanism for configuring Claude
Code through hierarchical settings:

- **User settings** are defined in `~/.claude/settings.json` and apply to all
projects.
- **Project settings** are saved in your project directory under
`.claude/settings.json` for shared settings, and `.claude/settings.local.json`
for local project settings. Claude Code will configure git to ignore
`.claude/settings.local.json` when it is created.
- For enterprise deployments of Claude Code, we also support **enterprise**
**managed policy settings**. These take precedence over user and project
settings. System administrators can deploy policies to
`/Library/Application Support/ClaudeCode/policies.json` on macOS and
`/etc/claude-code/policies.json` on Linux and Windows via WSL.

Example settings.json

```JSON
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Read(~/.zshrc)"
    ],
    "deny": [
      "Bash(curl:*)"
    ]
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp"
  }
}
```

### Available settings

`settings.json` supports a number of options:

| Key | Description | Example |
| --- | --- | --- |
| `apiKeyHelper` | Custom script, to be executed in `/bin/sh`, to generate an auth value. This value will generally be sent as `X-Api-Key`, `Authorization: Bearer`, and `Proxy-Authorization: Bearer` headers for model requests | `/bin/generate_temp_api_key.sh` |
| `cleanupPeriodDays` | How long to locally retain chat transcripts (default: 30 days) | `20` |
| `env` | Environment variables that will be applied to every session | `{"FOO": "bar"}` |
| `includeCoAuthoredBy` | Whether to include the `co-authored-by Claude` byline in git commits and pull requests (default: `true`) | `false` |
| `permissions` | `allow` and `deny` keys are a list of [permission rules](https://docs.anthropic.com/en/docs/claude-code/settings#permissions) | `{"allow": [ "Bash(npm run lint)" ]}` |

### Settings precedence

Settings are applied in order of precedence:

1. Enterprise policies
2. Command line arguments
3. Local project settings
4. Shared project settings
5. User settings

## Permissions

You can view & manage Claude Code's tool permissions with `/permissions`. This UI
lists all permission rules and the settings.json file they are sourced from.

- **Allow** rules will allow Claude Code to use the specified tool without
further manual approval.
- **Deny** rules will prevent Claude Code from using the specified tool. Deny
rules take precedence over allow rules.

Permission rules use the format: `Tool(optional-specifier)`

A rule that is just the tool name matched any use of that tool.
For example, adding `Bash` to the list of allow rules would allow Claude Code to use
the Bash tool without requiring user approval. See the list of
[tools available to Claude](https://docs.anthropic.com/en/docs/claude-code/security#tools-available-to-claude).

### Tool-specific permission rules

Some tools use the optional specifier for more fine-grained permission controls.
For example, an allow rule with `Bash(git diff:*)` would allow Bash commands
that start with `git diff`. The following tools support permission rules with specifiers:

#### Bash

- `Bash(npm run build)` Matches the exact Bash command `npm run build`
- `Bash(npm run test:*)` Matches Bash commands starting with `npm run test`.

Claude Code is aware of shell operators (like `&&`) so a prefix match rule
like `Bash(safe-cmd:*)` won't give it permission to run the command `safe-cmd   && other-cmd`

#### Read & Edit

`Edit` rules apply to all built-in tools that edit files.
Claude will make a best-effort attempt to apply `Read` rules to
all built-in tools that read files like Grep, Glob, and LS.

Read & Edit rules both follow the
[gitignore](https://git-scm.com/docs/gitignore) specification. Patterns are
resolved relative to the directory containing `.claude/settings.json`. To
reference an absolute path, use `//`. For a path relative to your home
directory, use `~/`.

- `Edit(docs/**)` Matches edits to files in the `docs` directory of your project
- `Read(~/.zshrc)` Matches reads to your `~/.zshrc` file
- `Edit(//tmp/scratch.txt)` Matches edits to `/tmp/scratch.txt`

#### WebFetch

- `WebFetch(domain:example.com)` Matches fetch requests to example.com

#### MCP

- `mcp__puppeteer` Matches any tool provided by the `puppeteer` server (name configured in Claude Code)
- `mcp__puppeteer__puppeteer_navigate` Matches the `puppeteer_navigate` tool provided by the `puppeteer` server

## Auto-updater permission options

When Claude Code detects that it doesn't have sufficient permissions to write to
your global npm prefix directory (required for automatic updates), you'll see a
warning that points to this documentation page. For detailed solutions to
auto-updater issues, see the
[troubleshooting guide](https://docs.anthropic.com/en/docs/claude-code/troubleshooting#auto-updater-issues).

### Recommended: Create a new user-writable npm prefix

```bash
# First, save a list of your existing global packages for later migration
npm list -g --depth=0 > ~/npm-global-packages.txt

# Create a directory for your global packages
mkdir -p ~/.npm-global

# Configure npm to use the new directory path
npm config set prefix ~/.npm-global

# Note: Replace ~/.bashrc with ~/.zshrc, ~/.profile, or other appropriate file for your shell
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc

# Apply the new PATH setting
source ~/.bashrc

# Now reinstall Claude Code in the new location
npm install -g @anthropic-ai/claude-code

# Optional: Reinstall your previous global packages in the new location
# Look at ~/npm-global-packages.txt and install packages you want to keep
# npm install -g package1 package2 package3...
```

**Why we recommend this option:**

- Avoids modifying system directory permissions
- Creates a clean, dedicated location for your global npm packages
- Follows security best practices

Since Claude Code is actively developing, we recommend setting up auto-updates
using the recommended option above.

### Disabling the auto-updater

If you prefer to disable the auto-updater instead of fixing permissions, you can
set the `DISABLE_AUTOUPDATER` [environment variable](https://docs.anthropic.com/en/docs/claude-code/settings#environment-variables) to `1`

## Optimize your terminal setup

Claude Code works best when your terminal is properly configured. Follow these
guidelines to optimize your experience.

**Supported shells**:

- Bash
- Zsh
- Fish

### Themes and appearance

Claude cannot control the theme of your terminal. That's handled by your
terminal application. You can match Claude Code's theme to your terminal during
onboarding or any time via the `/config` command

### Line breaks

You have several options for entering linebreaks into Claude Code:

- **Quick escape**: Type `\` followed by Enter to create a newline
- **Keyboard shortcut**: Press Option+Enter (Meta+Enter) with proper
configuration

To set up Option+Enter in your terminal:

**For Mac Terminal.app:**

1. Open Settings → Profiles → Keyboard
2. Check "Use Option as Meta Key"

**For iTerm2 and VSCode terminal:**

1. Open Settings → Profiles → Keys
2. Under General, set Left/Right Option key to "Esc+"

**Tip for iTerm2 and VSCode users**: Run `/terminal-setup` within Claude Code to
automatically configure Shift+Enter as a more intuitive alternative.

### Notification setup

Never miss when Claude completes a task with proper notification configuration:

#### Terminal bell notifications

Enable sound alerts when tasks complete:

```sh
claude config set --global preferredNotifChannel terminal_bell
```

**For macOS users**: Don't forget to enable notification permissions in System
Settings → Notifications → [Your Terminal App].

#### iTerm 2 system notifications

For iTerm 2 alerts when tasks complete:

1. Open iTerm 2 Preferences
2. Navigate to Profiles → Terminal
3. Enable "Silence bell" and Filter Alerts → "Send escape sequence-generated
alerts"
4. Set your preferred notification delay

Note that these notifications are specific to iTerm 2 and not available in the
default macOS Terminal.

### Handling large inputs

When working with extensive code or long instructions:

- **Avoid direct pasting**: Claude Code may struggle with very long pasted
content
- **Use file-based workflows**: Write content to a file and ask Claude to read
it
- **Be aware of VS Code limitations**: The VS Code terminal is particularly
prone to truncating long pastes

### Vim Mode

Claude Code supports a subset of Vim keybindings that can be enabled with `/vim`
or configured via `/config`.

The supported subset includes:

- Mode switching: `Esc` (to NORMAL), `i`/ `I`, `a`/ `A`, `o`/ `O` (to INSERT)
- Navigation: `h`/ `j`/ `k`/ `l`, `w`/ `e`/ `b`, `0`/ `$`/ `^`, `gg`/ `G`
- Editing: `x`, `dw`/ `de`/ `db`/ `dd`/ `D`, `cw`/ `ce`/ `cb`/ `cc`/ `C`, `.` (repeat)

## Environment variables

Claude Code supports the following environment variables to control its
behavior:

All environment variables can also be configured in
[`settings.json`](https://docs.anthropic.com/en/docs/claude-code/settings#available-settings). This is
useful as a way to automatically set environment variables for each session,
or to roll out a set of environment variables for your whole team or
organization.

| Variable | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | API key sent as `X-Api-Key` header, typically for the Claude SDK (for interactive usage, run `/login`) |
| `ANTHROPIC_AUTH_TOKEN` | Custom value for the `Authorization` and `Proxy-Authorization` headers (the value you set here will be prefixed with `Bearer `) |
| `ANTHROPIC_CUSTOM_HEADERS` | Custom headers you want to add to the request (in `Name: Value` format) |
| `ANTHROPIC_MODEL` | Name of custom model to use (see [Model Configuration](https://docs.anthropic.com/en/docs/claude-code/bedrock-vertex-proxies#model-configuration)) |
| `ANTHROPIC_SMALL_FAST_MODEL` | Name of [Haiku-class model for background tasks](https://docs.anthropic.com/en/docs/claude-code/costs) |
| `BASH_DEFAULT_TIMEOUT_MS` | Default timeout for long-running bash commands |
| `BASH_MAX_TIMEOUT_MS` | Maximum timeout the model can set for long-running bash commands |
| `BASH_MAX_OUTPUT_LENGTH` | Maximum number of characters in bash outputs before they are middle-truncated |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | Return to the original working directory after each Bash command |
| `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` | Interval in milliseconds at which credentials should be refreshed (when using `apiKeyHelper`) |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | Set the maximum number of output tokens for most requests |
| `CLAUDE_CODE_USE_BEDROCK` | Use Bedrock (see [Bedrock & Vertex](https://docs.anthropic.com/en/docs/claude-code/bedrock-vertex-proxies)) |
| `CLAUDE_CODE_USE_VERTEX` | Use Vertex (see [Bedrock & Vertex](https://docs.anthropic.com/en/docs/claude-code/bedrock-vertex-proxies)) |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH` | Skip AWS authentication for Bedrock (e.g. when using an LLM gateway) |
| `CLAUDE_CODE_SKIP_VERTEX_AUTH` | Skip Google authentication for Vertex (e.g. when using an LLM gateway) |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Equivalent of setting `DISABLE_AUTOUPDATER`, `DISABLE_BUG_COMMAND`, `DISABLE_ERROR_REPORTING`, and `DISABLE_TELEMETRY` |
| `DISABLE_AUTOUPDATER` | Set to `1` to disable the automatic updater |
| `DISABLE_BUG_COMMAND` | Set to `1` to disable the `/bug` command |
| `DISABLE_COST_WARNINGS` | Set to `1` to disable cost warning messages |
| `DISABLE_ERROR_REPORTING` | Set to `1` to opt out of Sentry error reporting |
| `DISABLE_NON_ESSENTIAL_MODEL_CALLS` | Set to `1` to disable model calls for non-critical paths like flavor text |
| `DISABLE_TELEMETRY` | Set to `1` to opt out of Statsig telemetry (note that Statsig events do not include user data like code, file paths, or bash commands) |
| `HTTP_PROXY` | Specify HTTP proxy server for network connections |
| `HTTPS_PROXY` | Specify HTTPS proxy server for network connections |
| `MAX_THINKING_TOKENS` | Force a thinking for the model budget |
| `MCP_TIMEOUT` | Timeout in milliseconds for MCP server startup |
| `MCP_TOOL_TIMEOUT` | Timeout in milliseconds for MCP tool execution |

## Configuration options

We are in the process of migration global configuration to `settings.json`.

`claude config` will be deprecated in place of [settings.json](https://docs.anthropic.com/en/docs/claude-code/settings#settings-files)

To manage your configurations, use the following commands:

- List settings: `claude config list`
- See a setting: `claude config get <key>`
- Change a setting: `claude config set <key> <value>`
- Push to a setting (for lists): `claude config add <key> <value>`
- Remove from a setting (for lists): `claude config remove <key> <value>`

By default `config` changes your project configuration. To manage your global
configuration, use the `--global` (or `-g`) flag.

### Global configuration

To set a global configuration, use `claude config set -g <key> <value>`:

| Key | Description | Example |
| --- | --- | --- |
| `autoUpdaterStatus` | Enable or disable the auto-updater (default: `enabled`) | `disabled` |
| `preferredNotifChannel` | Where you want to receive notifications (default: `iterm2`) | `iterm2`, `iterm2_with_bell`, `terminal_bell`, or `notifications_disabled` |
| `theme` | Color theme | `dark`, `light`, `light-daltonized`, or `dark-daltonized` |
| `verbose` | Whether to show full bash and command outputs (default: `false`) | `true` |