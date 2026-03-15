import pygame
import math
import random

from src.entities.player import Player
from src.entities.goblin import Goblin


TILE_SIZE = 48
FLOOR = 0
WALL  = 1
EMPTY = 2

ROOM_MAP = [
    [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],
    [2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],
    [2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2],
    [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],
]

ROWS = len(ROOM_MAP)
COLS = len(ROOM_MAP[0])

TORCH_POSITIONS = [
    (3,  2), (11, 2), (19, 2),
    (3, 14), (11,14), (19,14),
    (1,  5), (1, 11),
    (23, 5), (23,11),
]

MOVE_KEYS = {
    pygame.K_w: ( 0, -1),
    pygame.K_s: ( 0,  1),
    pygame.K_a: (-1,  0),
    pygame.K_d: ( 1,  0),
}

# Goblin patrol routes — list of (col, row) waypoints
GOBLIN_PATROLS = [
    [(3, 5),  (20, 5)],   # top patrol, walks horizontally
    [(3, 11), (20, 11)],  # bottom patrol
    [(12, 3), (12, 13)],  # middle vertical patrol
]


# ---------------------------------------------------------------------------
# Tile rendering
# ---------------------------------------------------------------------------

def _draw_floor_tile(surface, x, y, rng):
    ts = TILE_SIZE
    v  = rng.randint(-8, 8)
    pygame.draw.rect(surface, (38+v, 30+v, 22+v), (x, y, ts, ts))
    pygame.draw.line(surface, (25, 20, 14), (x, y),       (x+ts-1, y),     1)
    pygame.draw.line(surface, (25, 20, 14), (x, y),       (x, y+ts-1),     1)
    if rng.random() < 0.25:
        cx = x + rng.randint(8, ts-8)
        cy = y + rng.randint(8, ts-8)
        pygame.draw.line(surface, (28, 22, 16), (cx, cy),
                         (cx+rng.randint(-6,6), cy+rng.randint(-6,6)), 1)

def _draw_wall_tile(surface, x, y, row, col, rng):
    ts = TILE_SIZE
    if (row+col) % 2 == 0:
        base, hi, lo = (52,42,30), (68,56,40), (32,25,17)
    else:
        base, hi, lo = (46,37,26), (60,50,36), (28,22,14)
    pygame.draw.rect(surface, base, (x, y, ts, ts))
    pygame.draw.line(surface, hi, (x,y),         (x+ts-1,y),         1)
    pygame.draw.line(surface, hi, (x,y),         (x,y+ts-1),         1)
    pygame.draw.line(surface, lo, (x,y+ts-1),    (x+ts-1,y+ts-1),    1)
    pygame.draw.line(surface, lo, (x+ts-1,y),    (x+ts-1,y+ts-1),    1)
    pygame.draw.line(surface, (30,23,15), (x,y+ts//2), (x+ts,y+ts//2), 1)

def _draw_void_tile(surface, x, y):
    pygame.draw.rect(surface, (4,3,2), (x, y, TILE_SIZE, TILE_SIZE))

def build_tile_surface():
    ts   = TILE_SIZE
    surf = pygame.Surface((COLS*ts, ROWS*ts))
    surf.fill((4,3,2))
    rng  = random.Random(1337)
    for row in range(ROWS):
        for col in range(COLS):
            tile = ROOM_MAP[row][col]
            x, y = col*ts, row*ts
            if   tile == FLOOR: _draw_floor_tile(surf, x, y, rng)
            elif tile == WALL:  _draw_wall_tile(surf, x, y, row, col, rng)
            else:               _draw_void_tile(surf, x, y)
    return surf


# ---------------------------------------------------------------------------
# Torch
# ---------------------------------------------------------------------------

class Torch:
    def __init__(self, col, row):
        self.col   = col
        self.row   = row
        self.phase = random.uniform(0, math.tau)
        self.freq1 = random.uniform(2.8, 3.6)
        self.freq2 = random.uniform(5.0, 7.0)

    def flame_brightness(self, t):
        v = (math.sin(t*self.freq1+self.phase)*0.4 +
             math.sin(t*self.freq2+self.phase*1.3)*0.2 + 0.85)
        return max(0.55, min(1.0, v))

    def draw(self, surface, t, ox, oy):
        ts  = TILE_SIZE
        cx  = ox + self.col*ts + ts//2
        cy  = oy + self.row*ts + ts//2
        bri = self.flame_brightness(t)

        glow_r = int(ts*4.5)
        glow   = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        for radius, alpha in [(glow_r, int(18*bri)),
                               (glow_r*2//3, int(35*bri)),
                               (glow_r//3,   int(55*bri))]:
            pygame.draw.circle(glow, (200,130,40,alpha), (glow_r,glow_r), radius)
        surface.blit(glow, (cx-glow_r, cy-glow_r),
                     special_flags=pygame.BLEND_RGBA_ADD)

        pygame.draw.rect(surface, (80,65,45), (cx-4, cy,   8, 10))
        pygame.draw.rect(surface, (80,65,45), (cx-6, cy+8, 12, 4))

        fx = cx
        fy = cy - 2
        ox2 = int(math.sin(t*self.freq1*1.5+self.phase)*2)
        pygame.draw.polygon(surface, (int(200*bri), int(100*bri), 10), [
            (fx-6+ox2,fy),(fx-9+ox2,fy-8),(fx+ox2,fy-18),
            (fx+9+ox2,fy-8),(fx+6+ox2,fy)])
        pygame.draw.polygon(surface, (int(230*bri), int(155*bri), 20), [
            (fx-3+ox2,fy-2),(fx-5+ox2,fy-9),(fx+ox2,fy-16),
            (fx+5+ox2,fy-9),(fx+3+ox2,fy-2)])
        pygame.draw.polygon(surface, (255,230,160), [
            (fx-1+ox2,fy-4),(fx+ox2,fy-13),(fx+1+ox2,fy-4)])


# ---------------------------------------------------------------------------
# GameScene
# ---------------------------------------------------------------------------

class GameScene:
    def __init__(self, screen):
        self.screen = screen
        self.W, self.H = screen.get_size()
        self.clock  = pygame.time.Clock()
        self.time   = 0.0

        ts = TILE_SIZE
        self.offset_x = (self.W - COLS*ts) // 2
        self.offset_y = (self.H - ROWS*ts) // 2

        self.tile_surf = build_tile_surface()
        self.torches   = [Torch(c,r) for c,r in TORCH_POSITIONS]
        self.vignette  = self._build_vignette()

        self.player  = Player(12, 8, TILE_SIZE)
        self.goblins = [
            Goblin(patrol[0][0], patrol[0][1], TILE_SIZE, patrol)
            for patrol in GOBLIN_PATROLS
        ]

    def _build_vignette(self):
        surf   = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        cx, cy = self.W//2, self.H//2
        max_r  = int(math.hypot(cx, cy))
        for i in range(80, 0, -1):
            r     = int(max_r * i/80)
            alpha = int(200 * (i/80)**2.2)
            pygame.draw.circle(surf, (0,0,0,alpha), (cx,cy), r)
        return surf

    def _draw_ambient_darkness(self):
        dark = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        dark.fill((0,0,0,155))
        ts = TILE_SIZE
        for torch in self.torches:
            bri = torch.flame_brightness(self.time)
            cx  = self.offset_x + torch.col*ts + ts//2
            cy  = self.offset_y + torch.row*ts + ts//2
            pygame.draw.circle(dark, (0,0,0,0), (cx,cy), int(ts*5*bri))
        px = self.offset_x + int(self.player.px) + ts//2
        py = self.offset_y + int(self.player.py) + ts//2
        pygame.draw.circle(dark, (0,0,0,0), (px,py), int(ts*2.5))
        self.screen.blit(dark, (0,0))

    def _handle_input(self):
        keys = pygame.key.get_pressed()
        for key, (dc, dr) in MOVE_KEYS.items():
            if keys[key]:
                self.player.try_move(dc, dr, ROOM_MAP)
                break

    def run(self):
        while True:
            dt        = self.clock.tick(60) / 1000.0
            self.time += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

            self._handle_input()
            self.player.update(dt)
            for goblin in self.goblins:
                goblin.update(dt)

            # --- draw ---
            self.screen.fill((4,3,2))
            self.screen.blit(self.tile_surf, (self.offset_x, self.offset_y))
            self._draw_ambient_darkness()

            for torch in self.torches:
                torch.draw(self.screen, self.time, self.offset_x, self.offset_y)

            for goblin in self.goblins:
                goblin.draw(self.screen, self.offset_x, self.offset_y)

            self.player.draw(self.screen, self.offset_x, self.offset_y)

            self.screen.blit(self.vignette, (0,0))
            pygame.display.flip()