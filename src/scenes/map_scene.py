import pygame
import math
import random


class MapScene:
    def __init__(self, screen, room_map, visited, player_col, player_row,
                 chest_positions, goblin_patrols):
        self.screen       = screen
        self.W, self.H    = screen.get_size()
        self.clock        = pygame.time.Clock()
        self.time         = 0.0
        self.room_map     = room_map
        self.visited      = visited          # set of (col, row) floor tiles seen
        self.player_col   = player_col
        self.player_row   = player_row
        self.chest_pos    = chest_positions
        self.goblin_pos   = [(p[0][0], p[0][1]) for p in goblin_patrols]

        self.font_title  = pygame.font.SysFont("courier new", 28, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 14)

        self.open_anim = 0.0
        self.OPEN_DUR  = 0.4

        self.ROWS = len(room_map)
        self.COLS = len(room_map[0])

        # Map cell size — fit dungeon into ~70% of screen
        max_w = int(self.W * 0.70)
        max_h = int(self.H * 0.68)
        self.cell = min(max_w // self.COLS, max_h // self.ROWS)
        self.cell = max(self.cell, 4)

        self.map_w = self.COLS * self.cell
        self.map_h = self.ROWS * self.cell
        self.map_x = (self.W - self.map_w) // 2
        self.map_y = (self.H - self.map_h) // 2 + 20

        # Pre-render the paper background once
        self.paper_surf = self._build_paper()
        # Pre-render the static map (fog + tiles), updated on open
        self.map_surf   = self._build_map_surf()

    # ------------------------------------------------------------------ #
    # Paper texture
    # ------------------------------------------------------------------ #

    def _build_paper(self):
        """Worn parchment background with noise, stains and torn edges."""
        surf = pygame.Surface((self.W, self.H))
        rng  = random.Random(77)

        # Base parchment colour
        surf.fill((194, 168, 112))

        # Noise layer — vary each pixel slightly
        noise = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for _ in range(18000):
            nx = rng.randint(0, self.W - 1)
            ny = rng.randint(0, self.H - 1)
            v  = rng.randint(-22, 22)
            alpha = rng.randint(20, 60)
            pygame.draw.circle(noise, (max(0,min(255,130+v)),
                                       max(0,min(255,105+v)),
                                       max(0,min(255,60+v)), alpha),
                               (nx, ny), rng.randint(1, 4))
        surf.blit(noise, (0, 0))

        # Dark stains / water marks
        stain = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for _ in range(12):
            sx = rng.randint(0, self.W)
            sy = rng.randint(0, self.H)
            sr = rng.randint(40, 160)
            sa = rng.randint(12, 35)
            col = rng.choice([
                (80,  55,  20,  sa),
                (100, 75,  30,  sa),
                (60,  40,  10,  sa),
                (120, 90,  40,  sa),
            ])
            pygame.draw.ellipse(stain, col,
                                (sx - sr, sy - sr//2,
                                 sr*2, int(sr*1.3)))
        surf.blit(stain, (0, 0))

        # Vignette — darker burned edges
        vig = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        cx, cy = self.W // 2, self.H // 2
        max_r  = int(math.hypot(cx, cy))
        for i in range(60, 0, -1):
            r     = int(max_r * i / 60)
            alpha = int(110 * (i / 60) ** 1.8)
            pygame.draw.circle(vig, (50, 30, 8, alpha), (cx, cy), r)
        surf.blit(vig, (0, 0))

        # Torn / rough border
        border = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        rng2   = random.Random(88)
        # Draw jagged black border by drawing lots of small rects along edges
        for side in range(4):
            for i in range(0, max(self.W, self.H), 6):
                jag = rng2.randint(4, 22)
                al  = rng2.randint(140, 220)
                if side == 0:   # top
                    pygame.draw.rect(border, (20,12,4,al), (i, 0,      7, jag))
                elif side == 1: # bottom
                    pygame.draw.rect(border, (20,12,4,al), (i, self.H-jag, 7, jag))
                elif side == 2: # left
                    pygame.draw.rect(border, (20,12,4,al), (0, i,      jag, 7))
                else:           # right
                    pygame.draw.rect(border, (20,12,4,al), (self.W-jag, i, jag, 7))
        surf.blit(border, (0, 0))

        # Faint horizontal line texture (old paper fibres)
        lines = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for y in range(0, self.H, rng.randint(3, 6)):
            alpha = rng.randint(4, 14)
            pygame.draw.line(lines, (100, 75, 30, alpha), (0, y), (self.W, y), 1)
        surf.blit(lines, (0, 0))

        return surf

    # ------------------------------------------------------------------ #
    # Map surface
    # ------------------------------------------------------------------ #

    def _build_map_surf(self):
        """Render the tile map with fog of war onto a transparent surface."""
        surf = pygame.Surface((self.map_w, self.map_h), pygame.SRCALPHA)
        cell = self.cell
        rng  = random.Random(42)

        FLOOR = 0
        WALL  = 1

        for row in range(self.ROWS):
            for col in range(self.COLS):
                tile = self.room_map[row][col]
                x    = col * cell
                y    = row * cell

                if (col, row) not in self.visited:
                    # Fog — dark smudge so shape is slightly hinted
                    fog = pygame.Surface((cell, cell), pygame.SRCALPHA)
                    fog.fill((30, 18, 8, 180))
                    surf.blit(fog, (x, y))
                    continue

                if tile == FLOOR:
                    # Parchment-coloured floor with ink crosshatch
                    v = rng.randint(-10, 10)
                    pygame.draw.rect(surf, (155+v, 128+v, 78+v, 255),
                                     (x, y, cell, cell))
                    # Subtle grid lines
                    gc = (120, 95, 55, 80)
                    pygame.draw.line(surf, gc, (x,y),      (x+cell,y),      1)
                    pygame.draw.line(surf, gc, (x,y),      (x,y+cell),      1)
                    # Occasional hatching mark
                    if rng.random() < 0.15:
                        pygame.draw.line(surf, (100,75,40,60),
                                         (x+2,y+2),(x+cell-2,y+cell-2),1)

                elif tile == WALL:
                    # Dark ink wall block
                    v = rng.randint(-8, 8)
                    pygame.draw.rect(surf, (65+v, 48+v, 28+v, 255),
                                     (x, y, cell, cell))
                    # Brick mortar lines
                    mc = (45, 33, 18, 120)
                    pygame.draw.line(surf, mc, (x,y+cell//2),(x+cell,y+cell//2),1)
                    if (row+col) % 2 == 0:
                        pygame.draw.line(surf, mc,
                                         (x+cell//2,y),(x+cell//2,y+cell//2),1)
                    else:
                        pygame.draw.line(surf, mc,
                                         (x+cell//2,y+cell//2),(x+cell//2,y+cell),1)

        return surf

    # ------------------------------------------------------------------ #
    # Draw helpers
    # ------------------------------------------------------------------ #

    def _draw_title(self, alpha):
        title = self.font_title.render("— DUNGEON MAP —", True, (60, 38, 14))
        ts    = pygame.Surface(title.get_size(), pygame.SRCALPHA)
        ts.blit(title, (0, 0))
        ts.set_alpha(alpha)
        tx = self.W // 2 - title.get_width() // 2
        ty = self.map_y - title.get_height() - 10
        self.screen.blit(ts, (tx, ty))

    def _draw_icons(self):
        """Draw chest, goblin and player markers on the map."""
        cell = self.cell
        FLOOR = 0

        # Chests
        for col, row in self.chest_pos:
            if (col, row) in self.visited:
                cx = self.map_x + col * cell + cell // 2
                cy = self.map_y + row * cell + cell // 2
                r  = max(2, cell // 3)
                pygame.draw.rect(self.screen, (160, 110, 30),
                                 (cx-r, cy-r//2, r*2, int(r*1.4)))
                pygame.draw.rect(self.screen, (200, 160, 60),
                                 (cx-r, cy-r//2, r*2, int(r*1.4)), 1)

        # Goblins (red X)
        for col, row in self.goblin_pos:
            if (col, row) in self.visited:
                cx = self.map_x + col * cell + cell // 2
                cy = self.map_y + row * cell + cell // 2
                r  = max(2, cell // 3)
                pygame.draw.line(self.screen, (160, 40, 30),
                                 (cx-r, cy-r), (cx+r, cy+r), 2)
                pygame.draw.line(self.screen, (160, 40, 30),
                                 (cx+r, cy-r), (cx-r, cy+r), 2)

        # Player dot (ink blue circle with pulse)
        pcx = self.map_x + self.player_col * cell + cell // 2
        pcy = self.map_y + self.player_row * cell + cell // 2
        pulse = 0.7 + 0.3 * math.sin(self.time * 4)
        pr    = max(3, int(cell * 0.38 * pulse))
        pygame.draw.circle(self.screen, (40, 60, 120), (pcx, pcy), pr + 2)
        pygame.draw.circle(self.screen, (80, 110, 200), (pcx, pcy), pr)
        pygame.draw.circle(self.screen, (160, 190, 255), (pcx, pcy), max(1, pr//2))

    def _draw_legend(self, alpha):
        items = [
            ((80, 110, 200), "You"),
            ((160, 110, 30), "Chest"),
            ((160, 40,  30), "Enemy"),
        ]
        lx = self.map_x
        ly = self.map_y + self.map_h + 10
        for col, label in items:
            pygame.draw.circle(self.screen, col, (lx + 6, ly + 8), 5)
            ls = self.font_small.render(label, True, (60, 38, 14))
            s  = pygame.Surface(ls.get_size(), pygame.SRCALPHA)
            s.blit(ls, (0, 0))
            s.set_alpha(alpha)
            self.screen.blit(s, (lx + 16, ly))
            lx += ls.get_width() + 36

        # Close hint on right
        hint = self.font_small.render("M  close map", True, (80, 55, 22))
        hs   = pygame.Surface(hint.get_size(), pygame.SRCALPHA)
        hs.blit(hint, (0, 0))
        hs.set_alpha(alpha)
        self.screen.blit(hs, (self.map_x + self.map_w - hint.get_width(), ly))

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while True:
            dt         = self.clock.tick(60) / 1000.0
            self.time += dt
            self.open_anim = min(self.open_anim + dt, self.OPEN_DUR)
            t          = min(1.0, self.open_anim / self.OPEN_DUR)
            ease       = 1 - (1 - t) ** 3

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_m, pygame.K_ESCAPE):
                        return "game"

            # --- Draw ---
            # Paper background
            self.screen.blit(self.paper_surf, (0, 0))

            # Fade in map
            map_copy = self.map_surf.copy()
            map_copy.set_alpha(int(255 * ease))
            self.screen.blit(map_copy, (self.map_x, self.map_y))

            # Ink border around map area
            border_col = (55, 35, 12)
            pygame.draw.rect(self.screen, border_col,
                             (self.map_x - 2, self.map_y - 2,
                              self.map_w + 4, self.map_h + 4), 2)
            # Double border
            pygame.draw.rect(self.screen, (80, 55, 22),
                             (self.map_x - 6, self.map_y - 6,
                              self.map_w + 12, self.map_h + 12), 1)

            alpha = int(255 * ease)
            if ease > 0.5:
                self._draw_icons()
                self._draw_title(alpha)
                self._draw_legend(alpha)

            pygame.display.flip()