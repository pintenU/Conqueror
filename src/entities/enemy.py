import pygame
import math
import random


# ---------------------------------------------------------------------------
# Base Enemy class — all enemies share this structure
# ---------------------------------------------------------------------------

class Enemy:
    """
    Data-driven enemy. Constructed from an enemy definition dict
    (loaded from enemies.json via EntityFactory).
    Handles movement, patrol AI and drawing.
    """

    def __init__(self, col: int, row: int, tile_size: int,
                 patrol_tiles: list, definition: dict):
        self.tile_size    = tile_size
        self.patrol_tiles = patrol_tiles
        self.definition   = definition

        # Stats from definition
        self.enemy_type   = definition["name"]
        self.display_name = definition["display_name"]
        self.color        = tuple(definition["color"])
        self.move_speed   = definition.get("speed", 2.2)
        self.is_boss      = definition.get("is_boss", False)

        # Position
        self.tile_col  = col
        self.tile_row  = row
        self.px        = float(col * tile_size)
        self.py        = float(row * tile_size)
        self.target_px = self.px
        self.target_py = self.py
        self.moving    = False

        # Patrol state
        self._patrol_idx  = 0
        self._patrol_wait = 0.0
        self.PATROL_WAIT  = 1.2

        # Visual
        self._anim_time = 0.0
        self._phase     = random.uniform(0, math.tau)

    # ------------------------------------------------------------------ #
    # Movement / AI (same patrol logic as original Goblin)
    # ------------------------------------------------------------------ #

    def update(self, dt: float, player_col: int, player_row: int):
        self._anim_time += dt

        if self.moving:
            dx = self.target_px - self.px
            dy = self.target_py - self.py
            dist = math.hypot(dx, dy)
            step = self.move_speed * self.tile_size * dt
            if dist <= step:
                self.px = self.target_px
                self.py = self.target_py
                self.tile_col = int(self.target_px / self.tile_size)
                self.tile_row = int(self.target_py / self.tile_size)
                self.moving   = False
            else:
                self.px += dx / dist * step
                self.py += dy / dist * step
        else:
            self._patrol_wait -= dt
            if self._patrol_wait <= 0:
                self._advance_patrol(player_col, player_row)

    def _advance_patrol(self, player_col, player_row):
        if not self.patrol_tiles:
            return
        next_idx = (self._patrol_idx + 1) % len(self.patrol_tiles)
        nc, nr   = self.patrol_tiles[next_idx]
        # Don't walk onto player tile
        if nc == player_col and nr == player_row:
            self._patrol_wait = 0.3
            return
        self._patrol_idx  = next_idx
        self.target_px    = float(nc * self.tile_size)
        self.target_py    = float(nr * self.tile_size)
        self.moving       = True
        self._patrol_wait = self.PATROL_WAIT

    # ------------------------------------------------------------------ #
    # Drawing — each enemy type has its own look
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface, ox: int, oy: int):
        draw_x = int(self.px) + ox
        draw_y = int(self.py) + oy
        t = self._anim_time

        etype = self.enemy_type.lower().replace(" ", "_")
        if   etype == "goblin":    _draw_goblin(surface, draw_x, draw_y, t, self.tile_size)
        elif etype == "skeleton":  _draw_skeleton(surface, draw_x, draw_y, t, self.tile_size)
        elif etype == "troll":     _draw_troll(surface, draw_x, draw_y, t, self.tile_size)
        elif etype == "dark_mage": _draw_dark_mage(surface, draw_x, draw_y, t, self.tile_size)
        else:                      _draw_generic(surface, draw_x, draw_y, t,
                                                 self.tile_size, self.color)


# ---------------------------------------------------------------------------
# Per-enemy sprite drawers
# ---------------------------------------------------------------------------

def _draw_goblin(surf, x, y, t, ts):
    cx = x + ts//2; cy = y + ts//2
    bob = math.sin(t*3)*2
    # Shadow
    pygame.draw.ellipse(surf,(0,0,0,60),(cx-12,cy+14,24,8))
    # Legs
    for lx in [cx-6,cx+2]:
        pygame.draw.rect(surf,(50,100,40),(lx,cy+int(bob),8,12))
    # Body
    pygame.draw.ellipse(surf,(65,128,50),(cx-12,cy-10+int(bob),24,22))
    pygame.draw.ellipse(surf,(45,95,35),(cx-12,cy-10+int(bob),24,22),1)
    # Head
    pygame.draw.circle(surf,(80,148,60),(cx,cy-18+int(bob)),11)
    pygame.draw.circle(surf,(55,105,42),(cx,cy-18+int(bob)),11,1)
    # Ears
    for ex,ew in [(cx-12,6),(cx+6,6)]:
        pygame.draw.polygon(surf,(80,148,60),[(ex,cy-18+int(bob)),
                                               (ex+ew//2,cy-28+int(bob)),
                                               (ex+ew,cy-18+int(bob))])
    # Eyes
    for ex in [cx-4,cx+3]:
        pygame.draw.circle(surf,(20,12,5),(ex,cy-19+int(bob)),3)
        pygame.draw.circle(surf,(255,180,50),(ex,cy-19+int(bob)),1)
    # Arms
    for ax,adx in [(cx-14,cx-18),(cx+14,cx+18)]:
        pygame.draw.line(surf,(65,128,50),(ax,cy-4+int(bob)),(adx,cy+2+int(bob)),4)


def _draw_skeleton(surf, x, y, t, ts):
    cx = x + ts//2; cy = y + ts//2
    bob = math.sin(t*3.5)*2
    bone = (200,195,175); dark = (140,135,120)
    # Shadow
    pygame.draw.ellipse(surf,(0,0,0,50),(cx-10,cy+14,20,6))
    # Legs — thin bones
    for lx,angle in [(cx-7,-0.15),(cx+3,0.15)]:
        pygame.draw.line(surf,bone,(lx,cy+int(bob)),(lx+int(angle*20),cy+14+int(bob)),3)
    # Ribcage
    for i in range(3):
        pygame.draw.arc(surf,bone,(cx-10,cy-8+i*6+int(bob),20,8),0,math.pi,2)
    # Spine
    pygame.draw.line(surf,dark,(cx,cy-10+int(bob)),(cx,cy+int(bob)),2)
    # Head — round skull
    pygame.draw.circle(surf,bone,(cx,cy-22+int(bob)),11)
    pygame.draw.circle(surf,dark,(cx,cy-22+int(bob)),11,1)
    # Hollow eye sockets
    for ex in [cx-4,cx+4]:
        pygame.draw.circle(surf,(15,10,5),(ex,cy-23+int(bob)),4)
    # Teeth
    for tx in range(cx-5,cx+6,3):
        pygame.draw.rect(surf,bone,(tx,cy-14+int(bob),2,4))
    # Arms
    for ax,adx in [(cx-11,cx-16),(cx+11,cx+16)]:
        pygame.draw.line(surf,bone,(ax,cy-6+int(bob)),(adx,cy+int(bob)),3)


def _draw_troll(surf, x, y, t, ts):
    cx = x + ts//2; cy = y + ts//2
    bob = math.sin(t*1.8)*3
    col = (90,130,80); dark = (60,90,55)
    # Shadow — big
    pygame.draw.ellipse(surf,(0,0,0,60),(cx-18,cy+16,36,10))
    # Thick legs
    for lx in [cx-10,cx+4]:
        pygame.draw.rect(surf,dark,(lx,cy+int(bob),10,16))
    # Huge body
    pygame.draw.ellipse(surf,col,(cx-18,cy-14+int(bob),36,28))
    pygame.draw.ellipse(surf,dark,(cx-18,cy-14+int(bob),36,28),2)
    # Big head
    pygame.draw.circle(surf,col,(cx,cy-24+int(bob)),14)
    pygame.draw.circle(surf,dark,(cx,cy-24+int(bob)),14,2)
    # Flat nose
    pygame.draw.ellipse(surf,dark,(cx-4,cy-24+int(bob),8,5))
    # Eyes — small beady
    for ex in [cx-5,cx+5]:
        pygame.draw.circle(surf,(30,20,10),(ex,cy-27+int(bob)),3)
        pygame.draw.circle(surf,(200,80,20),(ex,cy-27+int(bob)),1)
    # Club arm
    pygame.draw.line(surf,dark,(cx+16,cy-8+int(bob)),(cx+24,cy-20+int(bob)),6)
    pygame.draw.circle(surf,(70,60,40),(cx+24,cy-22+int(bob)),7)


def _draw_dark_mage(surf, x, y, t, ts):
    cx = x + ts//2; cy = y + ts//2
    bob = math.sin(t*2)*2
    robe = (80,35,120); dark = (50,20,80)
    pulse = 0.6+0.4*math.sin(t*3)
    orb_col = (int(160*pulse),int(80*pulse),int(240*pulse))
    # Shadow — faint, floats
    pygame.draw.ellipse(surf,(0,0,0,40),(cx-10,cy+12+int(bob)//2,20,6))
    # Flowing robe — triangle
    pygame.draw.polygon(surf,robe,[(cx-12,cy-4+int(bob)),
                                    (cx,cy+16+int(bob)),
                                    (cx+12,cy-4+int(bob))])
    pygame.draw.polygon(surf,dark,[(cx-12,cy-4+int(bob)),
                                    (cx,cy+16+int(bob)),
                                    (cx+12,cy-4+int(bob))],1)
    # Body
    pygame.draw.ellipse(surf,robe,(cx-8,cy-14+int(bob),16,18))
    # Hood
    pygame.draw.polygon(surf,dark,[(cx-10,cy-12+int(bob)),
                                    (cx,cy-30+int(bob)),
                                    (cx+10,cy-12+int(bob))])
    # Glowing eyes in hood
    for ex in [cx-3,cx+3]:
        pygame.draw.circle(surf,orb_col,(ex,cy-20+int(bob)),3)
    # Staff + orb
    pygame.draw.line(surf,dark,(cx+10,cy-10+int(bob)),(cx+16,cy+8+int(bob)),3)
    pygame.draw.circle(surf,orb_col,(cx+10,cy-12+int(bob)),6)
    pygame.draw.circle(surf,(255,255,255),(cx+10,cy-12+int(bob)),3)
    # Magic aura
    gs = pygame.Surface((40,40),pygame.SRCALPHA)
    pygame.draw.circle(gs,(*orb_col,int(25*pulse)),(20,20),18)
    surf.blit(gs,(cx-20,cy-30+int(bob)),special_flags=pygame.BLEND_RGBA_ADD)


def _draw_generic(surf, x, y, t, ts, color):
    cx = x + ts//2; cy = y + ts//2
    bob = math.sin(t*2.5)*2
    pygame.draw.ellipse(surf,color,(cx-12,cy-12+int(bob),24,28))
    pygame.draw.ellipse(surf,tuple(max(0,c-40) for c in color),
                        (cx-12,cy-12+int(bob),24,28),2)
    pygame.draw.circle(surf,color,(cx,cy-20+int(bob)),10)
    for ex in [cx-3,cx+3]:
        pygame.draw.circle(surf,(20,12,5),(ex,cy-21+int(bob)),2)