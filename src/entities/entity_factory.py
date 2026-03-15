import json
import os
import random

from src.entities.enemy import Enemy


# ---------------------------------------------------------------------------
# EntityFactory — loads enemy definitions and spawns Enemy instances
# ---------------------------------------------------------------------------

_ENEMIES_PATH = os.path.join("data", "enemies.json")
_cache: dict | None = None


def _load_definitions() -> dict:
    global _cache
    if _cache is None:
        with open(_ENEMIES_PATH, "r") as f:
            data = json.load(f)
        _cache = data["enemies"]
    return _cache


def get_definition(enemy_type: str) -> dict:
    """Return the definition dict for a given enemy type key."""
    defs = _load_definitions()
    if enemy_type not in defs:
        raise ValueError(f"Unknown enemy type: '{enemy_type}'. "
                         f"Available: {list(defs.keys())}")
    return defs[enemy_type]


def spawn(enemy_type: str, col: int, row: int,
          tile_size: int, patrol_tiles: list) -> Enemy:
    """
    Create and return an Enemy of the given type.
    enemy_type must match a key in enemies.json.
    """
    definition = get_definition(enemy_type)
    return Enemy(col, row, tile_size, patrol_tiles, definition)


def spawn_patrol(enemy_type: str, patrol_tiles: list,
                 tile_size: int) -> Enemy:
    """
    Convenience — spawn an enemy starting at the first patrol tile.
    """
    start_col, start_row = patrol_tiles[0]
    return spawn(enemy_type, start_col, start_row,
                 tile_size, patrol_tiles)


def roll_loot(enemy_type: str) -> list:
    """
    Roll loot for a given enemy type using its loot table.
    Returns a list of Item instances.
    """
    from src.scenes.chest_scene import PotionItem, CandleItem, GoldItem

    item_map = {
        "PotionItem": PotionItem,
        "CandleItem": CandleItem,
        "GoldItem":   GoldItem,
    }

    definition  = get_definition(enemy_type)
    loot_table  = definition.get("loot_table", [])
    loot_rolls  = definition.get("loot_rolls", 2)

    if not loot_table:
        return []

    weights  = [entry["weight"] for entry in loot_table]
    total_w  = sum(weights)
    results  = []

    for _ in range(loot_rolls):
        roll = random.uniform(0, total_w)
        acc  = 0
        for entry, w in zip(loot_table, weights):
            acc += w
            if roll <= acc:
                cls = item_map.get(entry["item"])
                if cls:
                    if entry["item"] == "GoldItem" and "amount" in entry:
                        amount = random.choice(entry["amount"])
                        results.append(cls(amount))
                    else:
                        results.append(cls())
                break

    return results


def list_enemy_types() -> list[str]:
    """Return all available enemy type keys."""
    return list(_load_definitions().keys())


def get_stat(enemy_type: str, stat: str):
    """Quick helper — get a single stat value e.g. get_stat('goblin', 'hp')."""
    return get_definition(enemy_type).get(stat)