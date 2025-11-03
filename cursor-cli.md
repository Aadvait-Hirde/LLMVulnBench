# Cursor CLI

Cursor CLI lets you interact with AI agents directly from your terminal to write, review, and modify code. Whether you prefer an interactive terminal interface or print automation for scripts and CI pipelines, the CLI provides powerful coding assistance right where you work.

## Getting started

```
# Install
curl https://cursor.com/install -fsS | bash

# Run interactive session
cursor-agent
```

## Interactive mode

Start a conversational session with the agent to describe your goals, review proposed changes, and approve commands:

```
# Start interactive session
cursor-agent

# Start with initial prompt
cursor-agent "refactor the auth module to use JWT tokens"
```

## Non-interactive mode

Use print mode for non-interactive scenarios like scripts, CI pipelines, or automation:

```
# Run with specific prompt and model
cursor-agent -p "find and fix performance issues" --model "gpt-5"

# Use with git changes included for review
cursor-agent -p "review these changes for security issues" --output-format text
```

## Sessions

Resume previous conversations to maintain context across multiple interactions:

```
# List all previous chats
cursor-agent ls

# Resume latest conversation
cursor-agent resume

# Resume specific conversation
cursor-agent --resume="chat-id-here"
```

# Installation

## Installation

### macOS, Linux and Windows (WSL)

Install Cursor CLI with a single command:

```
curl https://cursor.com/install -fsS | bash
```

### Verification

After installation, verify that Cursor CLI is working correctly:

```
cursor-agent --version
```

## Post-installation setup

1. **Add ~/.local/bin to your PATH:**

For bash:

```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

For zsh:

```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```
2. **Start using Cursor Agent:**

```
cursor-agent
```

## Updates

Cursor CLI will try to auto-update by default to ensure you always have the latest version.

To manually update Cursor CLI to the latest version:

```
cursor-agent update
# or
cursor-agent upgrade
```

Both commands will update Cursor Agent to the latest version.

# Using Agent in CLI

## Prompting

Stating intent clearly is recommended for the best results. For example, you can use the prompt "do not write any code" to ensure that the agent won't edit any files. This is generally helpful when planning tasks before implementing them.

Agent currently has tools for file operations, searching, and running shell commands. More tools are being added, similar to the IDE agent.

## MCP

Agent supports [MCP (Model Context Protocol)](/docs/context/mcp/directory) for extended functionality and integrations. The CLI will automatically detect and respect your `mcp.json` configuration file, enabling the same MCP servers and tools that you've configured for the IDE.

## Rules

The CLI agent supports the same [rules system](/docs/context/rules) as the IDE. You can create rules in the `.cursor/rules` directory to provide context and guidance to the agent. These rules will be automatically loaded and applied based on their configuration, allowing you to customize the agent's behavior for different parts of your project or specific file types.

The CLI also reads `AGENTS.md` and `CLAUDE.md` at the project root (if
present) and applies them as rules alongside `.cursor/rules`.

## Working with Agent

### Navigation

Previous messages can be accessed using arrow up (ArrowUpArrow Up) where you can cycle through them.

### Review

Review changes with Ctrl+R. Press i to add follow-up instructions. Use ArrowUpArrow Up/ArrowDownArrow Down to scroll, and ArrowLeftArrow Left/ArrowRightArrow Right to switch files.

### Selecting context

Select files and folders to include in context with @. Free up space in the context window by running `/compress`. See [Summarization](/docs/agent/chat/summarization) for details.

## History

Continue from an existing thread with `--resume [thread id]` to load prior context.

To resume the most recent conversation, use `cursor-agent resume`.

You can also run `cursor-agent ls` to see a list of previous conversations.

## Command approval

Before running terminal commands, CLI will ask you to approve (y) or reject (n) execution.

## Non-interactive mode

Use `-p` or `--print` to run Agent in non-interactive mode. This will print the response to the console.

With non-interactive mode, you can invoke Agent in a non-interactive way. This allows you to integrate it in scripts, CI pipelines, etc.

You can combine this with `--output-format` to control how the output is formatted. For example, use `--output-format json` for structured output that's easier to parse in scripts, or `--output-format text` for plain text output of the agent's final response.

Cursor has full write access in non-interactive mode.

# Shell Mode

Shell Mode runs shell commands directly from the CLI without leaving your conversation. Use it for quick, non-interactive commands with safety checks and output displayed in the conversation.

## Command execution

Commands run in your login shell (`$SHELL`) with the CLI's working directory and environment. Chain commands to run in other directories:

```
cd subdir && npm test
```

## Output

Large outputs are truncated automatically and long-running processes timeout to maintain performance.

## Limitations

- Commands timeout after 30 seconds
- Long-running processes, servers, and interactive prompts are not supported
- Use short, non-interactive commands for best results

## Permissions

Commands are checked against your permissions and team settings before execution. See [Permissions](/docs/cli/reference/permissions) for detailed configuration.

Admin policies may block certain commands, and commands with redirection cannot be allowlisted inline.

## Usage guidelines

Shell Mode works well for status checks, quick builds, file operations, and environment inspection.

Avoid long-running servers, interactive applications, and commands requiring input.

Each command runs independently - use `cd <dir> && ...` to run commands in other directories.

## Troubleshooting

- If a command hangs, cancel with Ctrl+C and add non-interactive flags
- When prompted for permissions, approve once or add to allowlist with Tab
- For truncated output, use Ctrl+O to expand
- To run in different directories, use `cd <dir> && ...` since changes don't persist
- Shell Mode supports zsh and bash from your `$SHELL` variable

## FAQ

### Does `cd` persist across runs?

### Can I change the timeout?

### Where are permissions configured?

### How do I exit Shell Mode?

Press EscapeEsc when the input is empty, Backspace/Delete on empty input, or Ctrl+C to clear and exit.

# Using Headless CLI

Use Cursor CLI in scripts and automation workflows for code analysis, generation, and refactoring tasks.

## How it works

Use [print mode](/docs/cli/using#non-interactive-mode) (`-p, --print`) for non-interactive scripting and automation.

### File modification in scripts

Combine `--print` with `--force` to modify files in scripts:

```
# Enable file modifications in print mode
cursor-agent -p --force "Refactor this code to use modern ES6+ syntax"

# Without --force, changes are only proposed, not applied
cursor-agent -p "Add JSDoc comments to this file"  # Won't modify files

# Batch processing with actual file changes
find src/ -name "*.js" | while read file; do
  cursor-agent -p --force "Add comprehensive JSDoc comments to $file"
done
```

The `--force` flag allows the agent to make direct file changes without
confirmation

## Setup

See [Installation](/docs/cli/installation) and [Authentication](/docs/cli/reference/authentication) for complete setup details.

```
# Install Cursor CLI
curl https://cursor.com/install -fsS | bash

# Set API key for scripts
export CURSOR_API_KEY=your_api_key_here
cursor-agent -p "Analyze this code"
```

## Example scripts

Use different output formats for different script needs. See [Output format](/docs/cli/reference/output-format) for details.

### Searching the codebase

By default, `--print` uses `text` format for clean, final-answer-only responses:

```
#!/bin/bash
# Simple codebase question - uses text format by default

cursor-agent -p "What does this codebase do?"
```

### Automated code review

Use `--output-format json` for structured analysis:

```
#!/bin/bash
# simple-code-review.sh - Basic code review script

echo "Starting code review..."

# Review recent changes
cursor-agent -p --force --output-format text \
  "Review the recent code changes and provide feedback on:
  - Code quality and readability
  - Potential bugs or issues
  - Security considerations
  - Best practices compliance

  Provide specific suggestions for improvement and write to review.txt"

if [ $? -eq 0 ]; then
  echo "✅ Code review completed successfully"
else
  echo "❌ Code review failed"
  exit 1
fi
```

### Real-time progress tracking

Use `--output-format stream-json` for message-level progress tracking, or add `--stream-partial-output` for incremental streaming of deltas:

```
#!/bin/bash
# stream-progress.sh - Track progress in real-time

echo "🚀 Starting stream processing..."

# Track progress in real-time
accumulated_text=""
tool_count=0
start_time=$(date +%s)

cursor-agent -p --force --output-format stream-json --stream-partial-output \
  "Analyze this project structure and create a summary report in analysis.txt" | \
  while IFS= read -r line; do
    
    type=$(echo "$line" | jq -r '.type // empty')
    subtype=$(echo "$line" | jq -r '.subtype // empty')
    
    case "$type" in
      "system")
        if [ "$subtype" = "init" ]; then
          model=$(echo "$line" | jq -r '.model // "unknown"')
          echo "🤖 Using model: $model"
        fi
        ;;
        
      "assistant")
        # Accumulate incremental text deltas for smooth progress
        content=$(echo "$line" | jq -r '.message.content[0].text // empty')
        accumulated_text="$accumulated_text$content"
        
        # Show live progress (updates with each character delta)
        printf "\r📝 Generating: %d chars" ${#accumulated_text}
        ;;

      "tool_call")
        if [ "$subtype" = "started" ]; then
          tool_count=$((tool_count + 1))

          # Extract tool information
          if echo "$line" | jq -e '.tool_call.writeToolCall' > /dev/null 2>&1; then
            path=$(echo "$line" | jq -r '.tool_call.writeToolCall.args.path // "unknown"')
            echo -e "\n🔧 Tool #$tool_count: Creating $path"
          elif echo "$line" | jq -e '.tool_call.readToolCall' > /dev/null 2>&1; then
            path=$(echo "$line" | jq -r '.tool_call.readToolCall.args.path // "unknown"')
            echo -e "\n📖 Tool #$tool_count: Reading $path"
          fi

        elif [ "$subtype" = "completed" ]; then
          # Extract and show tool results
          if echo "$line" | jq -e '.tool_call.writeToolCall.result.success' > /dev/null 2>&1; then
            lines=$(echo "$line" | jq -r '.tool_call.writeToolCall.result.success.linesCreated // 0')
            size=$(echo "$line" | jq -r '.tool_call.writeToolCall.result.success.fileSize // 0')
            echo "   ✅ Created $lines lines ($size bytes)"
          elif echo "$line" | jq -e '.tool_call.readToolCall.result.success' > /dev/null 2>&1; then
            lines=$(echo "$line" | jq -r '.tool_call.readToolCall.result.success.totalLines // 0')
            echo "   ✅ Read $lines lines"
          fi
        fi
        ;;

      "result")
        duration=$(echo "$line" | jq -r '.duration_ms // 0')
        end_time=$(date +%s)
        total_time=$((end_time - start_time))

        echo -e "\n\n🎯 Completed in ${duration}ms (${total_time}s total)"
        echo "📊 Final stats: $tool_count tools, ${#accumulated_text} chars generated"
        ;;
    esac
  done
```

# GitHub Actions

Use Cursor CLI in GitHub Actions and other CI/CD systems to automate development tasks.

## GitHub Actions integration

Basic setup:

```
- name: Install Cursor CLI
  run: |
    curl https://cursor.com/install -fsS | bash
    echo "$HOME/.cursor/bin" >> $GITHUB_PATH

- name: Run Cursor Agent
  env:
    CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
  run: |
    cursor-agent -p "Your prompt here" --model gpt-5
```

## Cookbook examples

See our cookbook examples for practical workflows: [updating documentation](/docs/cli/cookbook/update-docs) and [fixing CI issues](/docs/cli/cookbook/fix-ci).

## Other CI systems

Use Cursor CLI in any CI/CD system with:

- **Shell script execution** (bash, zsh, etc.)
- **Environment variables** for API key configuration
- **Internet connectivity** to reach Cursor's API

## Autonomy levels

Choose your agent's autonomy level:

### Full autonomy approach

Give the agent complete control over git operations, API calls, and external interactions. Simpler setup, requires more trust.

**Example:** In our [Update Documentation](/docs/cli/cookbook/update-docs) cookbook, the first workflow lets the agent:

- Analyze PR changes
- Create and manage git branches
- Commit and push changes
- Post comments on pull requests
- Handle all error scenarios

```
- name: Update docs (full autonomy)
  run: |
    cursor-agent -p "You have full access to git, GitHub CLI, and PR operations. 
    Handle the entire docs update workflow including commits, pushes, and PR comments."
```

### Restricted autonomy approach

We recommend using this approach with **permission-based restrictions** for
production CI workflows. This gives you the best of both worlds: the agent can
intelligently handle complex analysis and file modifications while critical
operations remain deterministic and auditable.

Limit agent operations while handling critical steps in separate workflow steps. Better control and predictability.

**Example:** The second workflow in the same cookbook restricts the agent to only file modifications:

```
- name: Generate docs updates (restricted)
  run: |
    cursor-agent -p "IMPORTANT: Do NOT create branches, commit, push, or post PR comments. 
    Only modify files in the working directory. A later workflow step handles publishing."

- name: Publish docs branch (deterministic)
  run: |
    # Deterministic git operations handled by CI
    git checkout -B "docs/${{ github.head_ref }}"
    git add -A
    git commit -m "docs: update for PR"
    git push origin "docs/${{ github.head_ref }}"

- name: Post PR comment (deterministic)
  run: |
    # Deterministic PR commenting handled by CI
    gh pr comment ${{ github.event.pull_request.number }} --body "Docs updated"
```

### Permission-based restrictions

Use [permission configurations](/docs/cli/reference/permissions) to enforce restrictions at the CLI level:

```
{
  "permissions": {
    "allow": [
      "Read(**/*.md)",
      "Write(docs/**/*)",
      "Shell(grep)",
      "Shell(find)"
    ],
    "deny": ["Shell(git)", "Shell(gh)", "Write(.env*)", "Write(package.json)"]
  }
}
```

## Authentication

### Generate your API key

First, [generate an API key](/docs/cli/reference/authentication#api-key-authentication) from your Cursor dashboard.

### Configure repository secrets

Store your Cursor API key securely in your repository using the GitHub CLI:

```
# Repository secret
gh secret set CURSOR_API_KEY --repo OWNER/REPO --body "$CURSOR_API_KEY"

# Organization secret (all repos)
gh secret set CURSOR_API_KEY --org ORG --visibility all --body "$CURSOR_API_KEY"
```

Alternatively, use the GitHub UI: Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### Use in workflows

Set your `CURSOR_API_KEY` environment variable:

```
env:
  CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
```
# Slash commands

CommandDescription`/model <model>`Set or list models`/auto-run [state]`Toggle auto-run (default) or set [on|off|status]`/new-chat`Start a new chat session`/vim`Toggle Vim keys`/help [command]`Show help (/help [cmd])`/feedback <message>`Share feedback with the team`/resume <chat>`Resume a previous chat by folder name`/copy-req-id`Copy last request ID`/logout`Sign out from Cursor`/quit`Exit

# Parameters

## Global options

Global options can be used with any command:

OptionDescription`-v, --version`Output the version number`-a, --api-key <key>`API key for authentication (can also use `CURSOR_API_KEY` env var)`-p, --print`Print responses to console (for scripts or non-interactive use). Has access to all tools, including write and bash.`--output-format <format>`Output format (only works with `--print`): `text`, `json`, or `stream-json` (default: `text`)`--stream-partial-output`Stream partial output as individual text deltas (only works with `--print` and `stream-json` format)`-b, --background`Start in background mode (open composer picker on launch)`--fullscreen`Enable fullscreen mode`--resume [chatId]`Resume a chat session`-m, --model <model>`Model to use`-f, --force`Force allow commands unless explicitly denied`-h, --help`Display help for command
## Commands

CommandDescriptionUsage`login`Authenticate with Cursor`cursor-agent login``logout`Sign out and clear stored authentication`cursor-agent logout``status`Check authentication status`cursor-agent status``mcp`Manage MCP servers`cursor-agent mcp``update|upgrade`Update Cursor Agent to the latest version`cursor-agent update` or `cursor-agent upgrade``ls`Resume a chat session`cursor-agent ls``resume`Resume the latest chat session`cursor-agent resume``help [command]`Display help for command`cursor-agent help [command]`
When no command is specified, Cursor Agent starts in interactive chat mode by
default.

## MCP

Manage MCP servers configured for Cursor Agent.

SubcommandDescriptionUsage`login <identifier>`Authenticate with an MCP server configured in `.cursor/mcp.json``cursor-agent mcp login <identifier>``list`List configured MCP servers and their status`cursor-agent mcp list``list-tools <identifier>`List available tools and their argument names for a specific MCP`cursor-agent mcp list-tools <identifier>`
All MCP commands support `-h, --help` for command-specific help.

## Arguments

When starting in chat mode (default behavior), you can provide an initial prompt:

**Arguments:**

- `prompt` — Initial prompt for the agent

## Getting help

All commands support the global `-h, --help` option to display command-specific help.

# Authentication

Cursor CLI supports two authentication methods: browser-based login (recommended) and API keys.

## Browser authentication (recommended)

Use the browser flow for the easiest authentication experience:

```
# Log in using browser flow
cursor-agent login

# Check authentication status
cursor-agent status

# Log out and clear stored authentication
cursor-agent logout
```

The login command will open your default browser and prompt you to authenticate with your Cursor account. Once completed, your credentials are securely stored locally.

## API key authentication

For automation, scripts, or CI/CD environments, use API key authentication:

### Step 1: Generate an API key

Generate an API key in your Cursor dashboard under Integrations > User API Keys.

### Step 2: Set the API key

You can provide the API key in two ways:

**Option 1: Environment variable (recommended)**

```
export CURSOR_API_KEY=your_api_key_here
cursor-agent "implement user authentication"
```

**Option 2: Command line flag**

```
cursor-agent --api-key your_api_key_here "implement user authentication"
```

## Authentication status

Check your current authentication status:

```
cursor-agent status
```

This command will display:

- Whether you're authenticated
- Your account information
- Current endpoint configuration

## Troubleshooting

- **"Not authenticated" errors:** Run `cursor-agent login` or ensure your API key is correctly set
- **SSL certificate errors:** Use the `--insecure` flag for development environments
- **Endpoint issues:** Use the `--endpoint` flag to specify a custom API endpoint

# Permissions

Configure what the agent is allowed to do using permission tokens in your CLI configuration. Permissions are set in `~/.cursor/cli-config.json` (global) or `<project>/.cursor/cli.json` (project-specific).

## Permission types

### Shell commands

**Format:** `Shell(commandBase)`

Controls access to shell commands. The `commandBase` is the first token in the command line.

ExampleDescription`Shell(ls)`Allow running `ls` commands`Shell(git)`Allow any `git` subcommand`Shell(npm)`Allow npm package manager commands`Shell(rm)`Deny destructive file removal (commonly in `deny`)
### File reads

**Format:** `Read(pathOrGlob)`

Controls read access to files and directories. Supports glob patterns.

ExampleDescription`Read(src/**/*.ts)`Allow reading TypeScript files in `src``Read(**/*.md)`Allow reading markdown files anywhere`Read(.env*)`Deny reading environment files`Read(/etc/passwd)`Deny reading system files
### File writes

**Format:** `Write(pathOrGlob)`

Controls write access to files and directories. Supports glob patterns. When using in print mode, `--force` is required to write files.

ExampleDescription`Write(src/**)`Allow writing to any file under `src``Write(package.json)`Allow modifying package.json`Write(**/*.key)`Deny writing private key files`Write(**/.env*)`Deny writing environment files
## Configuration

Add permissions to the `permissions` object in your CLI configuration file:

```
{
  "permissions": {
    "allow": [
      "Shell(ls)",
      "Shell(git)",
      "Read(src/**/*.ts)",
      "Write(package.json)"
    ],
    "deny": ["Shell(rm)", "Read(.env*)", "Write(**/*.key)"]
  }
}
```

## Pattern matching

- Glob patterns use `**`, `*`, and `?` wildcards
- Relative paths are scoped to the current workspace
- Absolute paths can target files outside the project
- Deny rules take precedence over allow rules

# Configuration

Configure the Agent CLI using the `cli-config.json` file.

## File location

TypePlatformPathGlobalmacOS/Linux`~/.cursor/cli-config.json`GlobalWindows`$env:USERPROFILE\.cursor\cli-config.json`ProjectAll`<project>/.cursor/cli.json`
Only permissions can be configured at the project level. All other CLI
settings must be set globally.

Override with environment variables:

- **`CURSOR_CONFIG_DIR`**: custom directory path
- **`XDG_CONFIG_HOME`** (Linux/BSD): uses `$XDG_CONFIG_HOME/cursor/cli-config.json`

## Schema

### Required fields

FieldTypeDescription`version`numberConfig schema version (current: `1`)`editor.vimMode`booleanEnable Vim keybindings (default: `false`)`permissions.allow`string[]Permitted operations (see [Permissions](/docs/cli/reference/permissions))`permissions.deny`string[]Forbidden operations (see [Permissions](/docs/cli/reference/permissions))
### Optional fields

FieldTypeDescription`model`objectSelected model configuration`hasChangedDefaultModel`booleanCLI-managed model override flag
## Examples

### Minimal config

```
{
  "version": 1,
  "editor": { "vimMode": false },
  "permissions": { "allow": ["Shell(ls)"], "deny": [] }
}
```

### Enable Vim mode

```
{
  "version": 1,
  "editor": { "vimMode": true },
  "permissions": { "allow": ["Shell(ls)"], "deny": [] }
}
```

### Configure permissions

```
{
  "version": 1,
  "editor": { "vimMode": false },
  "permissions": {
    "allow": ["Shell(ls)", "Shell(echo)"],
    "deny": ["Shell(rm)"]
  }
}
```

See [Permissions](/docs/cli/reference/permissions) for available permission types and examples.

## Troubleshooting

**Config errors**: Move the file aside and restart:

```
mv ~/.cursor/cli-config.json ~/.cursor/cli-config.json.bad
```

**Changes don't persist**: Ensure valid JSON and write permissions. Some fields are CLI-managed and may be overwritten.

## Notes

- Pure JSON format (no comments)
- CLI performs self-repair for missing fields
- Corrupted files are backed up as `.bad` and recreated
- Permission entries are exact strings (see [Permissions](/docs/cli/reference/permissions) for details)

## Models

You can select a model for the CLI using the `/model` slash command.

```
/model auto
/model gpt-5
/model sonnet-4
```

See the [Slash commands](/docs/cli/reference/slash-commands) docs for other commands.

# Output Format

The Cursor Agent CLI provides multiple output formats with the `--output-format` option when combined with `--print`. These formats include structured formats for programmatic use (`json`, `stream-json`) and a simplified text format for human-readable output (`text`).

The default `--output-format` is `text`. This option is only valid when
printing (`--print`) or when print mode is inferred (non-TTY stdout or piped
stdin).

## JSON format

The `json` output format emits a single JSON object (followed by a newline) when the run completes successfully. Deltas and tool events are not emitted; text is aggregated into the final result.

On failure, the process exits with a non-zero code and writes an error message to stderr. No well-formed JSON object is emitted in failure cases.

### Success response

When successful, the CLI outputs a JSON object with the following structure:

```
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 1234,
  "duration_api_ms": 1234,
  "result": "<full assistant text>",
  "session_id": "<uuid>",
  "request_id": "<optional request id>"
}
```

FieldDescription`type`Always `"result"` for terminal results`subtype`Always `"success"` for successful completions`is_error`Always `false` for successful responses`duration_ms`Total execution time in milliseconds`duration_api_ms`API request time in milliseconds (currently equal to `duration_ms`)`result`Complete assistant response text (concatenation of all text deltas)`session_id`Unique session identifier`request_id`Optional request identifier (may be omitted)
## Stream JSON format

The `stream-json` output format emits newline-delimited JSON (NDJSON). Each line contains a single JSON object representing an event during execution. This format aggregates text deltas and outputs **one line per assistant message** (the complete message between tool calls).

The stream ends with a terminal `result` event on success. On failure, the process exits with a non-zero code and the stream may end early without a terminal event; an error message is written to stderr.

**Streaming partial output:** For real-time character-level streaming, use `--stream-partial-output` with `--output-format stream-json`. This emits text as it's generated in small chunks, with the same event structure but multiple `assistant` events per message. Concatenate all `message.content[].text` values to reconstruct the complete response.

### Event types

#### System initialization

Emitted once at the beginning of each session:

```
{
  "type": "system",
  "subtype": "init",
  "apiKeySource": "env|flag|login",
  "cwd": "/absolute/path",
  "session_id": "<uuid>",
  "model": "<model display name>",
  "permissionMode": "default"
}
```

Future fields like `tools` and `mcp_servers` may be added to this event.

#### User message

Contains the user's input prompt:

```
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [{ "type": "text", "text": "<prompt>" }]
  },
  "session_id": "<uuid>"
}
```

#### Assistant message

Emitted once per complete assistant message (between tool calls). Each event contains the full text of that message segment:

```
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [{ "type": "text", "text": "<complete message text>" }]
  },
  "session_id": "<uuid>"
}
```

#### Tool call events

Tool calls are tracked with start and completion events:

**Tool call started:**

```
{
  "type": "tool_call",
  "subtype": "started",
  "call_id": "<string id>",
  "tool_call": {
    "readToolCall": {
      "args": { "path": "file.txt" }
    }
  },
  "session_id": "<uuid>"
}
```

**Tool call completed:**

```
{
  "type": "tool_call",
  "subtype": "completed",
  "call_id": "<string id>",
  "tool_call": {
    "readToolCall": {
      "args": { "path": "file.txt" },
      "result": {
        "success": {
          "content": "file contents...",
          "isEmpty": false,
          "exceededLimit": false,
          "totalLines": 54,
          "totalChars": 1254
        }
      }
    }
  },
  "session_id": "<uuid>"
}
```

#### Tool call types

**Read file tool:**

- **Started**: `tool_call.readToolCall.args` contains `{ "path": "file.txt" }`
- **Completed**: `tool_call.readToolCall.result.success` contains file metadata and content

**Write file tool:**

- **Started**: `tool_call.writeToolCall.args` contains `{ "path": "file.txt", "fileText": "content...", "toolCallId": "id" }`
- **Completed**: `tool_call.writeToolCall.result.success` contains `{ "path": "/absolute/path", "linesCreated": 19, "fileSize": 942 }`

**Other tools:**

- May use `tool_call.function` structure with `{ "name": "tool_name", "arguments": "..." }`

#### Terminal result

The final event emitted on successful completion:

```
{
  "type": "result",
  "subtype": "success",
  "duration_ms": 1234,
  "duration_api_ms": 1234,
  "is_error": false,
  "result": "<full assistant text>",
  "session_id": "<uuid>",
  "request_id": "<optional request id>"
}
```

### Example sequence

Here's a representative NDJSON sequence showing the typical flow of events:

```
{"type":"system","subtype":"init","apiKeySource":"login","cwd":"/Users/user/project","session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff","model":"Claude 4 Sonnet","permissionMode":"default"}
{"type":"user","message":{"role":"user","content":[{"type":"text","text":"Read README.md and create a summary"}]},"session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"I'll read the README.md file"}]},"session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff"}
{"type":"tool_call","subtype":"started","call_id":"toolu_vrtx_01NnjaR886UcE8whekg2MGJd","tool_call":{"readToolCall":{"args":{"path":"README.md"}}},"session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff"}
{"type":"tool_call","subtype":"completed","call_id":"toolu_vrtx_01NnjaR886UcE8whekg2MGJd","tool_call":{"readToolCall":{"args":{"path":"README.md"},"result":{"success":{"content":"# Project\n\nThis is a sample project...","isEmpty":false,"exceededLimit":false,"totalLines":54,"totalChars":1254}}}},"session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"Based on the README, I'll create a summary"}]},"session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff"}
{"type":"tool_call","subtype":"started","call_id":"toolu_vrtx_01Q3VHVnWFSKygaRPT7WDxrv","tool_call":{"writeToolCall":{"args":{"path":"summary.txt","fileText":"# README Summary\n\nThis project contains...","toolCallId":"toolu_vrtx_01Q3VHVnWFSKygaRPT7WDxrv"}}},"session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff"}
{"type":"tool_call","subtype":"completed","call_id":"toolu_vrtx_01Q3VHVnWFSKygaRPT7WDxrv","tool_call":{"writeToolCall":{"args":{"path":"summary.txt","fileText":"# README Summary\n\nThis project contains...","toolCallId":"toolu_vrtx_01Q3VHVnWFSKygaRPT7WDxrv"},"result":{"success":{"path":"/Users/user/project/summary.txt","linesCreated":19,"fileSize":942}}}},"session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"Done! I've created the summary in summary.txt"}]},"session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff"}
{"type":"result","subtype":"success","duration_ms":5234,"duration_api_ms":5234,"is_error":false,"result":"I'll read the README.md fileBased on the README, I'll create a summaryDone! I've created the summary in summary.txt","session_id":"c6b62c6f-7ead-4fd6-9922-e952131177ff","request_id":"10e11780-df2f-45dc-a1ff-4540af32e9c0"}
```

## Text format

The `text` output format provides only the final assistant message without any intermediate progress updates or tool call summaries. This is the cleanest output format for scripts that only need the agent's final response.

This format is ideal when you want just the answer or final message from the agent, without any progress indicators or tool execution details.

### Example output

```
The command to move this branch onto main is `git rebase --onto main HEAD~3`.

```

Only the final assistant message (after the last tool call) is output, with no tool call summaries or intermediate text.

## Implementation notes

- Each event is emitted as a single line terminated by `\n`
- `thinking` events are suppressed in print mode and will not appear in any output format
- Field additions may occur over time in a backward-compatible way (consumers should ignore unknown fields)
- The `json` format waits for completion before outputting results
- The `stream-json` format outputs complete agent messages
- The `--stream-partial-output` flag provides real-time text deltas for character-level streaming (only works with `stream-json` format)
- Tool call IDs can be used to correlate start/completion events
- Session IDs remain consistent throughout a single agent execution

