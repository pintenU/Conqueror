import pygame
import math
import random

from src.entities.player import Player
from src.entities.goblin import Goblin


TILE_SIZE = 48
FLOOR = 0
WALL  = 1
EMPTY = 2

# ---------------------------------------------------------------------------
# Multi-room dungeon map (51 cols x 43 rows)
# Layout:
#   [Room A] --door-- [Room B] --door-- [Room C]
#       |                                   |
#     door                                door
#       |                                   |
#   [Room D] --door-- [Room E] --door-- [Room F]
#       |
#     door
#       |
#   [Room G]          [Room H] (connected to E via door)
#
# All rooms are rectangular, connected by single-tile doorways
# ---------------------------------------------------------------------------

# Helper to carve a room into a blank EMPTY map
def _room(grid, col, row, w, h):
    """Carve a room with walls at col,row of size w x h."""
    for r in range(row, row + h):
        for c in range(col, col + w):
            if r == row or r == row+h-1 or c == col or c == col+w-1:
                grid[r][c] = WALL
            else:
                grid[r][c] = FLOOR

def _door(grid, col, row):
    """Open a single doorway tile."""
    grid[row][col] = FLOOR

def _hcorridor(grid, col, row, length):
    """Horizontal corridor of floor tiles."""
    for c in range(col, col + length):
        grid[row][c] = FLOOR

def _vcorridor(grid, col, row, length):
    """Vertical corridor of floor tiles."""
    for r in range(row, row + length):
        grid[col][r] = FLOOR   # note: grid[row][col]


ROWS = 43
COLS = 51

def _build_room_map():
    grid = [[EMPTY]*COLS for _ in range(ROWS)]

    # Room A — top left  (col 1, row 1, 17w x 13h)
    _room(grid, 1, 1, 17, 13)
    # Room B — top middle (col 20, row 1, 13w x 13h)
    _room(grid, 20, 1, 13, 13)
    # Room C — top right  (col 35, row 1, 15w x 13h)
    _room(grid, 35, 1, 15, 13)

    # Room D — mid left   (col 1, row 16, 17w x 13h)
    _room(grid, 1, 16, 17, 13)
    # Room E — mid centre (col 20, row 16, 13w x 13h)
    _room(grid, 20, 16, 13, 13)
    # Room F — mid right  (col 35, row 16, 15w x 13h)
    _room(grid, 35, 16, 15, 13)

    # Room G — bottom left (col 1, row 31, 17w x 11h)
    _room(grid, 1, 31, 17, 11)
    # Room H — bottom centre (col 20, row 31, 13w x 11h)
    _room(grid, 20, 31, 13, 11)

    # --- Doorways + gap-filling corridors ---
    # A <-> B: open walls + fill the 2-col gap between them
    for c2 in range(17, 21):   # cols 17..20
        _door(grid, c2, 7)
        _door(grid, c2, 8)

    # B <-> C: open walls + fill gap
    for c2 in range(33, 36):
        _door(grid, c2, 7)
        _door(grid, c2, 8)

    # A <-> D: open walls + fill the 2-row gap
    for r2 in range(13, 17):
        _door(grid, 9,  r2)
        _door(grid, 10, r2)

    # C <-> F
    for r2 in range(13, 17):
        _door(grid, 42, r2)
        _door(grid, 43, r2)

    # D <-> E
    for c2 in range(17, 21):
        _door(grid, c2, 22)
        _door(grid, c2, 23)

    # E <-> F
    for c2 in range(33, 36):
        _door(grid, c2, 22)
        _door(grid, c2, 23)

    # D <-> G
    for r2 in range(28, 32):
        _door(grid, 9,  r2)
        _door(grid, 10, r2)

    # E <-> H
    for r2 in range(28, 32):
        _door(grid, 26, r2)
        _door(grid, 27, r2)

    return grid

ROOM_MAP = _build_room_map()

TORCH_POSITIONS = [
    # Room A
    (3,2),(13,2),(3,11),(13,11),
    # Room B
    (22,2),(30,2),(22,11),(30,11),
    # Room C
    (37,2),(47,2),(37,11),(47,11),
    # Room D
    (3,17),(13,17),(3,27),(13,27),
    # Room E
    (22,17),(30,17),(22,27),(30,27),
    # Room F
    (37,17),(47,17),(37,27),(47,27),
    # Room G
    (3,32),(13,32),(3,40),(13,40),
    # Room H
    (22,32),(30,32),(22,40),(30,40),
]

GOBLIN_PATROLS = [
    [(3,5),   (14,5)],
    [(22,5),  (31,5)],
    [(37,5),  (48,5)],
    [(3,20),  (14,20)],
    [(22,20), (31,20)],
    [(37,20), (48,20)],
    [(3,35),  (14,35)],
    [(22,35), (30,35)],
]

CHEST_POSITIONS = [
    (14, 10),
    (21, 10),
    (48, 10),
    (14, 26),
    (31, 26),
    (48, 26),
    (14, 39),
    (21, 39),
]

# Locked doors — (col, row, orientation)
# orientation: 'h' = horizontal passage, 'v' = vertical passage
LOCKED_DOORS = [
    (18, 7,  'h'),   # A <-> B
    (9,  14, 'v'),   # A <-> D
    (33, 22, 'h'),   # E <-> F
    (9,  29, 'v'),   # D <-> G
]

# Key IDs that unlock each door (same index as LOCKED_DOORS)
DOOR_KEY_IDS = ["key_ab", "key_ad", "key_ef", "key_dg"]

# Exit tile position — Room A, top-left corner area
EXIT_TILE = (3, 3)

MOVE_KEYS = {
    pygame.K_w: ( 0, -1),
    pygame.K_s: ( 0,  1),
    pygame.K_a: (-1,  0),
    pygame.K_d: ( 1,  0),
}


# ---------------------------------------------------------------------------
# Tile rendering
# ---------------------------------------------------------------------------

def _draw_floor_tile(surface, x, y, rng):
    ts = TILE_SIZE
    v  = rng.randint(-8, 8)
    pygame.draw.rect(surface, (38+v, 30+v, 22+v), (x, y, ts, ts))
    pygame.draw.line(surface, (25,20,14), (x,y), (x+ts-1,y), 1)
    pygame.draw.line(surface, (25,20,14), (x,y), (x,y+ts-1), 1)
    if rng.random() < 0.25:
        cx = x + rng.randint(8, ts-8)
        cy = y + rng.randint(8, ts-8)
        pygame.draw.line(surface, (28,22,16), (cx,cy),
                         (cx+rng.randint(-6,6), cy+rng.randint(-6,6)), 1)

def _draw_wall_tile(surface, x, y, row, col, rng):
    ts = TILE_SIZE
    if (row+col) % 2 == 0:
        base, hi, lo = (52,42,30), (68,56,40), (32,25,17)
    else:
        base, hi, lo = (46,37,26), (60,50,36), (28,22,14)
    pygame.draw.rect(surface, base, (x,y,ts,ts))
    pygame.draw.line(surface, hi, (x,y),      (x+ts-1,y),      1)
    pygame.draw.line(surface, hi, (x,y),      (x,y+ts-1),      1)
    pygame.draw.line(surface, lo, (x,y+ts-1), (x+ts-1,y+ts-1), 1)
    pygame.draw.line(surface, lo, (x+ts-1,y), (x+ts-1,y+ts-1), 1)
    pygame.draw.line(surface, (30,23,15), (x,y+ts//2), (x+ts,y+ts//2), 1)

def _draw_void_tile(surface, x, y):
    pygame.draw.rect(surface, (4,3,2), (x,y,TILE_SIZE,TILE_SIZE))

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
# Chest
# ---------------------------------------------------------------------------

class Chest:
    def __init__(self, col, row, items):
        self.col    = col
        self.row    = row
        self.items  = items
        self.opened = False

    def draw(self, surface, offset_x, offset_y, time):
        ts = TILE_SIZE
        x  = offset_x + self.col * ts
        y  = offset_y + self.row * ts
        cx = x + ts//2
        cy = y + ts//2
        cw, ch = int(ts*0.65), int(ts*0.45)
        bx = cx - cw//2
        by = cy - ch//2 + 4

        body_col = (90,62,28)  if self.opened else (110,78,36)
        lid_col  = (110,78,36) if self.opened else (130,95,46)

        pygame.draw.rect(surface, body_col, (bx, by+ch//2, cw, ch//2))
        pygame.draw.rect(surface, (70,48,20), (bx, by+ch//2, cw, ch//2), 1)
        if self.opened:
            pygame.draw.rect(surface, lid_col, (bx, by-ch//3, cw, ch//2))
        else:
            pygame.draw.rect(surface, lid_col, (bx, by, cw, ch//2))
        pygame.draw.rect(surface, (80,56,22),
                         (bx, by if not self.opened else by-ch//3, cw, ch//2), 1)
        lc = (180,148,55) if not self.opened else (80,65,30)
        pygame.draw.rect(surface, lc, (cx-5, by+ch//2-5, 10, 9))
        pygame.draw.rect(surface, (140,110,40), (cx-5, by+ch//2-5, 10, 9), 1)
        sc = (160,128,50)
        for sx,sy in [(bx+4,by+ch//2+4),(bx+cw-4,by+ch//2+4),
                      (bx+4,by+ch-4),   (bx+cw-4,by+ch-4)]:
            pygame.draw.circle(surface, sc, (sx,sy), 2)
        if not self.opened:
            shimmer = 0.5 + 0.5*math.sin(time*2.5)
            glow = pygame.Surface((ts,ts), pygame.SRCALPHA)
            pygame.draw.circle(glow,(220,185,60,int(20*shimmer)),(ts//2,ts//2),ts//2)
            surface.blit(glow,(x,y),special_flags=pygame.BLEND_RGBA_ADD)

    def is_adjacent(self, player_col, player_row):
        dc = abs(self.col - player_col)
        dr = abs(self.row - player_row)
        return (dc==1 and dr==0) or (dc==0 and dr==1)


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
        for radius, alpha in [(glow_r,int(18*bri)),
                               (glow_r*2//3,int(35*bri)),
                               (glow_r//3,int(55*bri))]:
            pygame.draw.circle(glow,(200,130,40,alpha),(glow_r,glow_r),radius)
        surface.blit(glow,(cx-glow_r,cy-glow_r),
                     special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.rect(surface,(80,65,45),(cx-4,cy,8,10))
        pygame.draw.rect(surface,(80,65,45),(cx-6,cy+8,12,4))
        fx,fy = cx,cy-2
        ox2 = int(math.sin(t*self.freq1*1.5+self.phase)*2)
        pygame.draw.polygon(surface,(int(200*bri),int(100*bri),10),[
            (fx-6+ox2,fy),(fx-9+ox2,fy-8),(fx+ox2,fy-18),
            (fx+9+ox2,fy-8),(fx+6+ox2,fy)])
        pygame.draw.polygon(surface,(int(230*bri),int(155*bri),20),[
            (fx-3+ox2,fy-2),(fx-5+ox2,fy-9),(fx+ox2,fy-16),
            (fx+5+ox2,fy-9),(fx+3+ox2,fy-2)])
        pygame.draw.polygon(surface,(255,230,160),[
            (fx-1+ox2,fy-4),(fx+ox2,fy-13),(fx+1+ox2,fy-4)])


# ---------------------------------------------------------------------------
# Locked Door
# ---------------------------------------------------------------------------

class LockedDoor:
    def __init__(self, col, row, orientation, key_id):
        self.col         = col
        self.row         = row
        self.orientation = orientation  # 'h' or 'v'
        self.key_id      = key_id
        self.locked      = True

    def blocks(self, player_col, player_row):
        """True if the player is trying to walk through this door."""
        if not self.locked:
            return False
        if self.orientation == 'h':
            return player_row in (self.row, self.row+1) and player_col == self.col
        else:
            return player_col in (self.col, self.col+1) and player_row == self.row

    def is_adjacent(self, player_col, player_row):
        """True if player is standing right next to the door."""
        if self.orientation == 'h':
            return (abs(player_col - self.col) <= 1 and
                    abs(player_row - self.row) <= 1)
        else:
            return (abs(player_col - self.col) <= 1 and
                    abs(player_row - self.row) <= 1)

    def draw(self, surface, ox, oy, time):
        if not self.locked:
            return
        ts = TILE_SIZE
        # Draw 2 door tiles
        tiles = [(self.col, self.row), (self.col + (1 if self.orientation=='h' else 0),
                                         self.row + (1 if self.orientation=='v' else 0))]
        pulse = 0.7 + 0.3 * math.sin(time * 2.0)
        for col, row in tiles:
            x = ox + col * ts
            y = oy + row * ts
            # Dark door fill
            pygame.draw.rect(surface, (55, 35, 15), (x, y, ts, ts))
            # Door planks
            for i in range(3):
                ply = y + 4 + i * (ts//3)
                pygame.draw.rect(surface, (75, 50, 22),
                                 (x+3, ply, ts-6, ts//3-3))
                pygame.draw.rect(surface, (45, 28, 10),
                                 (x+3, ply, ts-6, ts//3-3), 1)
            # Iron bands
            band = (90, 70, 30)
            pygame.draw.rect(surface, band, (x+2, y+ts//3-2, ts-4, 4))
            pygame.draw.rect(surface, band, (x+2, y+ts*2//3-2, ts-4, 4))
            # Lock keyhole
            kx, ky = x+ts//2, y+ts//2
            pygame.draw.circle(surface, (180, 140, 50), (kx, ky), 5)
            pygame.draw.circle(surface, (30, 20, 8), (kx, ky), 3)
            pygame.draw.rect(surface, (30, 20, 8), (kx-2, ky, 4, 5))
            # Glow pulse
            glow = pygame.Surface((ts, ts), pygame.SRCALPHA)
            pygame.draw.circle(glow, (180, 130, 40, int(30*pulse)),
                               (ts//2, ts//2), ts//2)
            surface.blit(glow, (x, y), special_flags=pygame.BLEND_RGBA_ADD)


# ---------------------------------------------------------------------------
# Exit Tile
# ---------------------------------------------------------------------------

class ExitTile:
    def __init__(self, col, row):
        self.col    = col
        self.row    = row
        self.locked = True

    def is_adjacent(self, player_col, player_row):
        dc = abs(self.col - player_col)
        dr = abs(self.row - player_row)
        return (dc <= 1 and dr == 0) or (dc == 0 and dr <= 1)

    def draw(self, surface, ox, oy, time):
        ts  = TILE_SIZE
        x   = ox + self.col * ts
        y   = oy + self.row * ts
        cx  = x + ts//2
        cy  = y + ts//2

        # Floor base already drawn — draw portal/gate on top
        pulse = 0.6 + 0.4 * math.sin(time * 2.5)

        if self.locked:
            # Locked — dark iron gate
            gate_col = (70, 55, 30)
            # Gate bars
            for bx in range(x+6, x+ts-4, 8):
                pygame.draw.line(surface, gate_col,
                                 (bx, y+4), (bx, y+ts-4), 3)
            pygame.draw.rect(surface, gate_col, (x+4, y+4, ts-8, 6))
            pygame.draw.rect(surface, gate_col, (x+4, y+ts-10, ts-8, 6))
            # Lock
            pygame.draw.rect(surface, (160,130,50), (cx-6,cy-5,12,10))
            pygame.draw.rect(surface, (120,95,35),  (cx-6,cy-5,12,10), 1)
            # Hint glow
            glow = pygame.Surface((ts,ts), pygame.SRCALPHA)
            pygame.draw.rect(glow,(180,140,40,int(20*pulse)),(0,0,ts,ts))
            surface.blit(glow,(x,y),special_flags=pygame.BLEND_RGBA_ADD)
        else:
            # Unlocked — glowing portal
            glow = pygame.Surface((ts,ts), pygame.SRCALPHA)
            pygame.draw.ellipse(glow,(100,180,255,int(60*pulse)),(4,4,ts-8,ts-8))
            surface.blit(glow,(x,y),special_flags=pygame.BLEND_RGBA_ADD)
            pygame.draw.ellipse(surface,(80,160,220),(x+6,y+6,ts-12,ts-12),2)
            pygame.draw.ellipse(surface,(160,220,255),(x+10,y+10,ts-20,ts-20),1)
            # Arrow up
            arr_col = (200,235,255)
            pygame.draw.line(surface,arr_col,(cx,cy+8),(cx,cy-8),2)
            pygame.draw.polygon(surface,arr_col,[
                (cx,cy-12),(cx-5,cy-6),(cx+5,cy-6)])


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

class Camera:
    """Keeps the player centred on screen by offsetting the world."""
    def __init__(self, screen_w, screen_h, map_cols, map_rows, tile_size):
        self.sw   = screen_w
        self.sh   = screen_h
        self.mw   = map_cols * tile_size
        self.mh   = map_rows * tile_size
        self.ts   = tile_size
        self.ox   = 0
        self.oy   = 0

    def update(self, player_px, player_py):
        ts = self.ts
        # Centre on player
        target_ox = self.sw//2 - int(player_px) - ts//2
        target_oy = self.sh//2 - int(player_py) - ts//2
        # Clamp so we don't show void beyond map edges
        self.ox = max(self.sw - self.mw, min(0, target_ox))
        self.oy = max(self.sh - self.mh, min(0, target_oy))


# ---------------------------------------------------------------------------
# E-prompt
# ---------------------------------------------------------------------------

def _draw_e_prompt(surface, font, cx, cy):
    text = font.render("[ E ]  Open", True, (210,185,120))
    bg   = pygame.Surface((text.get_width()+16, text.get_height()+8), pygame.SRCALPHA)
    bg.fill((10,8,5,180))
    bx = cx - bg.get_width()//2
    by = cy - bg.get_height() - 4
    surface.blit(bg,(bx,by))
    pygame.draw.rect(surface,(90,70,42),(bx,by,bg.get_width(),bg.get_height()),1)
    surface.blit(text,(bx+8,by+4))


def _draw_exit_prompt(surface, font, cx, cy, locked):
    text = font.render("[ F ]  " + ("Use Exit Key" if locked else "Leave Dungeon"),
                       True, (220, 200, 100))
    bg   = pygame.Surface((text.get_width()+16, text.get_height()+8), pygame.SRCALPHA)
    bg.fill((10,8,5,180))
    bx = cx - bg.get_width()//2
    by = cy - bg.get_height() - 4
    surface.blit(bg,(bx,by))
    pygame.draw.rect(surface,(160,130,50),(bx,by,bg.get_width(),bg.get_height()),1)
    surface.blit(text,(bx+8,by+4))


def _draw_key_prompt(surface, font, cx, cy):
    text = font.render("[ E ]  Use Key", True, (210, 185, 120))
    bg   = pygame.Surface((text.get_width()+16, text.get_height()+8), pygame.SRCALPHA)
    bg.fill((10, 8, 5, 180))
    bx = cx - bg.get_width()//2
    by = cy - bg.get_height() - 4
    surface.blit(bg,(bx,by))
    pygame.draw.rect(surface,(140,110,42),(bx,by,bg.get_width(),bg.get_height()),1)
    surface.blit(text,(bx+8,by+4))


# ---------------------------------------------------------------------------
# GameScene
# ---------------------------------------------------------------------------

class GameScene:
    def __init__(self, screen, inventory):
        self.inventory = inventory
        self.screen    = screen
        self.W, self.H = screen.get_size()
        self.clock     = pygame.time.Clock()
        self.time      = 0.0

        self.tile_surf = build_tile_surface()
        self.torches   = [Torch(c,r) for c,r in TORCH_POSITIONS]
        self.vignette  = self._build_vignette()

        # Spawn player in room A centre
        self.player = Player(9, 7, TILE_SIZE)

        self.goblins = [
            Goblin(p[0][0], p[0][1], TILE_SIZE, p)
            for p in GOBLIN_PATROLS
        ]

        from src.scenes.chest_scene import CandleItem, PotionItem, ShieldItem, SunSwordItem, KeyItem, GoldItem, ExitKeyItem
        import random as _rng

        def _rand_loot(n=2):
            """Pick n random filler items."""
            pool = [PotionItem, CandleItem, lambda: GoldItem(_rng.choice([5,10,15]))]
            return [_rng.choice(pool)() for _ in range(n)]

        chest_items = [
            # Chest 1 — Room A: exit key + potion (fixed)
            [ExitKeyItem(), PotionItem(), KeyItem("key_ab")],
            # Chest 2 — Room B: random 3
            _rand_loot(3),
            # Chest 3 — Room C: key + 2 randoms
            [KeyItem("key_ef")] + _rand_loot(2),
            # Chest 4 — Room D: key + 2 randoms
            [KeyItem("key_ad")] + _rand_loot(2),
            # Chest 5 — Room E: random 3
            _rand_loot(3),
            # Chest 6 — Room F: random 3
            _rand_loot(3),
            # Chest 7 — Room G: key + 2 randoms
            [KeyItem("key_dg")] + _rand_loot(2),
            # Chest 8 — Room H: random 3
            _rand_loot(3),
        ]
        self.chests = [
            Chest(col, row, items)
            for (col,row), items in zip(CHEST_POSITIONS, chest_items)
        ]

        self.font_small = pygame.font.SysFont("courier new", 15)

        self.COMBAT_COOLDOWN = 1.5
        self.combat_cooldown = self.COMBAT_COOLDOWN

        self._nearby_chest = None
        self._nearby_door  = None
        self._nearby_exit  = None

        # Exit tile
        self.exit_tile = ExitTile(EXIT_TILE[0], EXIT_TILE[1])

        # Locked doors
        self.locked_doors = [
            LockedDoor(col, row, ori, kid)
            for (col, row, ori), kid in zip(LOCKED_DOORS, DOOR_KEY_IDS)
        ]

        # Goblins defeated — track which to remove
        self._defeated_goblin_idx = None

        # Fog of war
        self.visited      = set()
        self.VISION_RADIUS = 4

        # Camera
        self.camera = Camera(self.W, self.H, COLS, ROWS, TILE_SIZE)
        self.camera.update(self.player.px, self.player.py)

    # ------------------------------------------------------------------ #

    def _build_vignette(self):
        surf   = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        cx, cy = self.W//2, self.H//2
        max_r  = int(math.hypot(cx, cy))
        for i in range(80, 0, -1):
            r     = int(max_r * i/80)
            alpha = int(200 * (i/80)**2.2)
            pygame.draw.circle(surf,(0,0,0,alpha),(cx,cy),r)
        return surf

    def _update_visited(self):
        pr   = self.VISION_RADIUS
        pcol = self.player.tile_col
        prow = self.player.tile_row
        for dc in range(-pr, pr+1):
            for dr in range(-pr, pr+1):
                if dc*dc + dr*dr <= pr*pr:
                    col = pcol+dc
                    row = prow+dr
                    if 0 <= row < ROWS and 0 <= col < COLS:
                        self.visited.add((col, row))

    def _draw_ambient_darkness(self):
        dark = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        dark.fill((0,0,0,155))
        ts = TILE_SIZE
        ox = self.camera.ox
        oy = self.camera.oy
        for torch in self.torches:
            bri = torch.flame_brightness(self.time)
            cx  = ox + torch.col*ts + ts//2
            cy  = oy + torch.row*ts + ts//2
            pygame.draw.circle(dark,(0,0,0,0),(cx,cy),int(ts*5*bri))
        px = ox + int(self.player.px) + ts//2
        py = oy + int(self.player.py) + ts//2
        pygame.draw.circle(dark,(0,0,0,0),(px,py),int(ts*2.5))
        self.screen.blit(dark,(0,0))

    def _handle_input(self):
        keys = pygame.key.get_pressed()
        for key, (dc, dr) in MOVE_KEYS.items():
            if keys[key]:
                self.player.try_move(dc, dr, ROOM_MAP)
                break

    def _check_combat(self):
        ts  = TILE_SIZE
        pcx = self.player.px + ts//2
        pcy = self.player.py + ts//2
        for goblin in self.goblins:
            gcx = goblin.px + ts//2
            gcy = goblin.py + ts//2
            if math.hypot(pcx-gcx, pcy-gcy) < ts*0.75:
                return True
        return False

    def _check_nearby_exit(self):
        if self.exit_tile.is_adjacent(self.player.tile_col, self.player.tile_row):
            return self.exit_tile
        return None

    def _check_nearby_door(self):
        """Returns adjacent locked door if player is next to one."""
        for door in self.locked_doors:
            if door.locked and door.is_adjacent(
                    self.player.tile_col, self.player.tile_row):
                return door
        return None

    def _check_nearby_chest(self):
        for chest in self.chests:
            if not chest.opened and chest.is_adjacent(
                    self.player.tile_col, self.player.tile_row):
                return chest
        return None

    # ------------------------------------------------------------------ #

    def run(self):
        while True:
            dt        = self.clock.tick(60)/1000.0
            self.time += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
                    if event.key == pygame.K_i:
                        return "inventory"
                    if event.key == pygame.K_m:
                        return "map"
                    if event.key == pygame.K_f:
                        if self._nearby_exit:
                            if self._nearby_exit.locked:
                                return "use_exit_key"
                            else:
                                return "world_map"
                    if event.key == pygame.K_e:
                        if self._nearby_chest:
                            self._nearby_chest.opened = True
                            self._chest_to_open = self._nearby_chest
                            return "chest"
                        if self._nearby_door and self._nearby_door.locked:
                            return "use_key"

            self._handle_input()
            self.player.update(dt)
            self._update_visited()

            for door in self.locked_doors:
                if not door.locked:
                    continue
                dx  = abs(self.player.tile_col - door.col)
                dy  = abs(self.player.tile_row - door.row)
                dx2 = abs(self.player.tile_col - (door.col + (1 if door.orientation=='h' else 0)))
                dy2 = abs(self.player.tile_row - (door.row + (1 if door.orientation=='v' else 0)))
                if (dx==0 and dy==0) or (dx2==0 and dy2==0):
                    self.player.tile_col = self.player._prev_col
                    self.player.tile_row = self.player._prev_row
                    self.player.target_px = float(self.player._prev_col * TILE_SIZE)
                    self.player.target_py = float(self.player._prev_row * TILE_SIZE)
                    self.player.px = self.player.target_px
                    self.player.py = self.player.target_py
                    self.player.moving = False

            for goblin in self.goblins:
                goblin.update(dt, self.player.tile_col, self.player.tile_row)
            self.combat_cooldown = max(0.0, self.combat_cooldown - dt)
            self.camera.update(self.player.px, self.player.py)

            if not self.player.moving:
                self._nearby_chest = self._check_nearby_chest()
                self._nearby_door  = self._check_nearby_door()
                self._nearby_exit  = self._check_nearby_exit()
            else:
                self._nearby_chest = None
                self._nearby_door  = None
                self._nearby_exit  = None

            if (not self.player.moving
                    and self.combat_cooldown <= 0.0
                    and self._check_combat()):
                return "combat"

            ox = self.camera.ox
            oy = self.camera.oy

            self.screen.fill((4,3,2))
            self.screen.blit(self.tile_surf,(ox,oy))
            self._draw_ambient_darkness()

            self.exit_tile.draw(self.screen,ox,oy,self.time)
            for door in self.locked_doors:
                door.draw(self.screen,ox,oy,self.time)
            for torch in self.torches:
                torch.draw(self.screen,self.time,ox,oy)
            for chest in self.chests:
                chest.draw(self.screen,ox,oy,self.time)
            for goblin in self.goblins:
                goblin.draw(self.screen,ox,oy)
            self.player.draw(self.screen,ox,oy)

            if self._nearby_exit:
                ts  = TILE_SIZE
                ecx = ox + self.exit_tile.col*ts + ts//2
                ecy = oy + self.exit_tile.row*ts
                _draw_exit_prompt(self.screen, self.font_small,
                                  ecx, ecy, self._nearby_exit.locked)

            if self._nearby_door and self._nearby_door.locked:
                ts  = TILE_SIZE
                dcx = ox + self._nearby_door.col*ts + ts//2
                dcy = oy + self._nearby_door.row*ts
                _draw_key_prompt(self.screen, self.font_small, dcx, dcy)

            if self._nearby_chest:
                ts  = TILE_SIZE
                ccx = ox + self._nearby_chest.col*ts + ts//2
                ccy = oy + self._nearby_chest.row*ts
                _draw_e_prompt(self.screen, self.font_small, ccx, ccy)

            self.screen.blit(self.vignette,(0,0))
            pygame.display.flip()