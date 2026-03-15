import pygame
import sys
import math

from src.ui.menu import MenuScene   # keep for now but we replace it
from src.scenes.main_menu_scene import MainMenuScene
from src.scenes.game_scene import GameScene
from src.scenes.combat_scene import CombatScene
from src.scenes.chest_scene import ChestScene
from src.scenes.inventory_scene import InventoryScene
from src.scenes.loot_scene import LootScene
from src.scenes.map_scene import MapScene
from src.scenes.world_map_scene import WorldMapScene
from src.scenes.town_scene import TownScene
from src.scenes.shop_scene import InnScene, GeneralShopScene, BlacksmithScene, AntiquityScene
from src.inventory import Inventory
from src.save_system import GameState, capture, restore, save_slot, format_playtime
from src.scenes.saves_scene import SavesScene


def _make_game_scene(screen, inventory, exit_unlocked=False):
    gs = GameScene(screen, inventory)
    if exit_unlocked:
        gs.exit_tile.locked = False
        from src.scenes.chest_scene import ExitKeyItem
        for chest in gs.chests:
            chest.items = [it for it in chest.items
                           if not isinstance(it, ExitKeyItem)]
    return gs


def _pause(screen, scene_stack):
    """
    Show the pause menu. Returns:
      "continue"  — resume
      "main_menu" — drop to main menu
      "exit"      — quit
    """
    result = MainMenuScene(screen, mode="pause").run()
    return result


def main():
    pygame.init()
    pygame.mixer.init()

    screen         = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Dungeon")

    inventory       = Inventory()
    game_scene      = None
    combat          = None
    dungeon_cleared = False
    prev_scene      = "menu"
    game_state      = GameState()   # live stats tracker
    _playtime_clock = 0.0           # seconds since last tick

    # ------------------------------------------------------------------ #
    # Start at main menu
    # ------------------------------------------------------------------ #
    scene = "main_menu"

    import time as _time
    _last_tick = _time.time()

    while True:
        # Tick playtime
        _now = _time.time()
        game_state.playtime_seconds += _now - _last_tick
        _last_tick = _now

        # ----------------------------------------------------------------
        # Main menu (startup)
        # ----------------------------------------------------------------
        if scene == "main_menu":
            result = MainMenuScene(screen, mode="start").run()
            if result == "new_game":
                # Reset everything for a fresh run
                inventory       = Inventory()
                game_scene      = None
                dungeon_cleared = False
                scene           = "start"
            elif result == "saves":
                scene = "saves"
            elif result == "exit":
                break

        # ----------------------------------------------------------------
        # Saves (from main menu — load only)
        # ----------------------------------------------------------------
        elif scene == "saves":
            result = SavesScene(screen, game_state=None, mode="load").run()
            if isinstance(result, tuple) and result[0] == "loaded":
                loaded_state = result[1]
                # Start fresh inventory and restore from save
                inventory       = Inventory()
                restore(loaded_state, inventory)
                game_state      = loaded_state
                dungeon_cleared = loaded_state.dungeon_cleared
                scene           = "town" if loaded_state.current_location == "town" else "start"
            elif result == "exit":
                scene = "exit"
            else:
                scene = "main_menu"

        # ----------------------------------------------------------------
        # Pause menu (accessible from anywhere)
        # ----------------------------------------------------------------
        elif scene == "pause":
            result = MainMenuScene(screen, mode="pause").run()
            if result == "continue":
                scene = prev_scene
            elif result == "saves":
                # Capture current state for saving
                capture(game_state, inventory, game_scene, dungeon_cleared,
                        "dungeon" if prev_scene == "game" else "town")
                r2 = SavesScene(screen, game_state=game_state, mode="both").run()
                if isinstance(r2, tuple) and r2[0] == "loaded":
                    loaded = r2[1]
                    inventory       = Inventory()
                    restore(loaded, inventory)
                    game_state      = loaded
                    dungeon_cleared = loaded.dungeon_cleared
                    game_scene      = None
                    scene = "town" if loaded.current_location == "town" else "start"
                else:
                    scene = "pause"
            elif result == "main_menu":
                scene = "main_menu"
            elif result == "exit":
                break

        # ----------------------------------------------------------------
        # Dungeon
        # ----------------------------------------------------------------
        elif scene == "start":
            game_scene = _make_game_scene(screen, inventory, dungeon_cleared)
            prev_scene = "game"
            result     = game_scene.run()
            if result == "pause":
                prev_scene = "game"
                scene = "pause"
            elif result == "inventory":
                prev_scene = "game"
                scene = "inventory"
            elif result == "town":
                if not game_scene.exit_tile.locked:
                    dungeon_cleared = True
                game_scene = None
                scene = "town"
            elif result == "menu":
                prev_scene = "game"
                scene = "pause"
            else:
                scene = result

        elif scene == "game":
            if game_scene is None:
                game_scene = _make_game_scene(screen, inventory, dungeon_cleared)
            prev_scene = "game"
            result     = game_scene.run()
            if result == "pause":
                prev_scene = "game"
                scene = "pause"
            elif result == "inventory":
                prev_scene = "game"
                scene = "inventory"
            elif result == "town":
                if game_scene and not game_scene.exit_tile.locked:
                    dungeon_cleared = True
                game_scene = None
                scene = "town"
            elif result == "menu":
                prev_scene = "game"
                scene = "pause"
            else:
                scene = result

        # ----------------------------------------------------------------
        # Combat
        # ----------------------------------------------------------------
        elif scene == "boss_combat":
            combat = CombatScene(screen, inventory, is_boss=True)
            result = combat.run()
            if game_scene:
                game_scene.combat_cooldown = game_scene.COMBAT_COOLDOWN
            if result == "loot":
                # Boss defeated — mark it
                game_scene.boss_defeated = True
                game_state.enemies_defeated += 1
                loot = getattr(combat,'_goblin_loot',[])
                # Boss always drops good loot
                from src.scenes.chest_scene import GoldItem, PotionItem
                combat._goblin_loot = [GoldItem(50), PotionItem(), PotionItem()]
                scene = "loot"
            else:
                scene = "game"

        elif scene == "combat":
            combat     = CombatScene(screen, inventory)
            prev_scene = "game"
            result     = combat.run()
            if game_scene:
                game_scene.combat_cooldown = game_scene.COMBAT_COOLDOWN

            if result == "pause":
                scene = "pause"
            elif result == "loot":
                if game_scene and game_scene.goblins:
                    ts  = 48
                    pcx = game_scene.player.px + ts//2
                    pcy = game_scene.player.py + ts//2
                    idx = min(
                        range(len(game_scene.goblins)),
                        key=lambda i: math.hypot(
                            game_scene.goblins[i].px+ts//2-pcx,
                            game_scene.goblins[i].py+ts//2-pcy))
                    defeated = game_scene.goblins.pop(idx)

                    pass  # key drop guarantee removed — keys in chests
                if result == "loot":
                    game_state.enemies_defeated += 1
                scene = "loot" if result == "loot" else "game"
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

        elif scene == "use_exit_key":
            result = InventoryScene(screen, inventory,
                                    use_mode=True,
                                    nearby_door=game_scene.exit_tile).run()
            scene = "game" if result != "exit" else "exit"

        # ----------------------------------------------------------------
        # Inventory
        # ----------------------------------------------------------------
        elif scene == "inventory":
            result = InventoryScene(screen, inventory).run()
            if result == "exit":
                scene = "exit"
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
            # Autosave slot 0 when arriving in town
            capture(game_state, inventory, game_scene, dungeon_cleared, "town")
            save_slot(0, game_state)
            prev_scene = "town"
            result     = TownScene(screen, inventory, "Ashenvale").run()

            if result == "start":
                game_scene = _make_game_scene(screen, inventory, dungeon_cleared)
                prev_scene = "game"
                r2 = game_scene.run()
                if r2 == "town" and not game_scene.exit_tile.locked:
                    dungeon_cleared = True
                if r2 in ("town","menu","pause"):
                    game_scene = None
                scene = "town" if r2 in ("town","menu","pause") else \
                        "pause" if r2 == "pause" else r2
            elif result == "inventory":
                prev_scene = "town"
                scene = "inventory"
            elif result == "pause":
                prev_scene = "town"
                scene = "pause"
            elif result in ("inn","blacksmith","shop","antiquity",
                            "world_map","exit"):
                scene = result
            else:
                scene = "town"

        # ----------------------------------------------------------------
        # Shops
        # ----------------------------------------------------------------
        elif scene == "inn":
            result = InnScene(screen, inventory).run()
            scene  = "town" if result != "exit" else "exit"

        elif scene == "blacksmith":
            result = BlacksmithScene(screen, inventory).run()
            scene  = "town" if result != "exit" else "exit"

        elif scene == "shop":
            result = GeneralShopScene(screen, inventory).run()
            scene  = "town" if result != "exit" else "exit"

        elif scene == "antiquity":
            result = AntiquityScene(screen, inventory).run()
            scene  = "town" if result != "exit" else "exit"

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
        # Exit
        # ----------------------------------------------------------------
        elif scene == "exit":
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()