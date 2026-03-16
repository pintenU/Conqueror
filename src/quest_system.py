"""
Quest system for Conqueror.
Quests are defined here, tracked in GameState, and checked after combat/events.
"""
import random

# ---------------------------------------------------------------------------
# Quest definitions
# ---------------------------------------------------------------------------

QUEST_POOL = [
    # --- Kill quests ---
    {
        "id": "kill_goblins_5",
        "title": "Pest Control",
        "desc": "Goblins have been raiding the farms. Put them down.",
        "type": "kill",
        "target": "goblin", "target_name": "Goblins",
        "required": 5, "progress": 0,
        "reward_gold": 30, "reward_exp": 40,
        "reward_item": None,
        "difficulty": 1,
        "flavour": "Farmer Aldric requests assistance.",
    },
    {
        "id": "kill_goblins_10",
        "title": "Goblin Purge",
        "desc": "Clear the dungeon of ten goblins.",
        "type": "kill",
        "target": "goblin", "target_name": "Goblins",
        "required": 10, "progress": 0,
        "reward_gold": 60, "reward_exp": 80,
        "reward_item": None,
        "difficulty": 2,
        "flavour": "Town Guard contract.",
    },
    {
        "id": "kill_skeletons_5",
        "title": "Lay Them to Rest",
        "desc": "Destroy 5 skeletons stirring in the depths.",
        "type": "kill",
        "target": "skeleton", "target_name": "Skeletons",
        "required": 5, "progress": 0,
        "reward_gold": 40, "reward_exp": 55,
        "reward_item": None,
        "difficulty": 2,
        "flavour": "The priest says they must be stopped.",
    },
    {
        "id": "kill_trolls_3",
        "title": "Troll Toll",
        "desc": "Slay 3 trolls blocking the deeper passages.",
        "type": "kill",
        "target": "troll", "target_name": "Trolls",
        "required": 3, "progress": 0,
        "reward_gold": 70, "reward_exp": 90,
        "reward_item": None,
        "difficulty": 3,
        "flavour": "Merchant guild posting.",
    },
    {
        "id": "kill_rats_5",
        "title": "Rat Extermination",
        "desc": "The dire rats have gotten out of hand. Kill 5.",
        "type": "kill",
        "target": "dire_rat", "target_name": "Dire Rats",
        "required": 5, "progress": 0,
        "reward_gold": 25, "reward_exp": 35,
        "reward_item": None,
        "difficulty": 1,
        "flavour": "Posted by the innkeeper.",
    },
    {
        "id": "kill_imps_4",
        "title": "Imp Infestation",
        "desc": "Four imps have been spotted near the gate. Banish them.",
        "type": "kill",
        "target": "imp", "target_name": "Imps",
        "required": 4, "progress": 0,
        "reward_gold": 45, "reward_exp": 60,
        "reward_item": None,
        "difficulty": 2,
        "flavour": "Widow Hara is frightened.",
    },
    # --- Boss kill quests ---
    {
        "id": "kill_goblin_king",
        "title": "Slay the Goblin King",
        "desc": "The Goblin King rules the depths. End his reign.",
        "type": "kill_boss",
        "target": "goblin_king", "target_name": "Goblin King",
        "required": 1, "progress": 0,
        "reward_gold": 150, "reward_exp": 200,
        "reward_item": None,
        "difficulty": 4,
        "flavour": "WANTED — Dead only. 150g reward.",
    },
    {
        "id": "kill_bone_lord",
        "title": "Shatter the Bone Lord",
        "desc": "An ancient skeleton lord has risen. Destroy it permanently.",
        "type": "kill_boss",
        "target": "bone_lord", "target_name": "Bone Lord",
        "required": 1, "progress": 0,
        "reward_gold": 180, "reward_exp": 240,
        "reward_item": "PotionItem",
        "difficulty": 4,
        "flavour": "WANTED — High priority.",
    },
    {
        "id": "kill_lich_king",
        "title": "Destroy the Lich King",
        "desc": "The Lich King commands the undead. Shatter his phylactery.",
        "type": "kill_boss",
        "target": "lich_king", "target_name": "Lich King",
        "required": 1, "progress": 0,
        "reward_gold": 220, "reward_exp": 300,
        "reward_item": "SunSwordItem",
        "difficulty": 5,
        "flavour": "WANTED — Town's most dangerous threat.",
    },
    # --- Clear dungeon ---
    {
        "id": "clear_dungeon",
        "title": "Clear the Dungeon",
        "desc": "Defeat the Goblin King and escape the dungeon alive.",
        "type": "clear_dungeon",
        "target": None, "target_name": "Dungeon",
        "required": 1, "progress": 0,
        "reward_gold": 100, "reward_exp": 150,
        "reward_item": None,
        "difficulty": 4,
        "flavour": "The town needs a hero.",
    },
    # --- Collect gold ---
    {
        "id": "collect_gold_100",
        "title": "Gold Rush",
        "desc": "Accumulate 100 gold from your adventures.",
        "type": "collect_gold",
        "target": None, "target_name": "Gold",
        "required": 100, "progress": 0,
        "reward_gold": 50, "reward_exp": 60,
        "reward_item": None,
        "difficulty": 2,
        "flavour": "Prove your worth as a treasure hunter.",
    },
    {
        "id": "collect_gold_250",
        "title": "Fortune Seeker",
        "desc": "Accumulate 250 gold total.",
        "type": "collect_gold",
        "target": None, "target_name": "Gold",
        "required": 250, "progress": 0,
        "reward_gold": 100, "reward_exp": 120,
        "reward_item": None,
        "difficulty": 3,
        "flavour": "The merchant guild is watching.",
    },
    # --- Find item ---
    {
        "id": "find_sunsword",
        "title": "Blade of the Sun",
        "desc": "Retrieve the legendary Sun Sword from the dungeon.",
        "type": "find_item",
        "target": "SunSwordItem", "target_name": "Sun Sword",
        "required": 1, "progress": 0,
        "reward_gold": 80, "reward_exp": 100,
        "reward_item": None,
        "difficulty": 3,
        "flavour": "A scholar seeks this ancient weapon.",
    },
    {
        "id": "find_shield",
        "title": "Iron Will",
        "desc": "Recover the Iron Shield said to be hidden in the dungeon.",
        "type": "find_item",
        "target": "ShieldItem", "target_name": "Iron Shield",
        "required": 1, "progress": 0,
        "reward_gold": 60, "reward_exp": 75,
        "reward_item": None,
        "difficulty": 2,
        "flavour": "Lost by a fallen adventurer.",
    },
    # --- Survive combat rounds ---
    {
        "id": "survive_10_rounds",
        "title": "Trial by Combat",
        "desc": "Survive 10 total rounds of combat.",
        "type": "survive_rounds",
        "target": None, "target_name": "Combat Rounds",
        "required": 10, "progress": 0,
        "reward_gold": 35, "reward_exp": 50,
        "reward_item": None,
        "difficulty": 1,
        "flavour": "Prove you can take a hit.",
    },
    {
        "id": "survive_25_rounds",
        "title": "Veteran Warrior",
        "desc": "Survive 25 total rounds of combat.",
        "type": "survive_rounds",
        "target": None, "target_name": "Combat Rounds",
        "required": 25, "progress": 0,
        "reward_gold": 75, "reward_exp": 100,
        "reward_item": None,
        "difficulty": 3,
        "flavour": "Only true warriors endure this long.",
    },
]

DIFFICULTY_STARS = {1:"★☆☆☆☆", 2:"★★☆☆☆", 3:"★★★☆☆", 4:"★★★★☆", 5:"★★★★★"}
DIFFICULTY_COL   = {
    1:(120,200,120), 2:(180,200,80), 3:(220,160,50),
    4:(220,90,50),   5:(200,50,200)
}

# ---------------------------------------------------------------------------
# QuestManager — owned by GameState
# ---------------------------------------------------------------------------

class QuestManager:
    MAX_ACTIVE = 3

    def __init__(self):
        self.active   = []   # list of quest dicts (copies from pool)
        self.completed= []   # list of quest ids
        self.available= []   # ids shown on notice board today
        self._refresh_available()

    def _refresh_available(self):
        """Pick 4 quests to show on the board (not already active/completed)."""
        taken = {q["id"] for q in self.active} | set(self.completed)
        pool  = [q for q in QUEST_POOL if q["id"] not in taken]
        random.shuffle(pool)
        self.available = [q["id"] for q in pool[:4]]

    def get_available(self):
        taken = {q["id"] for q in self.active} | set(self.completed)
        return [q for q in QUEST_POOL
                if q["id"] in self.available and q["id"] not in taken]

    def accept(self, quest_id) -> bool:
        if len(self.active) >= self.MAX_ACTIVE:
            return False
        if any(q["id"]==quest_id for q in self.active):
            return False
        q = next((q for q in QUEST_POOL if q["id"]==quest_id), None)
        if not q: return False
        import copy
        self.active.append(copy.deepcopy(q))
        return True

    def abandon(self, quest_id):
        self.active = [q for q in self.active if q["id"] != quest_id]
        self._refresh_available()

    def is_complete(self, q) -> bool:
        return q["progress"] >= q["required"]

    def check_completion(self, inventory, game_state, player_stats) -> list:
        """
        Check all active quests for completion.
        Returns list of (quest, reward_msg) for newly completed quests.
        """
        newly_done = []
        for q in list(self.active):
            if not self.is_complete(q):
                continue
            # Award rewards
            msgs = []
            if q["reward_gold"] > 0:
                from src.scenes.chest_scene import GoldItem
                inventory.add(GoldItem(q["reward_gold"]))
                game_state.gold_collected += q["reward_gold"]
                msgs.append(f"+{q['reward_gold']}g")
            if q["reward_exp"] > 0:
                leveled = player_stats.add_exp(q["reward_exp"])
                msgs.append(f"+{q['reward_exp']} EXP")
                if leveled:
                    msgs.append(f"LEVEL UP x{len(leveled)}!")
            if q["reward_item"]:
                item = _make_item(q["reward_item"])
                if item:
                    inventory.add(item)
                    msgs.append(f"+{q['reward_item'].replace('Item','')}")
            reward_str = "  ".join(msgs)
            newly_done.append((q, reward_str))
            self.completed.append(q["id"])
            self.active.remove(q)
        if newly_done:
            self._refresh_available()
        return newly_done

    # ---- Progress update methods ----

    def on_kill(self, enemy_type: str):
        for q in self.active:
            if q["type"] == "kill" and q["target"] == enemy_type:
                q["progress"] = min(q["required"], q["progress"]+1)
            elif q["type"] == "kill_boss" and q["target"] == enemy_type:
                q["progress"] = min(q["required"], q["progress"]+1)

    def on_boss_killed(self, boss_type: str):
        self.on_kill(boss_type)
        for q in self.active:
            if q["type"] == "clear_dungeon":
                q["progress"] = min(q["required"], q["progress"]+1)

    def on_gold_collected(self, total_gold: int):
        for q in self.active:
            if q["type"] == "collect_gold":
                q["progress"] = min(q["required"], total_gold)

    def on_item_found(self, item_class_name: str):
        for q in self.active:
            if q["type"] == "find_item" and q["target"] == item_class_name:
                q["progress"] = min(q["required"], q["progress"]+1)

    def on_combat_round(self):
        for q in self.active:
            if q["type"] == "survive_rounds":
                q["progress"] = min(q["required"], q["progress"]+1)

    # ---- Serialisation ----

    def to_dict(self):
        return {
            "active":    self.active,
            "completed": self.completed,
            "available": self.available,
        }

    def from_dict(self, d):
        self.active    = d.get("active",    [])
        self.completed = d.get("completed", [])
        self.available = d.get("available", [])
        if not self.available:
            self._refresh_available()


def _make_item(item_class_name: str):
    try:
        from src.scenes.chest_scene import (
            PotionItem, SunSwordItem, ShieldItem, GoldItem, CandleItem)
        mapping = {
            "PotionItem":  PotionItem,
            "SunSwordItem":SunSwordItem,
            "ShieldItem":  ShieldItem,
            "CandleItem":  CandleItem,
        }
        cls = mapping.get(item_class_name)
        return cls() if cls else None
    except Exception:
        return None