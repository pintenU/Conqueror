import json
import os
import time
import datetime


SAVE_DIR  = "saves"
NUM_SLOTS = 3


def _ensure_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def _slot_path(slot: int) -> str:
    return os.path.join(SAVE_DIR, f"slot_{slot}.json")


class GameState:
    def __init__(self):
        self.playtime_seconds  = 0.0
        self.enemies_defeated  = 0
        self.quests_cleared    = 0
        self.gold_collected    = 0
        self.chests_opened     = 0

        self.player_hp         = 30
        self.player_max_hp     = 30
        self.dungeon_cleared   = False
        self.current_location  = "dungeon"
        self.player_floor      = 1

        self.inventory_data    = []
        self.door_states       = []
        self.chest_states      = []
        self.armour_data       = {}
        self.stats_data        = {}
        self.quest_data        = {}
        # floor_states: {floor_int: {"unlocked_doors": [list of key_ids]}}
        # Stored as lists in JSON, converted to sets on load
        self.floor_states_data = {}

        self.save_time         = ""
        self.slot              = 0

    def to_dict(self) -> dict:
        return {
            "playtime_seconds": self.playtime_seconds,
            "enemies_defeated": self.enemies_defeated,
            "quests_cleared":   self.quests_cleared,
            "gold_collected":   self.gold_collected,
            "chests_opened":    self.chests_opened,
            "player_hp":        self.player_hp,
            "player_max_hp":    self.player_max_hp,
            "dungeon_cleared":  self.dungeon_cleared,
            "current_location": self.current_location,
            "player_floor":     self.player_floor,
            "inventory_data":   self.inventory_data,
            "door_states":      self.door_states,
            "chest_states":     self.chest_states,
            "armour_data":      self.armour_data,
            "stats_data":       self.stats_data,
            "quest_data":       self.quest_data,
            "floor_states_data": self.floor_states_data,
            "save_time":        self.save_time,
            "slot":             self.slot,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GameState":
        gs = cls()
        gs.playtime_seconds = d.get("playtime_seconds", 0.0)
        gs.enemies_defeated = d.get("enemies_defeated", 0)
        gs.quests_cleared   = d.get("quests_cleared",   0)
        gs.gold_collected   = d.get("gold_collected",   0)
        gs.chests_opened    = d.get("chests_opened",    0)
        gs.player_hp        = d.get("player_hp",        30)
        gs.player_max_hp    = d.get("player_max_hp",    30)
        gs.dungeon_cleared  = d.get("dungeon_cleared",  False)
        gs.current_location = d.get("current_location", "dungeon")
        gs.player_floor     = d.get("player_floor",     1)
        gs.inventory_data   = d.get("inventory_data",   [])
        gs.door_states      = d.get("door_states",      [])
        gs.chest_states     = d.get("chest_states",     [])
        gs.floor_states_data= d.get("floor_states_data",{})
        gs.save_time        = d.get("save_time",        "")
        gs.slot             = d.get("slot",             0)
        return gs


# ---------------------------------------------------------------------------
# floor_states conversion: game uses {int: {"unlocked_doors": set}}
#                          JSON uses {"1": {"unlocked_doors": ["key1","key2"]}}
# ---------------------------------------------------------------------------

def floor_states_to_data(floor_states: dict) -> dict:
    """Convert runtime floor_states (sets) → JSON-serialisable dict (lists)."""
    result = {}
    for floor_int, fstate in floor_states.items():
        result[str(floor_int)] = {
            "unlocked_doors": list(fstate.get("unlocked_doors", set()))
        }
    return result


def floor_states_from_data(data: dict) -> dict:
    """Convert saved floor_states_data (lists) → runtime floor_states (sets)."""
    result = {}
    for floor_str, fstate in data.items():
        try:
            floor_int = int(floor_str)
        except ValueError:
            continue
        result[floor_int] = {
            "unlocked_doors": set(fstate.get("unlocked_doors", []))
        }
    return result


# ---------------------------------------------------------------------------
# Item serialisation
# ---------------------------------------------------------------------------

def _item_to_dict(item, stack_count=1) -> dict:
    from src.scenes.chest_scene import (
        PotionItem, CandleItem, SwordItem, SunSwordItem,
        ShieldItem, GoldItem, KeyItem, ExitKeyItem
    )
    cls_name = type(item).__name__
    kwargs   = {}
    if isinstance(item, GoldItem):
        kwargs["amount"] = item.amount
    if isinstance(item, KeyItem) and not isinstance(item, ExitKeyItem):
        kwargs["key_id"] = item.key_id
    if hasattr(item, 'upgrade_level'):
        kwargs["upgrade_level"] = item.upgrade_level
    return {"type": cls_name, "kwargs": kwargs, "stack_count": stack_count}


def _dict_to_item(d: dict):
    from src.scenes.chest_scene import (
        PotionItem, CandleItem, SwordItem, SunSwordItem,
        ShieldItem, GoldItem, KeyItem, ExitKeyItem,
        FloorKeyItem, BossKeyItem, RoomKeyItem, StickItem, DebugSwordItem
    )
    cls_map = {
        "PotionItem":     PotionItem,
        "CandleItem":     CandleItem,
        "SwordItem":      SwordItem,
        "SunSwordItem":   SunSwordItem,
        "ShieldItem":     ShieldItem,
        "GoldItem":       GoldItem,
        "KeyItem":        KeyItem,
        "ExitKeyItem":    ExitKeyItem,
        "FloorKeyItem":   FloorKeyItem,
        "BossKeyItem":    BossKeyItem,
        "RoomKeyItem":    RoomKeyItem,
        "StickItem":      StickItem,
        "DebugSwordItem": DebugSwordItem,
    }
    cls_name = d["type"]
    kwargs   = dict(d.get("kwargs", {}))
    upgrade_level = kwargs.pop("upgrade_level", None)
    cls = cls_map.get(cls_name)
    if cls is None:
        return None
    try:
        item = cls(**kwargs)
    except Exception:
        try:
            item = cls()
        except Exception:
            return None
    if upgrade_level is not None:
        item.upgrade_level = upgrade_level
    return item


# ---------------------------------------------------------------------------
# capture / restore
# ---------------------------------------------------------------------------

def capture(state: GameState, inventory, game_scene=None,
            dungeon_cleared=False, current_location="dungeon",
            armour=None, player_stats=None, quest_manager=None,
            floor_states=None):
    state.dungeon_cleared  = dungeon_cleared
    state.current_location = current_location
    state.save_time        = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")

    state.inventory_data = [
        _item_to_dict(it, inventory.stack_count(it))
        for it in inventory.items
    ]

    from src.scenes.chest_scene import GoldItem
    state.gold_collected = inventory.count(GoldItem)

    if armour:
        state.armour_data = armour.to_dict()
    if player_stats:
        state.stats_data = player_stats.to_dict()
    if quest_manager:
        state.quest_data = quest_manager.to_dict()

    # Save floor_states (door/circle unlock progress across all floors)
    if floor_states is not None:
        state.floor_states_data = floor_states_to_data(floor_states)

    if game_scene:
        state.door_states  = [d.locked for d in getattr(game_scene, 'locked_doors', [])]
        state.chest_states = [
            {"opened": c.opened,
             "items":  [_item_to_dict(it) for it in c.items]}
            for c in getattr(game_scene, 'chests', [])
        ]


def restore(state: GameState, inventory, armour=None, player_stats=None,
            quest_manager=None):
    inventory._stacks = {}
    inventory._order  = []
    inventory._uid    = 0

    if armour and state.armour_data:
        armour.from_dict(state.armour_data)
    if player_stats and state.stats_data:
        player_stats.from_dict(state.stats_data)
    if quest_manager and state.quest_data:
        quest_manager.from_dict(state.quest_data)

    for d in state.inventory_data:
        item = _dict_to_item(d)
        if item is None:
            continue
        stack_count = d.get("stack_count", 1)
        if getattr(item, "stackable", False) and stack_count > 1:
            inventory.add(item)
            key = type(item).__name__
            if key in inventory._stacks:
                inventory._stacks[key]["count"] = stack_count
                if hasattr(inventory._stacks[key]["item"], "amount"):
                    inventory._stacks[key]["item"].amount = stack_count
        else:
            inventory.add(item)


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def save_slot(slot: int, state: GameState):
    _ensure_dir()
    state.slot      = slot
    state.save_time = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")
    with open(_slot_path(slot), "w") as f:
        json.dump(state.to_dict(), f, indent=2)


def load_slot(slot: int) -> "GameState | None":
    path = _slot_path(slot)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return GameState.from_dict(json.load(f))


def slot_exists(slot: int) -> bool:
    return os.path.exists(_slot_path(slot))


def delete_slot(slot: int):
    path = _slot_path(slot)
    if os.path.exists(path):
        os.remove(path)


def format_playtime(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"