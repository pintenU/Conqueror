import pygame
import math
import random

from src.entities.player import Player
from src.entities.goblin import Goblin
from src.entities.enemy import Enemy
from src.entities.entity_factory import spawn_patrol, roll_loot as factory_roll_loot


TILE_SIZE = 48
FLOOR = 0
WALL  = 1
EMPTY = 2

COLS = 80
ROWS = 38

def _room(g, col, row, w, h):
    for r in range(row, row+h):
        for c in range(col, col+w):
            g[r][c] = WALL if (r==row or r==row+h-1 or c==col or c==col+w-1) else FLOOR

def _corridor_h(g, col, row, length, thickness=3):
    for r in range(row, row+thickness):
        for c in range(col, col+length):
            g[r][c] = FLOOR

def _corridor_v(g, col, row, length, thickness=3):
    for r in range(row, row+length):
        for c in range(col, col+thickness):
            g[r][c] = FLOOR

def _build_room_map():
    g = [[EMPTY]*COLS for _ in range(ROWS)]

    # Main path rooms
    _room(g,  1, 14, 13, 11)   # Entrance
    _room(g, 18, 14, 13, 11)   # Room 1
    _room(g, 35, 14, 13, 11)   # Room 2
    _room(g, 52, 14, 13, 11)   # Room 3
    _room(g, 67, 11, 12, 16)   # Final room

    # Side rooms
    _room(g, 18,  3, 13,  9)   # Side A
    _room(g, 35, 27, 13,  8)   # Side B
    _room(g, 52,  3, 13,  9)   # Side C

    # Horizontal corridors
    _corridor_h(g, 14, 17, 4)
    _corridor_h(g, 31, 17, 4)
    _corridor_h(g, 48, 17, 4)
    _corridor_h(g, 65, 17, 2)

    # Vertical corridors
    _corridor_v(g, 22, 12, 2)
    _corridor_v(g, 40, 25, 2)
    _corridor_v(g, 57, 12, 2)

    # Punch doorways
    for r in range(17, 20):
        g[r][14] = FLOOR; g[r][13] = FLOOR
        g[r][18] = FLOOR; g[r][30] = FLOOR; g[r][31] = FLOOR
        g[r][35] = FLOOR; g[r][47] = FLOOR; g[r][48] = FLOOR
        g[r][52] = FLOOR; g[r][64] = FLOOR; g[r][65] = FLOOR
        g[r][67] = FLOOR

    for col in range(22, 25):
        g[11][col] = FLOOR; g[12][col] = FLOOR; g[14][col] = FLOOR
    for col in range(40, 43):
        g[24][col] = FLOOR; g[25][col] = FLOOR; g[27][col] = FLOOR
    for col in range(57, 60):
        g[11][col] = FLOOR; g[12][col] = FLOOR; g[14][col] = FLOOR

    return g

ROOM_MAP = _build_room_map()

TORCH_POSITIONS = [
    # Entrance — two on the north wall only
    (3,14),(10,14),
    # R1 — two on north wall
    (20,14),(28,14),
    # Side A — one on south wall
    (24,11),
    # R2 — two on north wall
    (37,14),(45,14),
    # Side B — one on north wall
    (40,27),
    # R3 — two on north wall
    (54,14),(62,14),
    # Side C — one on south wall
    (57,11),
    # Final — two on north wall, one each side
    (69,11),(76,11),
]

GOBLIN_PATROLS = [
    [(3,18),  (10,18)],
    [(20,18), (28,18)],
    [(20,6),  (28,6)],
    [(37,18), (45,18)],
    [(37,20), (45,20)],
    [(37,29), (45,29)],
    [(54,18), (62,18)],
    [(54,20), (62,20)],
    [(54,6),  (62,6)],
    [(69,15), (76,15)],
    [(69,20), (76,20)],
]

BOSS_PATROL = [(70, 18), (76, 18)]

CHEST_POSITIONS = [
    (10, 22),
    (28, 22),
    (28,  5),
    (45, 22),
    (45, 31),
    (62, 22),
    (62,  5),
    (76, 21),
]

LOCKED_DOORS = [
    (31, 17, 'h'),
    (48, 17, 'h'),
    (65, 17, 'h'),
]
DOOR_KEY_IDS = ["key_r1r2", "key_r2r3", "key_r3f"]

EXIT_TILE    = (3, 15)
PLAYER_SPAWN = (7, 18)

MOVE_KEYS = {
    pygame.K_w: ( 0, -1),
    pygame.K_s: ( 0,  1),
    pygame.K_a: (-1,  0),
    pygame.K_d: ( 1,  0),
}


def _draw_floor_tile(surface, x, y, rng):
    ts = TILE_SIZE
    v  = rng.randint(-8, 8)
    pygame.draw.rect(surface, (38+v,30+v,22+v), (x,y,ts,ts))
    pygame.draw.line(surface, (25,20,14), (x,y), (x+ts-1,y), 1)
    pygame.draw.line(surface, (25,20,14), (x,y), (x,y+ts-1), 1)
    if rng.random() < 0.22:
        cx2 = x + rng.randint(8,ts-8); cy2 = y + rng.randint(8,ts-8)
        pygame.draw.line(surface,(28,22,16),(cx2,cy2),
                         (cx2+rng.randint(-6,6),cy2+rng.randint(-6,6)),1)

def _draw_wall_tile(surface, x, y, row, col, rng):
    ts = TILE_SIZE
    if (row+col)%2==0: base,hi,lo=(52,42,30),(68,56,40),(32,25,17)
    else:              base,hi,lo=(46,37,26),(60,50,36),(28,22,14)
    pygame.draw.rect(surface,base,(x,y,ts,ts))
    pygame.draw.line(surface,hi,(x,y),(x+ts-1,y),1)
    pygame.draw.line(surface,hi,(x,y),(x,y+ts-1),1)
    pygame.draw.line(surface,lo,(x,y+ts-1),(x+ts-1,y+ts-1),1)
    pygame.draw.line(surface,lo,(x+ts-1,y),(x+ts-1,y+ts-1),1)
    pygame.draw.line(surface,(30,23,15),(x,y+ts//2),(x+ts,y+ts//2),1)

def _draw_void_tile(surface, x, y):
    pygame.draw.rect(surface,(4,3,2),(x,y,TILE_SIZE,TILE_SIZE))

def build_tile_surface():
    ts   = TILE_SIZE
    surf = pygame.Surface((COLS*ts, ROWS*ts))
    surf.fill((4,3,2))
    rng  = random.Random(1337)
    for row in range(ROWS):
        for col in range(COLS):
            tile = ROOM_MAP[row][col]
            x,y  = col*ts, row*ts
            if   tile==FLOOR: _draw_floor_tile(surf,x,y,rng)
            elif tile==WALL:  _draw_wall_tile(surf,x,y,row,col,rng)
            else:             _draw_void_tile(surf,x,y)
    return surf


class Chest:
    def __init__(self, col, row, items):
        self.col=col; self.row=row; self.items=items; self.opened=False

    def draw(self, surface, ox, oy, time):
        ts=TILE_SIZE; x=ox+self.col*ts; y=oy+self.row*ts
        cx=x+ts//2; cy=y+ts//2
        cw,ch=int(ts*0.65),int(ts*0.45)
        bx=cx-cw//2; by=cy-ch//2+4
        bc=(90,62,28) if self.opened else (110,78,36)
        lc2=(110,78,36) if self.opened else (130,95,46)
        pygame.draw.rect(surface,bc,(bx,by+ch//2,cw,ch//2))
        pygame.draw.rect(surface,(70,48,20),(bx,by+ch//2,cw,ch//2),1)
        if self.opened: pygame.draw.rect(surface,lc2,(bx,by-ch//3,cw,ch//2))
        else:           pygame.draw.rect(surface,lc2,(bx,by,cw,ch//2))
        pygame.draw.rect(surface,(80,56,22),
                         (bx,by if not self.opened else by-ch//3,cw,ch//2),1)
        lck=(180,148,55) if not self.opened else (80,65,30)
        pygame.draw.rect(surface,lck,(cx-5,by+ch//2-5,10,9))
        pygame.draw.rect(surface,(140,110,40),(cx-5,by+ch//2-5,10,9),1)
        for sx2,sy2 in [(bx+4,by+ch//2+4),(bx+cw-4,by+ch//2+4),
                        (bx+4,by+ch-4),(bx+cw-4,by+ch-4)]:
            pygame.draw.circle(surface,(160,128,50),(sx2,sy2),2)
        if not self.opened:
            shimmer=0.5+0.5*math.sin(time*2.5)
            glow=pygame.Surface((ts,ts),pygame.SRCALPHA)
            pygame.draw.circle(glow,(220,185,60,int(20*shimmer)),(ts//2,ts//2),ts//2)
            surface.blit(glow,(x,y),special_flags=pygame.BLEND_RGBA_ADD)

    def is_adjacent(self, pc, pr):
        return (abs(self.col-pc)==1 and self.row==pr) or \
               (self.col==pc and abs(self.row-pr)==1)


class Torch:
    def __init__(self, col, row):
        self.col=col; self.row=row
        self.phase=random.uniform(0,math.tau)
        self.freq1=random.uniform(2.8,3.6)
        self.freq2=random.uniform(5.0,7.0)

    def flame_brightness(self, t):
        v=(math.sin(t*self.freq1+self.phase)*0.4+
           math.sin(t*self.freq2+self.phase*1.3)*0.2+0.85)
        return max(0.55,min(1.0,v))

    def draw(self, surface, t, ox, oy):
        ts=TILE_SIZE; cx=ox+self.col*ts+ts//2; cy=oy+self.row*ts+ts//2
        bri=self.flame_brightness(t)
        gr=int(ts*2.0)   # much smaller glow — moody, not blinding
        glow=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
        for rad,alpha in [(gr,int(10*bri)),(gr*2//3,int(22*bri)),(gr//3,int(40*bri))]:
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


class LockedDoor:
    def __init__(self, col, row, orientation, key_id):
        self.col=col; self.row=row
        self.orientation=orientation; self.key_id=key_id
        self.locked=True

    def is_adjacent(self, pc, pr):
        return abs(pc-self.col)<=1 and abs(pr-self.row)<=1

    def draw(self, surface, ox, oy, time):
        if not self.locked: return
        ts=TILE_SIZE
        tiles=[(self.col,self.row),
               (self.col+(1 if self.orientation=='h' else 0),
                self.row+(1 if self.orientation=='v' else 0)),
               (self.col+(2 if self.orientation=='h' else 0),
                self.row+(2 if self.orientation=='v' else 0))]
        pulse=0.7+0.3*math.sin(time*2.0)
        for col,row in tiles:
            x=ox+col*ts; y=oy+row*ts
            pygame.draw.rect(surface,(55,35,15),(x,y,ts,ts))
            for i in range(3):
                ply=y+4+i*(ts//3)
                pygame.draw.rect(surface,(75,50,22),(x+3,ply,ts-6,ts//3-3))
                pygame.draw.rect(surface,(45,28,10),(x+3,ply,ts-6,ts//3-3),1)
            pygame.draw.rect(surface,(90,70,30),(x+2,y+ts//3-2,ts-4,4))
            pygame.draw.rect(surface,(90,70,30),(x+2,y+ts*2//3-2,ts-4,4))
            kx,ky=x+ts//2,y+ts//2
            pygame.draw.circle(surface,(180,140,50),(kx,ky),5)
            pygame.draw.circle(surface,(30,20,8),(kx,ky),3)
            pygame.draw.rect(surface,(30,20,8),(kx-2,ky,4,5))
            glow=pygame.Surface((ts,ts),pygame.SRCALPHA)
            pygame.draw.circle(glow,(180,130,40,int(30*pulse)),(ts//2,ts//2),ts//2)
            surface.blit(glow,(x,y),special_flags=pygame.BLEND_RGBA_ADD)


class ExitTile:
    def __init__(self, col, row):
        self.col=col; self.row=row; self.locked=True

    def is_adjacent(self, pc, pr):
        return (abs(self.col-pc)<=1 and self.row==pr) or \
               (self.col==pc and abs(self.row-pr)<=1)

    def draw(self, surface, ox, oy, time):
        ts=TILE_SIZE; x=ox+self.col*ts; y=oy+self.row*ts
        cx=x+ts//2; cy=y+ts//2
        pulse=0.6+0.4*math.sin(time*2.5)
        if self.locked:
            gc=(70,55,30)
            for bx2 in range(x+6,x+ts-4,8):
                pygame.draw.line(surface,gc,(bx2,y+4),(bx2,y+ts-4),3)
            pygame.draw.rect(surface,gc,(x+4,y+4,ts-8,6))
            pygame.draw.rect(surface,gc,(x+4,y+ts-10,ts-8,6))
            pygame.draw.rect(surface,(160,130,50),(cx-6,cy-5,12,10))
            pygame.draw.rect(surface,(120,95,35),(cx-6,cy-5,12,10),1)
            glow=pygame.Surface((ts,ts),pygame.SRCALPHA)
            pygame.draw.rect(glow,(180,140,40,int(20*pulse)),(0,0,ts,ts))
            surface.blit(glow,(x,y),special_flags=pygame.BLEND_RGBA_ADD)
        else:
            glow=pygame.Surface((ts,ts),pygame.SRCALPHA)
            pygame.draw.ellipse(glow,(100,180,255,int(60*pulse)),(4,4,ts-8,ts-8))
            surface.blit(glow,(x,y),special_flags=pygame.BLEND_RGBA_ADD)
            pygame.draw.ellipse(surface,(80,160,220),(x+6,y+6,ts-12,ts-12),2)
            pygame.draw.ellipse(surface,(160,220,255),(x+10,y+10,ts-20,ts-20),1)
            arr=(200,235,255)
            pygame.draw.line(surface,arr,(cx,cy+8),(cx,cy-8),2)
            pygame.draw.polygon(surface,arr,[(cx,cy-12),(cx-5,cy-6),(cx+5,cy-6)])


class Camera:
    def __init__(self, sw, sh, mc, mr, ts):
        self.sw=sw; self.sh=sh
        self.mw=mc*ts; self.mh=mr*ts
        self.ox=0; self.oy=0

    def update(self, px, py):
        ts=TILE_SIZE
        self.ox=max(self.sw-self.mw,min(0,self.sw//2-int(px)-ts//2))
        self.oy=max(self.sh-self.mh,min(0,self.sh//2-int(py)-ts//2))


def _draw_prompt(surface, font, cx, cy, text, col=(210,185,120), border=(90,70,42)):
    s=font.render(text,True,col)
    bg=pygame.Surface((s.get_width()+16,s.get_height()+8),pygame.SRCALPHA)
    bg.fill((10,8,5,180))
    bx=cx-bg.get_width()//2; by=cy-bg.get_height()-4
    surface.blit(bg,(bx,by))
    pygame.draw.rect(surface,border,(bx,by,bg.get_width(),bg.get_height()),1)
    surface.blit(s,(bx+8,by+4))

def _draw_e_prompt(surface, font, cx, cy):
    _draw_prompt(surface,font,cx,cy,"[ E ]  Open")

def _draw_exit_prompt(surface, font, cx, cy, locked):
    _draw_prompt(surface,font,cx,cy,
                 "[ F ]  "+("Use Exit Key" if locked else "Leave Dungeon"),
                 col=(220,200,100),border=(160,130,50))

def _draw_key_prompt(surface, font, cx, cy):
    _draw_prompt(surface,font,cx,cy,"[ E ]  Use Key",border=(140,110,42))


class GameScene:
    def __init__(self, screen, inventory, player_stats=None, game_state=None):
        self.inventory=inventory
        self.player_stats=player_stats
        self.game_state=game_state
        self.screen=screen
        self.W,self.H=screen.get_size()
        self.clock=pygame.time.Clock()
        self.time=0.0

        self.tile_surf=build_tile_surface()
        self.torches=[Torch(c,r) for c,r in TORCH_POSITIONS]
        self.vignette=self._build_vignette()
        self.player=Player(PLAYER_SPAWN[0],PLAYER_SPAWN[1],TILE_SIZE)
        self.goblins=[spawn_patrol('goblin',p,TILE_SIZE) for p in GOBLIN_PATROLS]

        self.boss = spawn_patrol('goblin_king',BOSS_PATROL,TILE_SIZE)
        self.boss_defeated = False

        from src.scenes.chest_scene import (CandleItem,PotionItem,ShieldItem,
                                             SunSwordItem,KeyItem,GoldItem,ExitKeyItem,IronIngotItem)
        import random as _r

        def _rand(n=2):
            pool=[PotionItem,CandleItem,lambda:GoldItem(_r.choice([5,10,15])),
                  lambda:IronIngotItem() if _r.random()<0.35 else PotionItem()]
            return [_r.choice(pool)() for _ in range(n)]

        chest_items=[
            [PotionItem(), KeyItem("key_r1r2"), PotionItem()],
            _rand(3),
            [KeyItem("key_r2r3")] + _rand(2),
            _rand(3),
            [KeyItem("key_r3f")] + _rand(2),
            _rand(3),
            _rand(3),
            [ExitKeyItem(), ShieldItem(), GoldItem(30)],
        ]
        self.chests=[Chest(col,row,items)
                     for (col,row),items in zip(CHEST_POSITIONS,chest_items)]

        self.font_small=pygame.font.SysFont("courier new",15)

        if player_stats and game_state:
            from src.ui.hud import HUD
            self._hud = HUD(screen)
        else:
            self._hud = None
        self.COMBAT_COOLDOWN=1.5
        self.combat_cooldown=self.COMBAT_COOLDOWN

        self._nearby_chest=None
        self._nearby_door=None
        self._nearby_exit=None

        self.exit_tile=ExitTile(EXIT_TILE[0],EXIT_TILE[1])
        self.locked_doors=[LockedDoor(col,row,ori,kid)
                           for (col,row,ori),kid in zip(LOCKED_DOORS,DOOR_KEY_IDS)]
        self._defeated_goblin_idx=None
        self._potion_msg       = ""
        self._potion_msg_timer = 0.0

        self.visited=set()
        self.VISION_RADIUS=4
        _hud_h = 52 if (player_stats and game_state) else 0
        self.camera=Camera(self.W,self.H-_hud_h,COLS,ROWS,TILE_SIZE)
        self.camera.update(self.player.px,self.player.py)

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
                    if 0<=row<ROWS and 0<=col<COLS:
                        self.visited.add((col,row))

    def _draw_ambient_darkness(self):
        ts=TILE_SIZE; ox=self.camera.ox; oy=self.camera.oy
        px=ox+int(self.player.px)+ts//2; py=oy+int(self.player.py)+ts//2

        # Build a darkness mask — start fully transparent, we'll paint darkness onto it
        dark=pygame.Surface((self.W,self.H),pygame.SRCALPHA)

        # Player vision gradient — draw from edge inward so centre stays clear
        # Draw largest (darkest) ring first, smallest (clearest) last
        vision_r = int(ts*5.5)
        steps = 32
        for i in range(steps, 0, -1):
            r = int(vision_r * i / steps)
            a = int(190 * ((i / steps) ** 1.4))
            pygame.draw.circle(dark, (0, 0, 0, a), (px, py), r)

        # Flood fill darkness everywhere outside the vision circle
        # by drawing a big dark rect and then cutting torch holes in it
        outer = pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        outer.fill((0,0,0,190))

        # Cut torch holes in the outer darkness
        for torch in self.torches:
            bri=torch.flame_brightness(self.time)
            cx=ox+torch.col*ts+ts//2; cy=oy+torch.row*ts+ts//2
            pygame.draw.circle(outer,(0,0,0,0),(cx,cy),int(ts*2.2*bri))

        # Cut out the full vision circle from outer so our gradient shows through
        pygame.draw.circle(outer,(0,0,0,0),(px,py),vision_r)

        # Composite: outer darkness on top, then gradient fills the vision area
        self.screen.blit(dark,(0,0))
        self.screen.blit(outer,(0,0))

    def _check_combat(self):
        ts=TILE_SIZE
        pcx=self.player.px+ts//2; pcy=self.player.py+ts//2
        for g in self.goblins:
            if math.hypot(g.px+ts//2-pcx,g.py+ts//2-pcy)<ts*0.75:
                return True
        return False

    def _check_boss_combat(self):
        if self.boss_defeated: return False
        ts=TILE_SIZE
        pcx=self.player.px+ts//2; pcy=self.player.py+ts//2
        return math.hypot(self.boss.px+ts//2-pcx,self.boss.py+ts//2-pcy)<ts*0.85

    def _check_nearby_chest(self):
        for chest in self.chests:
            if not chest.opened and len(chest.items)>0 and \
               chest.is_adjacent(self.player.tile_col,self.player.tile_row):
                return chest
        return None

    def _check_nearby_door(self):
        for door in self.locked_doors:
            if door.locked and door.is_adjacent(
                    self.player.tile_col,self.player.tile_row):
                return door
        return None

    def _check_nearby_exit(self):
        if self.exit_tile.is_adjacent(self.player.tile_col,self.player.tile_row):
            return self.exit_tile
        return None

    def _draw_boss(self, ox, oy):
        ts     = TILE_SIZE
        margin = (ts - int(ts*0.9)) // 2
        draw_x = int(self.boss.px) + ox + margin - ts//4
        draw_y = int(self.boss.py) + oy + margin - ts//2

        sh = pygame.Surface((int(ts*1.4), ts//3), pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,60),(0,0,int(ts*1.4),ts//3))
        self.screen.blit(sh,(draw_x-ts//8, draw_y+int(ts*1.1)))

        size = int(ts * 1.4)
        s = size; cx = draw_x + s//2; cy = draw_y + s//2
        bob = math.sin(self.time*2.0)*3

        bw,bh = int(s*0.7),int(s*0.55)
        bx = cx-bw//2; by = cy-bh//4+int(bob)
        pygame.draw.rect(self.screen,(65,128,50),(bx,by,bw,bh))
        pygame.draw.rect(self.screen,(40,85,30),(bx,by,bw,bh),2)
        for i in range(3):
            ax=bx+4+i*(bw//3)
            pygame.draw.rect(self.screen,(80,65,40),(ax,by+4,bw//3-4,bh//3))

        lw,lh=s//3,int(s*0.4)
        lby=by+bh-4+int(bob)
        pygame.draw.rect(self.screen,(50,100,40),(cx-lw-4,lby,lw,lh))
        pygame.draw.rect(self.screen,(50,100,40),(cx+4,lby,lw,lh))

        arm_y=by+bh//5
        pygame.draw.line(self.screen,(55,105,42),(cx-bw//2,arm_y),
                         (cx-bw//2-s//3,arm_y-s//5),5)
        club_x=cx-bw//2-s//3; club_y=arm_y-s//5
        pygame.draw.line(self.screen,(110,78,42),(club_x,club_y),
                         (club_x-s//4,club_y-s//3),6)
        pygame.draw.circle(self.screen,(90,62,30),(club_x-s//4,club_y-s//3),s//6)

        hr=int(s*0.32); hx=cx; hy=by-hr+int(bob)
        pygame.draw.circle(self.screen,(80,148,60),(hx,hy),hr)
        pygame.draw.circle(self.screen,(55,105,42),(hx,hy),hr,2)

        cp=[(hx-hr,hy-hr+4),(hx-hr+6,hy-hr-10),(hx-6,hy-hr-2),
            (hx,hy-hr-14),(hx+6,hy-hr-2),(hx+hr-6,hy-hr-10),(hx+hr,hy-hr+4)]
        pygame.draw.polygon(self.screen,(80,68,40),cp)
        pygame.draw.polygon(self.screen,(110,92,55),cp,2)

        eox=hr//2
        pygame.draw.circle(self.screen,(240,50,30),(hx-eox,hy),4)
        pygame.draw.circle(self.screen,(240,50,30),(hx+eox,hy),4)

        name_s = self.font_small.render("GOBLIN KING",True,(240,80,60))
        self.screen.blit(name_s,(cx-name_s.get_width()//2,draw_y-name_s.get_height()-4))

        gr=int(ts*2.5)
        glow=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
        pulse=0.4+0.3*math.sin(self.time*2.5)
        pygame.draw.circle(glow,(180,30,30,int(22*pulse)),(gr,gr),gr)
        self.screen.blit(glow,(cx-gr,cy-gr),special_flags=pygame.BLEND_RGBA_ADD)

    def run(self):
        while True:
            dt=self.clock.tick(60)/1000.0; self.time+=dt

            for event in pygame.event.get():
                if event.type==pygame.QUIT: return "exit"
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: return "pause"
                    if event.key==pygame.K_i:      return "inventory"
                    if event.key==pygame.K_m:      return "map"
                    if event.key==pygame.K_f:
                        if self._nearby_exit:
                            return "use_exit_key" if self._nearby_exit.locked else "town"
                    if event.key==pygame.K_e:
                        if self._nearby_chest:
                            self._chest_to_open=self._nearby_chest
                            return "chest"
                        if self._nearby_door and self._nearby_door.locked:
                            return "use_key"
                    if event.key==pygame.K_p:
                        from src.scenes.chest_scene import PotionItem
                        from src.scenes.combat_scene import POTION_HEAL, PLAYER_MAX_HP
                        max_hp = self.player_stats.max_hp if self.player_stats else PLAYER_MAX_HP
                        cur_hp = self.game_state.player_hp if self.game_state else max_hp
                        if not self.inventory.has(PotionItem):
                            self._potion_msg = "No potions left!"
                        elif cur_hp >= max_hp:
                            self._potion_msg = "Already at full HP!"
                        else:
                            self.inventory.remove_one(PotionItem)
                            healed = min(POTION_HEAL, max_hp - cur_hp)
                            if self.game_state:
                                self.game_state.player_hp = cur_hp + healed
                            self._potion_msg = f"Used potion. +{healed} HP  ({cur_hp+healed}/{max_hp})"
                        self._potion_msg_timer = 2.0

            keys=pygame.key.get_pressed()
            for key,(dc,dr) in MOVE_KEYS.items():
                if keys[key]:
                    self.player.try_move(dc,dr,ROOM_MAP); break

            self.player.update(dt)
            self._update_visited()

            for door in self.locked_doors:
                if not door.locked: continue
                for tc,tr in [(door.col,door.row),
                              (door.col+(1 if door.orientation=='h' else 0),
                               door.row+(1 if door.orientation=='v' else 0)),
                              (door.col+(2 if door.orientation=='h' else 0),
                               door.row+(2 if door.orientation=='v' else 0))]:
                    if (self.player.tile_col==tc and self.player.tile_row==tr):
                        self.player.tile_col=self.player._prev_col
                        self.player.tile_row=self.player._prev_row
                        self.player.target_px=float(self.player._prev_col*TILE_SIZE)
                        self.player.target_py=float(self.player._prev_row*TILE_SIZE)
                        self.player.px=self.player.target_px
                        self.player.py=self.player.target_py
                        self.player.moving=False

            for g in self.goblins:
                g.update(dt,self.player.tile_col,self.player.tile_row)
            if not self.boss_defeated:
                self.boss.update(dt,self.player.tile_col,self.player.tile_row)
            self.combat_cooldown=max(0.0,self.combat_cooldown-dt)
            self._potion_msg_timer=max(0.0,self._potion_msg_timer-dt)
            self.camera.update(self.player.px,self.player.py)

            if not self.player.moving:
                self._nearby_chest=self._check_nearby_chest()
                self._nearby_door=self._check_nearby_door()
                self._nearby_exit=self._check_nearby_exit()
            else:
                self._nearby_chest=self._nearby_door=self._nearby_exit=None

            if (not self.player.moving and self.combat_cooldown<=0.0
                    and self._check_combat()):
                return "combat"
            if (not self.player.moving and self.combat_cooldown<=0.0
                    and self._check_boss_combat()):
                return "boss_combat"

            ox=self.camera.ox; oy=self.camera.oy
            ts=TILE_SIZE
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
            for g in self.goblins:
                g.draw(self.screen,ox,oy)
            if not self.boss_defeated:
                self._draw_boss(ox,oy)
            self.player.draw(self.screen,ox,oy)

            if self._nearby_exit:
                ecx=ox+self.exit_tile.col*ts+ts//2
                ecy=oy+self.exit_tile.row*ts
                _draw_exit_prompt(self.screen,self.font_small,ecx,ecy,self._nearby_exit.locked)
            if self._nearby_door and self._nearby_door.locked:
                dcx=ox+self._nearby_door.col*ts+ts//2
                dcy=oy+self._nearby_door.row*ts
                _draw_key_prompt(self.screen,self.font_small,dcx,dcy)
            if self._nearby_chest:
                ccx=ox+self._nearby_chest.col*ts+ts//2
                ccy=oy+self._nearby_chest.row*ts
                _draw_e_prompt(self.screen,self.font_small,ccx,ccy)

            from src.scenes.chest_scene import PotionItem
            if self.inventory.has(PotionItem):
                count = self.inventory.count(PotionItem)
                ph_s  = self.font_small.render(f"[ P ]  Use Potion  (x{count})", True, (160,210,140))
                ph_bg = pygame.Surface((ph_s.get_width()+16,ph_s.get_height()+8),pygame.SRCALPHA)
                ph_bg.fill((10,8,5,160))
                phx = self.W - ph_s.get_width() - 28; phy = self.H - 80
                self.screen.blit(ph_bg,(phx-8,phy-4))
                self.screen.blit(ph_s,(phx,phy))

            self.screen.blit(self.vignette,(0,0))

            if self._potion_msg and self._potion_msg_timer > 0:
                alpha = min(1.0, self._potion_msg_timer / 0.4)
                col   = (120,210,120) if "Used" in self._potion_msg else (210,100,80)
                ms    = self.font_small.render(self._potion_msg, True, col)
                bg    = pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
                bg.fill((10,8,5,int(200*alpha)))
                bx2   = self.W//2-bg.get_width()//2; by2 = self.H-90
                self.screen.blit(bg,(bx2,by2))
                pygame.draw.rect(self.screen,col,(bx2,by2,bg.get_width(),bg.get_height()),1)
                ms.set_alpha(int(255*alpha))
                self.screen.blit(ms,(bx2+10,by2+4))

            if self.game_state:
                from src.scenes.chest_scene import GoldItem
                gold = sum(self.inventory.stack_count(it)
                           for it in self.inventory.items if isinstance(it, GoldItem))
                self.game_state.gold_collected = gold

            if self._hud and self.player_stats and self.game_state:
                self._hud.update(dt, self.player_stats, self.game_state)
                self._hud.draw(
                    self.player_stats, self.game_state,
                    goblins_remaining=len(self.goblins),
                    location_name="Dungeon — Ashenvale",
                    boss_alive=not self.boss_defeated,
                )

            pygame.display.flip()