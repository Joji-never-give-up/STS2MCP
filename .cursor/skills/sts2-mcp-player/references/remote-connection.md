# MCP connection (STS2MCP)

## Server name

- Cursor / Claude MCP config: **`sts2`**
- Command (example): `uv run --directory /path/to/STS2MCP/mcp python server.py`
- Game mod listens on **`localhost:15526`** by default; pass `--port` / `--host` to `server.py` if you changed the mod.

## Loop

1. `health_check`
2. `get_game_state` (dict) → `get_available_actions` (optional) → `act`
3. For metadata: `get_relevant_game_data`, `get_game_data_item`, `get_game_data_items`

There is no separate `sts2-ai-agent-remote` in this project; use one `sts2` entry pointing at your local `mcp/` directory.
