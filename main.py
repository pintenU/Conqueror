import pygame
import sys

from src.ui.menu import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.combat_scene import CombatScene
from src.scenes.chest_scene import ChestScene
from src.scenes.inventory_scene import InventoryScene
from src.inventory import Inventory


def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Dungeon")

    inventory  = Inventory()
    scene      = "menu"
    game_scene = None

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
            CombatScene(screen, inventory).run()
            # Always return to game, reset cooldown before re-entering
            if game_scene:
                game_scene.combat_cooldown = game_scene.COMBAT_COOLDOWN
            scene = "game"

        elif scene == "chest":
            items = game_scene._chest_to_open.items
            scene = ChestScene(screen, items, inventory).run()

        elif scene == "inventory":
            scene = InventoryScene(screen, inventory).run()

        elif scene == "exit":
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()