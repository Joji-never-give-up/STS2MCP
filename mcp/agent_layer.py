"""
STS2-Agent-style MCP surface on top of STS2MCP HTTP API (singleplayer only).

Provides health_check, get_game_state (dict), get_available_actions, act — plus
compatibility with sts2-ai-agent skill workflows. Multiplayer runs return a
clear error; use the existing mp_* tools instead.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def http_get_json(base_url: str, trust_env: bool) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/singleplayer"
    async with httpx.AsyncClient(timeout=15.0, trust_env=trust_env) as client:
        r = await client.get(url, params={"format": "json"})
        if r.status_code == 409:
            return {"_error": "multiplayer_active", "status_code": 409, "text": r.text}
        r.raise_for_status()
        return r.json()


def _post_result_ok(result: dict[str, Any]) -> bool:
    if result.get("_http409"):
        return False
    st = result.get("status")
    if st is None:
        return True
    return str(st).lower() != "error"


async def http_post_action(base_url: str, trust_env: bool, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/singleplayer"
    async with httpx.AsyncClient(timeout=30.0, trust_env=trust_env) as client:
        r = await client.post(url, json=body)
        if r.status_code == 409:
            return {"status": "error", "message": "Multiplayer run — use mp_* tools.", "_http409": True}
        r.raise_for_status()
        try:
            return r.json()
        except json.JSONDecodeError:
            return {"status": "ok", "message": r.text}


async def health_check_impl(base_url: str, trust_env: bool) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=5.0, trust_env=trust_env) as client:
            r = await client.get(f"{base_url.rstrip('/')}/api/v1/singleplayer", params={"format": "json"})
        # 409 = multiplayer run (wrong endpoint) — still means the mod is up.
        if r.status_code == 409:
            return {
                "ok": True,
                "http_status": 409,
                "base_url": base_url,
                "compat": "sts2mcp-agent-layer",
                "note": "Multiplayer run active — use mp_* tools; singleplayer agent_layer is unavailable until SP mode.",
            }
        r.raise_for_status()
        return {
            "ok": True,
            "http_status": r.status_code,
            "base_url": base_url,
            "compat": "sts2mcp-agent-layer",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "base_url": base_url}


def _a(name: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, **extra}


def _enemy_target_space(battle: dict[str, Any] | None) -> list[int]:
    if not battle:
        return []
    enemies = battle.get("enemies") or []
    return list(range(len(enemies)))


def synthesize_available_actions(state: dict[str, Any]) -> list[dict[str, Any]]:
    if state.get("_error") == "multiplayer_active":
        return []

    st = state.get("state_type") or ""
    actions: list[dict[str, Any]] = []

    if st == "menu":
        return [_a("noop_menu", note="Start or continue a run in the game UI; STS2MCP has no menu actions via API.")]

    if st == "unknown":
        return [_a("noop_unknown", note="Unrecognized room — check game manually.")]

    if st == "overlay":
        return [_a("noop_overlay", note="Unhandled overlay — may need manual click.")]

    battle = state.get("battle") if isinstance(state.get("battle"), dict) else None
    player = state.get("player") if isinstance(state.get("player"), dict) else None

    if st in ("monster", "elite", "boss"):
        turn = (battle or {}).get("turn")
        phase = (battle or {}).get("is_play_phase")
        if turn == "player" and phase is not False:
            actions.append(_a("end_turn"))
            hand = (player or {}).get("hand") or []
            enemies = (battle or {}).get("enemies") or []
            has_playable = any(
                isinstance(c, dict) and c.get("can_play", True) and c.get("index") is not None for c in hand
            )
            if has_playable:
                needs_target = any(
                    isinstance(c, dict)
                    and c.get("can_play", True)
                    and "Enemy" in str(c.get("target_type") or "")
                    for c in hand
                )
                actions.append(
                    _a(
                        "play_card",
                        requires_index=True,
                        index_kind="card_index",
                        requires_target=bool(needs_target and len(enemies) > 1),
                        valid_target_indices=_enemy_target_space(battle),
                    )
                )
            seen_slots: set[int] = set()
            for p in (player or {}).get("potions") or []:
                if isinstance(p, dict) and p.get("slot") is not None:
                    slot = int(p["slot"])
                    if slot in seen_slots:
                        continue
                    seen_slots.add(slot)
                    ptt = str(p.get("target_type") or "None")
                    need_t = ptt not in ("None", "") and "Enemy" in ptt
                    actions.append(
                        _a(
                            "use_potion",
                            requires_index=True,
                            index_kind="potion_slot",
                            requires_target=need_t,
                            valid_target_indices=_enemy_target_space(battle),
                        )
                    )
                    actions.append(_a("discard_potion", requires_index=True, index_kind="potion_slot"))
        return actions

    if st == "hand_select":
        hs = state.get("hand_select") or {}
        cards = hs.get("cards") or []
        for c in cards:
            if isinstance(c, dict) and c.get("index") is not None:
                actions.append(_a("select_deck_card", requires_index=True, index_kind="option_index"))
                break
        if hs.get("can_confirm"):
            actions.append(_a("confirm_selection"))
        actions.append(_a("cancel_selection"))
        return actions

    if st == "rewards":
        rw = state.get("rewards") or {}
        for item in rw.get("items") or []:
            if isinstance(item, dict) and item.get("index") is not None:
                actions.append(_a("claim_reward", requires_index=True, index_kind="option_index"))
        if rw.get("can_proceed"):
            actions.append(_a("proceed"))
        return actions

    if st == "card_reward":
        cr = state.get("card_reward") or {}
        for c in cr.get("cards") or []:
            if isinstance(c, dict) and c.get("index") is not None:
                actions.append(_a("choose_reward_card", requires_index=True, index_kind="option_index"))
        if cr.get("can_skip"):
            actions.append(_a("skip_reward_cards"))
        return actions

    if st == "map":
        opts = (state.get("map") or {}).get("next_options") or []
        if opts:
            actions.append(_a("choose_map_node", requires_index=True, index_kind="option_index"))
        return actions

    if st == "event":
        ev = state.get("event") or {}
        if ev.get("in_dialogue"):
            actions.append(_a("advance_dialogue"))
        for o in ev.get("options") or []:
            if isinstance(o, dict) and not o.get("is_locked") and o.get("index") is not None:
                actions.append(_a("choose_event_option", requires_index=True, index_kind="option_index"))
        return actions

    if st == "rest_site":
        rs = state.get("rest_site") or {}
        for o in rs.get("options") or []:
            if isinstance(o, dict) and o.get("index") is not None and o.get("is_enabled", True):
                actions.append(_a("choose_rest_option", requires_index=True, index_kind="option_index"))
        if rs.get("can_proceed"):
            actions.append(_a("proceed"))
        return actions

    if st == "shop":
        shop = state.get("shop") or {}
        items = shop.get("items") or []
        if items:
            actions.append(_a("buy_card", requires_index=True, index_kind="option_index"))
        if shop.get("can_proceed"):
            actions.append(_a("proceed"))
        return actions

    if st == "fake_merchant":
        fm = state.get("fake_merchant") or {}
        shop = fm.get("shop") or {}
        items = shop.get("items") or []
        if items:
            actions.append(_a("buy_card", requires_index=True, index_kind="option_index"))
        if shop.get("can_proceed"):
            actions.append(_a("proceed"))
        return actions

    if st == "treasure":
        tr = state.get("treasure") or {}
        for r in tr.get("relics") or []:
            if isinstance(r, dict) and r.get("index") is not None:
                actions.append(_a("choose_treasure_relic", requires_index=True, index_kind="option_index"))
        actions.append(_a("proceed"))
        return actions

    if st == "card_select":
        actions.append(_a("select_deck_card", requires_index=True, index_kind="option_index"))
        actions.append(_a("confirm_selection"))
        actions.append(_a("cancel_selection"))
        return actions

    if st == "bundle_select":
        actions.append(_a("bundle_select", requires_index=True, index_kind="option_index"))
        actions.append(_a("bundle_confirm_selection"))
        actions.append(_a("bundle_cancel_selection"))
        return actions

    if st == "relic_select":
        actions.append(_a("relic_select", requires_index=True, index_kind="option_index"))
        actions.append(_a("relic_skip"))
        return actions

    if st == "crystal_sphere":
        actions.append(_a("crystal_sphere_set_tool", requires_string=True))
        actions.append(_a("crystal_sphere_click_cell", requires_coords=True))
        actions.append(_a("crystal_sphere_proceed"))
        return actions

    return [_a("noop", state_type=st)]


def build_agent_view(raw: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any]:
    st = raw.get("state_type", "")
    phase = "menu" if st == "menu" else "run"
    view: dict[str, Any] = {
        "screen": st,
        "session": {"mode": "singleplayer", "phase": phase},
        "available_actions": actions,
    }
    for key in ("run", "player", "battle", "map", "event", "rewards", "shop", "rest_site"):
        if key in raw:
            view[key] = raw[key]
    return view


async def get_agent_state(base_url: str, trust_env: bool) -> dict[str, Any]:
    raw = await http_get_json(base_url, trust_env)
    if raw.get("_error") == "multiplayer_active":
        return {
            "ok": False,
            "error": {
                "code": "multiplayer_run",
                "message": "Singleplayer API returned HTTP 409. Use mp_get_game_state and mp_* tools for multiplayer.",
            },
        }
    actions = synthesize_available_actions(raw)
    agent_view = build_agent_view(raw, actions)
    # Match sts2-ai-agent: top-level keys include available_actions, screen, session, …
    return {"ok": True, **agent_view, "raw": raw}


def _entity_id_for_target(raw: dict[str, Any], target_index: int | None) -> str | None:
    battle = raw.get("battle") or {}
    enemies = battle.get("enemies") or []
    if target_index is None or not enemies:
        return None
    if 0 <= target_index < len(enemies):
        e = enemies[target_index]
        if isinstance(e, dict) and e.get("entity_id"):
            return str(e["entity_id"])
    return None


async def act_impl(
    base_url: str,
    trust_env: bool,
    action: str,
    card_index: int | None = None,
    target_index: int | None = None,
    option_index: int | None = None,
) -> dict[str, Any]:
    raw = await http_get_json(base_url, trust_env)
    if raw.get("_error") == "multiplayer_active":
        return {"ok": False, "error": {"code": "multiplayer_run", "message": "Use mp_* tools in multiplayer."}}

    a = action.strip().lower().replace("-", "_")

    # Refresh-friendly noop
    if a in ("noop", "noop_menu", "noop_unknown", "noop_overlay"):
        return {"ok": False, "error": {"code": "not_actionable", "message": action}}

    body: dict[str, Any] = {}

    if a == "play_card":
        if card_index is None:
            return {"ok": False, "error": {"code": "missing_card_index", "message": "play_card requires card_index"}}
        body = {"action": "play_card", "card_index": card_index}
        hand = ((raw.get("player") or {}).get("hand")) or []
        target_id: str | None = None
        for c in hand:
            if isinstance(c, dict) and c.get("index") == card_index:
                tt = str(c.get("target_type") or "")
                if "Enemy" in tt:
                    tid = _entity_id_for_target(raw, target_index)
                    if tid is None:
                        en = ((raw.get("battle") or {}).get("enemies")) or []
                        if len(en) == 1 and isinstance(en[0], dict):
                            tid = str(en[0].get("entity_id") or "")
                    target_id = tid
                break
        if target_id:
            body["target"] = target_id
        result = await http_post_action(base_url, trust_env, body)
        return {"ok": _post_result_ok(result), "result": result}

    if a == "end_turn":
        result = await http_post_action(base_url, trust_env, {"action": "end_turn"})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "choose_map_node":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "choose_map_node requires option_index"}}
        result = await http_post_action(base_url, trust_env, {"action": "choose_map_node", "index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "claim_reward":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "claim_reward requires option_index"}}
        result = await http_post_action(base_url, trust_env, {"action": "claim_reward", "index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "choose_reward_card":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "choose_reward_card requires option_index"}}
        result = await http_post_action(base_url, trust_env, {"action": "select_card_reward", "card_index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "skip_reward_cards":
        result = await http_post_action(base_url, trust_env, {"action": "skip_card_reward"})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "choose_event_option":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "choose_event_option requires option_index"}}
        result = await http_post_action(base_url, trust_env, {"action": "choose_event_option", "index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "advance_dialogue":
        result = await http_post_action(base_url, trust_env, {"action": "advance_dialogue"})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "choose_rest_option":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "choose_rest_option requires option_index"}}
        result = await http_post_action(base_url, trust_env, {"action": "choose_rest_option", "index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "proceed":
        result = await http_post_action(base_url, trust_env, {"action": "proceed"})
        return {"ok": _post_result_ok(result), "result": result}

    if a in ("buy_card", "buy_relic", "buy_potion"):
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": f"{a} requires option_index (shop item index)"}}
        result = await http_post_action(base_url, trust_env, {"action": "shop_purchase", "index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "use_potion":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "use_potion requires option_index (potion slot)"}}
        body = {"action": "use_potion", "slot": option_index}
        tid = _entity_id_for_target(raw, target_index)
        battle = raw.get("battle") or {}
        en = battle.get("enemies") or []
        if tid is None and len(en) == 1 and isinstance(en[0], dict):
            tid = str(en[0].get("entity_id") or "")
        if tid:
            body["target"] = tid
        result = await http_post_action(base_url, trust_env, body)
        return {"ok": _post_result_ok(result), "result": result}

    if a == "discard_potion":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "discard_potion requires option_index (potion slot)"}}
        result = await http_post_action(base_url, trust_env, {"action": "discard_potion", "slot": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "select_deck_card":
        if option_index is None and card_index is not None:
            option_index = card_index
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_index", "message": "select_deck_card requires option_index or card_index"}}
        st = raw.get("state_type")
        if st == "hand_select":
            result = await http_post_action(base_url, trust_env, {"action": "combat_select_card", "card_index": option_index})
        else:
            result = await http_post_action(base_url, trust_env, {"action": "select_card", "index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "confirm_selection":
        st = raw.get("state_type")
        if st == "hand_select":
            result = await http_post_action(base_url, trust_env, {"action": "combat_confirm_selection"})
        else:
            result = await http_post_action(base_url, trust_env, {"action": "confirm_selection"})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "cancel_selection":
        result = await http_post_action(base_url, trust_env, {"action": "cancel_selection"})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "choose_treasure_relic":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "choose_treasure_relic requires option_index"}}
        result = await http_post_action(base_url, trust_env, {"action": "claim_treasure_relic", "index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "bundle_select":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "bundle_select requires option_index"}}
        result = await http_post_action(base_url, trust_env, {"action": "select_bundle", "index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "bundle_confirm_selection":
        result = await http_post_action(base_url, trust_env, {"action": "confirm_bundle_selection"})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "bundle_cancel_selection":
        result = await http_post_action(base_url, trust_env, {"action": "cancel_bundle_selection"})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "relic_select":
        if option_index is None:
            return {"ok": False, "error": {"code": "missing_option_index", "message": "relic_select requires option_index"}}
        result = await http_post_action(base_url, trust_env, {"action": "select_relic", "index": option_index})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "relic_skip":
        result = await http_post_action(base_url, trust_env, {"action": "skip_relic_selection"})
        return {"ok": _post_result_ok(result), "result": result}

    if a == "crystal_sphere_proceed":
        result = await http_post_action(base_url, trust_env, {"action": "crystal_sphere_proceed"})
        return {"ok": _post_result_ok(result), "result": result}

    return {
        "ok": False,
        "error": {
            "code": "unsupported_action",
            "message": f"Action {action!r} is not mapped in STS2MCP agent_layer (yet). Use granular MCP tools.",
            "hint": "Supported: play_card, end_turn, choose_map_node, claim_reward, choose_reward_card, skip_reward_cards, "
            "choose_event_option, advance_dialogue, choose_rest_option, proceed, buy_card/buy_relic/buy_potion, "
            "use_potion, discard_potion, select_deck_card, confirm_selection, cancel_selection, choose_treasure_relic, "
            "bundle_*, relic_*, crystal_sphere_proceed.",
        },
    }
