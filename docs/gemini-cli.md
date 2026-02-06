# Gemini CLI

Gemini CLI is an open-source AI agent that brings the power of Google's Gemini models directly into your terminal. It provides lightweight, direct access to Gemini with a 1M token context window, built-in tools for file operations, shell commands, web fetching, and Google Search grounding. The CLI is designed for developers who work primarily in the command line, offering free tier access (60 requests/min, 1,000 requests/day) with a personal Google account, MCP (Model Context Protocol) support for custom integrations, and extensibility through custom commands and extensions.

The core architecture consists of three main packages: the CLI package (`packages/cli`) which handles the terminal UI and user interactions using Ink/React, the core package (`packages/core`) which manages tool execution and Gemini API communication, and the test utilities package. Gemini CLI supports multiple authentication methods including Google OAuth, Gemini API keys, and Vertex AI for enterprise deployments. It features hierarchical context files (GEMINI.md) for project-specific instructions, session management with checkpointing, sandboxed execution environments, and comprehensive telemetry options.

## Installation

Install Gemini CLI globally via npm or run directly with npx.

```bash
# Run instantly without installation
npx @google/gemini-cli

# Install globally with npm
npm install -g @google/gemini-cli

# Install stable, preview, or nightly versions
npm install -g @google/gemini-cli@latest    # stable
npm install -g @google/gemini-cli@preview   # weekly preview
npm install -g @google/gemini-cli@nightly   # daily nightly

# Install via Homebrew (macOS/Linux)
brew install gemini-cli
```

## Authentication

Configure authentication using environment variables or OAuth flow.

```bash
# Option 1: Login with Google (OAuth) - Free tier included
gemini
# Select "Login with Google" and follow the browser authentication flow

# For Gemini Code Assist License users, set project first
export GOOGLE_CLOUD_PROJECT="your-project-id"
gemini

# Option 2: Gemini API Key
export GEMINI_API_KEY="your-api-key-from-aistudio.google.com/apikey"
gemini

# Option 3: Vertex AI (Enterprise)
export GOOGLE_API_KEY="your-google-cloud-api-key"
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
gemini
```

## Basic CLI Usage

Start interactive sessions or run in headless mode for automation.

```bash
# Start interactive session in current directory
gemini

# Include additional directories in workspace
gemini --include-directories ../lib,../docs

# Use a specific model
gemini -m gemini-2.5-flash

# Start with an initial prompt
gemini -i "explain this codebase"

# Non-interactive mode (headless) for scripts
gemini -p "What is machine learning?"

# Headless with JSON output for programmatic processing
gemini -p "Explain the architecture" --output-format json

# Streaming JSON for real-time event monitoring
gemini -p "Run tests and deploy" --output-format stream-json

# Auto-approve all tool calls (YOLO mode)
gemini -p "fix all lint errors" --yolo

# Auto-approve only edit operations
gemini --approval-mode auto_edit

# Resume a previous session
gemini --resume latest
gemini --resume 5
gemini --resume a1b2c3d4-e5f6-7890-abcd-ef1234567890

# List available sessions
gemini --list-sessions
```

## Slash Commands

Built-in commands for session control, memory management, and CLI configuration.

```bash
# Get help
/help

# Display available tools
/tools
/tools desc    # With descriptions

# Memory management (GEMINI.md context files)
/memory show      # Display loaded context
/memory refresh   # Reload all context files
/memory add <text>  # Add to AI memory
/memory list      # List context file paths

# Chat session management
/chat save my-checkpoint     # Save conversation state
/chat resume my-checkpoint   # Resume from checkpoint
/chat list                   # List saved checkpoints
/chat delete my-checkpoint   # Delete checkpoint
/chat share output.md        # Export conversation

# Session browser for resuming previous sessions
/resume

# Compression and optimization
/compress    # Summarize chat to save tokens
/clear       # Clear terminal screen

# Model and settings
/model       # Open model selection dialog
/settings    # Open settings editor
/theme       # Change visual theme
/auth        # Change authentication method

# MCP server management
/mcp         # List configured MCP servers
/mcp desc    # Show server descriptions
/mcp auth    # Manage OAuth for MCP servers
/mcp refresh # Restart and re-discover tools

# Extension management
/extensions  # List active extensions

# Restore file state (requires checkpointing enabled)
/restore              # List available checkpoints
/restore <tool_id>    # Restore to specific checkpoint

# Rewind conversation and file changes
/rewind    # Browse and rewind interactions (or press Esc twice)

# Session statistics
/stats     # Show token usage, cached savings, duration

# Manage additional directories
/directory add ../other-project
/directory show

# Generate project context file
/init      # Create tailored GEMINI.md for current project

# Toggle vim mode
/vim

# File a bug report
/bug Title of the bug

# Exit
/quit
```

## At Commands (@) - File Context Injection

Include file or directory contents directly in your prompts.

```bash
# Include a specific file
> @README.md Explain this documentation

# Include directory contents
> @src/components/ Summarize these React components

# Multiple files
> @package.json @tsconfig.json Review my project configuration

# Escape spaces in paths
> @My\ Documents/file.txt What is this about?

# Git-aware filtering automatically excludes node_modules, .git, etc.
> @./  # Include current directory (respects .gitignore)
```

## Shell Mode (!)

Execute shell commands directly from within Gemini CLI.

```bash
# Execute single shell command
> !git status
> !npm test
> !ls -la

# Toggle shell mode (all input becomes shell commands)
> !
# Now in shell mode - type commands directly
ls
git diff
exit  # or type ! again to exit shell mode

# Commands set GEMINI_CLI=1 environment variable for detection
```

## Headless Mode with JSON Output

Structured output for automation, CI/CD pipelines, and scripting.

```bash
# Basic JSON output
gemini -p "What is the capital of France?" --output-format json
# Output:
# {
#   "response": "The capital of France is Paris.",
#   "stats": {
#     "models": { "gemini-2.5-pro": { "api": {...}, "tokens": {...} } },
#     "tools": { "totalCalls": 0, "totalSuccess": 0, ... },
#     "files": { "totalLinesAdded": 0, "totalLinesRemoved": 0 }
#   }
# }

# Parse response with jq
result=$(gemini -p "Explain Docker" --output-format json)
echo "$result" | jq -r '.response'

# Code review automation
cat src/auth.py | gemini -p "Review this code for security issues" > review.txt

# Generate commit messages
git diff --cached | gemini -p "Write a commit message" --output-format json | jq -r '.response'

# Batch file analysis
for file in src/*.py; do
    gemini -p "Find bugs in this code" --output-format json < "$file" | \
        jq -r '.response' > "reports/$(basename "$file").analysis"
done

# Streaming JSON for real-time monitoring
gemini --output-format stream-json -p "Run tests"
# Output (JSONL - one JSON object per line):
# {"type":"init","timestamp":"...","session_id":"abc123","model":"gemini-2.5-pro"}
# {"type":"message","role":"user","content":"Run tests",...}
# {"type":"tool_use","tool_name":"Bash","parameters":{"command":"npm test"},...}
# {"type":"tool_result","tool_id":"...","status":"success","output":"...",...}
# {"type":"result","status":"success","stats":{...},...}
```

## Configuration (settings.json)

Configure Gemini CLI through JSON settings files with hierarchical precedence.

```json
// User settings: ~/.gemini/settings.json
// Project settings: .gemini/settings.json
{
  "general": {
    "vimMode": true,
    "preferredEditor": "code",
    "previewFeatures": false,
    "checkpointing": { "enabled": true },
    "sessionRetention": {
      "enabled": true,
      "maxAge": "30d",
      "maxCount": 100
    }
  },
  "ui": {
    "theme": "GitHub",
    "hideBanner": false,
    "hideTips": false,
    "showLineNumbers": true,
    "showCitations": false,
    "useAlternateBuffer": false,
    "customWittyPhrases": ["Thinking deeply...", "Processing..."]
  },
  "model": {
    "name": "gemini-2.5-pro",
    "maxSessionTurns": -1,
    "compressionThreshold": 0.5,
    "summarizeToolOutput": {
      "run_shell_command": { "tokenBudget": 2000 }
    }
  },
  "tools": {
    "sandbox": "docker",
    "autoAccept": false,
    "allowed": ["run_shell_command(git status)", "run_shell_command(npm test)"],
    "exclude": ["dangerous_tool"],
    "enableToolOutputTruncation": true
  },
  "context": {
    "fileName": ["GEMINI.md", "CONTEXT.md"],
    "includeDirectories": ["../shared-lib", "~/common-utils"],
    "fileFiltering": {
      "respectGitIgnore": true,
      "respectGeminiIgnore": true,
      "enableFuzzySearch": true
    }
  },
  "privacy": {
    "usageStatisticsEnabled": true
  },
  "security": {
    "disableYoloMode": false,
    "blockGitExtensions": false,
    "environmentVariableRedaction": {
      "enabled": true,
      "allowed": ["MY_PUBLIC_KEY"],
      "blocked": ["INTERNAL_SECRET"]
    }
  },
  "telemetry": {
    "enabled": false,
    "target": "local",
    "otlpEndpoint": "http://localhost:4317",
    "logPrompts": false
  },
  "experimental": {
    "enableAgents": false,
    "skills": false,
    "codebaseInvestigatorSettings": {
      "enabled": true,
      "maxNumTurns": 10,
      "maxTimeMinutes": 3
    }
  }
}
```

## MCP Server Configuration

Configure Model Context Protocol servers for custom tool integrations.

```json
// In settings.json
{
  "mcpServers": {
    // Python MCP server via stdio
    "pythonTools": {
      "command": "python",
      "args": ["-m", "my_mcp_server", "--port", "8080"],
      "cwd": "./mcp-servers/python",
      "env": {
        "DATABASE_URL": "$DB_CONNECTION_STRING",
        "API_KEY": "${EXTERNAL_API_KEY}"
      },
      "timeout": 15000,
      "trust": false
    },

    // Node.js MCP server (trusted - no confirmation prompts)
    "nodeServer": {
      "command": "node",
      "args": ["dist/server.js", "--verbose"],
      "cwd": "./mcp-servers/node",
      "trust": true
    },

    // Docker-based MCP server
    "dockerizedServer": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "API_KEY", "my-mcp-server:latest"],
      "env": { "API_KEY": "$EXTERNAL_SERVICE_TOKEN" }
    },

    // HTTP-based MCP server
    "httpServer": {
      "httpUrl": "http://localhost:3000/mcp",
      "headers": {
        "Authorization": "Bearer $API_TOKEN",
        "Content-Type": "application/json"
      },
      "timeout": 5000
    },

    // SSE-based MCP server with OAuth
    "sseServer": {
      "url": "https://api.example.com/sse",
      "authProviderType": "dynamic_discovery"
    },

    // MCP server with tool filtering
    "filteredServer": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "includeTools": ["safe_tool", "file_reader"],
      "excludeTools": ["dangerous_tool"]
    },

    // Google Cloud with Service Account Impersonation
    "gcpServer": {
      "url": "https://my-service.run.app/sse",
      "authProviderType": "service_account_impersonation",
      "targetAudience": "CLIENT_ID.apps.googleusercontent.com",
      "targetServiceAccount": "sa@project.iam.gserviceaccount.com"
    }
  },

  // Global MCP settings
  "mcp": {
    "allowed": ["pythonTools", "nodeServer"],
    "excluded": ["experimental-server"]
  }
}
```

## MCP Server CLI Management

Manage MCP servers from the command line.

```bash
# Add stdio server
gemini mcp add my-server python server.py -- --arg value
gemini mcp add -e API_KEY=123 -e DEBUG=true my-server /path/to/server arg1 arg2

# Add HTTP server
gemini mcp add --transport http http-server https://api.example.com/mcp/
gemini mcp add --transport http -H "Authorization: Bearer token" secure-http https://api.example.com/mcp/

# Add SSE server
gemini mcp add --transport sse sse-server https://api.example.com/sse/

# Add with options
gemini mcp add --timeout 30000 --trust --scope project my-server ./server.py

# List configured servers
gemini mcp list
# Output:
# ✓ stdio-server: command: python3 server.py (stdio) - Connected
# ✓ http-server: https://api.example.com/mcp (http) - Connected
# ✗ sse-server: https://api.example.com/sse (sse) - Disconnected

# Remove server
gemini mcp remove my-server
gemini mcp remove --scope user my-server
```

## Creating Extensions

Create custom extensions with MCP servers, commands, and context.

```bash
# Create new extension from template
gemini extensions new my-extension mcp-server

# Extension structure:
# my-extension/
# ├── gemini-extension.json    # Extension manifest
# ├── example.ts               # MCP server source
# ├── package.json
# ├── tsconfig.json
# ├── GEMINI.md                # Optional context
# ├── commands/                # Custom commands
# │   └── fs/
# │       └── grep-code.toml
# └── skills/                  # Agent skills
#     └── security-audit/
#         └── SKILL.md

# Build and link for development
cd my-extension
npm install
npm run build
gemini extensions link .

# Install from GitHub
gemini extensions install https://github.com/user/my-extension

# Manage extensions
gemini extensions list
gemini extensions update
gemini extensions uninstall my-extension
gemini extensions enable my-extension
gemini extensions disable my-extension
```

```json
// gemini-extension.json
{
  "name": "my-extension",
  "version": "1.0.0",
  "contextFileName": "GEMINI.md",
  "mcpServers": {
    "nodeServer": {
      "command": "node",
      "args": ["${extensionPath}${/}dist${/}example.js"],
      "cwd": "${extensionPath}"
    }
  }
}
```

```typescript
// example.ts - MCP Server
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const server = new McpServer({ name: 'my-server', version: '1.0.0' });

// Register a tool
server.registerTool(
  'fetch_data',
  {
    description: 'Fetches data from an API',
    inputSchema: z.object({ query: z.string() }).shape,
  },
  async ({ query }) => {
    const response = await fetch(`https://api.example.com/search?q=${query}`);
    const data = await response.json();
    return { content: [{ type: 'text', text: JSON.stringify(data) }] };
  },
);

// Register a prompt (becomes a slash command)
server.registerPrompt(
  'summarize',
  {
    title: 'Summarize Text',
    description: 'Summarize the provided text',
    argsSchema: { text: z.string() },
  },
  ({ text }) => ({
    messages: [{ role: 'user', content: { type: 'text', text: `Summarize: ${text}` } }],
  }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Custom Commands

Create reusable prompt templates with TOML files.

```toml
# commands/dev/review.toml
prompt = """
Review the following code for:
1. Security vulnerabilities
2. Performance issues
3. Code style violations

Code to review:
@{{{args}}}
"""

# commands/git/commit-msg.toml
prompt = """
Generate a concise commit message for these changes:
!{git diff --cached}
"""

# Usage: /dev:review src/main.ts
# Usage: /git:commit-msg
```

## Context Files (GEMINI.md)

Provide project-specific instructions and context.

```markdown
<!-- ~/.gemini/GEMINI.md (global) -->
<!-- .gemini/GEMINI.md (project) -->
<!-- subdirectory/GEMINI.md (local) -->

# Project: My TypeScript Library

## General Instructions
- Follow existing coding style
- Add JSDoc comments to all functions
- Use TypeScript 5.0+ features
- Prefer functional programming patterns

## Coding Style
- 2 spaces for indentation
- Interface names prefixed with `I` (e.g., `IUserService`)
- Private members prefixed with `_`
- Always use strict equality (`===`)

## API Guidelines
- Use `fetchWithRetry` utility for all HTTP requests
- Include robust error handling
- Log all API calls

## Dependencies
- Avoid new dependencies unless necessary
- Document reason for any new dependency
```

## Environment Variables

Configure Gemini CLI through environment variables.

```bash
# Authentication
export GEMINI_API_KEY="your-api-key"
export GOOGLE_API_KEY="your-google-cloud-api-key"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Model configuration
export GEMINI_MODEL="gemini-2.5-flash"

# Sandbox configuration
export GEMINI_SANDBOX=docker  # true, false, docker, podman

# Telemetry
export GEMINI_TELEMETRY_ENABLED=true
export GEMINI_TELEMETRY_TARGET=gcp
export GEMINI_TELEMETRY_OTLP_ENDPOINT="http://localhost:4317"

# System prompt override
export GEMINI_SYSTEM_MD=true  # Use .gemini/system.md
export GEMINI_WRITE_SYSTEM_MD=true  # Write built-in prompt to file

# Proxy
export HTTPS_PROXY="http://proxy.example.com:8080"

# Debug mode
export DEBUG=true

# Disable colors
export NO_COLOR=1

# Custom CLI title
export CLI_TITLE="My AI Assistant"
```

## Sandboxing

Run tools in isolated environments for security.

```bash
# Enable sandbox via flag
gemini --sandbox
gemini -s

# Sandbox is auto-enabled with YOLO mode
gemini --yolo

# Custom sandbox Dockerfile
# .gemini/sandbox.Dockerfile
# FROM gemini-cli-sandbox
# RUN apt-get update && apt-get install -y my-tools

# Build and use custom sandbox
BUILD_SANDBOX=1 gemini -s
```

## Summary

Gemini CLI serves as a powerful bridge between developers and Google's Gemini AI models, enabling sophisticated AI-assisted workflows directly from the terminal. The primary use cases include code understanding and generation (querying large codebases, debugging, generating documentation), automation (CI/CD integration, batch processing, scripting with JSON output), and extending capabilities through MCP servers and custom extensions. The CLI excels at tasks requiring deep codebase analysis, multi-file operations, and iterative development workflows where maintaining context across interactions is critical.

Integration patterns typically involve combining headless mode with JSON output for automation pipelines, configuring MCP servers for domain-specific tools (databases, APIs, cloud services), and creating custom extensions for team-specific workflows. The hierarchical configuration system (system defaults, user settings, project settings) enables flexible deployment from individual developer machines to enterprise environments with centralized policy controls. For CI/CD integration, the streaming JSON output format provides real-time visibility into AI agent actions, while the session management features enable long-running development workflows with checkpointing and restoration capabilities.
