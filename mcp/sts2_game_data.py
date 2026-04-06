"""Bundled STS2 English metadata (same layout as sts2-ai-agent mcp_server/data/eng)."""

from __future__ import annotations

import json
import os
import threading
from typing import Any

JSON_FILE_EXTENSION = ".json"
JSON_FILE_EXTENSION_LENGTH = len(JSON_FILE_EXTENSION)
KNOWN_ITEM_ID_KEYS = ("id", "ID", "Id")
ITEM_IDS_SEPARATOR = ","

SCENE_COMBAT = "combat"
SCENE_SHOP = "shop"
SCENE_EVENT = "event"
SCENE_MENU = "menu"

_SCENE_FIELD_SETS: dict[str, dict[str, list[str]]] = {
    SCENE_COMBAT: {
        "cards": [
            "id",
            "name",
            "description",
            "type",
            "rarity",
            "target",
            "cost",
            "is_x_cost",
            "star_cost",
            "is_x_star_cost",
            "damage",
            "block",
            "keywords",
            "tags",
            "vars",
            "upgrade",
        ],
        "monsters": [
            "id",
            "name",
            "type",
            "min_hp",
            "max_hp",
            "moves",
            "damage_values",
            "block_values",
        ],
        "powers": [
            "id",
            "name",
            "description",
            "type",
            "stack_type",
        ],
    },
    SCENE_SHOP: {
        "cards": ["id", "name", "description", "type", "rarity", "cost"],
        "relics": ["id", "name", "description", "rarity", "pool"],
        "potions": ["id", "name", "description", "rarity"],
    },
    SCENE_EVENT: {
        "events": ["id", "name", "description", "options"],
    },
}

_GAME_DATA_CACHE: dict[str, Any] | None = None
_GAME_DATA_INDEXES: dict[str, dict[str, Any]] = {}
_GAME_DATA_LOCK = threading.Lock()
_GAME_DATA_INDEX_LOCK = threading.Lock()


def _data_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "eng"))


def _load_game_data() -> dict[str, Any]:
    global _GAME_DATA_CACHE
    if _GAME_DATA_CACHE is not None:
        return _GAME_DATA_CACHE

    with _GAME_DATA_LOCK:
        if _GAME_DATA_CACHE is not None:
            return _GAME_DATA_CACHE

        data_dir = _data_dir()
        if not os.path.isdir(data_dir):
            raise RuntimeError(f"Game data directory not found: {data_dir!r}.")

        data: dict[str, Any] = {}
        for filename in sorted(os.listdir(data_dir)):
            path = os.path.join(data_dir, filename)
            if os.path.isdir(path):
                continue
            if not filename.lower().endswith(JSON_FILE_EXTENSION):
                continue
            key = filename[:-JSON_FILE_EXTENSION_LENGTH]
            with open(path, "r", encoding="utf-8") as f:
                data[key] = json.load(f)

        _GAME_DATA_CACHE = data
        return data


def _add_case_insensitive_item_id(index: dict[str, Any], item_id: str, item: Any) -> None:
    normalized = item_id.strip()
    if not normalized:
        return
    index[normalized] = item
    index[normalized.upper()] = item
    index[normalized.lower()] = item


def ensure_game_data_index(collection: str) -> dict[str, Any]:
    global _GAME_DATA_INDEXES
    if collection in _GAME_DATA_INDEXES:
        return _GAME_DATA_INDEXES[collection]

    with _GAME_DATA_INDEX_LOCK:
        if collection in _GAME_DATA_INDEXES:
            return _GAME_DATA_INDEXES[collection]

        data = _load_game_data()
        if collection not in data:
            raise KeyError(f"Unknown game data collection: {collection}")

        items = data[collection]
        index: dict[str, Any] = {}
        if isinstance(items, dict):
            for raw_id, item in items.items():
                _add_case_insensitive_item_id(index=index, item_id=str(raw_id), item=item)
        elif isinstance(items, list):
            for item in items:
                item_id = ""
                for key in KNOWN_ITEM_ID_KEYS:
                    candidate = item.get(key) if isinstance(item, dict) else None
                    if candidate:
                        item_id = str(candidate).strip()
                        break
                if not item_id:
                    continue
                _add_case_insensitive_item_id(index=index, item_id=item_id, item=item)
        else:
            raise TypeError(f"Unsupported data type for collection {collection!r}: {type(items)}")

        _GAME_DATA_INDEXES[collection] = index
        return index


def lookup_game_data_item(collection: str, item_id: str) -> Any:
    if not item_id:
        return None
    index = ensure_game_data_index(collection)
    return index.get(item_id) or index.get(item_id.upper()) or index.get(item_id.lower())


def get_game_data_items_raw(collection: str, item_ids: str) -> dict[str, Any]:
    if not item_ids:
        return {}
    index = ensure_game_data_index(collection)
    ids = [s.strip() for s in item_ids.split(ITEM_IDS_SEPARATOR) if s.strip()]
    result: dict[str, Any] = {}
    for i in ids:
        result[i] = lookup_game_data_item(collection, i)
    return result


def get_game_data_items_fields(collection: str, item_ids: str, fields: str | None) -> dict[str, Any]:
    if not item_ids:
        return {}
    index = ensure_game_data_index(collection)
    ids = [s.strip() for s in item_ids.split(ITEM_IDS_SEPARATOR) if s.strip()]
    requested_fields = [s.strip() for s in fields.split(ITEM_IDS_SEPARATOR) if s.strip()] if fields else []

    result: dict[str, Any] = {}
    for item_id in ids:
        item = lookup_game_data_item(collection, item_id)
        if item is None:
            result[item_id] = None
            continue
        if not requested_fields or not isinstance(item, dict):
            result[item_id] = item
            continue
        result[item_id] = {key: item[key] for key in requested_fields if key in item}
    return result


def detect_scene_from_state_type(state_type: str) -> str:
    st = (state_type or "").lower()
    if st in ("monster", "elite", "boss", "hand_select"):
        return SCENE_COMBAT
    if st in ("shop", "fake_merchant"):
        return SCENE_SHOP
    if st == "event":
        return SCENE_EVENT
    return SCENE_MENU


def get_relevant_game_data_impl(collection: str, item_ids: str, state_type: str) -> dict[str, Any]:
    scene = detect_scene_from_state_type(state_type)
    suggested = _SCENE_FIELD_SETS.get(scene, {}).get(collection)
    if not suggested:
        return get_game_data_items_raw(collection, item_ids)
    fields = ",".join(suggested)
    return get_game_data_items_fields(collection, item_ids, fields)


def game_data_error(collection: str, exc: Exception) -> dict[str, Any]:
    if isinstance(exc, KeyError):
        try:
            available = sorted(_load_game_data().keys())
        except Exception:
            available = []
        return {
            "error": {
                "type": "unknown_collection",
                "collection": collection,
                "message": str(exc),
                "available_collections": available,
            }
        }
    if isinstance(exc, RuntimeError):
        return {"error": {"type": "game_data_unavailable", "collection": collection, "message": str(exc)}}
    return {"error": {"type": "invalid_game_data", "collection": collection, "message": str(exc)}}
