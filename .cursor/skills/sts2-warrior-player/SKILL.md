---
name: sts2-warrior-player
description: Play Slay the Spire 2 as Ironclad (warrior) only via STS2MCP MCP (server sts2). Strict state-first loop with health_check, get_game_state, act. Strategy follows Mobalytics T0 archetypes (Strength, Block, Exhaust, Bloodletting, Strike). Singleplayer guided tools; use mp_* only in co-op. Use when user wants warrior-only runs or Ironclad pickups/pathing.
---

# STS2 Warrior (Ironclad) Player — STS2MCP

Use this skill to run STS2 with one goal: play as **Ironclad** (`IRONCLAD` / The Ironclad) from live state, using **this repo’s** MCP server **`sts2`**.

**Meta reference:** [Mobalytics — STS2 Ironclad Guide](https://mobalytics.gg/slay-the-spire-2/characters/ironclad-guide) · [Ironclad Cards](https://mobalytics.gg/slay-the-spire-2/ironclad-cards). **Always** let `get_game_state` / `get_relevant_game_data` override theory when they disagree with memory.

## Trigger

- Play **warrior / Ironclad / 战士** only.
- Warrior-focused rewards, shops, pathing — still **state-first** (`get_game_state` → `act`).
- Avoid other characters.

## Runtime requirements

- **MCP server name:** `sts2` (see project `README.md` and `mcp/server.py`).
- **Singleplayer guided loop:** `health_check` → `get_game_state` (dict) → `get_available_actions` (optional) → `act` → repeat.
- **Metadata:** `get_relevant_game_data` / `get_game_data_item` for card/relic text (`mcp/data/eng`).
- **Multiplayer:** if `get_game_state` returns `ok: false` or singleplayer API is wrong mode, use **`mp_get_game_state`** and **`mp_*`** only — do not use guided `act` for co-op.
- Do not rely on sts2-ai-agent–only features (menu `embark`, `wait_for_event`, handoff tools) — see **`mcp/README.md`** “Not ported”.

## Non-negotiable loop

1. `health_check` once at session start.
2. Before every decision: **`get_game_state`**.
3. Only call **`act`** with `action` names present in **`available_actions`** (from the same payload).
4. After each `act`, read the result and **`get_game_state`** again; never reuse old hand/reward/shop indices.
5. Resolve **`raw.state_type`** before acting; follow [`../sts2-mcp-player/references/screen-playbooks.md`](../sts2-mcp-player/references/screen-playbooks.md).

## Character lock: Ironclad only

- **STS2MCP does not expose character select / embark over HTTP.** Start or continue a run as **Ironclad in the game UI** before heavy agent play.
- Once in run, verify **`raw.player.character`** (or equivalent) matches Ironclad / The Ironclad. If another character, **stop** and report — do not continue “as warrior.”
- Never switch character unless the user explicitly overrides.

---

## Macro run management (do not skip)

Ironclad is **beginner-friendly** but **low ceiling** if you bleed HP and thicken the deck without a plan. **Starting relic:** `Burning Blood` — small heal after each combat (not a substitute for safe pathing).

- **HP budget:** Act 2+ still needs rests / shops / potions when the map allows. If HP is critically low, **prioritize safe nodes and campfires** over greed.
- **Gold → value:** removals, high-impact relics/cards, potions that buy turns.
- **Elites:** Ironclad likes time to scale; **over-eliting while weak** is a common loss. Path from **`raw.map`** only.
- **Deck shape:** pick toward **one primary archetype** (below); use removals / **Brand**-style tools when the deck gets fuzzy.

---

## T0 Archetypes (Mobalytics roadmap)

Declare internally which line you are **committing to** (hybrid early, then converge). Use English card ids from state/metadata; resolve with `get_game_data_item` when unsure.

### 1. Strength（力量）

**Idea:** Stack **Strength**, then **multi-hit** attacks.

**Key cards (guide):** `TWIN_STRIKE`; `FIGHT_ME`, `INFLAME`, `RUPTURE`, `WHIRLWIND`; `DEMON_FORM`, `BRAND`, Thrash (if in data).

**Relics (examples):** Anchor, Horn Cleat, Permafrost; Brimstone; Ruined Helmet; Sword of Jade.

**Combat tips:** Vulnerable multiplies big Strength turns; extra Energy helps setup + payoff.

---

### 2. Block（格挡 / Body Slam）

**Idea:** Block first, convert to damage — **Body Slam**; **Barricade** retention when available.

**Key cards:** `BODY_SLAM`, `SHRUG_IT_OFF`, `TRUE_GRIT`; Flame Barrier, `TAUNT` (upgraded = 2 Vulnerable → pairs with **Colossus**), Stone Armor; **Juggernaut**, **Barricade**, **Crimson Mantle** (watch **Unmovable** clash), **Impervious**.

**Relics:** Cloak Clasp (triggers Juggernaut), Fresnel Lens, Vambrace, Sai, Parrying Shield, Pael's Legion, Bronze Scales.

**Combat tips:** Plating-style armor; Weak / reducing enemy Strength preserves block.

---

### 3. Exhaust（消耗）

**Idea:** Corruption + Dark Embrace + Feel No Pain; **Juggernaut** adds damage. Finisher-oriented (Ashen Strike, Body Slam, Pact's End) without dead-branch loops.

**Key cards:** `CORRUPTION`, `TRUE_GRIT`, `BODY_SLAM`; Ashen Strike, `BURNING_PACT` (lower priority once `DARK_EMBRACE`), **Evil Eye**, `FEEL_NO_PAIN`, **Forgotten Ritual**; `DARK_EMBRACE`, `BRAND` (less mandatory with `CORRUPTION` online), **Offering**, **Pact's End**, Thrash.

**Relics:** Charon's Ashes, Forgotten Soul, Burning Sticks, Joss Paper.

**Combat tips:** Vulnerable for finishers.

---

### 4. Bloodletting（自伤 / Rupture）

**Idea:** Self-damage payoffs; **Rupture** / **Inferno**; multi-hit scales with Strength.

**Key cards:** `BLOODLETTING`, Breakthrough; `RUPTURE`, Inferno, Hemokinesis; **Crimson Mantle**, `BRAND`, **Offering**, **Feed** (flat damage + max HP buffer), **Tear Asunder**.

**Relics:** Centennial Puzzle, Demon Tongue, Self-Forming Clay.

**Combat tips:** Pain curse can be fuel; **Rupture** + upgrades; **Crimson Mantle** + **Inferno** for consistent self-damage.

---

### 5. Strike（Perfected Strike）

**Idea:** **Perfected Strike** scales with “Strike” names; strong early with starter Strikes; avoid stuffing bad Strikes late.

**Key cards:** `PERFECTED_STRIKE`, `TWIN_STRIKE`, `POMMEL_STRIKE`, Breakthrough, Tremble; `TAUNT`, `EXPECT_A_FIGHT`; `PYRE`, Hellraiser (draw/infinite lines), Colossus, Cruelty.

**Relics:** Strike Dummy, Intimidating Helmet, Ancient energy relics.

**Combat tips:** Keep some block; `UPPERCUT` for utility if Energy allows.

---

## Choosing a line from live state

1. Read **relics**, **offers**, **deck**, **HP**, **map** from `get_game_state` / `raw`.
2. Pick the **closest T0 shell** for the next 1–2 acts.
3. On rewards, take cards that **advance that shell** or **fix the biggest hole** (draw, energy, block).
4. If nothing fits, **skip** or take neutral utility (`SHRUG_IT_OFF`, draw, efficient damage).

---

## Screen routing (STS2MCP + `act`)

Use **`act`** names from `available_actions`; **`state_type`** in `raw`. Menus / character select are **not** in the MCP API — use the game UI.

| state_type | Focus |
|------------|--------|
| `map` | Path toward elites/rests per plan; `choose_map_node` |
| `monster` / `elite` / `boss` | `play_card`, `end_turn`, potions — Ironclad sequencing per archetype |
| `rewards` / `card_reward` | Pick/skip toward committed line |
| `shop` / `fake_merchant` | `buy_card` (shop index), value buys |
| `rest_site` | Heal vs upgrade vs smith per risk |
| `event` | Event options from `raw` |

Details: [`../sts2-mcp-player/references/screen-playbooks.md`](../sts2-mcp-player/references/screen-playbooks.md).

## Reporting during play

At each pivot (shop, elite/boss, rest, act transition):

- **archetype:** Strength / Block / Exhaust / Bloodletting / Strike / hybrid (early)
- **Mobalytics** subsection
- **card / relic** taken or skipped
- **risk** next 1–2 fights
- **next** priority

## Starter prompt template

```text
使用 sts2-warrior-player，MCP 名 sts2。只玩战士（IRONCLAD / The Ironclad）。
开局先在游戏内选角并开始或继续一局战士。
单机：health_check → get_game_state → 仅用 available_actions 中的 name 调用 act → 重复。
流派：Mobalytics Ironclad T0（Strength / Block / Exhaust / Bloodletting / Strike），以 get_game_state 与 get_relevant_game_data 为准。
禁止复用旧索引。联机时只用 mp_*。
```
