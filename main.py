import pygame
import sys
import math

from src.ui.menu import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.combat_scene import CombatScene
from src.scenes.chest_scene import ChestScene
from src.scenes.inventory_scene import InventoryScene
from src.scenes.loot_scene import LootScene
from src.scenes.map_scene import MapScene
from src.scenes.world_map_scene import WorldMapScene
from src.inventory import Inventory


def main():
    pygame.init()
    pygame.mixer.init()

    screen    = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Dungeon")

    inventory  = Inventory()
    scene      = "menu"
    game_scene = None
    combat     = None   # keep reference so we can read loot after

    while True:
        if scene == "menu":
            scene = MenuScene(screen).run()

        elif scene == "start":
            game_scene = GameScene(screen, inventory)
            scene = game_scene.run()

        elif scene == "game":
            if game_scene is None:
                game_scene = GameScene(screen, inventory)
            scene = game_scene.run()

        elif scene == "combat":
            combat = CombatScene(screen, inventory)
            result = combat.run()
            if game_scene:
                game_scene.combat_cooldown = game_scene.COMBAT_COOLDOWN
            if result == "loot":
                # Remove the closest goblin to the player
                if game_scene and game_scene.goblins:
                    ts  = 48
                    pcx = game_scene.player.px + ts // 2
                    pcy = game_scene.player.py + ts // 2
                    idx = min(
                        range(len(game_scene.goblins)),
                        key=lambda i: math.hypot(
                            game_scene.goblins[i].px + ts//2 - pcx,
                            game_scene.goblins[i].py + ts//2 - pcy))
                    defeated = game_scene.goblins.pop(idx)

                    # Room B goblin (patrol cols 22-31, row 5) always drops key_ab
                    from src.scenes.chest_scene import KeyItem
                    patrol = getattr(defeated, 'patrol_tiles', [])
                    is_room_b_goblin = any(
                        col in range(20, 34) and row == 5
                        for col, row in patrol)
                    if is_room_b_goblin and combat:
                        loot = getattr(combat, '_goblin_loot', [])
                        # Replace or add the key
                        combat._goblin_loot = [KeyItem("key_ab")] + [
                            it for it in loot
                            if not isinstance(it, KeyItem)]
                scene = "loot"
            else:
                scene = "game"

        elif scene == "loot":
            loot = getattr(combat, '_goblin_loot', []) if combat else []
            scene = LootScene(screen, loot, inventory).run()
            if scene != "exit":
                scene = "game"

        elif scene == "chest":
            items = game_scene._chest_to_open.items
            scene = ChestScene(screen, items, inventory).run()
            if scene != "exit":
                scene = "game"

        elif scene == "use_key":
            scene = InventoryScene(screen, inventory,
                                   use_mode=True,
                                   nearby_door=game_scene._nearby_door).run()
            if scene != "exit":
                scene = "game"

        elif scene == "inventory":
            scene = InventoryScene(screen, inventory).run()
            if scene != "exit":
                scene = "game"

        elif scene == "map":
            from src.scenes.game_scene import ROOM_MAP, GOBLIN_PATROLS, CHEST_POSITIONS
            scene = MapScene(
                screen, ROOM_MAP, game_scene.visited,
                game_scene.player.tile_col, game_scene.player.tile_row,
                CHEST_POSITIONS, GOBLIN_PATROLS,
            ).run()
            if scene != "exit":
                scene = "game"

        elif scene == "use_exit_key":
            # Open inventory in key-use mode for the exit
            scene = InventoryScene(screen, inventory,
                                   use_mode=True,
                                   nearby_door=game_scene.exit_tile).run()
            # If the exit key was used, unlock the tile
            from src.scenes.chest_scene import ExitKeyItem
            if not game_scene.exit_tile.locked:
                pass   # already unlocked by inventory scene
            else:
                # Check if player used the exit key
                if not inventory.has(ExitKeyItem):
                    game_scene.exit_tile.locked = False
            if scene != "exit":
                scene = "game"

        elif scene == "world_map":
            destination = WorldMapScene(screen, "Dungeon").run()
            if destination == "exit":
                scene = "exit"
            elif destination == "cancelled":
                scene = "game"
            else:
                # For now, just return to game — 
                # future: load new dungeon for destination
                scene = "game"

        elif scene == "exit":
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()