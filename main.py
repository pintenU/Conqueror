import pygame
import sys

from src.ui.menu import MenuScene


def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Dungeon")

    while True:
        result = MenuScene(screen).run()

        if result == "exit":
            break

        if result == "start":
            # Placeholder — swap this out when the game scene is ready
            print("Game starting... (scene not built yet)")
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()