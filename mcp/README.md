# MCP Tools

## STS2-Agent–compatible (singleplayer)

These mirror the **sts2-ai-agent** guided surface: one `act()` plus metadata tools. They sit on top of the same HTTP API as the granular tools below.

| Tool | Description |
|---|---|
| `health_check()` | Mod HTTP reachable (409 in multiplayer still counts as “mod up”). |
| `get_game_state()` | **Dict** with `available_actions`, `screen`, `session`, `run`, `player`, `battle`, … plus `raw` mod JSON. |
| `get_available_actions()` | Same action list as embedded in `get_game_state`. |
| `act(action, card_index?, target_index?, option_index?)` | Dispatch STS2-Agent-style names (`play_card`, `end_turn`, `choose_map_node`, …). |
| `get_game_data_item(collection, item_id)` | Bundled English metadata (from `mcp/data/eng`). |
| `get_game_data_items(collection, item_ids)` | Batch metadata by comma-separated ids. |
| `get_relevant_game_data(collection, item_ids)` | Trimmed fields using current `state_type`. |

Multiplayer runs: `get_game_state` / `get_available_actions` return `ok: false`; use `mp_*` tools.

**Not ported from sts2-ai-agent:** main-menu / timeline / character-select actions, SSE `wait_for_event`, `wait_until_actionable`, planner/combat handoff, runtime knowledge files, `run_console_command`. The STS2_MCP mod does not expose those over HTTP; use the game UI where needed.

## Singleplayer (granular)

| Tool | Scope | Description |
|---|---|---|
| `fetch_game_state(format?)` | General | Current state as **string** (`markdown` or `json` text) |
| `use_potion(slot, target?)` | General | Use a potion (works in and out of combat) |
| `discard_potion(slot)` | General | Discard a potion to free up the slot |
| `proceed_to_map()` | General | Proceed from rewards/rest site/shop/treasure to the map |
| `combat_play_card(card_index, target?)` | Combat | Play a card from hand |
| `combat_end_turn()` | Combat | End the current turn |
| `combat_select_card(card_index)` | Combat Selection | Select a card from hand during exhaust/discard prompts |
| `combat_confirm_selection()` | Combat Selection | Confirm the in-combat card selection |
| `rewards_claim(reward_index)` | Rewards | Claim a reward from the post-combat screen |
| `rewards_pick_card(card_index)` | Rewards | Select a card from the card reward screen |
| `rewards_skip_card()` | Rewards | Skip the card reward |
| `map_choose_node(node_index)` | Map | Choose a map node to travel to |
| `rest_choose_option(option_index)` | Rest Site | Choose a rest site option (rest, smith, etc.) |
| `shop_purchase(item_index)` | Shop | Purchase an item from the shop |
| `event_choose_option(option_index)` | Event | Choose an event option (including Proceed) |
| `event_advance_dialogue()` | Event | Advance ancient event dialogue |
| `deck_select_card(card_index)` | Card Select | Pick/toggle a card in the selection screen |
| `deck_confirm_selection()` | Card Select | Confirm the current card selection |
| `deck_cancel_selection()` | Card Select | Cancel/skip card selection |
| `bundle_select(bundle_index)` | Bundle Select | Open a bundle preview |
| `bundle_confirm_selection()` | Bundle Select | Confirm the current bundle preview |
| `bundle_cancel_selection()` | Bundle Select | Cancel the current bundle preview |
| `relic_select(relic_index)` | Relic Select | Choose a relic from the selection screen |
| `relic_skip()` | Relic Select | Skip relic selection |
| `treasure_claim_relic(relic_index)` | Treasure | Claim a relic from the treasure chest |
| `crystal_sphere_set_tool(tool)` | Crystal Sphere | Switch the active divination tool |
| `crystal_sphere_click_cell(x, y)` | Crystal Sphere | Click a hidden cell in the grid |
| `crystal_sphere_proceed()` | Crystal Sphere | Continue after the minigame finishes |

## Multiplayer

All multiplayer tools are prefixed with `mp_`. They route through `/api/v1/multiplayer` and are only available during multiplayer (co-op) runs. The endpoints automatically guard against cross-mode calls.

| Tool | Scope | Description |
|---|---|---|
| `mp_get_game_state(format?)` | General | Get multiplayer game state (all players, votes, bids) |
| `mp_combat_play_card(card_index, target?)` | Combat | Play a card from the local player's hand |
| `mp_combat_end_turn()` | Combat | Submit end-turn vote (turn ends when all players submit) |
| `mp_combat_undo_end_turn()` | Combat | Retract end-turn vote |
| `mp_use_potion(slot, target?)` | General | Use a potion from the local player's slots |
| `mp_discard_potion(slot)` | General | Discard a potion from the local player's slots |
| `mp_proceed_to_map()` | General | Proceed from current screen to the map |
| `mp_map_vote(node_index)` | Map | Vote for a map node (travel when all agree) |
| `mp_event_choose_option(option_index)` | Event | Vote for / choose an event option |
| `mp_event_advance_dialogue()` | Event | Advance ancient event dialogue |
| `mp_rest_choose_option(option_index)` | Rest Site | Choose a rest site option (per-player, no vote) |
| `mp_shop_purchase(item_index)` | Shop | Purchase an item (per-player inventory) |
| `mp_rewards_claim(reward_index)` | Rewards | Claim a post-combat reward |
| `mp_rewards_pick_card(card_index)` | Rewards | Select a card from the card reward screen |
| `mp_rewards_skip_card()` | Rewards | Skip the card reward |
| `mp_deck_select_card(card_index)` | Card Select | Pick/toggle a card in the selection screen |
| `mp_deck_confirm_selection()` | Card Select | Confirm the current card selection |
| `mp_deck_cancel_selection()` | Card Select | Cancel/skip card selection |
| `mp_bundle_select(bundle_index)` | Bundle Select | Open a bundle preview |
| `mp_bundle_confirm_selection()` | Bundle Select | Confirm the current bundle preview |
| `mp_bundle_cancel_selection()` | Bundle Select | Cancel the current bundle preview |
| `mp_combat_select_card(card_index)` | Combat Selection | Select a card during in-combat selection prompts |
| `mp_combat_confirm_selection()` | Combat Selection | Confirm in-combat card selection |
| `mp_relic_select(relic_index)` | Relic Select | Choose a relic from the selection screen |
| `mp_relic_skip()` | Relic Select | Skip relic selection |
| `mp_treasure_claim_relic(relic_index)` | Treasure | Bid on a relic (relic fight if contested) |
| `mp_crystal_sphere_set_tool(tool)` | Crystal Sphere | Switch the active divination tool |
| `mp_crystal_sphere_click_cell(x, y)` | Crystal Sphere | Click a hidden cell in the grid |
| `mp_crystal_sphere_proceed()` | Crystal Sphere | Continue after the minigame finishes |
