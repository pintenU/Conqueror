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

GOBLIN_PATROLS = [
    [(3, 5),  (20, 5)],
    [(3, 11), (20, 11)],
    [(12, 3), (12, 13)],
]

# Chest positions as (col, row)
CHEST_POSITIONS = [
    (7, 4),
    (18, 12),
]


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
        cx = x + ts // 2
        cy = y + ts // 2

        cw, ch = int(ts*0.65), int(ts*0.45)
        bx = cx - cw//2
        by = cy - ch//2 + 4

        if self.opened:
            # Opened chest — lighter, lid tilted
            body_col = (90, 62, 28)
            lid_col  = (110, 78, 36)
        else:
            body_col = (110, 78, 36)
            lid_col  = (130, 95, 46)

        # Body
        pygame.draw.rect(surface, body_col, (bx, by + ch//2, cw, ch//2))
        pygame.draw.rect(surface, (70, 48, 20), (bx, by + ch//2, cw, ch//2), 1)

        # Lid
        if self.opened:
            pygame.draw.rect(surface, lid_col, (bx, by - ch//3, cw, ch//2))
        else:
            pygame.draw.rect(surface, lid_col, (bx, by, cw, ch//2))
        pygame.draw.rect(surface, (80, 56, 22),
                         (bx, by if not self.opened else by - ch//3, cw, ch//2), 1)

        # Lock
        lc = (180, 148, 55) if not self.opened else (80, 65, 30)
        pygame.draw.rect(surface, lc, (cx-5, by+ch//2-5, 10, 9))
        pygame.draw.rect(surface, (140,110,40), (cx-5, by+ch//2-5, 10, 9), 1)

        # Studs
        sc = (160, 128, 50)
        for sx, sy in [(bx+4, by+ch//2+4), (bx+cw-4, by+ch//2+4),
                       (bx+4, by+ch-4),    (bx+cw-4, by+ch-4)]:
            pygame.draw.circle(surface, sc, (sx, sy), 2)

        # Golden shimmer if closed (entice the player)
        if not self.opened:
            shimmer = 0.5 + 0.5 * math.sin(time * 2.5)
            glow = pygame.Surface((ts, ts), pygame.SRCALPHA)
            pygame.draw.circle(glow, (220, 185, 60, int(20 * shimmer)),
                               (ts//2, ts//2), ts//2)
            surface.blit(glow, (x, y), special_flags=pygame.BLEND_RGBA_ADD)

    def is_adjacent(self, player_col, player_row):
        """Returns True if player is one tile away (cardinal directions)."""
        dc = abs(self.col - player_col)
        dr = abs(self.row - player_row)
        return (dc == 1 and dr == 0) or (dc == 0 and dr == 1)


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
# "Press E" prompt
# ---------------------------------------------------------------------------

def _draw_e_prompt(surface, font, cx, cy):
    text = font.render("[ E ]  Open", True, (210, 185, 120))
    bg   = pygame.Surface((text.get_width()+16, text.get_height()+8),
                          pygame.SRCALPHA)
    bg.fill((10, 8, 5, 180))
    bx = cx - bg.get_width()//2
    by = cy - bg.get_height() - 4
    surface.blit(bg,   (bx, by))
    pygame.draw.rect(surface, (90, 70, 42), (bx, by, bg.get_width(), bg.get_height()), 1)
    surface.blit(text, (bx+8, by+4))


# ---------------------------------------------------------------------------
# GameScene
# ---------------------------------------------------------------------------

class GameScene:
    def __init__(self, screen, inventory):
        self.inventory = inventory
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
        self.player    = Player(12, 8, TILE_SIZE)
        self.goblins   = [
            Goblin(p[0][0], p[0][1], TILE_SIZE, p)
            for p in GOBLIN_PATROLS
        ]

        # Import here to avoid circular issues
        from src.scenes.chest_scene import CandleItem, PotionItem, ShieldItem
        self.chests = [
            Chest(CHEST_POSITIONS[0][0], CHEST_POSITIONS[0][1],
                  [PotionItem(), CandleItem()]),
            Chest(CHEST_POSITIONS[1][0], CHEST_POSITIONS[1][1],
                  [ShieldItem(), CandleItem()]),
        ]

        self.font_small = pygame.font.SysFont("courier new", 15)

        # Combat re-trigger cooldown — starts at full so first frame never triggers
        self.COMBAT_COOLDOWN = 1.5
        self.combat_cooldown = self.COMBAT_COOLDOWN

        # Which chest the player can open right now (or None)
        self._nearby_chest = None

    def _build_vignette(self):
        surf   = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        cx, cy = self.W//2, self.H//2
        max_r  = int(math.hypot(cx, cy))
        for i in range(80, 0, -1):
            r     = int(max_r * i/80)
            alpha = int(200 * (i/80)**2.2)
            pygame.draw.circle(surf,(0,0,0,alpha),(cx,cy),r)
        return surf

    def _draw_ambient_darkness(self):
        dark = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        dark.fill((0,0,0,155))
        ts = TILE_SIZE
        for torch in self.torches:
            bri = torch.flame_brightness(self.time)
            cx  = self.offset_x + torch.col*ts + ts//2
            cy  = self.offset_y + torch.row*ts + ts//2
            pygame.draw.circle(dark,(0,0,0,0),(cx,cy),int(ts*5*bri))
        px = self.offset_x + int(self.player.px) + ts//2
        py = self.offset_y + int(self.player.py) + ts//2
        pygame.draw.circle(dark,(0,0,0,0),(px,py),int(ts*2.5))
        self.screen.blit(dark,(0,0))

    def _handle_input(self):
        keys = pygame.key.get_pressed()
        for key, (dc, dr) in MOVE_KEYS.items():
            if keys[key]:
                self.player.try_move(dc, dr, ROOM_MAP)
                break

    def _check_combat(self):
        import math
        ts = TILE_SIZE
        # Player centre in pixel space
        pcx = self.player.px + ts // 2
        pcy = self.player.py + ts // 2
        for goblin in self.goblins:
            gcx = goblin.px + ts // 2
            gcy = goblin.py + ts // 2
            dist = math.hypot(pcx - gcx, pcy - gcy)
            if dist < ts * 0.75:
                return True
        return False

    def _check_nearby_chest(self):
        """Returns the first adjacent unopened chest, or None."""
        for chest in self.chests:
            if not chest.opened and chest.is_adjacent(
                    self.player.tile_col, self.player.tile_row):
                return chest
        return None

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
                    if event.key == pygame.K_i:
                        return "inventory"
                    if event.key == pygame.K_e:
                        if self._nearby_chest:
                            self._nearby_chest.opened = True
                            # Pass chest items to chest scene via return value
                            self._chest_to_open = self._nearby_chest
                            return "chest"

            self._handle_input()
            self.player.update(dt)
            for goblin in self.goblins:
                goblin.update(dt, self.player.tile_col, self.player.tile_row)
            self.combat_cooldown = max(0.0, self.combat_cooldown - dt)

            # Update nearby chest prompt
            if not self.player.moving:
                self._nearby_chest = self._check_nearby_chest()
            else:
                self._nearby_chest = None

            # Trigger combat (guarded by cooldown)
            if (not self.player.moving
                    and self.combat_cooldown <= 0.0
                    and self._check_combat()):
                return "combat"

            # --- Draw ---
            self.screen.fill((4,3,2))
            self.screen.blit(self.tile_surf,(self.offset_x,self.offset_y))
            self._draw_ambient_darkness()

            for torch in self.torches:
                torch.draw(self.screen,self.time,self.offset_x,self.offset_y)

            for chest in self.chests:
                chest.draw(self.screen,self.offset_x,self.offset_y,self.time)

            for goblin in self.goblins:
                goblin.draw(self.screen,self.offset_x,self.offset_y)

            self.player.draw(self.screen,self.offset_x,self.offset_y)

            # "Press E" prompt above nearby chest
            if self._nearby_chest:
                ts = TILE_SIZE
                cx = (self.offset_x + self._nearby_chest.col*ts + ts//2)
                cy = (self.offset_y + self._nearby_chest.row*ts)
                _draw_e_prompt(self.screen, self.font_small, cx, cy)

            self.screen.blit(self.vignette,(0,0))
            pygame.display.flip()