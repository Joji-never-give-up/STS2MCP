---
name: sts2-mcp-player
description: Play or validate Slay the Spire 2 through the STS2MCP MCP server (name sts2). Uses health_check, get_game_state (dict), get_available_actions, act, and bundled game metadata tools—same guided loop as sts2-ai-agent. Use for singleplayer routing by state_type, or granular tools; mp_* for multiplayer. State-first; no stale indexes.
---

# STS2 MCP Player (STS2MCP)

Use this skill when driving **this repository’s** Python MCP bridge (`mcp/server.py`). The MCP server name in client config is **`sts2`** (see project `README.md`).

## MCP server

- **Server id:** `sts2` (not `sts2-ai-agent`).
- **Mod HTTP:** default `http://localhost:15526` (override with `python server.py --host … --port …`).

## Guided loop (singleplayer, STS2-Agent–compatible)

These tools are implemented in `mcp/server.py` + `mcp/agent_layer.py`:

1. `health_check` once at session start.
2. `get_game_state` → **dict** with `available_actions`, `screen`, `session`, `player`, `battle`, `raw`, …
3. Optionally `get_available_actions` if you want the action list without full state.
4. `act(action=..., card_index=?, target_index=?, option_index=?)` — only use **`name`** values that appear in `available_actions`.
5. `get_relevant_game_data` / `get_game_data_item` / `get_game_data_items` for English card/relic/monster metadata (`mcp/data/eng`).

If `get_game_state` returns `ok: false` (multiplayer / HTTP 409 on singleplayer API), **stop using** `act` and switch to **`mp_get_game_state`** and **`mp_*`** tools only.

## Granular tools (alternative)

- `fetch_game_state(format="json"|"markdown")` — string payload.
- Per-screen tools: `combat_play_card`, `map_choose_node`, `rewards_claim`, … — see [`mcp/README.md`](../../../mcp/README.md).

## Routing by `state_type`

Read **`raw.state_type`** (or top-level **`screen`**) from `get_game_state`. Map screens to `act` names — see [`references/screen-playbooks.md`](references/screen-playbooks.md) and [`docs/raw-simplified.md`](../../../docs/raw-simplified.md).

**Not available on STS2MCP HTTP API:** main-menu / timeline / character-select / embark (no `continue_run`, `embark`, etc.). Handle those **in the game UI**, then resume the MCP loop once `state_type` is in-run (`map`, `monster`, …).

## Game data priority

- Do not guess card text, relic effects, or monster stats from memory when metadata tools exist.
- Prefer `get_relevant_game_data` → then `get_game_data_item` / `get_game_data_items`.

## Non-negotiable state rules

- Recompute **every** index from the latest `get_game_state` / `fetch_game_state` payload.
- After `act`, always `get_game_state` again before the next `act`.
- Treat **`raw`** as the full mod JSON; **`available_actions`** is synthesized for `act` — if something is missing, fall back to **granular** tools from `mcp/README.md`.

## References (this repo)

- [`references/screen-playbooks.md`](references/screen-playbooks.md) — STS2MCP `state_type` guardrails.
- [`references/remote-connection.md`](references/remote-connection.md) — server name `sts2`.
- [`references/debug-and-validation.md`](references/debug-and-validation.md) — validation notes.
- [`AGENTS.md`](../../../AGENTS.md) — strategy + polling.
- [`mcp/README.md`](../../../mcp/README.md) — full tool table (agent + granular + limitations vs sts2-ai-agent).

## Starter prompt template

```text
使用 sts2-mcp-player：MCP 服务器名为 sts2（本仓库 mcp/server.py）。
单机流程：health_check → get_game_state（字典）→ 只用 available_actions 里出现的 name 调用 act → 重复。
需要词条时用 get_relevant_game_data。不要用旧索引。
联机时改用 mp_get_game_state 与 mp_*，不要用单机的 get_game_state/act。
主菜单/选角请在游戏内操作，API 无法代点。
```
