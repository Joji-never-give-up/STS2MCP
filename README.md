<p align="center">
  <img src="docs/teaser.png" alt="STS2 MCP" width="90%" />
</p>

<p align="center"><em>An Experimental Research Project to Fully-Automate your Slay the Spire 2 Runs</em></p>

A mod for [**Slay the Spire 2**](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) that lets AI agents play the game. Exposes game state and actions via a localhost REST API, with an optional **Python MCP server** ([`mcp/server.py`](mcp/server.py)) for Claude Desktop, **Claude Code**, **Cursor**, and similar clients.

The MCP bridge includes:

- **Granular tools** — one tool per action (e.g. `combat_play_card`, `map_choose_node`, …). Raw state as a string: **`fetch_game_state`** (`markdown` or `json` text).
- **STS2-Agent–style guided tools (singleplayer)** — `health_check`, **`get_game_state`** (structured **dict** with synthesized `available_actions`), **`get_available_actions`**, **`act`**, plus **`get_game_data_item` / `get_game_data_items` / `get_relevant_game_data`** backed by bundled English metadata in [`mcp/data/eng`](mcp/data/eng). See [`mcp/README.md`](mcp/README.md) for the full tool list and what is **not** ported (menu actions, SSE waits, planner handoff, etc.).
- **Agent skills** — [`sts2-mcp-player`](.cursor/skills/sts2-mcp-player/SKILL.md) (general play) and [`sts2-warrior-player`](.cursor/skills/sts2-warrior-player/SKILL.md) (Ironclad / Mobalytics-oriented). Same content is symlinked under [`.claude/skills/`](.claude/skills/) for **Claude Code** (`/sts2-mcp-player`, `/sts2-warrior-player`).

Singleplayer and multiplayer (co-op) supported. Tested against STS2 `v0.99.1`.

> [!warning]
> This mod allows external programs to read and control your game via a localhost API. Use at your own risk with runs you care less about.

> [!caution]
> Multiplayer support is in **beta** — expect bugs. Any multiplayer issues encountered with this mod installed are very likely caused by the mod, not the game. Please disable the mod and verify the issue persists before reporting bugs to the STS2 developers.

## For Players

### 1. Install the Mod

Grab a release from the [upstream project](https://github.com/Gennadiyev/STS2MCP/releases/latest) (or build from source below), then:

1. Copy `STS2_MCP.dll` and `STS2_MCP.json` to `<game_install>/mods/`
2. Launch the game and enable mods in settings (a consent dialog appears on first launch)
3. The mod starts an HTTP server on `localhost:15526` automatically

### 2. Connect an AI client (MCP + skills)

**Requirements:** [Python 3.11+](https://www.python.org/) and [uv](https://docs.astral.sh/uv/). **Clone this repo** and use an **absolute path** to its `mcp/` directory in the config below.

#### MCP server (`sts2`)

Add this to **Cursor** MCP settings, **Claude Code** `.mcp.json`, or **Claude Desktop** `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sts2": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/this/repo/mcp", "python", "server.py"]
    }
  }
}
```

The game must be running with the mod loaded (`localhost:15526` by default). The server accepts `--host` and `--port` if you changed the mod’s bind address. Use `--no-trust-env` if HTTP proxies break localhost in containers.

#### Cursor

Open the **repository root** as the workspace so [`.cursor/skills/`](.cursor/skills/) is loaded. Optional skills: [`sts2-mcp-player`](.cursor/skills/sts2-mcp-player/SKILL.md), [`sts2-warrior-player`](.cursor/skills/sts2-warrior-player/SKILL.md).

#### Claude Code

Use the same MCP JSON as above. Skills live under [`.claude/skills/`](.claude/skills/) (symlinks to `.cursor/skills/`). After restart, run **`/sts2-mcp-player`** or **`/sts2-warrior-player`**, or rely on auto-discovery from each skill’s `description`. The shortcut command [`/playsts2`](.claude/commands/playsts2.md) is a shorter gameplay prompt.

#### Everyone

Read [`AGENTS.md`](AGENTS.md) for strategy and polling tips, [`docs/raw-simplified.md`](docs/raw-simplified.md) for HTTP `state_type` ↔ actions, and [`mcp/README.md`](mcp/README.md) for the full tool surface (granular vs guided).

**Singleplayer guided loop:** `health_check` → `get_game_state` (dict) → `act` only with actions listed in `available_actions` → repeat; use `get_relevant_game_data` for card/relic text. **Multiplayer:** use `mp_get_game_state` and `mp_*` tools only — not the singleplayer `act` layer. Main menu / character select are **not** exposed over MCP; handle those in the game UI first.

## For Developers

### Build & Install

Requires [.NET 9 SDK](https://dotnet.microsoft.com/download/dotnet/9.0) and the base game.

**PowerShell** (recommended):

```powershell
# Pass game path directly:
.\build.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Slay the Spire 2"

# Or set it once and forget:
$env:STS2_GAME_DIR = "D:\SteamLibrary\steamapps\common\Slay the Spire 2"
.\build.ps1
```

The script builds `STS2_MCP.dll` into `out/STS2_MCP/`. Copy it along with the manifest JSON to `<game_install>/mods/` to install:

```
out/STS2_MCP/STS2_MCP.dll           ->  <game_install>/mods/STS2_MCP.dll
mod_manifest.json                   ->  <game_install>/mods/STS2_MCP.json
```

### Python MCP (this repo)

| Path | Role |
|------|------|
| [`mcp/server.py`](mcp/server.py) | FastMCP entry: granular tools + guided `health_check` / `get_game_state` / `act` / game-data tools |
| [`mcp/agent_layer.py`](mcp/agent_layer.py) | Maps `act` actions to the mod HTTP API |
| [`mcp/sts2_game_data.py`](mcp/sts2_game_data.py) | Loads [`mcp/data/eng`](mcp/data/eng) for metadata queries |

Run from `mcp/` with `uv sync` then `uv run python server.py` (or rely on the `uv run` args in your MCP client config).

## License

MIT

## FAQ

### Why let the AI play the game for me?

I start building this mod with the hope that I can co-op with an AI player. Singleplayer is originally just built for validation.

### You did not answer the question!

First of all, I play lots of games, including service games that has daily/weekly tasks. I really hoped that modern AI could save me from the grind, which, if you have tried one or more of the GUI agents, never really materialized. Let's face it: modern AI is still pretty bad at gaming because no one cares.

About my intention, as a researcher that loves playing games, the purpose of STS2MCP is to test AI models and agents in a rarely explored (we call it out-of-distribution) domain. Ultimately, this might turn into a benchmark for evaluating the reasoning and decision-making capabilities of different language models.

STS2 is just an example to show how good (or bad) current AI agents are at playing such games. **I have no intention to replace human players with AI, and I would definitely rather play STS2 myself** as a big fan of the game.

### Is this a cheat mod?

It can be, but it doesn't have to be. The mod itself does not alter the gameplay. It is just an interface that allows external programs to interact with the game. What you do with that interface is up to you.

### How many tokens do a run consume?

I evaluated on the Ironclad. Claude Sonnet 4.6 uses slightly more than 8M tokens (counting both input, output and tool responses) for a full run. GPT-5.4 averages 7.34M tokens. Depending on your prompt and model choice, it can be more or less.

### Do you have a roadmap for future features?

The project is still too early to have a clear roadmap. My current focus is to make sure the core features are stable and well-documented. However, I am open to suggestions and contributions from the community.

- Solidifying multiplayer features and fixing bugs is a priority
- Add support for in-game communication in multiplayer runs when collaborating with an AI agent
- Self-reflection and learning from past runs to improve future performance
- Benchmarking different models and agents is also on my mind
