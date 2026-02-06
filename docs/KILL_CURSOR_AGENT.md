# How to Kill Cursor-Agent Processes

If you need to stop cursor-agent processes after closing the terminal, use these commands:

## Find Cursor-Agent Processes

```bash
# Find all cursor-agent process IDs
pgrep -f "cursor-agent"

# See full process details
ps aux | grep -i "cursor-agent" | grep -v grep
```

## Kill Cursor-Agent Processes

```bash
# Kill all cursor-agent processes (graceful)
pkill -f "cursor-agent"

# Force kill if needed (use with caution)
pkill -9 -f "cursor-agent"
```

## Kill Specific Process by PID

```bash
# First find the PID
pgrep -f "cursor-agent"

# Then kill it
kill <PID>

# Or force kill
kill -9 <PID>
```

## Verify Process is Killed

```bash
# Check if process still exists
pgrep -f "cursor-agent" || echo "No cursor-agent processes found"

# Or check with ps
ps aux | grep -i "cursor-agent" | grep -v grep
```

## Common Cursor-Agent Process Types

- **worker-server**: Background service (usually safe to kill)
- **CLI processes**: Active code generation (kill if you want to stop generation)

## Notes

- The worker-server is a persistent service and will restart automatically when cursor-agent is used again
- Killing active CLI processes will stop any ongoing code generation
- Use `kill` (SIGTERM) first, then `kill -9` (SIGKILL) if the process doesn't respond

