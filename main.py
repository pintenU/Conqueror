import pygame
import sys

from src.ui.menu import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.combat_scene import CombatScene


def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Dungeon")

    scene = "menu"

    while True:
        if scene == "menu":
            scene = MenuScene(screen).run()

        elif scene == "start":
            scene = GameScene(screen).run()

        elif scene == "game":
            scene = GameScene(screen).run()

        elif scene == "combat":
            scene = CombatScene(screen).run()

        elif scene == "exit":
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()