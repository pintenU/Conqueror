import pygame
import sys
import math

from src.ui.menu import MenuScene
from src.scenes.main_menu_scene import MainMenuScene
from src.scenes.game_scene import GameScene
from src.scenes.combat_scene import CombatScene
from src.scenes.chest_scene import ChestScene
from src.scenes.inventory_scene import InventoryScene
from src.scenes.loot_scene import LootScene
from src.scenes.map_scene import MapScene
from src.scenes.world_map_scene import WorldMapScene
from src.scenes.town_scene import TownScene
from src.scenes.blacksmith_scene import BlacksmithScene
from src.scenes.shop_scene import InnScene, GeneralShopScene, AntiquityScene
from src.inventory import Inventory
from src.armour import ArmourSystem
from src.scenes.armour_scene import ArmourScene
from src.player_stats import PlayerStats, EXP_GOBLIN, EXP_BOSS
from src.quest_system import QuestManager
from src.scenes.quest_scene import NoticeBoardScene, QuestLogScene
from src.entities.entity_factory import get_stat, roll_loot as factory_loot
from src.scenes.levelup_scene import LevelUpScene
from src.save_system import GameState, capture, restore, save_slot, load_slot, format_playtime
from src.scenes.saves_scene import SavesScene
from src.scenes.death_scene import DeathScene


def _make_game_scene(screen, inventory, exit_unlocked=False, floor=1,
                     player_stats=None, game_state=None,
                     floor_states=None, return_spawn=None):
    gs = GameScene(screen, inventory,
                   player_stats=player_stats, game_state=game_state,
                   floor=floor, floor_states=floor_states,
                   return_spawn=return_spawn)
    return gs


def main():
    pygame.init()
    pygame.mixer.init()

    screen         = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Dungeon")

    inventory       = Inventory()
    armour          = ArmourSystem()
    player_stats    = PlayerStats()
    quest_manager   = QuestManager()
    game_scene      = None
    pre_inv_scene   = "game"
    town_idx        = 0
    combat          = None
    dungeon_cleared = False
    prev_scene      = "menu"
    game_state      = GameState()
    current_floor   = 1   # track which dungeon floor player is on
    floor_states    = {}  # persisted door/circle states per floor {floor: {unlocked_doors: set}}

    scene = "main_menu"

    import time as _time
    _last_tick = _time.time()

    while True:
        _now = _time.time()
        game_state.playtime_seconds += _now - _last_tick
        _last_tick = _now

        # ----------------------------------------------------------------
        # Main menu
        # ----------------------------------------------------------------
        if scene == "main_menu":
            result = MainMenuScene(screen, mode="start").run()
            if result == "new_game":
                inventory       = Inventory()
                armour          = ArmourSystem()
                player_stats    = PlayerStats()
                quest_manager   = QuestManager()
                game_scene      = None
                dungeon_cleared = False
                floor_states    = {}
                current_floor   = 1
                scene           = "start"
            elif result == "saves":
                scene = "saves"
            elif result == "exit":
                break

        # ----------------------------------------------------------------
        # Saves
        # ----------------------------------------------------------------
        elif scene == "saves":
            result = SavesScene(screen, game_state=None, mode="load").run()
            if isinstance(result, tuple) and result[0] == "loaded":
                loaded_state = result[1]
                inventory       = Inventory()
                restore(loaded_state, inventory)
                game_state      = loaded_state
                dungeon_cleared = loaded_state.dungeon_cleared
                current_floor   = getattr(loaded_state, "player_floor", 1)
                if loaded_state.current_location == "town":
                    scene = "town"
                elif current_floor > 1:
                    scene = f"floor_{current_floor}"
                else:
                    scene = "start"
            elif result == "exit":
                scene = "exit"
            else:
                scene = "main_menu"

        # ----------------------------------------------------------------
        # Pause menu
        # ----------------------------------------------------------------
        elif scene == "pause":
            result = MainMenuScene(screen, mode="pause").run()
            if result == "continue":
                scene = prev_scene
            elif result == "saves":
                game_state.player_max_hp = player_stats.max_hp
                game_state.player_floor = current_floor
                capture(game_state, inventory, game_scene, dungeon_cleared,
                        "dungeon" if prev_scene == "game" else "town", armour, player_stats, quest_manager)
                r2 = SavesScene(screen, game_state=game_state, mode="both").run()
                if isinstance(r2, tuple) and r2[0] == "loaded":
                    loaded = r2[1]
                    inventory       = Inventory()
                    restore(loaded, inventory, armour, player_stats, quest_manager)
                    game_state      = loaded
                    dungeon_cleared = loaded.dungeon_cleared
                    current_floor   = getattr(loaded, "player_floor", 1)
                    game_scene      = None
                    game_state.player_max_hp = player_stats.max_hp
                    if loaded.current_location == "town":
                        scene = "town"
                    elif current_floor > 1:
                        scene = f"floor_{current_floor}"
                    else:
                        scene = "start"
                else:
                    scene = "pause"
            elif result == "main_menu":
                scene = "main_menu"
            elif result == "exit":
                break

        # ----------------------------------------------------------------
        # Dungeon — first entry
        # ----------------------------------------------------------------
        elif scene == "start":
            game_scene = _make_game_scene(screen, inventory, floor=1,
                                          player_stats=player_stats, game_state=game_state,
                                          floor_states=floor_states)
            prev_scene = "game"
            result     = game_scene.run()
            if result == "pause":
                prev_scene = "game"
                scene = "pause"
            elif result == "inventory":
                prev_scene = "game"
                scene = "inventory"
            elif result == "town":
                game_scene = None
                scene = "town"
            elif result == "menu":
                prev_scene = "game"
                scene = "pause"
            elif result.startswith("floor_"):
                game_scene = None
                scene = result
            else:
                scene = result

        # ----------------------------------------------------------------
        # Dungeon — returning
        # ----------------------------------------------------------------
        elif scene == "game":
            if game_scene is None:
                game_scene = _make_game_scene(screen, inventory, floor=1,
                                          player_stats=player_stats, game_state=game_state,
                                          floor_states=floor_states)
            prev_scene = "game"
            result     = game_scene.run()
            if result == "pause":
                prev_scene = "game"
                scene = "pause"
            elif result == "inventory":
                prev_scene = "game"
                scene = "inventory"
            elif result == "town":
                game_scene = None
                scene = "town"
            elif result == "menu":
                prev_scene = "game"
                scene = "pause"
            elif result.startswith("floor_"):
                game_scene = None
                scene = result
            else:
                scene = result

        # ----------------------------------------------------------------
        # Combat
        # ----------------------------------------------------------------
        elif scene == "boss_combat":
            combat = CombatScene(screen, inventory, is_boss=True, armour=armour)
            result = combat.run()
            if game_scene:
                game_scene.combat_cooldown = game_scene.COMBAT_COOLDOWN
            if combat:
                game_state.player_hp = combat.player_hp
            if result == "death":
                game_state.player_hp = game_state.player_max_hp
                scene = "death"
            elif result == "loot":
                game_scene.boss_defeated = True
                game_state.enemies_defeated += 1
                quest_manager.on_boss_killed('goblin_king')
                quest_manager.on_combat_round()
                quest_manager.on_gold_collected(game_state.gold_collected)
                newly_done = quest_manager.check_completion(inventory, game_state, player_stats)
                leveled = player_stats.add_exp(EXP_BOSS)
                for new_level in leveled:
                    LevelUpScene(screen, player_stats, new_level).run()
                    game_state.player_max_hp = player_stats.max_hp
                combat._goblin_loot = factory_loot('goblin_king')
                scene = "loot"
            else:
                scene = "game"

        elif scene == "combat":
            _etype = None
            if game_scene and game_scene._active_enemy:
                _etype = game_scene._active_enemy.enemy_type
            combat = CombatScene(screen, inventory, armour=armour,
                                 player_hp=game_state.player_hp,
                                 player_stats=player_stats,
                                 enemy_type=_etype)
            prev_scene = "game"
            result     = combat.run()
            if game_scene:
                game_scene.combat_cooldown = game_scene.COMBAT_COOLDOWN
            if combat:
                game_state.player_hp = combat.player_hp

            if result == "pause":
                scene = "pause"
            elif result == "death":
                game_state.player_hp = game_state.player_max_hp
                scene = "death"
            elif result == "loot":
                # Remove defeated enemy from game scene
                if game_scene and game_scene._active_enemy:
                    e = game_scene._active_enemy
                    if e in game_scene.enemies:
                        game_scene.enemies.remove(e)
                    # Inject key drops into loot
                    from src.scenes.chest_scene import FloorKeyItem, BossKeyItem, RoomKeyItem
                    def _make_key(kid):
                        if kid == "floor_key":   return FloorKeyItem()
                        elif kid == "boss_key":  return BossKeyItem()
                        else:                    return RoomKeyItem(kid)
                    if e.drops_key:
                        combat._goblin_loot.append(_make_key(e.drops_key))
                    # Extra drops — check which room enemy belongs to
                    from src.scenes.game_scene import FLOOR_DATA
                    extra = FLOOR_DATA.get(game_scene.floor,{}).get("extra_drops",{})
                    for room_key, extra_kids in extra.items():
                        room_tiles = set(map(tuple, FLOOR_DATA[game_scene.floor]["rooms"].get(room_key,[])))
                        if (e.tile_col, e.tile_row) in room_tiles:
                            for kid in extra_kids:
                                combat._goblin_loot.append(_make_key(kid))
                    # Chieftain floor 1 extra: key_to_circle
                    if e.enemy_type == "goblin_chieftain" and game_scene.floor == 1:
                        combat._goblin_loot.append(_make_key("key_to_circle"))
                    game_scene._active_enemy = None
                game_state.enemies_defeated += 1
                from src.entities.entity_factory import get_stat
                _exp = EXP_GOBLIN
                if combat and combat.enemy_type:
                    _exp = get_stat(combat.enemy_type, "exp") or EXP_GOBLIN
                leveled = player_stats.add_exp(_exp)
                for new_level in leveled:
                    LevelUpScene(screen, player_stats, new_level).run()
                    game_state.player_hp = min(game_state.player_hp, player_stats.max_hp)
                    game_state.player_max_hp = player_stats.max_hp
                scene = "loot"
            else:
                scene = "game"

        # ----------------------------------------------------------------
        # Loot
        # ----------------------------------------------------------------
        elif scene == "loot":
            loot  = getattr(combat,'_goblin_loot',[]) if combat else []
            result = LootScene(screen, loot, inventory).run()
            scene  = "game" if result != "exit" else "exit"

        # ----------------------------------------------------------------
        # Chest
        # ----------------------------------------------------------------

        # ----------------------------------------------------------------
        # Floor transitions
        # ----------------------------------------------------------------
        elif scene == "floor_2":
            current_floor = 2
            # Spawn offset from return circle at (6,20) to avoid instant re-trigger
            game_scene = _make_game_scene(screen, inventory, floor=2,
                                          player_stats=player_stats, game_state=game_state,
                                          floor_states=floor_states,
                                          return_spawn=(9, 19))
            prev_scene = "game"
            scene = "game"

        elif scene == "floor_3":
            current_floor = 3
            game_scene = _make_game_scene(screen, inventory, floor=3,
                                          player_stats=player_stats, game_state=game_state,
                                          floor_states=floor_states)
            prev_scene = "game"
            scene = "game"

        elif scene == "floor_4":
            current_floor = 4
            game_scene = _make_game_scene(screen, inventory, floor=4,
                                          player_stats=player_stats, game_state=game_state,
                                          floor_states=floor_states)
            prev_scene = "game"
            scene = "game"

        elif scene == "floor_1":
            current_floor = 1
            # Returning from floor 2 — spawn just beside the floor circle, not on it
            # Floor circle is at (50,21); spawn 3 tiles left so player isn't auto-triggered
            from src.scenes.game_scene import FLOOR_DATA
            f1_circle = FLOOR_DATA[1]["floor_circle"]
            return_pos = (f1_circle[0] - 3, f1_circle[1])
            game_scene = _make_game_scene(screen, inventory, floor=1,
                                          player_stats=player_stats, game_state=game_state,
                                          floor_states=floor_states,
                                          return_spawn=return_pos)
            prev_scene = "game"
            scene = "game"

        elif scene == "chest":
            chest  = game_scene._chest_to_open
            result = ChestScene(screen, chest.items, inventory, chest=chest).run()
            scene  = "game" if result != "exit" else "exit"

        # ----------------------------------------------------------------
        # Keys / exit
        # ----------------------------------------------------------------
        elif scene == "use_key":
            result = InventoryScene(screen, inventory,
                                    use_mode=True,
                                    nearby_door=game_scene._nearby_door).run()
            scene = "game" if result != "exit" else "exit"

        # Floor transitions handled by game_scene returning "floor_2", "floor_3" etc

        # ----------------------------------------------------------------
        # Inventory
        # ----------------------------------------------------------------
        elif scene == "inventory":
            result = InventoryScene(screen, inventory).run()
            if result == "exit":
                scene = "exit"
            elif result == "armour":
                scene = "armour"
            elif result == "back":
                scene = prev_scene
            else:
                scene = prev_scene

        # ----------------------------------------------------------------
        # Map
        # ----------------------------------------------------------------
        elif scene == "map":
            from src.scenes.game_scene import ROOM_MAP, GOBLIN_PATROLS, CHEST_POSITIONS
            result = MapScene(
                screen, ROOM_MAP, game_scene.visited,
                game_scene.player.tile_col, game_scene.player.tile_row,
                CHEST_POSITIONS, GOBLIN_PATROLS,
            ).run()
            scene = "game" if result != "exit" else "exit"

        # ----------------------------------------------------------------
        # Town
        # ----------------------------------------------------------------
        elif scene == "town":
            game_state.player_max_hp = player_stats.max_hp
            game_state.player_floor = current_floor
            capture(game_state, inventory, game_scene, dungeon_cleared, "town", armour, player_stats, quest_manager)
            save_slot(0, game_state)
            prev_scene = "town"
            raw        = TownScene(screen, inventory, "Ashenvale", start_idx=town_idx).run()
            result, town_idx = raw if isinstance(raw, tuple) else (raw, 0)

            if result == "start":
                # Enter dungeon — do NOT run inline, go to "game" scene properly
                current_floor = 1
                floor_states  = {}   # fresh run from town
                game_scene = _make_game_scene(screen, inventory, floor=1,
                                              player_stats=player_stats, game_state=game_state,
                                              floor_states=floor_states)
                prev_scene = "game"
                scene = "game"
            elif result == "inventory":
                prev_scene = "town"
                pre_inv_scene = "town"
                scene = "inventory"
            elif result == "pause":
                prev_scene = "town"
                scene = "pause"
            elif result in ("inn","blacksmith","shop","antiquity",
                            "world_map","notice_board","quest_log","exit"):
                scene = result
            else:
                scene = "town"

        # ----------------------------------------------------------------
        # Shops
        # ----------------------------------------------------------------
        elif scene == "inn":
            result = InnScene(screen, inventory, game_state=game_state).run()
            scene  = "town" if result != "exit" else "exit"

        elif scene == "blacksmith":
            result = BlacksmithScene(screen, inventory, armour=armour).run()
            scene  = "town" if result != "exit" else "exit"

        elif scene == "shop":
            result = GeneralShopScene(screen, inventory).run()
            scene  = "town" if result != "exit" else "exit"

        elif scene == "antiquity":
            result = AntiquityScene(screen, inventory).run()
            scene  = "town" if result != "exit" else "exit"

        elif scene == "notice_board":
            result = NoticeBoardScene(screen, quest_manager, game_state).run()
            scene  = "town" if result not in ("exit",) else "exit"

        elif scene == "quest_log":
            result = QuestLogScene(screen, quest_manager).run()
            scene  = "town" if result not in ("exit",) else "exit"

        # ----------------------------------------------------------------
        # World map
        # ----------------------------------------------------------------
        elif scene == "world_map":
            destination = WorldMapScene(screen, "Ashenvale").run()
            if destination == "exit":
                scene = "exit"
            else:
                scene = "town"

        # ----------------------------------------------------------------
        # Death
        # ----------------------------------------------------------------
        elif scene == "death":
            result = DeathScene(screen).run()
            if result == "load_save":
                loaded = None
                for slot in range(3):
                    s2 = load_slot(slot)
                    if s2 is not None:
                        if loaded is None or s2.save_time > loaded.save_time:
                            loaded = s2
                if loaded:
                    inventory   = Inventory()
                    restore(loaded, inventory)
                    game_state  = loaded
                    dungeon_cleared = loaded.dungeon_cleared
                    game_scene  = None
                    scene = "town" if loaded.current_location == "town" else "start"
                else:
                    scene = "main_menu"
            else:
                scene = "main_menu"

        # ----------------------------------------------------------------
        # Armour
        # ----------------------------------------------------------------
        elif scene == "armour":
            result = ArmourScene(screen, inventory, armour).run()
            if result == "exit":
                scene = "exit"
            elif result == "inventory":
                scene = "inventory"
            else:
                scene = pre_inv_scene

        # ----------------------------------------------------------------
        # Exit
        # ----------------------------------------------------------------
        elif scene == "exit":
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()