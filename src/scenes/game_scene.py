import pygame
import math
import random

from src.entities.player import Player
from src.entities.enemy import Enemy
from src.entities.entity_factory import spawn_patrol, roll_loot as factory_roll_loot

TILE_SIZE = 48
FLOOR = 0
WALL  = 1
EMPTY = 2

# ---------------------------------------------------------------------------
# Map builders
# ---------------------------------------------------------------------------

def _room(g,col,row,w,h,R,C):
    for r in range(row,row+h):
        for c in range(col,col+w):
            if 0<=r<R and 0<=c<C:
                g[r][c]=WALL if(r==row or r==row+h-1 or c==col or c==col+w-1) else FLOOR

def _ch(g,col,row,l,t,R,C):
    for r in range(row,row+t):
        for c in range(col,col+l):
            if 0<=r<R and 0<=c<C: g[r][c]=FLOOR

def _cv(g,col,row,l,t,R,C):
    for r in range(row,row+l):
        for c in range(col,col+t):
            if 0<=r<R and 0<=c<C: g[r][c]=FLOOR

def _op(g,pts,R,C):
    for r,c in pts:
        if 0<=r<R and 0<=c<C: g[r][c]=FLOOR

# ---- Floor 1 (60x50) ----
def build_floor1():
    R,C=50,60
    g=[[EMPTY]*C for _ in range(R)]
    def rm(col,row,w,h):  _room(g,col,row,w,h,R,C)
    def ch(col,row,l,t=2):_ch(g,col,row,l,t,R,C)
    def cv(col,row,l,t=2):_cv(g,col,row,l,t,R,C)
    def op(pts):           _op(g,pts,R,C)

    rm( 1,18,10, 9)  # Spawn
    rm(14,18,13, 9)  # Central (3 goblins)
    rm(30,18,13, 9)  # Right (2 goblins)
    rm(14, 4,13,10)  # Special N
    rm( 1,31,10, 9)  # Chieftain
    rm(14,31,13, 9)  # Chest room

    ch(11,20,3); ch(27,20,3); ch(43,20,5)
    cv(19,14,4); cv(5,27,4); cv(19,27,4)

    # Open room walls at corridor junctions (row, col)
    op([(20,10),(21,10),(20,14),(21,14),   # spawn↔central
        (20,26),(21,26),(20,30),(21,30),   # central↔right
        (20,42),(21,42),                   # right→circle
        (18,19),(18,20),(13,19),(13,20),   # central↔special N
        (26,5),(26,6),(31,5),(31,6),       # spawn↔chieftain
        (26,19),(26,20),(31,19),(31,20)])  # central↔chest room

    # Floor circle
    for r in range(19,24):
        for c in range(48,54):
            if 0<=c<C: g[r][c]=FLOOR

    return g

# ---- Floor 2 (75x55) ----
def build_floor2():
    R,C=55,75
    g=[[EMPTY]*C for _ in range(R)]
    def rm(col,row,w,h):  _room(g,col,row,w,h,R,C)
    def ch(col,row,l,t=2):_ch(g,col,row,l,t,R,C)
    def cv(col,row,l,t=2):_cv(g,col,row,l,t,R,C)
    def op(pts):           _op(g,pts,R,C)

    rm(15, 2,45, 9)   # Special top (boss key)
    rm(15,14,13,10)   # Room A (3 goblins)
    rm(31,14,10, 9)   # Room B (1 goblin)
    rm(44,14,10, 9)   # Room C (1 goblin)
    rm(57, 4,16,32)   # Big room (6 goblins + chieftain) — dead end
    rm(31,26,10, 9)   # Room D (1 goblin)
    rm(20,38,13, 9)   # Room E (1 goblin + chest)

    # Spawn circle
    for r in range(16,22):
        for c in range(3,10): g[r][c]=FLOOR

    # Floor circle (bottom left)
    for r in range(40,46):
        for c in range(3,10): g[r][c]=FLOOR

    ch(10,18,5,2)   # spawn→A: cols 10-14
    ch(28,18,4,2)   # A→B:     cols 28-31
    ch(41,17,4,2)   # B→C:     cols 41-44
    ch(54,17,4,2)   # C→big:   cols 54-57
    cv(35,23,3,2)   # B↓D:     rows 23-25
    cv(35,35,3,2)   # D↓:      rows 35-37
    ch(25,35,10,2)  # D↓E horizontal connector
    cv(35,11,3,2)   # B↑special: rows 11-13
    ch(10,41,10,2)  # E→circle: cols 10-19

    # Open walls (row, col)
    op([(18,15),(19,15),                   # spawn→A (Room A left wall)
        (18,27),(19,27),(18,30),(19,30),   # A→B
        (17,40),(18,40),(17,43),(18,43),   # B→C
        (17,53),(18,53),(17,56),(18,56),   # C→big
        (14,35),(14,36),(11,35),(11,36),   # B↑special
        (22,35),(22,36),(26,35),(26,36),   # B↓D
        (34,35),(34,36),                   # D bottom
        (35,25),(36,25),(37,25),(38,25),(39,25),(38,26),(39,26),   # D→E connector
        (41,20),(42,20),(41,19),(42,19)])  # E→floor circle

    return g

# ---- Floor 3 (70x50) ----
def build_floor3():
    R,C=50,70
    g=[[EMPTY]*C for _ in range(R)]
    def rm(col,row,w,h):  _room(g,col,row,w,h,R,C)
    def ch(col,row,l,t=2):_ch(g,col,row,l,t,R,C)
    def cv(col,row,l,t=2):_cv(g,col,row,l,t,R,C)
    def op(pts):           _op(g,pts,R,C)

    rm(14, 3,13, 9)   # Special N
    rm(14,15,13,10)   # Hub (1 goblin)
    rm(30,12,22,18)   # Big room (7 goblins)
    rm(55,15,10,12)   # Small room (chieftain)

    # Spawn circle
    for r in range(17,23):
        for c in range(3,10):
            g[r][c]=FLOOR
    # Floor circle south — extended left to col 13 so return spawn (15,36) lands inside
    for r in range(34,40):
        for c in range(13,22):
            g[r][c]=FLOOR

    ch(10,19,5); ch(27,19,3); ch(52,19,3)  # spawn→hub: cols 10-14 (was 11-13, too short)
    cv(19,12,3); cv(19,25,9)

    # Open walls (row, col)
    op([(19,9),(20,9),(19,14),(20,14),     # spawn→hub (hub left wall col 14)
        (12,19),(13,19),(12,20),(13,20),   # hub↑special
        (14,19),(15,19),(14,20),(15,20),
        (19,26),(20,26),(19,30),(20,30),   # hub→big
        (19,51),(20,51),(19,55),(20,55),   # big→small
        (24,19),(24,20),                   # hub bottom wall → floor circle corridor
        (33,19),(34,19),(33,20),(34,20)])  # hub↓floor circle

    return g

# ---- Floor 4 (80x60) ----
def build_floor4():
    R,C=60,80
    g=[[EMPTY]*C for _ in range(R)]
    def rm(col,row,w,h):  _room(g,col,row,w,h,R,C)
    def ch(col,row,l,t=2):_ch(g,col,row,l,t,R,C)
    def cv(col,row,l,t=2):_cv(g,col,row,l,t,R,C)
    def op(pts):           _op(g,pts,R,C)

    rm(14,10,13,10)   # Room 1 (2 goblins)
    rm(30,10,12,10)   # Room 2 (1 goblin)
    rm(45, 5,30,16)   # Special (boss key)
    rm(20,28,36,24)   # Boss arena

    # Spawn circle
    for r in range(12,18):
        for c in range(3,10):
            g[r][c]=FLOOR

    ch(10,14,5); ch(27,14,3); ch(42,11,3)  # spawn→room1: cols 10-14 (was 11-13, too short)
    cv(35,20,8)

    # Open walls (row, col)
    op([(14,9),(15,9),(14,14),(15,14),     # spawn→room1 (room1 left wall col 14)
        (14,26),(15,26),(14,30),(15,30),   # room1→room2
        (11,44),(12,44),(11,45),(12,45),   # room2→special
        (19,35),(19,36),                   # room2 bottom wall → arena corridor
        (20,35),(21,35),(27,35),(28,35),(28,36)])  # room2↓arena (arena top wall)

    # Fill arena interior
    for r in range(29,51):
        for c in range(21,55):
            if 0<=r<R and 0<=c<C and g[r][c]==EMPTY:
                g[r][c]=FLOOR

    return g

FLOOR_BUILDERS = {1:build_floor1, 2:build_floor2, 3:build_floor3, 4:build_floor4}
FLOOR_SIZES    = {1:(60,50), 2:(75,55), 3:(70,50), 4:(80,60)}

# ---------------------------------------------------------------------------
# Per-floor data: spawns, rooms, enemies, chests, torches, doors
# ---------------------------------------------------------------------------

FLOOR_DATA = {
    # ------- FLOOR 1 -------
    1: {
        "player_spawn": (5, 22),
        "floor_circle": (50, 21),   # tile player steps on to go to next floor
        "floor_circle_key": "floor_key",

        # Locked doors: (col, row, orientation, key_id)
        # Format: (col, row, orientation, key_id)
        # 'h' = door spans cols (col, col+1) at given row — blocks vertical corridor
        # 'v' = door spans rows (row, row+1) at given col — blocks horizontal corridor
        "locked_doors": [
            (42,20,'v',"key_to_circle"),    # right room → floor circle (blocks rows 20-21)
            (19,26,'h',"key_to_chest"),     # central bottom → chest room (blocks cols 19-20)
            (5, 26,'h',"key_to_chieftain"), # spawn bottom → chieftain (blocks cols 5-6)
        ],

        # Rooms: list of floor tiles the enemy can roam in
        "rooms": {
            "spawn":      [(c,r) for r in range(19,26) for c in range(2, 10)],
            "central":    [(c,r) for r in range(19,26) for c in range(15,26)],
            "right":      [(c,r) for r in range(19,26) for c in range(31,42)],
            "special_n":  [(c,r) for r in range( 5,13) for c in range(15,26)],
            "chieftain":  [(c,r) for r in range(32,39) for c in range(2, 10)],
            "chest_room": [(c,r) for r in range(32,39) for c in range(15,26)],
        },

        # Enemies: (type, room_key, count, key_drop)
        # key_drop = key_id that one random enemy in this group drops
        "enemies": [
            ("goblin",           "central",    3, "key_to_chest"),    # one drops key to central→chest
            ("goblin",           "right",      2, None),              # no key
            ("goblin",           "chest_room", 1, "key_to_chieftain"),# drops key to spawn→chieftain
            ("goblin_chieftain", "chieftain",  1, "floor_key"),       # drops floor key
            # chieftain also drops key_to_circle — handled via extra_drops below
        ],
        "extra_drops": {
            "chieftain": ["key_to_circle"],  # chieftain drops this in addition to floor_key
        },

        # Chests: (col, row, is_gold, items_fn)
        "chests": [
            {"col":23,"row":22,"gold":False,"items":["potion","potion","gold"]},
            {"col":23,"row":35,"gold":False,"items":["potion","gold"]},
            {"col":23,"row": 8,"gold":True, "items":["gold","gold","potion"]},  # special N
        ],

        # Torches
        "torches": [
            (3,19),(8,19),(3,25),(8,25),
            (16,19),(24,19),(16,25),(24,25),
            (32,19),(40,19),(32,25),(40,25),
            (16,5),(24,5),(16,12),(24,12),
            (3,32),(8,32),(3,38),(8,38),
            (16,32),(24,32),(16,38),(24,38),
        ],

        # Ground items (col, row, item_type)
        "ground_items": [
            (5, 22, "debug_sword"),
        ],

        # Boss key locked doors (col, row, orientation)
        "boss_key_doors": [
            (19, 14, 'v'),  # special N room door (top wall of central room)
        ],
    },

    # ------- FLOOR 2 -------
    2: {
        "player_spawn": (6, 19),
        "floor_circle": (6, 43),
        "floor_circle_key": "floor_key",
        "return_circle": (6, 20),   # return to Floor 1 — in spawn area

        # Doors:
        # spawn→A:   key from A goblins (3)
        # A→B:       key from B goblin (also drops B↓D key)
        # B→C:       key from C goblin
        # C→big:     key from big room goblins (one random of 6)
        # B↑special: boss key door
        # B↓D:       key from B goblin (same goblin, extra_drops)
        # D↓E:       key from D goblin
        # E→circle:  open corridor, floor key used at circle
        "locked_doors": [
            (10,18,'v',"key_spawn_to_a"),   # spawn→A corridor entrance
            (28,18,'v',"key_a_to_b"),       # A→B corridor entrance
            (41,17,'v',"key_b_to_c"),       # B→C corridor entrance
            (54,17,'v',"key_c_to_big"),     # C→big corridor entrance
            (35,23,'h',"key_b_to_d"),       # B↓D corridor entrance
            (25,35,'v',"key_d_to_e"),       # D→E horizontal connector
        ],

        "rooms": {
            "spawn_area": [(c,r) for r in range(17,21) for c in range(4, 9)],
            "room_a":     [(c,r) for r in range(15,23) for c in range(16,27)],
            "room_b":     [(c,r) for r in range(15,23) for c in range(32,40)],
            "room_c":     [(c,r) for r in range(15,22) for c in range(45,53)],
            "big_room":   [(c,r) for r in range( 6,34) for c in range(59,71)],
            "room_d":     [(c,r) for r in range(27,34) for c in range(32,40)],
            "room_e":     [(c,r) for r in range(39,46) for c in range(22,32)],
            "special":    [(c,r) for r in range( 3,10) for c in range(16,59)],
        },

        # Enemies: (type, room, count, primary_key_drop)
        "enemies": [
            # Goblin in spawn area holds key to enter Room A — fight it first
            ("goblin",           "spawn_area", 1, "key_spawn_to_a"),
            ("goblin",           "room_a",     3, "key_a_to_b"),   # A goblins drop A→B key
            ("goblin",           "room_b",     1, "key_b_to_c"),   # B goblin drops B→C key
            ("goblin",           "room_c",     1, "key_c_to_big"), # C goblin drops C→big key
            ("goblin",           "big_room",   6, None),
            ("goblin_chieftain", "big_room",   1, "floor_key"),    # chieftain drops floor key
            ("goblin",           "room_d",     1, "key_d_to_e"),   # D goblin drops D→E key
            ("goblin",           "room_e",     1, None),
        ],

        # B goblin also drops B↓D key (extra drop)
        "extra_drops": {
            "room_b": ["key_b_to_d"],
        },

        "chests": [
            # Big room chests
            {"col":63,"row":10,"gold":False,"items":["potion","gold"]},
            {"col":67,"row":20,"gold":False,"items":["potion","potion"]},
            {"col":63,"row":30,"gold":False,"items":["potion","gold"]},
            # Room E chest
            {"col":29,"row":43,"gold":False,"items":["potion","gold"]},
            # Special room (boss key) — many chests + gold chest
            {"col":22,"row": 6,"gold":False,"items":["potion","gold","potion"]},
            {"col":33,"row": 6,"gold":False,"items":["potion","gold"]},
            {"col":44,"row": 6,"gold":False,"items":["potion","potion","gold"]},
            {"col":52,"row": 6,"gold":True, "items":["gold","gold","gold","potion","potion"]},
        ],

        "torches": [
            # Room A
            (16,15),(25,15),(16,22),(25,22),
            # Room B
            (32,15),(39,15),(32,22),(39,22),
            # Room C
            (45,15),(52,15),(45,21),(52,21),
            # Big room
            (59,6),(71,6),(59,19),(71,19),(59,32),(71,32),
            # Room D
            (32,27),(39,27),(32,33),(39,33),
            # Room E
            (22,39),(31,39),(22,45),(31,45),
            # Special top
            (17,3),(35,3),(55,3),
        ],

        "ground_items": [],
        "boss_key_doors": [(35,11,'h')],   # B↑special top corridor
    },

    # ------- FLOOR 3 -------
    3: {
        "player_spawn": (6, 20),
        "floor_circle": (18, 36),
        "floor_circle_key": "floor_key",
        "return_circle": (6, 20),   # return to Floor 2 — in spawn area

        "locked_doors": [
            (27,19,'v',"key_hub_to_big"),    # blocks rows 19-20 at col 27 (2-wide corridor)
            (52,19,'v',"key_big_to_small"),  # blocks rows 19-20 at col 52
            (19,25,'h',"key_floor_circle"),  # blocks cols 19-20 at row 25
        ],

        "rooms": {
            "hub":      [(c,r) for r in range(16,24) for c in range(15,26)],
            "big_room": [(c,r) for r in range(13,29) for c in range(31,51)],
            "small":    [(c,r) for r in range(16,26) for c in range(56,64)],
            "special":  [(c,r) for r in range( 4,11) for c in range(15,26)],
        },

        "enemies": [
            ("goblin",           "hub",      1, "key_hub_to_big"),
            ("goblin",           "big_room", 7, "key_big_to_small"),
            ("goblin_chieftain", "small",    1, "floor_key"),    # also drops key_floor_circle
        ],

        # Chieftain drops floor_key + key_floor_circle (unlocks path to the circle)
        "extra_drops": {
            "small": ["key_floor_circle"],
        },

        "chests": [
            {"col":22,"row":19,"gold":False,"items":["potion","gold"]},
            {"col":48,"row":20,"gold":False,"items":["potion","potion","gold"]},
            {"col":22,"row": 7,"gold":True, "items":["gold","gold","potion","potion"]},
        ],

        "torches": [
            (16,16),(25,16),(16,23),(25,23),
            (32,13),(50,13),(32,28),(50,28),
            (57,16),(63,16),(57,25),(63,25),
            (16,4),(25,4),(16,10),(25,10),
        ],

        "ground_items": [],
        "boss_key_doors": [(19,12,'h')],   # blocks cols 19-20 at row 12 (full corridor width)
    },

    # ------- FLOOR 4 -------
    4: {
        "player_spawn": (6, 15),
        "floor_circle": None,
        "floor_circle_key": None,
        "return_circle": (6, 15),   # return to Floor 3 — in spawn area

        "locked_doors": [
            (11,14,'v',"key_spawn_to_r1"),  # blocks rows 14-15 at col 11 (spawn→room1)
            (27,14,'v',"key_r1_to_r2"),     # blocks rows 14-15 at col 27 (room1→room2)
            (42,11,'v',"key_special"),      # blocks rows 11-12 at col 42 (room2→special)
            (35,20,'h',"key_r2_to_arena"),  # blocks cols 35-36 at row 20 (room2↓arena)
        ],

        "rooms": {
            "spawn_area": [(c,r) for r in range(13,17) for c in range(4, 9)],
            "room1":   [(c,r) for r in range(11,19) for c in range(15,26)],
            "room2":   [(c,r) for r in range(11,19) for c in range(31,41)],
            "special": [(c,r) for r in range( 6,20) for c in range(46,74)],
            "arena":   [(c,r) for r in range(29,51) for c in range(21,55)],
        },

        "enemies": [
            ("goblin",           "spawn_area", 1, "key_spawn_to_r1"), # drops key to room1
            ("goblin",           "room1", 2, "key_r1_to_r2"),         # drops key to room2
            ("goblin",           "room2", 1, "key_r2_to_arena"),      # drops key to arena
            ("goblin",           "room2", 1, "key_special"),          # drops key to special room
            # Arena enemies — must all die before boss spawns
            ("goblin",           "arena", 3, None),
            ("goblin_chieftain", "arena", 1, None),
        ],

        "chests": [
            {"col":55,"row":10,"gold":False,"items":["potion","gold","potion"]},
            {"col":65,"row":10,"gold":False,"items":["potion","gold"]},
            {"col":70,"row":10,"gold":True, "items":["gold","gold","gold","potion","potion"]},
        ],

        "torches": [
            (16,11),(25,11),(16,18),(25,18),
            (32,11),(40,11),(32,18),(40,18),
            (47,6),(73,6),(47,19),(73,19),
            (22,29),(54,29),(22,50),(54,50),
            (22,39),(54,39),
        ],

        "ground_items": [],
        "boss_key_doors": [(42,11,'v')],   # blocks rows 11-12 at col 42

        # Boss arena specific
        "boss_spawn_col": 37,
        "boss_spawn_row": 40,
    },
}


# ---------------------------------------------------------------------------
# Tile rendering helpers
# ---------------------------------------------------------------------------

def _draw_floor_tile(surface, x, y, rng):
    ts=TILE_SIZE; v=rng.randint(-8,8)
    pygame.draw.rect(surface,(38+v,30+v,22+v),(x,y,ts,ts))
    pygame.draw.line(surface,(25,20,14),(x,y),(x+ts-1,y),1)
    pygame.draw.line(surface,(25,20,14),(x,y),(x,y+ts-1),1)
    if rng.random()<0.18:
        cx2=x+rng.randint(8,ts-8); cy2=y+rng.randint(8,ts-8)
        pygame.draw.line(surface,(28,22,16),(cx2,cy2),
                         (cx2+rng.randint(-6,6),cy2+rng.randint(-6,6)),1)

def _draw_wall_tile(surface, x, y, row, col, rng):
    ts=TILE_SIZE
    if (row+col)%2==0: base,hi,lo=(52,42,30),(68,56,40),(32,25,17)
    else:              base,hi,lo=(46,37,26),(60,50,36),(28,22,14)
    pygame.draw.rect(surface,base,(x,y,ts,ts))
    pygame.draw.line(surface,hi,(x,y),(x+ts-1,y),1)
    pygame.draw.line(surface,hi,(x,y),(x,y+ts-1),1)
    pygame.draw.line(surface,lo,(x,y+ts-1),(x+ts-1,y+ts-1),1)
    pygame.draw.line(surface,lo,(x+ts-1,y),(x+ts-1,y+ts-1),1)
    pygame.draw.line(surface,(30,23,15),(x,y+ts//2),(x+ts,y+ts//2),1)

def build_tile_surface(room_map, cols, rows):
    ts=TILE_SIZE
    surf=pygame.Surface((cols*ts,rows*ts))
    surf.fill((4,3,2))
    rng=random.Random(1337)
    for row in range(rows):
        for col in range(cols):
            tile=room_map[row][col]
            x,y=col*ts,row*ts
            if   tile==FLOOR: _draw_floor_tile(surf,x,y,rng)
            elif tile==WALL:  _draw_wall_tile(surf,x,y,row,col,rng)
            else:             pygame.draw.rect(surf,(4,3,2),(x,y,ts,ts))
    return surf

# ---------------------------------------------------------------------------
# Torch
# ---------------------------------------------------------------------------

class Torch:
    def __init__(self,col,row):
        self.col=col; self.row=row
        self.phase=random.uniform(0,math.tau)
        self.freq1=random.uniform(2.8,3.6)
        self.freq2=random.uniform(5.0,7.0)

    def flame_brightness(self,t):
        v=(math.sin(t*self.freq1+self.phase)*0.4+
           math.sin(t*self.freq2+self.phase*1.3)*0.2+0.85)
        return max(0.55,min(1.0,v))

    def draw(self,surface,t,ox,oy):
        ts=TILE_SIZE; cx=ox+self.col*ts+ts//2; cy=oy+self.row*ts+ts//2
        bri=self.flame_brightness(t)
        gr=int(ts*0.9)
        glow=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
        for rad,alpha in [(gr,int(18*bri)),(gr*2//3,int(35*bri)),(gr//3,int(55*bri))]:
            pygame.draw.circle(glow,(200,130,40,alpha),(gr,gr),rad)
        surface.blit(glow,(cx-gr,cy-gr),special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.rect(surface,(80,65,45),(cx-4,cy,8,10))
        pygame.draw.rect(surface,(80,65,45),(cx-6,cy+8,12,4))
        fx,fy=cx,cy-2
        ox2=int(math.sin(t*self.freq1*1.5+self.phase)*2)
        pygame.draw.polygon(surface,(int(200*bri),int(100*bri),10),[
            (fx-6+ox2,fy),(fx-9+ox2,fy-8),(fx+ox2,fy-18),
            (fx+9+ox2,fy-8),(fx+6+ox2,fy)])
        pygame.draw.polygon(surface,(int(230*bri),int(155*bri),20),[
            (fx-3+ox2,fy-2),(fx-5+ox2,fy-9),(fx+ox2,fy-16),
            (fx+5+ox2,fy-9),(fx+3+ox2,fy-2)])
        pygame.draw.polygon(surface,(255,230,160),
            [(fx-1+ox2,fy-4),(fx+ox2,fy-13),(fx+1+ox2,fy-4)])

# ---------------------------------------------------------------------------
# Chest
# ---------------------------------------------------------------------------

class Chest:
    def __init__(self,col,row,items,is_gold=False):
        self.col=col; self.row=row
        self.items=items; self.opened=False
        self.is_gold=is_gold

    def draw(self,surface,ox,oy,time):
        ts=TILE_SIZE; x=ox+self.col*ts; y=oy+self.row*ts
        cx2=x+ts//2; cy2=y+ts//2
        cw,ch=int(ts*0.65),int(ts*0.45)
        bx=cx2-cw//2; by=cy2-ch//2+4
        if self.is_gold:
            bc=(90,72,10) if self.opened else (120,98,15)
            lc2=(160,135,30) if self.opened else (200,170,40)
            lck=(220,190,50) if not self.opened else (100,82,15)
            stud=(220,185,50)
        else:
            bc=(90,62,28) if self.opened else (110,78,36)
            lc2=(110,78,36) if self.opened else (130,95,46)
            lck=(180,148,55) if not self.opened else (80,65,30)
            stud=(160,128,50)
        pygame.draw.rect(surface,bc,(bx,by+ch//2,cw,ch//2))
        pygame.draw.rect(surface,(70,48,20),(bx,by+ch//2,cw,ch//2),1)
        if self.opened: pygame.draw.rect(surface,lc2,(bx,by-ch//3,cw,ch//2))
        else:           pygame.draw.rect(surface,lc2,(bx,by,cw,ch//2))
        pygame.draw.rect(surface,(80,56,22),
                         (bx,by if not self.opened else by-ch//3,cw,ch//2),1)
        pygame.draw.rect(surface,lck,(cx2-5,by+ch//2-5,10,9))
        pygame.draw.rect(surface,(140,110,40),(cx2-5,by+ch//2-5,10,9),1)
        for sx2,sy2 in [(bx+4,by+ch//2+4),(bx+cw-4,by+ch//2+4),
                        (bx+4,by+ch-4),(bx+cw-4,by+ch-4)]:
            pygame.draw.circle(surface,stud,(sx2,sy2),2)
        if not self.opened:
            shimmer=0.5+0.5*math.sin(time*2.5)
            col=(220,185,50) if self.is_gold else (220,185,60)
            glow=pygame.Surface((ts,ts),pygame.SRCALPHA)
            pygame.draw.circle(glow,(*col,int(25*shimmer)),(ts//2,ts//2),ts//2)
            surface.blit(glow,(x,y),special_flags=pygame.BLEND_RGBA_ADD)

    def is_adjacent(self,pc,pr):
        return (abs(self.col-pc)==1 and self.row==pr) or \
               (self.col==pc and abs(self.row-pr)==1)

# ---------------------------------------------------------------------------
# Locked Door
# ---------------------------------------------------------------------------

class LockedDoor:
    def __init__(self,col,row,orientation,key_id,is_boss_key=False,size=2):
        self.col=col; self.row=row
        self.orientation=orientation; self.key_id=key_id
        self.locked=True; self.is_boss_key=is_boss_key
        self.size=size

    def tiles(self):
        """Return the tiles this door occupies.
        orientation 'h' = blocks horizontally (cols), 'v' = blocks vertically (rows).
        size defaults to 2 to match 2-wide corridors."""
        result=[]
        size = getattr(self, 'size', 2)
        for i in range(size):
            dc = i if self.orientation=='h' else 0
            dr = i if self.orientation=='v' else 0
            result.append((self.col+dc, self.row+dr))
        return result

    def is_adjacent(self,pc,pr):
        return abs(pc-self.col)<=1 and abs(pr-self.row)<=1

    def draw(self,surface,ox,oy,time):
        if not self.locked: return
        ts=TILE_SIZE
        pulse=0.7+0.3*math.sin(time*2.0)
        col=(180,80,40) if self.is_boss_key else (55,35,15)
        for dc,dr in self.tiles():
            x=ox+dc*ts; y=oy+dr*ts
            pygame.draw.rect(surface,col,(x,y,ts,ts))
            for i in range(3):
                ply=y+4+i*(ts//3)
                pygame.draw.rect(surface,(75,50,22),(x+3,ply,ts-6,ts//3-3))
                pygame.draw.rect(surface,(45,28,10),(x+3,ply,ts-6,ts//3-3),1)
            kx,ky=x+ts//2,y+ts//2
            pygame.draw.circle(surface,(180,140,50),(kx,ky),5)
            pygame.draw.circle(surface,(30,20,8),(kx,ky),3)
            pygame.draw.rect(surface,(30,20,8),(kx-2,ky,4,5))
            glow=pygame.Surface((ts,ts),pygame.SRCALPHA)
            gc=(220,100,50,int(30*pulse)) if self.is_boss_key else (180,130,40,int(30*pulse))
            pygame.draw.circle(glow,gc,(ts//2,ts//2),ts//2)
            surface.blit(glow,(x,y),special_flags=pygame.BLEND_RGBA_ADD)

# ---------------------------------------------------------------------------
# Floor Circle (transition tile)
# ---------------------------------------------------------------------------

class FloorCircle:
    def __init__(self,col,row,locked=True):
        self.col=col; self.row=row; self.locked=locked

    def is_on(self,pc,pr):
        return abs(pc-self.col)<=1 and abs(pr-self.row)<=1

    def draw(self,surface,ox,oy,time):
        ts=TILE_SIZE; x=ox+self.col*ts; y=oy+self.row*ts
        cx2=x+ts//2; cy2=y+ts//2
        pulse=0.5+0.4*math.sin(time*2.5)
        if self.locked:
            col=(80,60,30,int(40*pulse))
            pygame.draw.circle(surface,(80,65,35),(cx2,cy2),ts//2-4,3)
            pygame.draw.circle(surface,(120,95,45),(cx2,cy2),ts//4,2)
        else:
            col=(60,160,255,int(60*pulse))
            glow=pygame.Surface((ts*2,ts*2),pygame.SRCALPHA)
            pygame.draw.circle(glow,(60,160,255,int(50*pulse)),(ts,ts),ts)
            surface.blit(glow,(cx2-ts,cy2-ts),special_flags=pygame.BLEND_RGBA_ADD)
            pygame.draw.circle(surface,(80,180,255),(cx2,cy2),ts//2-4,3)
            pygame.draw.circle(surface,(140,210,255),(cx2,cy2),ts//4,2)
            # Down arrow
            pygame.draw.polygon(surface,(180,230,255),[
                (cx2-8,cy2-4),(cx2+8,cy2-4),(cx2,cy2+10)])

# ---------------------------------------------------------------------------
# Return Circle (go back to previous floor)
# ---------------------------------------------------------------------------

class ReturnCircle:
    """Always-unlocked portal back to the previous floor."""
    def __init__(self, col, row):
        self.col = col; self.row = row

    def is_on(self, pc, pr):
        return abs(pc-self.col)<=2 and abs(pr-self.row)<=2

    def draw(self, surface, ox, oy, time):
        ts=TILE_SIZE; x=ox+self.col*ts; y=oy+self.row*ts
        cx2=x+ts//2; cy2=y+ts//2
        pulse=0.5+0.4*math.sin(time*2.5)
        # Orange/amber colour to distinguish from floor circle (blue)
        glow=pygame.Surface((ts*2,ts*2),pygame.SRCALPHA)
        pygame.draw.circle(glow,(255,160,40,int(50*pulse)),(ts,ts),ts)
        surface.blit(glow,(cx2-ts,cy2-ts),special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.circle(surface,(220,140,40),(cx2,cy2),ts//2-4,3)
        pygame.draw.circle(surface,(255,200,100),(cx2,cy2),ts//4,2)
        # Up arrow
        pygame.draw.polygon(surface,(255,210,120),[
            (cx2-8,cy2+4),(cx2+8,cy2+4),(cx2,cy2-10)])


# ---------------------------------------------------------------------------
# Ground Item
# ---------------------------------------------------------------------------

class GroundItem:
    def __init__(self,col,row,item):
        self.col=col; self.row=row
        self.item=item; self.picked=False

    def draw(self,surface,ox,oy,time):
        if self.picked: return
        ts=TILE_SIZE
        x=ox+self.col*ts+ts//2; y=oy+self.row*ts+ts//2
        bob=int(math.sin(time*2.5)*3)
        glow=pygame.Surface((ts,ts),pygame.SRCALPHA)
        pygame.draw.ellipse(glow,(180,160,80,35),(4,ts//2,ts-8,ts//3))
        surface.blit(glow,(ox+self.col*ts,oy+self.row*ts))
        self.item.draw_icon(surface,x,y+bob,int(ts*0.52))

    def check_pickup(self,player_col,player_row):
        return not self.picked and self.col==player_col and self.row==player_row

# ---------------------------------------------------------------------------
# Roaming Enemy AI
# ---------------------------------------------------------------------------

class RoamingEnemy:
    """Enemy that wanders randomly within a set of allowed tiles."""
    def __init__(self, col, row, tile_size, room_tiles, definition, drops_key=None):
        self.tile_size   = tile_size
        self.room_tiles  = set(room_tiles)
        self.definition  = definition
        self.enemy_type  = definition["name"].lower().replace(" ","_")
        self.display_name= definition["display_name"]
        self.color       = tuple(definition["color"])
        self.move_speed  = definition.get("speed",2.2)
        self.is_boss     = definition.get("is_boss",False)
        self.drops_key   = drops_key  # key_id this enemy drops, or None

        self.tile_col = col; self.tile_row = row
        self.px = float(col*tile_size); self.py = float(row*tile_size)
        self.target_px=self.px; self.target_py=self.py
        self.moving=False
        self._wait=random.uniform(0.5,1.5)
        self._anim_time=random.uniform(0,math.tau)

    def update(self,dt,player_col,player_row):
        self._anim_time+=dt
        if self.moving:
            dx=self.target_px-self.px; dy=self.target_py-self.py
            dist=math.hypot(dx,dy)
            step=self.move_speed*self.tile_size*dt
            if dist<=step:
                self.px=self.target_px; self.py=self.target_py
                self.tile_col=int(self.target_px/self.tile_size)
                self.tile_row=int(self.target_py/self.tile_size)
                self.moving=False
                self._wait=random.uniform(0.4,1.2)
            else:
                self.px+=dx/dist*step; self.py+=dy/dist*step
        else:
            self._wait-=dt
            if self._wait<=0:
                self._pick_next(player_col,player_row)

    def _pick_next(self,player_col,player_row):
        neighbours=[
            (self.tile_col+1,self.tile_row),
            (self.tile_col-1,self.tile_row),
            (self.tile_col,self.tile_row+1),
            (self.tile_col,self.tile_row-1),
        ]
        valid=[t for t in neighbours
               if t in self.room_tiles
               and not(t[0]==player_col and t[1]==player_row)]
        if not valid:
            self._wait=0.5; return
        nc,nr=random.choice(valid)
        self.target_px=float(nc*self.tile_size)
        self.target_py=float(nr*self.tile_size)
        self.moving=True

    def draw(self,surface,ox,oy):
        from src.entities.enemy import (
            _draw_goblin,_draw_generic)
        draw_x=int(self.px)+ox; draw_y=int(self.py)+oy
        t=self._anim_time; ts=self.tile_size
        etype=self.enemy_type
        if etype=="goblin":
            _draw_goblin(surface,draw_x,draw_y,t,ts)
        elif etype=="goblin_chieftain":
            _draw_chieftain(surface,draw_x,draw_y,t,ts)
        else:
            _draw_generic(surface,draw_x,draw_y,t,ts,self.color)


def _draw_chieftain(surf,x,y,t,ts):
    """Goblin Chieftain — bigger, armoured, with a crown."""
    from src.entities.enemy import _draw_goblin,_lerp_col
    s=ts; cx=x+s//2; cy=y+s//2
    bob=int(math.sin(t*2.0)*max(3,s//16))
    col=(60,120,40); dark=(35,80,22); armour=(80,65,40); gold=(190,155,40)

    # Shadow
    sh=pygame.Surface((s,s//4),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,60),(0,0,s,s//4))
    surf.blit(sh,(cx-s//2,cy+s//3))

    # Boots
    bfw=max(7,s//8)
    for bx2 in [cx-s//6-bfw//2,cx+s//6-bfw//2]:
        pygame.draw.rect(surf,(45,35,20),(bx2,cy+s//3+bob,bfw,max(5,s//10)))

    # Legs
    lw=max(6,s//8); lh=max(10,s//3)
    for lx2 in [cx-s//6-lw//2,cx+s//6-lw//2]:
        pygame.draw.rect(surf,col,(lx2,cy+bob,lw,lh))

    # Body — wider than normal goblin
    bw=max(16,s*3//4); bh=max(12,s//2)
    pygame.draw.ellipse(surf,col,(cx-bw//2,cy-bh//3+bob,bw,bh))
    pygame.draw.ellipse(surf,dark,(cx-bw//2,cy-bh//3+bob,bw,bh),max(1,s//40))
    # Armour chest plate
    pygame.draw.rect(surf,armour,(cx-bw//3,cy-bh//4+bob,bw*2//3,bh//2))
    pygame.draw.rect(surf,dark,(cx-bw//3,cy-bh//4+bob,bw*2//3,bh//2),max(1,s//48))

    # Arms
    aw=max(4,s//10)
    pygame.draw.line(surf,col,(cx-bw//2,cy-bh//5+bob),(cx-bw//2-s//4,cy+bob),aw)
    pygame.draw.line(surf,col,(cx+bw//2,cy-bh//5+bob),(cx+bw//2+s//5,cy+bob),aw)
    # Club in left hand
    pygame.draw.line(surf,armour,(cx-bw//2-s//4,cy+bob),(cx-bw//2-s//3,cy-s//4+bob),max(3,s//14))
    pygame.draw.circle(surf,(70,55,30),(cx-bw//2-s//3,cy-s//4+bob),max(5,s//10))

    # Head — bigger
    hr=max(8,s//4)
    pygame.draw.circle(surf,col,(cx,cy-bh//3-hr+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-bh//3-hr+bob),hr,max(1,s//40))

    # Crown
    crown_pts=[
        (cx-hr,   cy-bh//3-hr*2+bob+4),
        (cx-hr+4, cy-bh//3-hr*2-8+bob),
        (cx-hr//2,cy-bh//3-hr*2+bob+2),
        (cx,      cy-bh//3-hr*2-10+bob),
        (cx+hr//2,cy-bh//3-hr*2+bob+2),
        (cx+hr-4, cy-bh//3-hr*2-8+bob),
        (cx+hr,   cy-bh//3-hr*2+bob+4),
    ]
    pygame.draw.polygon(surf,gold,crown_pts)
    pygame.draw.polygon(surf,dark,crown_pts,max(1,s//48))

    # Ears
    for ex,sign in [(cx-hr,-1),(cx+hr,1)]:
        pygame.draw.polygon(surf,col,[
            (ex,cy-bh//3-hr+bob),
            (ex+sign*max(5,s//10),cy-bh//3-hr-max(6,s//8)+bob),
            (ex+sign*max(3,s//14),cy-bh//3-hr+max(3,s//16)+bob)])

    # Eyes — red
    er=max(2,s//20); eox=max(3,hr//2)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(220,50,30),(ex,cy-bh//3-hr+bob),er)
        pygame.draw.circle(surf,(255,150,100),(ex,cy-bh//3-hr+bob),max(1,er-1))

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

class Camera:
    def __init__(self,sw,sh,mc,mr,ts):
        self.sw=sw; self.sh=sh
        self.mw=mc*ts; self.mh=mr*ts
        self.ox=0; self.oy=0

    def update(self,px,py):
        ts=TILE_SIZE
        self.ox=max(self.sw-self.mw,min(0,self.sw//2-int(px)-ts//2))
        self.oy=max(self.sh-self.mh,min(0,self.sh//2-int(py)-ts//2))

# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _draw_prompt(surface,font,cx,cy,text,col=(210,185,120),border=(90,70,42)):
    s=font.render(text,True,col)
    bg=pygame.Surface((s.get_width()+16,s.get_height()+8),pygame.SRCALPHA)
    bg.fill((10,8,5,180))
    bx=cx-bg.get_width()//2; by=cy-bg.get_height()-4
    surface.blit(bg,(bx,by))
    pygame.draw.rect(surface,border,(bx,by,bg.get_width(),bg.get_height()),1)
    surface.blit(s,(bx+8,by+4))

MOVE_KEYS={
    pygame.K_w:(0,-1),pygame.K_s:(0,1),
    pygame.K_a:(-1,0),pygame.K_d:(1,0),
}


# ---------------------------------------------------------------------------
# GameScene
# ---------------------------------------------------------------------------

def _make_debug_sword():
    """DEBUG: 80-damage sword for testing. Remove before release."""
    from src.scenes.chest_scene import DebugSwordItem
    return DebugSwordItem()


class GameScene:
    def __init__(self, screen, inventory, player_stats=None, game_state=None,
                 floor=1, floor_states=None, return_spawn=None):
        self.inventory    = inventory
        self.player_stats = player_stats
        self.game_state   = game_state
        self.floor        = floor
        # floor_states: shared dict {floor: {unlocked_door_key_ids: set}}
        self.floor_states = floor_states if floor_states is not None else {}
        self.return_spawn = return_spawn  # (col,row) override for spawn position
        self.screen       = screen
        self.W,self.H     = screen.get_size()
        self.clock        = pygame.time.Clock()
        self.time         = 0.0
        self.font_small   = pygame.font.SysFont("courier new",15)

        # Build map for this floor
        fdata             = FLOOR_DATA[floor]
        cols,rows         = FLOOR_SIZES[floor] if floor in {1:60,2:75,3:70,4:80} else (60,50)
        # Recompute from FLOOR_BUILDERS
        self.room_map     = FLOOR_BUILDERS[floor]()
        _sizes            = {1:(60,50),2:(75,55),3:(70,50),4:(80,60)}
        self.COLS,self.ROWS = _sizes[floor]
        self.tile_surf    = build_tile_surface(self.room_map,self.COLS,self.ROWS)
        self.vignette     = self._build_vignette()

        # Player — use return_spawn if coming back from a higher floor
        sp = self.return_spawn if self.return_spawn else fdata["player_spawn"]
        self.player=Player(sp[0],sp[1],TILE_SIZE)

        # Torches
        self.torches=[Torch(c,r) for c,r in fdata["torches"]]

        # Locked doors
        boss_key_door_tiles={
            (col,row) for col,row,ori in fdata.get("boss_key_doors",[])
        }
        self.locked_doors=[]
        for door_def in fdata["locked_doors"]:
            col,row,ori,kid = door_def[:4]
            is_bk=(col,row) in boss_key_door_tiles
            self.locked_doors.append(LockedDoor(col,row,ori,kid,is_boss_key=is_bk,size=2))
        # Boss key doors (if not already in locked_doors)
        existing_bk={(d.col,d.row) for d in self.locked_doors if d.is_boss_key}
        for col,row,ori in fdata.get("boss_key_doors",[]):
            if (col,row) not in existing_bk:
                self.locked_doors.append(LockedDoor(col,row,ori,"boss_key",is_boss_key=True,size=2))
        # Restore previously unlocked doors for this floor
        unlocked_ids = self.floor_states.get(floor, {}).get("unlocked_doors", set())
        for door in self.locked_doors:
            if door.key_id in unlocked_ids:
                door.locked = False

        # Floor circle (go to next floor)
        fc=fdata["floor_circle"]
        self.floor_circle=FloorCircle(fc[0],fc[1],locked=True) if fc else None
        # Restore floor circle unlock if previously opened
        if self.floor_circle and "floor_circle" in unlocked_ids:
            self.floor_circle.locked=False
        # Return circle (go back to previous floor)
        rc=fdata.get("return_circle")
        self.return_circle=ReturnCircle(rc[0],rc[1]) if rc and floor>1 else None

        # Build enemies with random key assignment
        self.enemies=[]
        self._build_enemies(fdata)

        # Chests
        self.chests=self._build_chests(fdata)

        # Ground items
        self.ground_items=self._build_ground_items(fdata)

        # Boss arena state (floor 4 only)
        self.boss_spawned  = False
        self.boss_defeated = False
        self.boss          = None
        self._arena_cleared= False

        # HUD
        if player_stats and game_state:
            from src.ui.hud import HUD
            self._hud=HUD(screen)
        else:
            self._hud=None

        self.COMBAT_COOLDOWN=1.5
        self.combat_cooldown=self.COMBAT_COOLDOWN
        self._nearby_chest=None
        self._nearby_door=None
        self._active_enemy=None
        self._potion_msg=""; self._potion_msg_timer=0.0

        self.visited=set()
        self.VISION_RADIUS=4
        _hud_h=52 if (player_stats and game_state) else 0
        self.camera=Camera(self.W,self.H-_hud_h,self.COLS,self.ROWS,TILE_SIZE)
        self.camera.update(self.player.px,self.player.py)
        # Cooldown prevents instant re-trigger of floor/return circles on spawn
        self.circle_cooldown = 1.5

    # ------------------------------------------------------------------ #
    # Build helpers
    # ------------------------------------------------------------------ #

    def _build_enemies(self, fdata):
        from src.entities.entity_factory import get_definition
        for etype, room_key, count, key_drop in fdata["enemies"]:
            room_tiles=fdata["rooms"].get(room_key,[])
            if not room_tiles: continue
            defn=get_definition(etype)
            # Pick a random tile to place each enemy, spread them out
            placed_tiles=random.sample(room_tiles, min(count,len(room_tiles)))
            for i,tile in enumerate(placed_tiles):
                # Assign key_drop to ONE random enemy in group
                drops = key_drop if (i==0 and key_drop) else None
                e=RoamingEnemy(tile[0],tile[1],TILE_SIZE,room_tiles,defn,drops_key=drops)
                self.enemies.append(e)

    def _build_chests(self, fdata):
        from src.scenes.chest_scene import PotionItem,GoldItem,CandleItem
        def _make_items(item_list):
            result=[]
            for it in item_list:
                if it=="potion":   result.append(PotionItem())
                elif it=="gold":   result.append(GoldItem(random.choice([10,15,20])))
                elif it=="candle": result.append(CandleItem())
            return result
        chests=[]
        for cd in fdata["chests"]:
            items=_make_items(cd["items"])
            chests.append(Chest(cd["col"],cd["row"],items,is_gold=cd["gold"]))
        return chests

    def _build_ground_items(self, fdata):
        from src.scenes.chest_scene import StickItem, RoomKeyItem
        result=[]
        for gi in fdata.get("ground_items",[]):
            col,row,itype=gi
            if itype=="debug_sword":
                item=_make_debug_sword()
            elif itype=="stick":
                item=StickItem()
            elif itype.startswith("key_"):
                item=RoomKeyItem(itype)
            else:
                continue
            result.append(GroundItem(col,row,item))
        return result

    # ------------------------------------------------------------------ #

    def _build_vignette(self):
        surf=pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        cx,cy=self.W//2,self.H//2
        mr=int(math.hypot(cx,cy))
        for i in range(80,0,-1):
            r=int(mr*i/80); a=int(200*(i/80)**2.2)
            pygame.draw.circle(surf,(0,0,0,a),(cx,cy),r)
        return surf

    def _update_visited(self):
        pr=self.VISION_RADIUS; pc=self.player.tile_col; prow=self.player.tile_row
        for dc in range(-pr,pr+1):
            for dr in range(-pr,pr+1):
                if dc*dc+dr*dr<=pr*pr:
                    col=pc+dc; row=prow+dr
                    if 0<=row<self.ROWS and 0<=col<self.COLS:
                        self.visited.add((col,row))

    def _draw_ambient_darkness(self):
        ts=TILE_SIZE; ox=self.camera.ox; oy=self.camera.oy
        px=ox+int(self.player.px)+ts//2; py=oy+int(self.player.py)+ts//2
        dark=pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        vision_r=int(ts*5.5); steps=32
        for i in range(steps,0,-1):
            r=int(vision_r*i/steps)
            a=int(190*((i/steps)**1.4))
            pygame.draw.circle(dark,(0,0,0,a),(px,py),r)
        outer=pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        outer.fill((0,0,0,190))
        for torch in self.torches:
            bri=torch.flame_brightness(self.time)
            cx=ox+torch.col*ts+ts//2; cy=oy+torch.row*ts+ts//2
            pygame.draw.circle(outer,(0,0,0,0),(cx,cy),int(ts*2.2*bri))
        pygame.draw.circle(outer,(0,0,0,0),(px,py),vision_r)
        self.screen.blit(dark,(0,0))
        self.screen.blit(outer,(0,0))

    def _check_nearby(self):
        pc=self.player.tile_col; pr=self.player.tile_row
        self._nearby_chest=next((c for c in self.chests
                                  if not c.opened and c.items and c.is_adjacent(pc,pr)),None)
        self._nearby_door=next((d for d in self.locked_doors
                                 if d.locked and d.is_adjacent(pc,pr)),None)

    def _check_floor_circle(self):
        if not self.floor_circle or self.floor_circle.locked: return False
        return self.floor_circle.is_on(self.player.tile_col,self.player.tile_row)

    def _check_combat(self):
        ts=TILE_SIZE
        pcx=self.player.px+ts//2; pcy=self.player.py+ts//2
        for e in self.enemies:
            if math.hypot(e.px+ts//2-pcx,e.py+ts//2-pcy)<ts*0.75:
                self._active_enemy=e
                return True
        if self.boss and not self.boss_defeated:
            if math.hypot(self.boss.px+ts//2-pcx,self.boss.py+ts//2-pcy)<ts*0.85:
                self._active_enemy=self.boss
                return True
        return False

    def _check_arena_clear(self):
        """Check if all arena enemies are dead → spawn boss."""
        if self.floor!=4 or self.boss_spawned: return
        arena_tiles=set(map(tuple,FLOOR_DATA[4]["rooms"]["arena"]))
        arena_enemies=[e for e in self.enemies
                       if any(t in arena_tiles for t in [(e.tile_col,e.tile_row)])]
        if not arena_enemies:
            self._spawn_boss()

    def _spawn_boss(self):
        from src.entities.entity_factory import get_definition
        fdata=FLOOR_DATA[4]
        defn=get_definition("goblin_king")
        bc=fdata.get("boss_spawn_col",37)
        br=fdata.get("boss_spawn_row",40)
        room_tiles=fdata["rooms"]["arena"]
        self.boss=RoamingEnemy(bc,br,TILE_SIZE,room_tiles,defn,drops_key="boss_key")
        self.boss_spawned=True

    def _use_key_on_door(self, door):
        """Try to use any matching key from inventory on this door."""
        from src.scenes.chest_scene import FloorKeyItem, BossKeyItem, KeyItem, RoomKeyItem
        for item in list(self.inventory.items):
            if door.is_boss_key and isinstance(item, BossKeyItem):
                door.locked=False
                self.inventory.remove(item)
                self._persist_door(door)
                return True
            if isinstance(item, FloorKeyItem) and door.key_id=="floor_key":
                door.locked=False
                self.inventory.remove(item)
                self._persist_door(door)
                return True
            if hasattr(item,'key_id') and item.key_id==door.key_id:
                door.locked=False
                self.inventory.remove(item)
                self._persist_door(door)
                return True
        return False

    def _persist_door(self, door):
        """Save this door's unlocked state to floor_states."""
        if self.floor not in self.floor_states:
            self.floor_states[self.floor] = {"unlocked_doors": set()}
        self.floor_states[self.floor]["unlocked_doors"].add(door.key_id)

    def _use_floor_key(self):
        from src.scenes.chest_scene import FloorKeyItem
        for item in list(self.inventory.items):
            if isinstance(item, FloorKeyItem):
                self.inventory.remove(item)
                if self.floor_circle:
                    self.floor_circle.locked=False
                    # Persist floor circle unlock
                    if self.floor not in self.floor_states:
                        self.floor_states[self.floor] = {"unlocked_doors": set()}
                    self.floor_states[self.floor]["unlocked_doors"].add("floor_circle")
                return True
        return False

    def _draw_boss_indicator(self, ox, oy):
        if not self.boss or self.boss_defeated: return
        ts=TILE_SIZE
        draw_x=int(self.boss.px)+ox; draw_y=int(self.boss.py)+oy
        # Big red glow
        gr=int(ts*2.5)
        glow=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
        pulse=0.4+0.3*math.sin(self.time*2.5)
        pygame.draw.circle(glow,(180,30,30,int(22*pulse)),(gr,gr),gr)
        self.screen.blit(glow,(draw_x+ts//2-gr,draw_y+ts//2-gr),
                         special_flags=pygame.BLEND_RGBA_ADD)
        self.boss.draw(self.screen,ox,oy)
        name_s=self.font_small.render("GOBLIN KING",True,(240,80,60))
        self.screen.blit(name_s,(draw_x+ts//2-name_s.get_width()//2,draw_y-name_s.get_height()-4))

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self):
        while True:
            dt=self.clock.tick(60)/1000.0; self.time+=dt

            for event in pygame.event.get():
                if event.type==pygame.QUIT: return "exit"
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: return "pause"
                    if event.key==pygame.K_i:      return "inventory"
                    if event.key==pygame.K_m:      return "map"

                    if event.key==pygame.K_e:
                        if self._nearby_chest:
                            self._chest_to_open=self._nearby_chest
                            return "chest"
                        if self._nearby_door:
                            ok=self._use_key_on_door(self._nearby_door)
                            if not ok:
                                self._potion_msg="Wrong key!"; self._potion_msg_timer=1.5

                    if event.key==pygame.K_f:
                        if self.circle_cooldown>0: pass
                        elif self.return_circle and self.return_circle.is_on(
                                self.player.tile_col,self.player.tile_row):
                            return f"floor_{self.floor-1}"
                        elif self.floor_circle and self.floor_circle.is_on(
                                self.player.tile_col,self.player.tile_row):
                            if self.floor_circle.locked:
                                ok=self._use_floor_key()
                                if not ok:
                                    self._potion_msg="Need a Floor Key!"; self._potion_msg_timer=1.5
                            else:
                                return f"floor_{self.floor+1}"

                    if event.key==pygame.K_p:
                        from src.scenes.chest_scene import PotionItem
                        from src.scenes.combat_scene import POTION_HEAL,PLAYER_MAX_HP
                        max_hp=self.player_stats.max_hp if self.player_stats else PLAYER_MAX_HP
                        cur_hp=self.game_state.player_hp if self.game_state else max_hp
                        if not self.inventory.has(PotionItem):
                            self._potion_msg="No potions!"
                        elif cur_hp>=max_hp:
                            self._potion_msg="Already at full HP!"
                        else:
                            self.inventory.remove_one(PotionItem)
                            healed=min(POTION_HEAL,max_hp-cur_hp)
                            if self.game_state: self.game_state.player_hp=cur_hp+healed
                            self._potion_msg=f"+{healed} HP ({cur_hp+healed}/{max_hp})"
                        self._potion_msg_timer=2.0

            keys=pygame.key.get_pressed()
            for key,(dc,dr) in MOVE_KEYS.items():
                if keys[key]:
                    self.player.try_move(dc,dr,self.room_map); break

            self.player.update(dt)
            self._update_visited()

            # Block player from walking into locked doors
            for door in self.locked_doors:
                if not door.locked: continue
                for tc,tr in door.tiles():
                    if self.player.tile_col==tc and self.player.tile_row==tr:
                        self.player.tile_col=getattr(self.player,'_prev_col',self.player.tile_col)
                        self.player.tile_row=getattr(self.player,'_prev_row',self.player.tile_row)
                        self.player.target_px=float(self.player.tile_col*TILE_SIZE)
                        self.player.target_py=float(self.player.tile_row*TILE_SIZE)
                        self.player.px=self.player.target_px
                        self.player.py=self.player.target_py
                        self.player.moving=False

            # Ground item pickup
            for gi in self.ground_items:
                if gi.check_pickup(self.player.tile_col,self.player.tile_row):
                    self.inventory.add(gi.item)
                    gi.picked=True
                    self._potion_msg=f"Picked up {gi.item.name}!"
                    self._potion_msg_timer=1.5

            # Enemy updates
            for e in self.enemies:
                e.update(dt,self.player.tile_col,self.player.tile_row)
            if self.boss and not self.boss_defeated:
                self.boss.update(dt,self.player.tile_col,self.player.tile_row)

            # Boss arena check
            if self.floor==4 and not self.boss_spawned:
                self._check_arena_clear()

            self.combat_cooldown=max(0.0,self.combat_cooldown-dt)
            self.circle_cooldown=max(0.0,self.circle_cooldown-dt)
            self._potion_msg_timer=max(0.0,self._potion_msg_timer-dt)
            self.camera.update(self.player.px,self.player.py)

            if not self.player.moving:
                self._check_nearby()
            else:
                self._nearby_chest=self._nearby_door=None

            # Combat trigger
            if not self.player.moving and self.combat_cooldown<=0.0 and self._check_combat():
                if self._active_enemy is self.boss:
                    return "boss_combat"
                return "combat"

            # Floor transition trigger (auto on step)
            if self.circle_cooldown<=0 and self.floor_circle and not self.floor_circle.locked:
                if self.floor_circle.is_on(self.player.tile_col,self.player.tile_row):
                    return f"floor_{self.floor+1}"

            # ---- Draw ----
            ox=self.camera.ox; oy=self.camera.oy
            ts=TILE_SIZE
            self.screen.fill((4,3,2))
            self.screen.blit(self.tile_surf,(ox,oy))
            self._draw_ambient_darkness()

            for door in self.locked_doors:
                door.draw(self.screen,ox,oy,self.time)
            for torch in self.torches:
                torch.draw(self.screen,self.time,ox,oy)
            for chest in self.chests:
                chest.draw(self.screen,ox,oy,self.time)
            if self.floor_circle:
                self.floor_circle.draw(self.screen,ox,oy,self.time)
            if self.return_circle:
                self.return_circle.draw(self.screen,ox,oy,self.time)
            for gi in self.ground_items:
                gi.draw(self.screen,ox,oy,self.time)
            for e in self.enemies:
                e.draw(self.screen,ox,oy)
            if self.boss and not self.boss_defeated:
                self._draw_boss_indicator(ox,oy)
            self.player.draw(self.screen,ox,oy)

            # Prompts
            if self._nearby_chest:
                ccx=ox+self._nearby_chest.col*ts+ts//2
                ccy=oy+self._nearby_chest.row*ts
                _draw_prompt(self.screen,self.font_small,ccx,ccy,"[ E ]  Open")
            if self._nearby_door:
                dcx=ox+self._nearby_door.col*ts+ts//2
                dcy=oy+self._nearby_door.row*ts
                txt="[ E ]  Boss Key" if self._nearby_door.is_boss_key else "[ E ]  Use Key"
                _draw_prompt(self.screen,self.font_small,dcx,dcy,txt,col=(220,185,80))
            if self.floor_circle and self.floor_circle.is_on(
                    self.player.tile_col,self.player.tile_row):
                fcx=ox+self.floor_circle.col*ts+ts//2
                fcy=oy+self.floor_circle.row*ts
                if self.floor_circle.locked:
                    _draw_prompt(self.screen,self.font_small,fcx,fcy,
                                 "[ F ]  Use Floor Key",col=(200,170,60))
                else:
                    _draw_prompt(self.screen,self.font_small,fcx,fcy,
                                 "[ F ]  Go to next floor",col=(120,200,255))
            if self.return_circle and self.return_circle.is_on(
                    self.player.tile_col,self.player.tile_row):
                rcx=ox+self.return_circle.col*ts+ts//2
                rcy=oy+self.return_circle.row*ts
                _draw_prompt(self.screen,self.font_small,rcx,rcy,
                             f"[ F ]  Return to Floor {self.floor-1}",col=(255,200,80))

            # Potion hint
            from src.scenes.chest_scene import PotionItem
            if self.inventory.has(PotionItem):
                count=self.inventory.count(PotionItem)
                ph_s=self.font_small.render(f"[ P ]  Potion (x{count})",True,(160,210,140))
                ph_bg=pygame.Surface((ph_s.get_width()+16,ph_s.get_height()+8),pygame.SRCALPHA)
                ph_bg.fill((10,8,5,160))
                phx=self.W-ph_s.get_width()-28; phy=self.H-80
                self.screen.blit(ph_bg,(phx-8,phy-4))
                self.screen.blit(ph_s,(phx,phy))

            # Floor indicator
            fl_s=self.font_small.render(f"Floor {self.floor}",True,(140,110,55))
            self.screen.blit(fl_s,(8,8))

            self.screen.blit(self.vignette,(0,0))

            # Message
            if self._potion_msg and self._potion_msg_timer>0:
                alpha=min(1.0,self._potion_msg_timer/0.4)
                col=(120,210,120) if ("HP" in self._potion_msg or "Picked" in self._potion_msg) else (210,100,80)
                ms=self.font_small.render(self._potion_msg,True,col)
                bg=pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
                bg.fill((10,8,5,int(200*alpha)))
                bx2=self.W//2-bg.get_width()//2; by2=self.H-90
                self.screen.blit(bg,(bx2,by2))
                pygame.draw.rect(self.screen,col,(bx2,by2,bg.get_width(),bg.get_height()),1)
                ms.set_alpha(int(255*alpha))
                self.screen.blit(ms,(bx2+10,by2+4))

            # HUD
            if self.game_state:
                from src.scenes.chest_scene import GoldItem
                gold=sum(self.inventory.stack_count(it)
                         for it in self.inventory.items if isinstance(it,GoldItem))
                self.game_state.gold_collected=gold
            if self._hud and self.player_stats and self.game_state:
                self._hud.update(dt,self.player_stats,self.game_state)
                self._hud.draw(self.player_stats,self.game_state,
                               goblins_remaining=len(self.enemies),
                               location_name=f"Dungeon — Floor {self.floor}",
                               boss_alive=self.boss_spawned and not self.boss_defeated)

            pygame.display.flip()