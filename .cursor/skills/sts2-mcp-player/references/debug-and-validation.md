# Debug and validation (STS2MCP)

## What exists

- **Granular MCP tools** in `mcp/server.py` map 1:1 to HTTP `action` values — use them for harness-style tests.
- **`act`** + **`get_game_state`** — guided surface for agents (singleplayer).

## What does not exist (vs sts2-ai-agent)

- No `run_console_command`, no SSE `wait_for_event` in this bridge.
- No planner/combat handoff tools.

For full API details see **`docs/raw-full.md`**.
