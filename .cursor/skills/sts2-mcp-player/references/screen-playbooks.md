# Screen playbooks (STS2MCP)

Use **`raw.state_type`** from `get_game_state` (or `fetch_game_state` JSON). **`act`** uses names synthesized to match sts2-ai-agent (`play_card`, `end_turn`, `choose_map_node`, …). See **`docs/raw-simplified.md`** for the authoritative table.

## Menu / no run

- `state_type: menu` — **no MCP actions** for menu; start or continue a run in the **game UI**, then poll `get_game_state` until `state_type` is in-run.

## Map

- `map` — `act("choose_map_node", option_index=…)` using **`map.next_options`** indices from `raw`.

## Combat

- `monster` / `elite` / `boss` — `play_card`, `end_turn`, `use_potion`, `discard_potion` (via `act` with `option_index` for potion slots).
- `hand_select` — `select_deck_card`, `confirm_selection`, `cancel_selection` (mapped to combat/deck HTTP actions in `agent_layer`).

## Rewards

- `rewards` — `claim_reward` (per item index), then `proceed` when `can_proceed`.
- `card_reward` — `choose_reward_card`, `skip_reward_cards`.

## Event / rest / shop / treasure

- `event` — `choose_event_option`, `advance_dialogue` when `in_dialogue`.
- `rest_site` — `choose_rest_option`, `proceed` if `can_proceed`.
- `shop` / `fake_merchant` — `buy_card` (shop line index), `proceed`.
- `treasure` — `choose_treasure_relic`, `proceed`.

## Overlays

- `card_select`, `bundle_select`, `relic_select`, `crystal_sphere` — match `available_actions` names; Crystal Sphere may need **granular** tools (`crystal_sphere_*`) if `act` does not cover a step.

## Multiplayer

- If singleplayer API returns **409**, use **`mp_*`** tools only — do not use `act`.
