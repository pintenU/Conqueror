import pygame
import math
import random


def _lerp_col(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))


class Enemy:
    def __init__(self, col, row, tile_size, patrol_tiles, definition):
        self.tile_size    = tile_size
        self.patrol_tiles = patrol_tiles
        self.definition   = definition
        self.enemy_type   = definition["name"]
        self.display_name = definition["display_name"]
        self.color        = tuple(definition["color"])
        self.move_speed   = definition.get("speed", 2.2)
        self.is_boss      = definition.get("is_boss", False)
        self.tile_col  = col; self.tile_row  = row
        self.px        = float(col * tile_size)
        self.py        = float(row * tile_size)
        self.target_px = self.px; self.target_py = self.py
        self.moving    = False
        self._patrol_idx  = 0; self._patrol_wait = 0.0
        self.PATROL_WAIT  = 1.2
        self._anim_time = 0.0
        self._phase     = random.uniform(0, math.tau)

    def update(self, dt, player_col, player_row):
        self._anim_time += dt
        if self.moving:
            dx = self.target_px - self.px; dy = self.target_py - self.py
            dist = math.hypot(dx, dy)
            step = self.move_speed * self.tile_size * dt
            if dist <= step:
                self.px = self.target_px; self.py = self.target_py
                self.tile_col = int(self.target_px / self.tile_size)
                self.tile_row = int(self.target_py / self.tile_size)
                self.moving   = False
            else:
                self.px += dx/dist*step; self.py += dy/dist*step
        else:
            self._patrol_wait -= dt
            if self._patrol_wait <= 0:
                self._advance_patrol(player_col, player_row)

    def _advance_patrol(self, player_col, player_row):
        if not self.patrol_tiles: return
        next_idx = (self._patrol_idx+1) % len(self.patrol_tiles)
        nc,nr = self.patrol_tiles[next_idx]
        if nc==player_col and nr==player_row:
            self._patrol_wait=0.3; return
        self._patrol_idx  = next_idx
        self.target_px    = float(nc*self.tile_size)
        self.target_py    = float(nr*self.tile_size)
        self.moving       = True
        self._patrol_wait = self.PATROL_WAIT

    def draw(self, surface, ox, oy):
        draw_x = int(self.px)+ox; draw_y = int(self.py)+oy
        t = self._anim_time
        etype = self.enemy_type.lower().replace(" ","_")
        ts = self.tile_size
        if   etype=="goblin":            _draw_goblin(surface,draw_x,draw_y,t,ts)
        elif etype=="skeleton":          _draw_skeleton(surface,draw_x,draw_y,t,ts)
        elif etype=="troll":             _draw_troll(surface,draw_x,draw_y,t,ts)
        elif etype=="dark_mage":         _draw_dark_mage(surface,draw_x,draw_y,t,ts)
        elif etype=="imp":               _draw_imp(surface,draw_x,draw_y,t,ts)
        elif etype=="dire_rat":          _draw_dire_rat(surface,draw_x,draw_y,t,ts)
        elif etype=="orc_warrior":       _draw_orc_warrior(surface,draw_x,draw_y,t,ts)
        elif etype=="stone_golem":       _draw_stone_golem(surface,draw_x,draw_y,t,ts)
        elif etype=="werewolf":          _draw_werewolf(surface,draw_x,draw_y,t,ts)
        elif etype=="lich":              _draw_lich(surface,draw_x,draw_y,t,ts)
        elif etype=="bone_lord":         _draw_bone_lord(surface,draw_x,draw_y,t,ts)
        elif etype=="mountain_king":     _draw_mountain_king(surface,draw_x,draw_y,t,ts)
        elif etype=="archmage":          _draw_archmage(surface,draw_x,draw_y,t,ts)
        elif etype=="inferno_duke":      _draw_inferno_duke(surface,draw_x,draw_y,t,ts)
        elif etype=="rat_king":          _draw_rat_king(surface,draw_x,draw_y,t,ts)
        elif etype=="warchief_grommak":  _draw_warchief_grommak(surface,draw_x,draw_y,t,ts)
        elif etype=="ancient_colossus":  _draw_ancient_colossus(surface,draw_x,draw_y,t,ts)
        elif etype=="the_alpha":         _draw_the_alpha(surface,draw_x,draw_y,t,ts)
        elif etype=="lich_king":         _draw_lich_king(surface,draw_x,draw_y,t,ts)
        else:                            _draw_generic(surface,draw_x,draw_y,t,ts,self.color)


# ---------------------------------------------------------------------------
# Draw functions — ALL values scale with ts so they work at any size
# ---------------------------------------------------------------------------

def _draw_goblin(surf, x, y, t, ts):
    s  = ts          # unit = ts
    cx = x + s//2; cy = y + s//2
    bob = int(math.sin(t*3) * max(2, s//24))
    # Shadow
    sh = pygame.Surface((s, s//4), pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,50),(0,0,s,s//4))
    surf.blit(sh,(cx-s//2, cy+s//3))
    # Legs
    lw = max(4, s//12); lh = max(6, s//4)
    for lx in [cx-lw-2, cx+2]:
        pygame.draw.rect(surf,(50,100,40),(lx, cy+s//8+bob, lw, lh))
    # Body
    bw=max(12,s//2); bh=max(10,s//2)
    pygame.draw.ellipse(surf,(65,128,50),(cx-bw//2,cy-bh//4+bob,bw,bh))
    pygame.draw.ellipse(surf,(45,95,35),(cx-bw//2,cy-bh//4+bob,bw,bh),max(1,s//48))
    # Head
    hr=max(6,s//4)
    pygame.draw.circle(surf,(80,148,60),(cx,cy-hr+bob),hr)
    pygame.draw.circle(surf,(55,105,42),(cx,cy-hr+bob),hr,max(1,s//48))
    # Ears
    ep=max(4,s//12)
    for ex,sign in [(cx-hr,-1),(cx+hr,1)]:
        pygame.draw.polygon(surf,(80,148,60),[
            (ex,cy-hr+bob),(ex+sign*ep,cy-hr-ep*2+bob),(ex+sign*ep*2,cy-hr+bob)])
    # Eyes
    er=max(2,s//24)
    eox=max(3,hr//2)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(20,12,5),(ex,cy-hr+bob),er+1)
        pygame.draw.circle(surf,(255,180,50),(ex,cy-hr+bob),er-1)
    # Arms
    aw=max(2,s//24)
    for ax,adx in [(cx-bw//2,cx-bw//2-s//6),(cx+bw//2,cx+bw//2+s//6)]:
        pygame.draw.line(surf,(65,128,50),(ax,cy-bh//8+bob),(adx,cy+bob),aw)


def _draw_skeleton(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*3.5)*max(2,s//24))
    bone=(200,195,175); dark=(140,135,120)
    # Shadow
    sh = pygame.Surface((s,s//5),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,45),(0,0,s,s//5))
    surf.blit(sh,(cx-s//2,cy+s//3))
    # Legs — thin, from pelvis down
    lw=max(2,s//20)
    pelvis_y = cy + s//8 + bob
    for lx,angle in [(cx-s//10,-0.15),(cx+s//10,0.15)]:
        foot_x = lx+int(angle*s//3)
        foot_y = pelvis_y+s//3
        pygame.draw.line(surf,bone,(lx,pelvis_y),(foot_x,foot_y),lw)
        # Foot
        pygame.draw.line(surf,bone,(foot_x,foot_y),(foot_x+int(angle*s//8),foot_y),lw)
    # Pelvis bone
    pygame.draw.line(surf,dark,(cx-s//8,pelvis_y),(cx+s//8,pelvis_y),max(2,s//24))
    # Spine — up from pelvis
    spine_top = cy - s//5 + bob
    pygame.draw.line(surf,dark,(cx,pelvis_y),(cx,spine_top),max(2,s//24))
    # Ribcage — 3 curved ribs each side
    rib_w = max(1,s//28)
    for i in range(3):
        rib_y = spine_top + i*(s//10)
        spread = max(6,s//5 - i*(s//20))
        pygame.draw.arc(surf,bone,(cx-spread,rib_y,spread,s//12),0,math.pi,rib_w)
        pygame.draw.arc(surf,bone,(cx,rib_y,spread,s//12),0,math.pi,rib_w)
    # Arms — from shoulder outward
    shoulder_y = spine_top + s//20
    aw = max(2,s//28)
    pygame.draw.line(surf,bone,(cx-s//8,shoulder_y),(cx-s//3,shoulder_y+s//8),aw)
    pygame.draw.line(surf,bone,(cx+s//8,shoulder_y),(cx+s//3,shoulder_y+s//8),aw)
    # Skull — properly sized relative to body
    hr = max(5,s//6)
    skull_y = spine_top - hr - max(2,s//24)
    pygame.draw.circle(surf,bone,(cx,skull_y),hr)
    pygame.draw.circle(surf,dark,(cx,skull_y),hr,max(1,s//48))
    # Jaw
    jaw_w = max(6,hr)
    pygame.draw.arc(surf,dark,(cx-jaw_w//2,skull_y,jaw_w,hr//2),math.pi,2*math.pi,max(1,s//48))
    # Eye sockets
    er=max(2,s//28); eox=max(3,hr//3)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(15,10,5),(ex,skull_y-hr//6),er)
    # Teeth
    tw=max(1,s//60); th=max(3,s//20)
    for tx in range(cx-hr//2+2,cx+hr//2-2,max(2,s//30)):
        pygame.draw.rect(surf,bone,(tx,skull_y+hr//3,tw,th))


def _draw_troll(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*1.8)*max(3,s//16))
    col=(90,130,80); dark=(60,90,55); boot=(55,80,40)
    # Shadow
    sh = pygame.Surface((s,s//4),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,60),(0,0,s,s//4))
    surf.blit(sh,(cx-s//2,cy+s*2//5))
    # Boots/feet
    bfw=max(8,s//6); bfh=max(5,s//10)
    for bx in [cx-s//5-bfw//2, cx+s//5-bfw//2]:
        pygame.draw.rect(surf,boot,(bx,cy+s//3+bob,bfw,bfh))
    # Thick legs
    lw=max(7,s//7); lh=max(12,s//3)
    for lx in [cx-s//5-lw//2, cx+s//5-lw//2]:
        pygame.draw.rect(surf,dark,(lx,cy+bob,lw,lh))
    # Massive barrel body
    bw=max(22,s*4//5); bh=max(18,s*3//5)
    pygame.draw.ellipse(surf,col,(cx-bw//2,cy-bh//2+bob,bw,bh))
    pygame.draw.ellipse(surf,dark,(cx-bw//2,cy-bh//2+bob,bw,bh),max(2,s//32))
    # Belly crease
    pygame.draw.arc(surf,dark,(cx-bw//3,cy-bh//6+bob,bw*2//3,bh//4),0,math.pi,max(1,s//48))
    # Arms — thick, one raised with club
    aw=max(5,s//10)
    # Left arm — raised holding club
    pygame.draw.line(surf,col,(cx-bw//2+s//16,cy-bh//4+bob),
                     (cx-bw//2-s//5,cy-bh//2-s//8+bob),aw)
    # Club
    cl=max(3,s//16)
    club_tx=cx-bw//2-s//5; club_ty=cy-bh//2-s//8+bob
    pygame.draw.line(surf,dark,(club_tx,club_ty),(club_tx-s//8,club_ty-s//4),cl)
    cr=max(6,s//9)
    pygame.draw.circle(surf,(70,60,40),(club_tx-s//8,club_ty-s//4),cr)
    pygame.draw.circle(surf,(90,75,50),(club_tx-s//8,club_ty-s//4),cr,max(1,s//48))
    # Right arm — hanging
    pygame.draw.line(surf,col,(cx+bw//2-s//16,cy-bh//4+bob),
                     (cx+bw//2+s//8,cy+bob),aw)
    # Thick neck
    nw=max(8,s//8); nh=max(6,s//10)
    pygame.draw.rect(surf,col,(cx-nw//2,cy-bh//2-nh+bob,nw,nh))
    # Big head
    hr=max(10,s//4)
    pygame.draw.circle(surf,col,(cx,cy-bh//2-hr+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-bh//2-hr+bob),hr,max(2,s//32))
    # Flat wide nose
    nw2=max(5,s//10); nh2=max(3,s//14)
    pygame.draw.ellipse(surf,dark,(cx-nw2//2,cy-bh//2-hr+hr//4+bob,nw2,nh2))
    # Beady eyes
    er=max(3,s//16); eox=max(4,s//10)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(20,12,5),(ex,cy-bh//2-hr-hr//4+bob),er)
        pygame.draw.circle(surf,(200,80,20),(ex,cy-bh//2-hr-hr//4+bob),max(1,er-1))
    # Brow ridge
    pygame.draw.line(surf,dark,(cx-eox-er,cy-bh//2-hr-hr//4-er+bob),
                     (cx+eox+er,cy-bh//2-hr-hr//4-er+bob),max(2,s//32))


def _draw_dark_mage(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*2)*max(2,s//24))
    robe=(80,35,120); dark=(50,20,80)
    pulse=0.6+0.4*math.sin(t*3)
    orb_col=(int(160*pulse),int(80*pulse),max(0,min(255, max(0,min(255,int(240*pulse))))))
    sh = pygame.Surface((s,s//5),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,35),(0,0,s,s//5))
    surf.blit(sh,(cx-s//2,cy+s//3+bob//2))
    # Flowing robe
    rw=max(10,s//2); rh=max(12,s//2)
    pygame.draw.polygon(surf,robe,[
        (cx-rw//2,cy-rh//4+bob),(cx,cy+rh//2+bob),(cx+rw//2,cy-rh//4+bob)])
    pygame.draw.polygon(surf,dark,[
        (cx-rw//2,cy-rh//4+bob),(cx,cy+rh//2+bob),(cx+rw//2,cy-rh//4+bob)],max(1,s//48))
    # Body
    bw=max(8,s//3); bh=max(10,s//3)
    pygame.draw.ellipse(surf,robe,(cx-bw//2,cy-bh//2+bob,bw,bh))
    # Hood
    hr=max(6,s//4)
    pygame.draw.polygon(surf,dark,[
        (cx-hr,cy-hr//2+bob),(cx,cy-hr*2+bob),(cx+hr,cy-hr//2+bob)])
    # Glowing eyes
    er=max(2,s//20); eox=max(2,s//20)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,orb_col,(ex,cy-hr+bob),er)
    # Staff
    sw=max(2,s//32)
    pygame.draw.line(surf,dark,(cx+hr,cy-hr//4+bob),(cx+hr+s//8,cy+s//4+bob),sw)
    or2=max(4,s//12)
    pygame.draw.circle(surf,orb_col,(cx+hr,cy-hr//2+bob),or2)
    pygame.draw.circle(surf,(255,255,255),(cx+hr,cy-hr//2+bob),max(2,or2//2))
    # Aura
    gs=pygame.Surface((or2*4,or2*4),pygame.SRCALPHA)
    pygame.draw.circle(gs, (orb_col[0], orb_col[1], orb_col[2], max(0,min(255, max(0,min(255,int(30*pulse)))))),(or2*2,or2*2),or2*2)
    surf.blit(gs,(cx+hr-or2*2,cy-hr//2+bob-or2*2),special_flags=pygame.BLEND_RGBA_ADD)




def _draw_imp(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*4)*max(2,s//20))   # fast bob
    hover = int(math.sin(t*2)*max(3,s//12)) # hovers up/down
    rc=(180,50,50); dark=(130,30,30)
    pulse=0.6+0.4*math.sin(t*3)
    # Shadow — faint since it hovers
    sh=pygame.Surface((s,s//6),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,30),(0,0,s,s//6))
    surf.blit(sh,(cx-s//2,cy+s//3+s//8))
    # Wings — two triangles behind body
    ww=max(8,s//3); wh=max(6,s//4)
    for wx,wsign in [(cx-s//5,-1),(cx+s//5,1)]:
        wc=_lerp_col((140,30,30),(200,80,80),0.5+0.5*math.sin(t*4+wsign))
        pygame.draw.polygon(surf,wc,[
            (wx,cy-s//8+hover+bob),
            (wx+wsign*ww,cy-wh+hover+bob),
            (wx+wsign*ww//2,cy+wh//2+hover+bob)])
        pygame.draw.polygon(surf,dark,[
            (wx,cy-s//8+hover+bob),
            (wx+wsign*ww,cy-wh+hover+bob),
            (wx+wsign*ww//2,cy+wh//2+hover+bob)],max(1,s//48))
    # Tail
    tx2=cx+s//4; ty2=cy+s//8+hover+bob
    pygame.draw.line(surf,dark,(tx2,ty2),(tx2+s//6,ty2+s//8),max(2,s//24))
    pygame.draw.polygon(surf,dark,[
        (tx2+s//6,ty2+s//8),
        (tx2+s//4,ty2+s//5),
        (tx2+s//6+s//16,ty2+s//4)])
    # Small body
    bw=max(10,s//3); bh=max(10,s//3)
    pygame.draw.ellipse(surf,rc,(cx-bw//2,cy-bh//4+hover+bob,bw,bh))
    pygame.draw.ellipse(surf,dark,(cx-bw//2,cy-bh//4+hover+bob,bw,bh),max(1,s//48))
    # Head
    hr=max(6,s//5)
    pygame.draw.circle(surf,rc,(cx,cy-hr+hover+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-hr+hover+bob),hr,max(1,s//48))
    # Horns
    hw=max(3,s//20); hh=max(5,s//10)
    for hox in [-s//8, s//8]:
        pygame.draw.polygon(surf,dark,[
            (cx+hox-hw//2,cy-hr+hover+bob),
            (cx+hox,cy-hr-hh+hover+bob),
            (cx+hox+hw//2,cy-hr+hover+bob)])
    # Glowing eyes
    er=max(2,s//20); eox=max(3,hr//3)
    eye_col=(int(255*pulse),int(200*pulse),0)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,eye_col,(ex,cy-hr+hover+bob),er)
    # Claws
    cw=max(1,s//32)
    for cx2,dx2 in [(cx-bw//2,cx-bw//2-s//8),(cx+bw//2,cx+bw//2+s//8)]:
        pygame.draw.line(surf,dark,(cx2,cy-bh//8+hover+bob),(dx2,cy+hover+bob),cw)


def _draw_dire_rat(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*5)*max(2,s//24))   # skittery
    fc2=(130,110,80); dark=(90,75,50); belly=(180,160,120)
    # Shadow
    sh=pygame.Surface((s,s//5),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,50),(0,0,s,s//5))
    surf.blit(sh,(cx-s//2,cy+s//4))
    # Long tail
    tpts=[(cx+s//3,cy+s//8+bob),(cx+s//2,cy+bob),(cx+s*2//3,cy-s//8+bob)]
    if len(tpts)>1:
        pygame.draw.lines(surf,dark,False,tpts,max(2,s//24))
    # Body — low and elongated
    bw=max(16,s*2//3); bh=max(10,s//3)
    pygame.draw.ellipse(surf,fc2,(cx-bw//2,cy-bh//3+bob,bw,bh))
    pygame.draw.ellipse(surf,dark,(cx-bw//2,cy-bh//3+bob,bw,bh),max(1,s//48))
    # Belly
    belly_w=max(10,bw*2//3); belly_h=max(6,bh//2)
    pygame.draw.ellipse(surf,belly,(cx-belly_w//2,cy-bh//5+bob,belly_w,belly_h))
    # Legs — four stubby ones
    lw=max(2,s//24); lh=max(4,s//12)
    for lx in [cx-bw//3,cx-bw//6,cx+bw//6,cx+bw//3]:
        pygame.draw.line(surf,dark,(lx,cy+bh//4+bob),(lx,cy+lh+bh//4+bob),lw)
    # Head — pointed snout
    hr=max(5,s//6)
    pygame.draw.circle(surf,fc2,(cx-bw//3,cy-bh//4+bob),hr)
    # Snout
    pygame.draw.ellipse(surf,belly,(cx-bw//3-hr//2-hr//4,cy-bh//4+bob-hr//4,hr,hr//2))
    # Ears
    er=max(4,s//12)
    for eox in [-s//10,s//16]:
        pygame.draw.circle(surf,fc2,(cx-bw//3+eox,cy-bh//4-hr+bob),er)
        pygame.draw.circle(surf,belly,(cx-bw//3+eox,cy-bh//4-hr+bob),max(2,er-2))
    # Red eyes — beady
    pygame.draw.circle(surf,(200,40,40),(cx-bw//3-hr//3,cy-bh//4-hr//4+bob),max(2,s//28))
    # Whiskers
    ww=max(1,s//48)
    for wy in [cy-bh//4-hr//8+bob, cy-bh//4+hr//8+bob]:
        pygame.draw.line(surf,belly,(cx-bw//3-hr,wy),(cx-bw//3-hr-s//8,wy-s//16),ww)
        pygame.draw.line(surf,belly,(cx-bw//3-hr,wy),(cx-bw//3-hr-s//8,wy+s//16),ww)


def _draw_orc_warrior(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*2.2)*max(2,s//20))
    skin=(80,120,55); dark=(55,85,35); armour=(90,80,65); metal=(140,130,115)
    # Shadow
    sh=pygame.Surface((s,s//4),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,60),(0,0,s,s//4))
    surf.blit(sh,(cx-s//2,cy+s//3))
    # Boots
    bfw=max(8,s//8); bfh=max(5,s//10)
    for bx in [cx-s//6-bfw//2, cx+s//6-bfw//2]:
        pygame.draw.rect(surf,(55,45,30),(bx,cy+s//3+bob,bfw,bfh))
    # Legs with greaves
    lw=max(6,s//8); lh=max(10,s//3)
    for lx in [cx-s//6-lw//2, cx+s//6-lw//2]:
        pygame.draw.rect(surf,skin,(lx,cy+bob,lw,lh))
        pygame.draw.rect(surf,metal,(lx,cy+bob,lw,lh//2))  # greave
        pygame.draw.rect(surf,dark,(lx,cy+bob,lw,lh//2),max(1,s//48))
    # Body with chest plate
    bw=max(18,s*3//4); bh=max(14,s//2)
    pygame.draw.ellipse(surf,skin,(cx-bw//2,cy-bh//3+bob,bw,bh))
    # Chest plate
    cw=max(14,bw*3//4); ch=max(10,bh*2//3)
    pygame.draw.rect(surf,armour,(cx-cw//2,cy-bh//3+bob,cw,ch))
    pygame.draw.rect(surf,dark,(cx-cw//2,cy-bh//3+bob,cw,ch),max(1,s//48))
    # Plate line detail
    pygame.draw.line(surf,metal,(cx,cy-bh//3+bob),(cx,cy-bh//3+ch+bob),max(1,s//48))
    pygame.draw.line(surf,metal,(cx-cw//2,cy-bh//3+ch//2+bob),(cx+cw//2,cy-bh//3+ch//2+bob),max(1,s//48))
    # Shield arm (left)
    aw=max(4,s//10)
    pygame.draw.line(surf,skin,(cx-bw//2+s//16,cy-bh//4+bob),(cx-bw//2-s//5,cy+bob),aw)
    sw=max(8,s//6); sh2=max(10,s//5)
    pygame.draw.ellipse(surf,metal,(cx-bw//2-s//5-sw//2,cy-sh2//2+bob,sw,sh2))
    pygame.draw.ellipse(surf,dark,(cx-bw//2-s//5-sw//2,cy-sh2//2+bob,sw,sh2),max(1,s//48))
    # Axe arm (right)
    pygame.draw.line(surf,skin,(cx+bw//2-s//16,cy-bh//4+bob),(cx+bw//2+s//8,cy-bh//3+bob),aw)
    # Axe
    pygame.draw.line(surf,dark,(cx+bw//2+s//8,cy-bh//3+bob),(cx+bw//2+s//4,cy-bh//2-s//8+bob),max(3,s//16))
    pygame.draw.polygon(surf,metal,[
        (cx+bw//2+s//4,cy-bh//2-s//8+bob),
        (cx+bw//2+s//3,cy-bh//2-s//5+bob),
        (cx+bw//2+s//5,cy-bh//2+bob)])
    # Neck
    nw=max(6,s//8)
    pygame.draw.rect(surf,skin,(cx-nw//2,cy-bh//3-nw+bob,nw,nw))
    # Head
    hr=max(8,s//5)
    pygame.draw.circle(surf,skin,(cx,cy-bh//3-hr+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-bh//3-hr+bob),hr,max(1,s//48))
    # Helmet
    pygame.draw.arc(surf,metal,(cx-hr,cy-bh//3-hr*2+bob,hr*2,hr*2),0,math.pi,max(3,s//16))
    # Tusks
    tw=max(2,s//32)
    for tox in [-s//10,s//10]:
        pygame.draw.line(surf,(220,210,190),(cx+tox,cy-bh//3-hr//2+bob),
                         (cx+tox,cy-bh//3-hr//2+s//12+bob),tw)
    # Eyes — angry
    er=max(2,s//24); eox=max(3,hr//3)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(200,50,30),(ex,cy-bh//3-hr+bob),er)


def _draw_stone_golem(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*1.2)*max(1,s//32))  # very slow
    sc=(140,135,125); light=(170,165,155); dark=(100,95,88); crack=(80,75,70)
    # Shadow — huge
    sh=pygame.Surface((s,s//3),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,70),(0,0,s,s//3))
    surf.blit(sh,(cx-s//2,cy+s*2//5))
    # Feet — big stone blocks
    fw=max(10,s//5); fh=max(7,s//8)
    for fx in [cx-s//5-fw//2, cx+s//5-fw//2]:
        pygame.draw.rect(surf,dark,(fx,cy+s//3+bob,fw,fh))
        pygame.draw.rect(surf,crack,(fx,cy+s//3+bob,fw,fh),max(1,s//48))
    # Legs — thick stone pillars
    lw=max(10,s//5); lh=max(12,s//3)
    for lx in [cx-s//5-lw//2, cx+s//5-lw//2]:
        pygame.draw.rect(surf,sc,(lx,cy+bob,lw,lh))
        pygame.draw.rect(surf,dark,(lx,cy+bob,lw,lh),max(1,s//48))
    # Massive body — rectangular stone block
    bw=max(24,s*4//5); bh=max(18,s*3//5)
    pygame.draw.rect(surf,sc,(cx-bw//2,cy-bh//2+bob,bw,bh))
    pygame.draw.rect(surf,dark,(cx-bw//2,cy-bh//2+bob,bw,bh),max(2,s//24))
    # Stone texture — cracks
    cw=max(1,s//48)
    pygame.draw.line(surf,crack,(cx-bw//4,cy-bh//2+bob),(cx-bw//6,cy+bob),cw)
    pygame.draw.line(surf,crack,(cx+bw//5,cy-bh//4+bob),(cx+bw//3,cy+bh//4+bob),cw)
    pygame.draw.line(surf,crack,(cx-bw//3,cy+bob),(cx-bw//6,cy+bh//4+bob),cw)
    # Highlight edge
    pygame.draw.line(surf,light,(cx-bw//2+max(1,s//48),cy-bh//2+bob),
                     (cx-bw//2+max(1,s//48),cy+bh//2+bob),max(2,s//32))
    # Massive arms — stone slabs
    aw=max(8,s//6); al=max(12,s//3)
    for ax,asign in [(cx-bw//2,cx-bw//2-al),(cx+bw//2,cx+bw//2+al)]:
        pygame.draw.rect(surf,sc,(min(ax,asign),cy-bh//4+bob,al,aw))
        pygame.draw.rect(surf,dark,(min(ax,asign),cy-bh//4+bob,al,aw),max(1,s//48))
    # Head — square stone block
    hw=max(14,s//3); hh=max(12,s//3)
    pygame.draw.rect(surf,sc,(cx-hw//2,cy-bh//2-hh+bob,hw,hh))
    pygame.draw.rect(surf,dark,(cx-hw//2,cy-bh//2-hh+bob,hw,hh),max(2,s//24))
    # Glowing eyes — energy cracks
    er=max(3,s//16); eox=max(4,hw//5)
    eye_col=(80,200,255)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.rect(surf,eye_col,(ex-er//2,cy-bh//2-hh+hh//3+bob,er,er//2))
    # Mouth — crack
    pygame.draw.line(surf,crack,(cx-hw//4,cy-bh//2-hh+hh*2//3+bob),
                     (cx+hw//4,cy-bh//2-hh+hh*2//3+bob),max(1,s//48))


def _draw_werewolf(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*2.8)*max(2,s//20))
    fc2=(110,85,60); dark=(75,55,35); fur=(140,110,75)
    # Shadow
    sh=pygame.Surface((s,s//4),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,55),(0,0,s,s//4))
    surf.blit(sh,(cx-s//2,cy+s//3))
    # Digitigrade legs — bent backwards like a wolf
    lw=max(5,s//10); kh=max(8,s//8)
    for lx,sign in [(cx-s//7,-1),(cx+s//7,1)]:
        # Upper leg
        pygame.draw.line(surf,fc2,(lx,cy+bob),(lx,cy+kh+bob),lw)
        # Lower leg — angled
        pygame.draw.line(surf,fc2,(lx,cy+kh+bob),(lx+sign*s//8,cy+s//3+bob),lw)
        # Paw
        pygame.draw.ellipse(surf,dark,(lx+sign*s//8-s//16,cy+s//3+bob,s//8,s//16))
    # Muscular body
    bw=max(16,s*2//3); bh=max(14,s//2)
    pygame.draw.ellipse(surf,fc2,(cx-bw//2,cy-bh//3+bob,bw,bh))
    pygame.draw.ellipse(surf,dark,(cx-bw//2,cy-bh//3+bob,bw,bh),max(1,s//48))
    # Fur tuft on chest
    fw=max(6,bw//3); fh=max(4,bh//4)
    pygame.draw.ellipse(surf,fur,(cx-fw//2,cy-bh//3+bh//8+bob,fw,fh))
    # Arms with claws
    aw=max(4,s//10)
    for ax,adx,sign in [(cx-bw//2,cx-bw//2-s//4,-1),(cx+bw//2,cx+bw//2+s//4,1)]:
        pygame.draw.line(surf,fc2,(ax,cy-bh//5+bob),(adx,cy+bob),aw)
        # Claws
        cw2=max(1,s//32)
        for i in range(3):
            cangle=math.radians(-30+i*30)
            clx=adx+int(math.cos(cangle)*s//10*sign)
            cly=cy+bob+int(math.sin(cangle)*s//10)
            pygame.draw.line(surf,dark,(adx,cy+bob),(clx,cly),cw2)
    # Neck fur
    pygame.draw.ellipse(surf,fur,(cx-s//8,cy-bh//3-s//12+bob,s//4,s//8))
    # Wolf head — elongated snout
    hr=max(8,s//5)
    pygame.draw.circle(surf,fc2,(cx,cy-bh//3-hr+bob),hr)
    # Snout — elongated
    snw=max(6,hr); snh=max(5,hr//2)
    pygame.draw.ellipse(surf,fc2,(cx-snw-snw//4,cy-bh//3-hr//2+bob,snw*2,snh))
    pygame.draw.ellipse(surf,dark,(cx-snw-snw//4,cy-bh//3-hr//2+bob,snw*2,snh),max(1,s//48))
    # Nose
    pygame.draw.circle(surf,dark,(cx-snw//3,cy-bh//3-hr//2+bob),max(2,s//28))
    # Ears — pointed
    er2=max(5,s//10)
    for eox2 in [-hr//2,hr//2]:
        pygame.draw.polygon(surf,fc2,[
            (cx+eox2-er2//2,cy-bh//3-hr+bob),
            (cx+eox2,cy-bh//3-hr-er2+bob),
            (cx+eox2+er2//2,cy-bh//3-hr+bob)])
    # Yellow eyes — feral
    er=max(2,s//22); eox=max(3,hr//3)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(220,185,40),(ex,cy-bh//3-hr+bob),er)
        pygame.draw.circle(surf,(20,12,5),(ex,cy-bh//3-hr+bob),max(1,er-1))


def _draw_lich(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*1.5)*max(2,s//20))
    hover = int(math.sin(t*0.8)*max(4,s//10))  # slow hover
    robe=(60,20,100); dark=(40,10,70); bone=(200,195,175)
    pulse=0.5+0.5*math.sin(t*2)
    aura_col=(int(140*pulse),int(50*pulse),max(0,min(255, max(0,min(255,int(220*pulse))))))
    # Shadow — faint, far below since hovering
    sh=pygame.Surface((s,s//6),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,25),(0,0,s,s//6))
    surf.blit(sh,(cx-s//2,cy+s*2//5))
    # Floating robe — tattered hem
    rw=max(14,s*3//5); rh=max(16,s*3//5)
    # Tattered robe base
    pygame.draw.polygon(surf,robe,[
        (cx-rw//2,cy-rh//4+hover+bob),
        (cx-rw//2-rw//8,cy+rh//2+hover+bob),
        (cx-rw//4,cy+rh//3+hover+bob),
        (cx,cy+rh//2+hover+bob),
        (cx+rw//4,cy+rh//3+hover+bob),
        (cx+rw//2+rw//8,cy+rh//2+hover+bob),
        (cx+rw//2,cy-rh//4+hover+bob)])
    pygame.draw.polygon(surf,dark,[
        (cx-rw//2,cy-rh//4+hover+bob),
        (cx-rw//2-rw//8,cy+rh//2+hover+bob),
        (cx-rw//4,cy+rh//3+hover+bob),
        (cx,cy+rh//2+hover+bob),
        (cx+rw//4,cy+rh//3+hover+bob),
        (cx+rw//2+rw//8,cy+rh//2+hover+bob),
        (cx+rw//2,cy-rh//4+hover+bob)],max(1,s//48))
    # Skeletal arms
    aw=max(2,s//28)
    pygame.draw.line(surf,bone,(cx-rw//2,cy-rh//8+hover+bob),(cx-rw//2-s//5,cy-rh//4+hover+bob),aw)
    pygame.draw.line(surf,bone,(cx+rw//2,cy-rh//8+hover+bob),(cx+rw//2+s//5,cy-rh//4+hover+bob),aw)
    # Orb of power in right hand
    or2=max(5,s//10)
    pygame.draw.circle(surf,aura_col,(cx+rw//2+s//5,cy-rh//4+hover+bob),or2)
    pygame.draw.circle(surf,(255,255,255),(cx+rw//2+s//5,cy-rh//4+hover+bob),max(2,or2//2))
    # Aura around orb
    gs=pygame.Surface((or2*4,or2*4),pygame.SRCALPHA)
    pygame.draw.circle(gs, (aura_col[0], aura_col[1], aura_col[2], max(0,min(255, max(0,min(255,int(40*pulse)))))),(or2*2,or2*2),or2*2)
    surf.blit(gs,(cx+rw//2+s//5-or2*2,cy-rh//4+hover+bob-or2*2),special_flags=pygame.BLEND_RGBA_ADD)
    # Skull head — with crown
    hr=max(8,s//5)
    pygame.draw.circle(surf,bone,(cx,cy-rh//4-hr+hover+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-rh//4-hr+hover+bob),hr,max(1,s//48))
    # Crown
    cr_h=max(4,s//12)
    pygame.draw.rect(surf,(180,150,30),(cx-hr,cy-rh//4-hr*2+hover+bob,hr*2,cr_h))
    pygame.draw.rect(surf,(140,115,22),(cx-hr,cy-rh//4-hr*2+hover+bob,hr*2,cr_h),max(1,s//48))
    for cx3 in [cx-hr+max(2,s//20), cx, cx+hr-max(2,s//20)]:
        pygame.draw.rect(surf,(200,170,35),(cx3-max(2,s//32),cy-rh//4-hr*2-max(3,s//16)+hover+bob,max(4,s//20),max(4,s//12)))
    # Hollow eye sockets — glowing
    er=max(3,s//16); eox=max(3,hr//2)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(10,5,15),(ex,cy-rh//4-hr+hover+bob),er)
        pygame.draw.circle(surf,aura_col,(ex,cy-rh//4-hr+hover+bob),max(2,er-1))
    # Jaw — grinning skull
    jaw_w=max(8,hr); jaw_h=max(4,hr//3)
    pygame.draw.arc(surf,dark,(cx-jaw_w//2,cy-rh//4-hr+hr//3+hover+bob,jaw_w,jaw_h),math.pi,2*math.pi,max(1,s//48))
    tw2=max(1,s//60)
    for tx3 in range(cx-hr//2+2,cx+hr//2-2,max(2,s//28)):
        pygame.draw.rect(surf,bone,(tx3,cy-rh//4-hr+hr//3+hover+bob,tw2,max(3,s//20)))

def _draw_generic(surf, x, y, t, ts, color):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*2.5)*max(2,s//24))
    bw=max(10,s//2); bh=max(12,s*3//5)
    pygame.draw.ellipse(surf,color,(cx-bw//2,cy-bh//4+bob,bw,bh))
    pygame.draw.ellipse(surf,tuple(max(0,c-40) for c in color),
                        (cx-bw//2,cy-bh//4+bob,bw,bh),max(1,s//48))
    hr=max(5,s//5)
    pygame.draw.circle(surf,color,(cx,cy-hr*2+bob),hr)
    er=max(1,s//32)
    for ex in [cx-s//12,cx+s//12]:
        pygame.draw.circle(surf,(20,12,5),(ex,cy-hr*2+bob),er)


# ---------------------------------------------------------------------------
# Boss sprite drawers — larger, more detailed versions
# ---------------------------------------------------------------------------

def _draw_bone_lord(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*1.8)*max(2,s//20))
    bone=(220,215,195); dark=(155,150,135); gold=(200,170,50); armour=(100,90,75)
    # Shadow
    sh=pygame.Surface((s,s//4),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,60),(0,0,s,s//4))
    surf.blit(sh,(cx-s//2,cy+s*2//5))
    # Legs — armoured bone pillars
    lw=max(5,s//9); lh=max(12,s//3)
    for lx in [cx-s//6-lw//2, cx+s//6-lw//2]:
        pygame.draw.line(surf,bone,(lx+lw//2,cy+bob),(lx+lw//2,cy+lh+bob),lw)
        pygame.draw.rect(surf,armour,(lx,cy+bob,lw,lw))
        pygame.draw.rect(surf,armour,(lx,cy+lh-lw+bob,lw,lw))
    # Tattered robe bottom
    rw=max(18,s*3//5)
    pygame.draw.polygon(surf,armour,[
        (cx-rw//2,cy+bob),(cx-rw//3,cy+lh+bob),
        (cx,cy+lh-s//8+bob),(cx+rw//3,cy+lh+bob),(cx+rw//2,cy+bob)])
    # Armoured torso
    bw=max(18,s*3//4); bh=max(14,s//2)
    pygame.draw.rect(surf,armour,(cx-bw//2,cy-bh//2+bob,bw,bh))
    pygame.draw.rect(surf,dark,(cx-bw//2,cy-bh//2+bob,bw,bh),max(2,s//32))
    # Armour detail lines
    for i in range(3):
        liy=cy-bh//2+i*(bh//3)+bob
        pygame.draw.line(surf,dark,(cx-bw//2,liy),(cx+bw//2,liy),max(1,s//48))
    # Bone arms — skeletal with pauldrons
    aw=max(3,s//12)
    for ax,sign in [(cx-bw//2,-1),(cx+bw//2,1)]:
        # Pauldron
        pygame.draw.circle(surf,armour,(ax,cy-bh//3+bob),max(6,s//10))
        # Arm bones
        pygame.draw.line(surf,bone,(ax,cy-bh//4+bob),(ax+sign*s//4,cy+bob),aw)
        pygame.draw.line(surf,bone,(ax+sign*s//4,cy+bob),(ax+sign*s//3,cy+s//8+bob),aw)
        # Clawed hand
        for ci in range(3):
            ca=math.radians(-30+ci*30)
            pygame.draw.line(surf,bone,
                (ax+sign*s//3,cy+s//8+bob),
                (ax+sign*s//3+int(math.cos(ca)*s//8*sign),cy+s//8+bob+int(math.sin(ca)*s//8)),
                max(1,s//48))
    # Thick neck vertebrae
    nw=max(5,s//10)
    for i in range(3):
        pygame.draw.circle(surf,bone,(cx,cy-bh//2-i*nw+bob),nw//2)
    # Giant skull — with crown
    hr=max(10,s//4)
    pygame.draw.circle(surf,bone,(cx,cy-bh//2-hr*2+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-bh//2-hr*2+bob),hr,max(2,s//32))
    # Bone crown
    cw=max(4,s//14)
    for ci,ch2 in [(-hr,s//8),(-hr//2,s//5),(0,s//6),(hr//2,s//5),(hr,s//8)]:
        pygame.draw.line(surf,gold,(cx+ci,cy-bh//2-hr*2+bob-hr),
                         (cx+ci,cy-bh//2-hr*2+bob-hr-ch2),cw)
    pygame.draw.rect(surf,gold,(cx-hr,cy-bh//2-hr*2+bob-hr,hr*2,cw))
    # Hollow glowing eye sockets
    er=max(3,s//14); eox=max(4,hr//3)
    pulse=0.5+0.5*math.sin(t*3)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(10,8,5),(ex,cy-bh//2-hr*2+bob),er)
        pygame.draw.circle(surf,(int(100*pulse),int(200*pulse),max(0,min(255, max(0,min(255,int(255*pulse)))))),
                           (ex,cy-bh//2-hr*2+bob),max(2,er-1))
    # Jaw
    pygame.draw.arc(surf,dark,(cx-hr//2,cy-bh//2-hr*2+hr//3+bob,hr,hr//3),
                    math.pi,2*math.pi,max(1,s//48))


def _draw_mountain_king(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*1.2)*max(2,s//24))
    col=(100,145,90); dark=(65,100,55); rock=(130,120,100); light=(150,170,130)
    # Shadow — enormous
    sh=pygame.Surface((s,s//3),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,70),(0,0,s,s//3))
    surf.blit(sh,(cx-s//2,cy+s*2//5))
    # Massive feet
    fw=max(12,s//5); fh=max(8,s//8)
    for fx in [cx-s//4-fw//2, cx+s//4-fw//2]:
        pygame.draw.ellipse(surf,dark,(fx,cy+s//3+bob,fw,fh))
    # Tree-trunk legs
    lw=max(12,s*3//14); lh=max(14,s*2//5)
    for lx in [cx-s//4-lw//2, cx+s//4-lw//2]:
        pygame.draw.rect(surf,col,(lx,cy+bob,lw,lh))
        pygame.draw.rect(surf,dark,(lx,cy+bob,lw,lh),max(2,s//32))
        # Moss patches
        pygame.draw.ellipse(surf,light,(lx+lw//4,cy+lh//3+bob,lw//2,lh//4))
    # Massive barrel body
    bw=max(26,s*9//10); bh=max(20,s*7//10)
    pygame.draw.ellipse(surf,col,(cx-bw//2,cy-bh//2+bob,bw,bh))
    pygame.draw.ellipse(surf,dark,(cx-bw//2,cy-bh//2+bob,bw,bh),max(2,s//24))
    # Rocky texture patches
    for rx,ry,rr in [(cx-bw//3,cy-bh//4+bob,s//10),
                      (cx+bw//4,cy+bh//8+bob,s//12),
                      (cx,cy-bh//3+bob,s//14)]:
        pygame.draw.circle(surf,rock,(rx,ry),rr)
    # Boulder arm (left, raised)
    aw=max(8,s//7)
    pygame.draw.line(surf,col,(cx-bw//2+s//16,cy-bh//4+bob),(cx-bw//2-s//3,cy-bh//2-s//8+bob),aw)
    # Boulder
    br=max(8,s//8)
    boulx=cx-bw//2-s//3; bouly=cy-bh//2-s//8+bob
    pygame.draw.circle(surf,rock,(boulx,bouly),br)
    pygame.draw.circle(surf,dark,(boulx,bouly),br,max(2,s//32))
    # Right arm hanging
    pygame.draw.line(surf,col,(cx+bw//2-s//16,cy-bh//4+bob),(cx+bw//2+s//6,cy+bob),aw)
    # Thick neck
    nw=max(10,s//7)
    pygame.draw.rect(surf,col,(cx-nw//2,cy-bh//2-nw+bob,nw,nw+max(2,s//16)))
    # Giant head
    hr=max(12,s*3//10)
    pygame.draw.circle(surf,col,(cx,cy-bh//2-hr+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-bh//2-hr+bob),hr,max(2,s//24))
    # Rocky brow
    pygame.draw.arc(surf,rock,(cx-hr,cy-bh//2-hr*2+bob,hr*2,hr),0,math.pi,max(4,s//16))
    # Flat wide nose
    nw2=max(8,s//8); nh2=max(5,s//12)
    pygame.draw.ellipse(surf,dark,(cx-nw2//2,cy-bh//2-hr+hr//4+bob,nw2,nh2))
    # Small angry eyes under brow
    er=max(3,s//14); eox=max(5,s//10)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(15,10,5),(ex,cy-bh//2-hr-hr//4+bob),er)
        pygame.draw.circle(surf,(220,90,20),(ex,cy-bh//2-hr-hr//4+bob),max(1,er-1))
    # Tusks
    tw=max(3,s//20)
    for tox in [-s//10,s//10]:
        pygame.draw.line(surf,(230,220,195),(cx+tox,cy-bh//2-hr+hr//2+bob),
                         (cx+tox,cy-bh//2-hr+hr+bob),tw)
    # Mossy beard
    for mi in range(5):
        mx2=cx-s//8+mi*(s//20); my2=cy-bh//2-hr+hr*3//4+bob
        pygame.draw.line(surf,light,(mx2,my2),(mx2,my2+max(4,s//12)),max(1,s//48))


def _draw_archmage(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*1.5)*max(2,s//20))
    hover=int(math.sin(t*0.7)*max(6,s//8))
    robe=(100,30,160); dark=(65,15,110); bone=(210,200,180)
    pulse=0.5+0.5*math.sin(t*2.5)
    orb=(int(160*pulse),int(60*pulse),max(0,min(255, max(0,min(255,int(240*pulse))))))
    orb2=(int(240*pulse),int(140*pulse),max(0,min(255, max(0,min(255,int(40*pulse))))))
    # Shadow — faint (hovering high)
    sh=pygame.Surface((s,s//6),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,20),(0,0,s,s//6))
    surf.blit(sh,(cx-s//2,cy+s*2//5+s//8))
    # Wide ornate robe
    rw=max(18,s*4//5); rh=max(18,s*3//5)
    pts=[(cx-rw//2,cy-rh//4+hover+bob),
         (cx-rw//2-rw//6,cy+rh//2+hover+bob),
         (cx-rw//4,cy+rh//3+hover+bob),
         (cx,cy+rh//2+hover+bob),
         (cx+rw//4,cy+rh//3+hover+bob),
         (cx+rw//2+rw//6,cy+rh//2+hover+bob),
         (cx+rw//2,cy-rh//4+hover+bob)]
    pygame.draw.polygon(surf,robe,pts)
    pygame.draw.polygon(surf,dark,pts,max(2,s//32))
    # Gold trim on robe
    trim_col=(180,150,40)
    pygame.draw.line(surf,trim_col,(cx-rw//2,cy-rh//4+hover+bob),
                     (cx-rw//2-rw//6,cy+rh//2+hover+bob),max(2,s//32))
    pygame.draw.line(surf,trim_col,(cx+rw//2,cy-rh//4+hover+bob),
                     (cx+rw//2+rw//6,cy+rh//2+hover+bob),max(2,s//32))
    # Staff — ornate
    stx=cx+rw//2+s//10; sty=cy-rh//4+hover+bob
    pygame.draw.line(surf,dark,(stx,sty),(stx,sty+rh),max(3,s//16))
    # Spinning orbs around staff top
    for oi in range(3):
        oa=math.radians(t*120+oi*120)
        ox2=stx+int(math.cos(oa)*s//8)
        oy2=sty+int(math.sin(oa)*s//8)
        oc=(orb,orb2,bone)[oi]
        pygame.draw.circle(surf,oc,(ox2,oy2),max(3,s//16))
    # Body under robe
    bw=max(12,s//3); bh=max(10,s//3)
    pygame.draw.ellipse(surf,robe,(cx-bw//2,cy-bh//2+hover+bob,bw,bh))
    # Skeletal hands
    hw=max(2,s//28)
    pygame.draw.line(surf,bone,(cx-rw//2,cy-rh//8+hover+bob),
                     (cx-rw//2-s//5,cy-rh//4+hover+bob),hw)
    # Wizard hat
    hr=max(7,s//6)
    hat_cx=cx; hat_base_y=cy-rh//4-hr+hover+bob
    # Hat brim
    pygame.draw.ellipse(surf,dark,(hat_cx-hr,hat_base_y,hr*2,hr//3))
    pygame.draw.ellipse(surf,robe,(hat_cx-hr+max(2,s//32),hat_base_y,hr*2-max(4,s//16),hr//4))
    # Hat cone
    pygame.draw.polygon(surf,dark,[
        (hat_cx-hr,hat_base_y),(hat_cx+hr,hat_base_y),
        (hat_cx,hat_base_y-hr*2)])
    pygame.draw.polygon(surf,robe,[
        (hat_cx-hr+max(2,s//48),hat_base_y),
        (hat_cx+hr-max(2,s//48),hat_base_y),
        (hat_cx,hat_base_y-hr*2+max(2,s//48))],max(1,s//48))
    # Star on hat
    pygame.draw.circle(surf,(220,200,50),(hat_cx,hat_base_y-hr),max(3,s//20))
    # Face — old and gaunt
    face_y=cy-rh//4-hr//2+hover+bob
    pygame.draw.circle(surf,bone,(cx,face_y),max(5,s//7))
    # Long beard
    for bi in range(5):
        bx2=cx-s//10+bi*(s//20)
        pygame.draw.line(surf,bone,(bx2,face_y+max(3,s//8)),
                         (bx2,face_y+max(6,s//4)),max(1,s//48))
    # Glowing eyes
    er=max(2,s//20); eox=max(3,s//16)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,orb,(ex,face_y),er)


def _draw_inferno_duke(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*3)*max(2,s//20))
    hover=int(math.sin(t*1.5)*max(4,s//12))
    rc=(220,60,20); dark=(150,30,10); fire=(255,180,30)
    pulse=0.6+0.4*math.sin(t*4)
    # Shadow — faint
    sh=pygame.Surface((s,s//5),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,30),(0,0,s,s//5))
    surf.blit(sh,(cx-s//2,cy+s*2//5))
    # Fire aura around whole body
    for fi in range(6):
        fa=math.radians(t*60+fi*60)
        fx2=cx+int(math.cos(fa)*s//3)
        fy2=cy+int(math.sin(fa)*s//3)+hover+bob
        fr=max(4,s//10)
        gs=pygame.Surface((fr*2,fr*2),pygame.SRCALPHA)
        pygame.draw.circle(gs,(int(255*pulse),int(120*pulse),0,max(0,min(255, max(0,min(255,int(40*pulse)))))),(fr,fr),fr)
        surf.blit(gs,(fx2-fr,fy2-fr),special_flags=pygame.BLEND_RGBA_ADD)
    # Large wings
    ww=max(12,s*2//5); wh=max(10,s//3)
    for wx,wsign in [(cx-s//5,-1),(cx+s//5,1)]:
        wc=_lerp_col((160,30,10),(240,100,20),0.5+0.5*math.sin(t*3+wsign))
        # Wing membrane — 3 segments
        for wi in range(3):
            wa=math.radians(wsign*(30+wi*25))
            wex=wx+wsign*int(math.cos(wa)*ww)
            wey=cy-wh//2+int(math.sin(wa)*wh)+hover+bob
            pygame.draw.line(surf,dark,(wx,cy+hover+bob),(wex,wey),max(2,s//24))
        pygame.draw.polygon(surf,wc,[
            (wx,cy+hover+bob),
            (wx+wsign*ww,cy-wh+hover+bob),
            (wx+wsign*ww*3//4,cy+wh//3+hover+bob)])
        pygame.draw.polygon(surf,dark,[
            (wx,cy+hover+bob),
            (wx+wsign*ww,cy-wh+hover+bob),
            (wx+wsign*ww*3//4,cy+wh//3+hover+bob)],max(1,s//48))
    # Tail with fire tip
    pygame.draw.line(surf,dark,(cx+s//5,cy+s//8+hover+bob),
                     (cx+s//3,cy+s//4+hover+bob),max(3,s//16))
    pygame.draw.polygon(surf,fire,[
        (cx+s//3,cy+s//4+hover+bob),
        (cx+s//3+s//8,cy+s//5+hover+bob),
        (cx+s//3+s//12,cy+s//3+hover+bob)])
    # Muscular body
    bw=max(14,s//2); bh=max(14,s//2)
    pygame.draw.ellipse(surf,rc,(cx-bw//2,cy-bh//4+hover+bob,bw,bh))
    pygame.draw.ellipse(surf,dark,(cx-bw//2,cy-bh//4+hover+bob,bw,bh),max(2,s//32))
    # Clawed arms
    aw=max(3,s//12)
    for ax,sign in [(cx-bw//2,-1),(cx+bw//2,1)]:
        pygame.draw.line(surf,rc,(ax,cy-bh//8+hover+bob),
                         (ax+sign*s//4,cy+hover+bob),aw)
        for ci in range(3):
            ca=math.radians(-30+ci*30)
            pygame.draw.line(surf,dark,
                (ax+sign*s//4,cy+hover+bob),
                (ax+sign*s//4+int(math.cos(ca)*s//10*sign),
                 cy+hover+bob+int(math.sin(ca)*s//10)),max(1,s//48))
    # Head
    hr=max(8,s//5)
    pygame.draw.circle(surf,rc,(cx,cy-bh//4-hr+hover+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-bh//4-hr+hover+bob),hr,max(2,s//32))
    # Large curved horns
    hw=max(4,s//14)
    for hox,hsign in [(-hr,-1),(hr,1)]:
        pygame.draw.arc(surf,dark,
            (cx+hox-s//8,cy-bh//4-hr*2-s//8+hover+bob,s//6,s//6),
            math.radians(180+hsign*90),math.radians(270+hsign*90),hw)
    # Glowing fire eyes
    er=max(3,s//14); eox=max(3,hr//3)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,fire,(ex,cy-bh//4-hr+hover+bob),er)
        pygame.draw.circle(surf,(255,255,200),(ex,cy-bh//4-hr+hover+bob),max(1,er-1))
    # Crown of flames
    for fi in range(5):
        fa=math.radians(fi*36-90)
        fhx=cx+int(math.cos(fa)*hr)
        fhy=cy-bh//4-hr*2+int(math.sin(fa)*hr//3)+hover+bob
        fh2=max(5,s//10)+int(pulse*s//20)
        pygame.draw.polygon(surf,fire,[
            (fhx-max(2,s//32),fhy),(fhx,fhy-fh2),(fhx+max(2,s//32),fhy)])


def _draw_rat_king(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*2.5)*max(2,s//20))
    fc2=(150,125,90); dark=(100,80,55); belly=(190,165,120); crown_col=(180,150,30)
    pulse=0.5+0.5*math.sin(t*3)
    # Shadow
    sh=pygame.Surface((s,s//3),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,60),(0,0,s,s//3))
    surf.blit(sh,(cx-s//2,cy+s//3))
    # Multiple tails writhing
    for ti in range(4):
        ta=math.radians(t*80+ti*90)
        tx2=cx+s//4+int(math.cos(ta)*s//4)
        ty2=cy+s//8+int(math.sin(ta)*s//6)+bob
        pygame.draw.line(surf,dark,(cx+s//4,cy+bob),(tx2,ty2),max(2,s//24))
    # Large lumpy body — mass of rats
    bw=max(22,s*4//5); bh=max(18,s*3//5)
    pygame.draw.ellipse(surf,fc2,(cx-bw//2,cy-bh//3+bob,bw,bh))
    pygame.draw.ellipse(surf,dark,(cx-bw//2,cy-bh//3+bob,bw,bh),max(2,s//32))
    # Sub-rat heads peeking out of body
    for ri,rpos in enumerate([(-bw//3,bh//4),( bw//3,bh//5),(-bw//4,-bh//8),(bw//4,bh//3)]):
        rx2=cx+rpos[0]; ry2=cy-bh//3+rpos[1]+bob
        rr=max(4,s//14)
        pygame.draw.circle(surf,fc2,(rx2,ry2),rr)
        for rex in [rx2-rr//2,rx2+rr//2]:
            pygame.draw.circle(surf,(180,30,30),(rex,ry2-rr//4),max(1,s//32))
    # Belly
    belly_w=max(12,bw*2//3); belly_h=max(8,bh//2)
    pygame.draw.ellipse(surf,belly,(cx-belly_w//2,cy-bh//8+bob,belly_w,belly_h))
    # Stubby arms
    aw=max(4,s//12)
    for ax,sign in [(cx-bw//2,-1),(cx+bw//2,1)]:
        pygame.draw.line(surf,fc2,(ax,cy-bh//5+bob),(ax+sign*s//5,cy+bob),aw)
    # Main head — big rat head
    hr=max(8,s//5)
    pygame.draw.circle(surf,fc2,(cx,cy-bh//3-hr+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-bh//3-hr+bob),hr,max(2,s//32))
    # Crown
    cw=max(3,s//14); ch=max(4,s//10)
    pygame.draw.rect(surf,crown_col,(cx-hr,cy-bh//3-hr*2+bob,hr*2,cw))
    for ci in [-hr+cw,-hr//2,0,hr//2-cw,hr-cw]:
        pygame.draw.rect(surf,crown_col,(cx+ci,cy-bh//3-hr*2-ch+bob,cw,ch))
    for ci in [-hr+cw,-hr//2+cw//2,hr//2-cw]: # gems
        pygame.draw.circle(surf,(200,50,50),(cx+ci+cw//2,cy-bh//3-hr*2-ch//2+bob),max(2,s//30))
    # Pointed snout
    snw=max(8,hr); snh=max(5,hr//2)
    pygame.draw.ellipse(surf,fc2,(cx-snw-snw//4,cy-bh//3-hr//2+bob,snw*2,snh))
    pygame.draw.circle(surf,dark,(cx-snw//3,cy-bh//3-hr//2+bob),max(2,s//28))
    # Ears
    er=max(5,s//10)
    for eox2 in [-hr//2,hr//2]:
        pygame.draw.circle(surf,fc2,(cx+eox2,cy-bh//3-hr*2+hr//3+bob),er)
        pygame.draw.circle(surf,belly,(cx+eox2,cy-bh//3-hr*2+hr//3+bob),max(2,er-2))
    # Red eyes
    pygame.draw.circle(surf,(int(220*pulse),40,40),(cx-hr//3,cy-bh//3-hr+hr//4+bob),max(3,s//16))
    pygame.draw.circle(surf,(int(220*pulse),40,40),(cx+hr//3,cy-bh//3-hr+hr//4+bob),max(3,s//16))
    # Whiskers
    ww=max(1,s//48)
    for wy in [cy-bh//3-hr//4+bob,cy-bh//3+hr//4+bob]:
        for wsign in [-1,1]:
            pygame.draw.line(surf,belly,(cx-snw,wy),(cx-snw-s//8,wy+wsign*s//20),ww)


def _draw_warchief_grommak(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*2)*max(2,s//20))
    skin=(85,130,60); dark=(55,90,35); armour=(95,85,70); metal=(155,145,130)
    blood=(180,30,30); gold=(190,160,40)
    # Shadow
    sh=pygame.Surface((s,s//4),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,65),(0,0,s,s//4))
    surf.blit(sh,(cx-s//2,cy+s*2//5))
    # Plated boots
    bfw=max(10,s//7); bfh=max(7,s//9)
    for bx in [cx-s//5-bfw//2, cx+s//5-bfw//2]:
        pygame.draw.rect(surf,metal,(bx,cy+s//3+bob,bfw,bfh))
        pygame.draw.rect(surf,dark,(bx,cy+s//3+bob,bfw,bfh),max(1,s//48))
    # Armoured legs
    lw=max(8,s//7); lh=max(12,s//3)
    for lx in [cx-s//5-lw//2, cx+s//5-lw//2]:
        pygame.draw.rect(surf,skin,(lx,cy+bob,lw,lh))
        pygame.draw.rect(surf,metal,(lx,cy+bob,lw,lh//2),max(2,s//32))
    # Cape behind body
    cw=max(16,s*3//4)
    pygame.draw.polygon(surf,(150,20,20),[
        (cx-cw//2,cy-s//3+bob),(cx+cw//2,cy-s//3+bob),
        (cx+cw//3,cy+s//3+bob),(cx-cw//3,cy+s//3+bob)])
    # Armoured body
    bw=max(20,s*4//5); bh=max(16,s*3//5)
    pygame.draw.rect(surf,armour,(cx-bw//2,cy-bh//2+bob,bw,bh))
    pygame.draw.rect(surf,dark,(cx-bw//2,cy-bh//2+bob,bw,bh),max(2,s//24))
    # Armour plates
    pw=bw//3; ph=bh//2
    for pi in range(3):
        pygame.draw.rect(surf,metal,(cx-bw//2+pi*pw+max(1,s//48),cy-bh//2+bob,pw-max(1,s//48),ph))
        pygame.draw.rect(surf,dark,(cx-bw//2+pi*pw+max(1,s//48),cy-bh//2+bob,pw-max(1,s//48),ph),max(1,s//48))
    # Blood/battle damage on armour
    pygame.draw.line(surf,blood,(cx-bw//4,cy-bh//3+bob),(cx,cy-bh//6+bob),max(1,s//48))
    # Huge axe (right arm)
    aw=max(5,s//10)
    pygame.draw.line(surf,skin,(cx+bw//2-s//16,cy-bh//4+bob),(cx+bw//2+s//4,cy-bh//2-s//8+bob),aw)
    # Axe head — double-bladed
    ax2=cx+bw//2+s//4; ay2=cy-bh//2-s//8+bob
    pygame.draw.polygon(surf,metal,[(ax2,ay2),(ax2+s//5,ay2-s//8),(ax2+s//8,ay2+s//8)])
    pygame.draw.polygon(surf,metal,[(ax2,ay2),(ax2+s//5,ay2+s//8),(ax2+s//8,ay2-s//8)])
    pygame.draw.polygon(surf,gold,[(ax2,ay2),(ax2+s//5,ay2-s//8),(ax2+s//8,ay2+s//8)],max(1,s//48))
    # Shield (left arm)
    pygame.draw.line(surf,skin,(cx-bw//2+s//16,cy-bh//4+bob),(cx-bw//2-s//5,cy+bob),aw)
    sw=max(10,s//6); sh2=max(14,s//4)
    pygame.draw.ellipse(surf,metal,(cx-bw//2-s//5-sw//2,cy-sh2//2+bob,sw,sh2))
    pygame.draw.ellipse(surf,dark,(cx-bw//2-s//5-sw//2,cy-sh2//2+bob,sw,sh2),max(2,s//32))
    pygame.draw.circle(surf,gold,(cx-bw//2-s//5,cy+bob),max(3,s//20))
    # Thick neck
    nw=max(7,s//8)
    pygame.draw.rect(surf,skin,(cx-nw//2,cy-bh//2-nw+bob,nw,nw))
    # Imposing head
    hr=max(9,s//5)
    pygame.draw.circle(surf,skin,(cx,cy-bh//2-hr+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-bh//2-hr+bob),hr,max(2,s//32))
    # War helmet
    pygame.draw.arc(surf,metal,(cx-hr,cy-bh//2-hr*2+bob,hr*2,hr*2),0,math.pi,max(4,s//14))
    # Nose guard
    ng_w=max(3,s//18); ng_h=max(6,hr)
    pygame.draw.rect(surf,metal,(cx-ng_w//2,cy-bh//2-hr+bob,ng_w,ng_h))
    # Battle scar
    pygame.draw.line(surf,blood,(cx-hr//3,cy-bh//2-hr-hr//3+bob),(cx,cy-bh//2-hr+hr//3+bob),max(1,s//48))
    # Tusks
    tw=max(3,s//20)
    for tox in [-s//10,s//10]:
        pygame.draw.line(surf,(230,218,195),(cx+tox,cy-bh//2-hr+hr//2+bob),
                         (cx+tox,cy-bh//2-hr+hr+bob),tw)
    # Eyes — burning red rage
    er=max(2,s//18); eox=max(3,hr//3)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(220,40,20),(ex,cy-bh//2-hr+bob),er)


def _draw_ancient_colossus(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*0.8)*max(1,s//40))  # barely moves
    sc=(155,150,138); light=(185,180,168); dark=(105,100,92); crack=(75,70,65)
    glow=(60,180,255)
    pulse=0.4+0.4*math.sin(t*1.5)
    # Massive shadow
    sh=pygame.Surface((s,s//3),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,80),(0,0,s,s//3))
    surf.blit(sh,(cx-s//2,cy+s*2//5))
    # Ancient rune carvings (glowing)
    for ri in range(4):
        ra=math.radians(ri*90+t*10)
        rx2=cx+int(math.cos(ra)*s//4)
        ry2=cy+int(math.sin(ra)*s//5)+bob
        gs2=pygame.Surface((max(4,s//10),max(4,s//10)),pygame.SRCALPHA)
        gs2.fill((int(glow[0]*pulse),int(glow[1]*pulse),int(glow[2]*pulse),max(0,min(255, max(0,min(255,int(60*pulse)))))))
        surf.blit(gs2,(rx2,ry2),special_flags=pygame.BLEND_RGBA_ADD)
    # Massive stone feet
    fw=max(14,s//5); fh=max(10,s//8)
    for fx in [cx-s//4-fw//2, cx+s//4-fw//2]:
        pygame.draw.rect(surf,dark,(fx,cy+s//3+bob,fw,fh))
        pygame.draw.rect(surf,crack,(fx,cy+s//3+bob,fw,fh),max(2,s//32))
    # Pillar legs
    lw=max(14,s*3//14); lh=max(16,s*2//5)
    for lx in [cx-s//4-lw//2, cx+s//4-lw//2]:
        pygame.draw.rect(surf,sc,(lx,cy+bob,lw,lh))
        pygame.draw.rect(surf,dark,(lx,cy+bob,lw,lh),max(2,s//28))
        # Crack detail
        pygame.draw.line(surf,crack,(lx+lw//3,cy+bob),(lx+lw//4,cy+lh+bob),max(1,s//48))
    # Colossal body — stone monolith
    bw=max(28,s*9//10); bh=max(22,s*4//5)
    pygame.draw.rect(surf,sc,(cx-bw//2,cy-bh//2+bob,bw,bh))
    pygame.draw.rect(surf,dark,(cx-bw//2,cy-bh//2+bob,bw,bh),max(3,s//24))
    # Stone texture
    for ci in range(4):
        cix=cx-bw//2+ci*(bw//4)
        pygame.draw.line(surf,crack,(cix,cy-bh//2+bob),(cix,cy+bh//2+bob),max(1,s//48))
    pygame.draw.line(surf,crack,(cx-bw//2,cy+bob),(cx+bw//2,cy+bob),max(1,s//48))
    # Light face on body
    pygame.draw.rect(surf,light,(cx-bw//3,cy-bh//3+bob,bw*2//3,bh//2))
    pygame.draw.rect(surf,crack,(cx-bw//3,cy-bh//3+bob,bw*2//3,bh//2),max(1,s//48))
    # Slab arms
    aw2=max(10,s//8); al=max(14,s//3)
    for ax,asign in [(cx-bw//2,cx-bw//2-al),(cx+bw//2,cx+bw//2+al)]:
        pygame.draw.rect(surf,sc,(min(ax,asign),cy-bh//5+bob,al,aw2))
        pygame.draw.rect(surf,dark,(min(ax,asign),cy-bh//5+bob,al,aw2),max(2,s//32))
    # Massive square head
    hw=max(16,s*2//5); hh=max(14,s//3)
    pygame.draw.rect(surf,sc,(cx-hw//2,cy-bh//2-hh+bob,hw,hh))
    pygame.draw.rect(surf,dark,(cx-hw//2,cy-bh//2-hh+bob,hw,hh),max(3,s//24))
    # Glowing energy eyes — large
    er=max(5,s//12); eox=max(6,hw//5)
    for ex in [cx-eox,cx+eox]:
        ec_col=(int(glow[0]*pulse),int(glow[1]*pulse),int(glow[2]*pulse))
        pygame.draw.rect(surf,ec_col,(ex-er//2,cy-bh//2-hh+hh//3+bob,er,er//2))
        # Glow around eyes
        gs3=pygame.Surface((er*3,er*3),pygame.SRCALPHA)
        pygame.draw.ellipse(gs3, (ec_col[0], ec_col[1], ec_col[2], max(0,min(255, max(0,min(255,int(50*pulse)))))),(0,0,er*3,er*3))
        surf.blit(gs3,(ex-er*3//2,cy-bh//2-hh+hh//3+bob-er),special_flags=pygame.BLEND_RGBA_ADD)
    # Crack across face
    pygame.draw.line(surf,crack,(cx-hw//3,cy-bh//2-hh+bob),
                     (cx+hw//4,cy-bh//2+bob),max(2,s//32))


def _draw_the_alpha(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*2.5)*max(2,s//20))
    fc2=(130,100,70); dark=(85,60,38); fur=(165,130,90); blood=(180,25,25)
    pulse=0.5+0.5*math.sin(t*3)
    # Shadow
    sh=pygame.Surface((s,s//4),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,60),(0,0,s,s//4))
    surf.blit(sh,(cx-s//2,cy+s*2//5))
    # Battle-scarred digitigrade legs
    lw=max(6,s//9); kh=max(10,s//8)
    for lx,sign in [(cx-s//6,-1),(cx+s//6,1)]:
        pygame.draw.line(surf,fc2,(lx,cy+bob),(lx,cy+kh+bob),lw)
        pygame.draw.line(surf,fc2,(lx,cy+kh+bob),(lx+sign*s//7,cy+s//3+bob),lw)
        # Paw — large
        pygame.draw.ellipse(surf,dark,(lx+sign*s//7-s//12,cy+s//3+bob,s//6,s//10))
        # Claws on paws
        for ci in range(3):
            ca=math.radians(-20+ci*20)
            pygame.draw.line(surf,dark,
                (lx+sign*s//7,cy+s//3+s//14+bob),
                (lx+sign*s//7+int(math.cos(ca)*s//10*sign),cy+s//3+s//14+bob+int(math.sin(ca)*s//10)),
                max(1,s//48))
    # Muscular body — larger than werewolf
    bw=max(18,s*3//4); bh=max(16,s*3//5)
    pygame.draw.ellipse(surf,fc2,(cx-bw//2,cy-bh//3+bob,bw,bh))
    pygame.draw.ellipse(surf,dark,(cx-bw//2,cy-bh//3+bob,bw,bh),max(2,s//32))
    # Dense fur on chest and shoulders
    for fi in range(8):
        fa=math.radians(fi*22.5)
        fx2=cx+int(math.cos(fa)*bw//3)
        fy2=cy-bh//4+int(math.sin(fa)*bh//4)+bob
        pygame.draw.line(surf,fur,(cx,cy-bh//4+bob),(fx2,fy2),max(2,s//28))
    # Battle scars
    pygame.draw.line(surf,blood,(cx-bw//4,cy-bh//4+bob),(cx,cy+bob),max(1,s//48))
    pygame.draw.line(surf,blood,(cx+bw//5,cy-bh//3+bob),(cx+bw//3,cy+bob),max(1,s//48))
    # Massive arms with giant claws
    aw=max(5,s//9)
    for ax,sign,adx in [(cx-bw//2,cx-bw//2-s//3,-1),(cx+bw//2,cx+bw//2+s//3,1)]:
        pygame.draw.line(surf,fc2,(ax,cy-bh//5+bob),(adx,cy-s//8+bob),aw)
        # Giant claws
        for ci in range(4):
            ca=math.radians(-45+ci*30)
            pygame.draw.line(surf,dark,(adx,cy-s//8+bob),
                (adx+int(math.cos(ca)*s//6*sign),cy-s//8+bob+int(math.sin(ca)*s//6)),
                max(2,s//28))
    # Alpha's wolf head — massive
    hr=max(10,s//4)
    pygame.draw.circle(surf,fc2,(cx,cy-bh//3-hr+bob),hr)
    pygame.draw.circle(surf,dark,(cx,cy-bh//3-hr+bob),hr,max(2,s//32))
    # Long battle-worn snout
    snw=max(8,hr+s//10); snh=max(6,hr//2)
    pygame.draw.ellipse(surf,fc2,(cx-snw-snw//3,cy-bh//3-hr//2+bob,snw*2,snh))
    pygame.draw.ellipse(surf,dark,(cx-snw-snw//3,cy-bh//3-hr//2+bob,snw*2,snh),max(1,s//48))
    # Nose
    pygame.draw.circle(surf,dark,(cx-snw//3,cy-bh//3-hr//2+bob),max(3,s//24))
    # Battle scar on face
    pygame.draw.line(surf,blood,(cx-hr//2,cy-bh//3-hr+hr//3+bob),
                     (cx+hr//3,cy-bh//3-hr-hr//3+bob),max(2,s//32))
    # Large pointed ears with fur
    er2=max(7,s//9)
    for eox2 in [-hr//2,hr//2]:
        pygame.draw.polygon(surf,fc2,[
            (cx+eox2-er2//2,cy-bh//3-hr+bob),
            (cx+eox2,cy-bh//3-hr-er2+bob),
            (cx+eox2+er2//2,cy-bh//3-hr+bob)])
        pygame.draw.polygon(surf,fur,[
            (cx+eox2-er2//3,cy-bh//3-hr+bob),
            (cx+eox2,cy-bh//3-hr-er2+er2//3+bob),
            (cx+eox2+er2//3,cy-bh//3-hr+bob)])
    # Glowing amber eyes
    er=max(3,s//14); eox=max(4,hr//3)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(int(230*pulse),int(180*pulse),20),(ex,cy-bh//3-hr+bob),er)
        pygame.draw.circle(surf,(20,12,5),(ex,cy-bh//3-hr+bob),max(1,er-1))
    # Alpha crown — bone and tooth necklace
    necklace_y=cy-bh//3-hr+hr//2+bob
    for ni in range(7):
        nx2=cx-s//6+ni*(s//22)
        pygame.draw.line(surf,(210,195,160),(nx2,necklace_y),(nx2,necklace_y+max(4,s//14)),max(1,s//48))


def _draw_lich_king(surf, x, y, t, ts):
    s  = ts
    cx = x+s//2; cy = y+s//2
    bob = int(math.sin(t*1.2)*max(2,s//20))
    hover=int(math.sin(t*0.6)*max(8,s//8))
    robe=(50,15,90); dark=(30,8,60); bone=(210,200,178)
    gold=(200,165,35); ice=(100,210,240)
    pulse=0.4+0.5*math.sin(t*2)
    soul=(max(0,min(255,max(0,min(255, max(0,min(255,int(100*pulse))))))),
          max(0,min(255,max(0,min(255, max(0,min(255,int(30*pulse))))))),
          max(0,min(255,max(0,min(255, max(0,min(255,int(200*pulse))))))))
    # Shadow — very faint (high hover)
    sh=pygame.Surface((s,s//7),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,15),(0,0,s,s//7))
    surf.blit(sh,(cx-s//2,cy+s//2+s//8))
    # Phylactery orbiting — glowing gem
    pa=math.radians(t*90)
    px2=cx+int(math.cos(pa)*s//3); py2=cy+int(math.sin(pa)*s//4)+hover+bob
    gs4=pygame.Surface((max(8,s//8),max(8,s//8)),pygame.SRCALPHA)
    gs4.fill((soul[0], soul[1], soul[2], max(0,min(255,max(0,min(255, max(0,min(255,int(100*pulse)))))))))
    surf.blit(gs4,(px2-max(4,s//16),py2-max(4,s//16)))
    pygame.draw.rect(surf,soul,(px2-max(4,s//16),py2-max(4,s//16),max(8,s//8),max(8,s//8)),max(2,s//32))
    # Soul wisps orbiting body
    for wi in range(5):
        wa=math.radians(t*60+wi*72)
        wx2=cx+int(math.cos(wa)*s*2//5)
        wy2=cy+int(math.sin(wa)*s//3)+hover+bob
        gs5=pygame.Surface((max(6,s//10),max(6,s//10)),pygame.SRCALPHA)
        gs5.fill((soul[0], soul[1], soul[2], max(0,min(255, max(0,min(255,int(40*pulse)))))))
        surf.blit(gs5,(wx2,wy2),special_flags=pygame.BLEND_RGBA_ADD)
    # Massive tattered robes — many layers
    rw=max(20,s*4//5); rh=max(20,s*4//5)
    # Outer tattered layer
    tatter_pts=[(cx-rw//2,cy-rh//4+hover+bob),
                (cx-rw//2-rw//5,cy+rh//2+hover+bob),
                (cx-rw//3,cy+rh//3+hover+bob),
                (cx-rw//6,cy+rh//2+rh//8+hover+bob),
                (cx,cy+rh//2+hover+bob),
                (cx+rw//6,cy+rh//2+rh//8+hover+bob),
                (cx+rw//3,cy+rh//3+hover+bob),
                (cx+rw//2+rw//5,cy+rh//2+hover+bob),
                (cx+rw//2,cy-rh//4+hover+bob)]
    pygame.draw.polygon(surf,dark,tatter_pts)
    pygame.draw.polygon(surf,robe,tatter_pts,max(2,s//32))
    # Inner robe
    irw=max(14,rw*2//3); irh=max(14,rh*2//3)
    pygame.draw.ellipse(surf,robe,(cx-irw//2,cy-irh//4+hover+bob,irw,irh))
    # Gold trim everywhere
    pygame.draw.polygon(surf,gold,tatter_pts,max(1,s//48))
    # Skeletal arms
    aw=max(2,s//24)
    # Left arm — raised summoning
    pygame.draw.line(surf,bone,(cx-rw//2,cy-rh//8+hover+bob),
                     (cx-rw//2-s//5,cy-rh//2+hover+bob),aw)
    pygame.draw.line(surf,bone,(cx-rw//2-s//5,cy-rh//2+hover+bob),
                     (cx-rw//2-s//4,cy-rh//3+hover+bob),aw)
    # Soul orb in left hand
    or3=max(6,s//10)
    pygame.draw.circle(surf,soul,(cx-rw//2-s//4,cy-rh//3+hover+bob),or3)
    pygame.draw.circle(surf,(255,255,255),(cx-rw//2-s//4,cy-rh//3+hover+bob),max(2,or3//2))
    gs6=pygame.Surface((or3*4,or3*4),pygame.SRCALPHA)
    pygame.draw.circle(gs6, (soul[0], soul[1], soul[2], max(0,min(255, max(0,min(255,int(60*pulse)))))),(or3*2,or3*2),or3*2)
    surf.blit(gs6,(cx-rw//2-s//4-or3*2,cy-rh//3+hover+bob-or3*2),special_flags=pygame.BLEND_RGBA_ADD)
    # Right arm — holding sceptre
    pygame.draw.line(surf,bone,(cx+rw//2,cy-rh//8+hover+bob),
                     (cx+rw//2+s//5,cy-rh//4+hover+bob),aw)
    # Sceptre
    scy=cy-rh//4+hover+bob
    pygame.draw.line(surf,gold,(cx+rw//2+s//5,scy),(cx+rw//2+s//5,scy+rh//2),max(3,s//20))
    pygame.draw.circle(surf,ice,(cx+rw//2+s//5,scy),max(5,s//12))
    pygame.draw.circle(surf,(255,255,255),(cx+rw//2+s//5,scy),max(2,s//20))
    # Lich King skull — massive with crown
    hr=max(10,s//4)
    skull_y=cy-rh//4-hr*2+hover+bob
    pygame.draw.circle(surf,bone,(cx,skull_y),hr)
    pygame.draw.circle(surf,dark,(cx,skull_y),hr,max(2,s//32))
    # Imperial crown
    cbase_y=skull_y-hr
    pygame.draw.rect(surf,gold,(cx-hr,cbase_y,hr*2,max(4,s//14)))
    for ci,ch3 in [(-hr+s//20,s//8),(-hr//2,s//5),(0,s//6),(hr//2,s//5),(hr-s//20,s//8)]:
        pygame.draw.rect(surf,gold,(cx+ci,cbase_y-ch3,max(4,s//18),ch3))
    # Crown jewels — soul gems
    for ci,jc in [(-hr//2,soul),(0,ice),(hr//2,soul)]:
        pygame.draw.circle(surf,jc,(cx+ci,cbase_y-max(4,s//18)//2),max(3,s//24))
    # Hollow glowing eye sockets
    er=max(4,s//14); eox=max(4,hr//3)
    for ex in [cx-eox,cx+eox]:
        pygame.draw.circle(surf,(5,3,15),(ex,skull_y),er)
        pygame.draw.circle(surf,soul,(ex,skull_y),max(2,er-1))
        # Eye glow halo
        gs7=pygame.Surface((er*4,er*4),pygame.SRCALPHA)
        pygame.draw.circle(gs7, (soul[0], soul[1], soul[2], max(0,min(255, max(0,min(255,int(40*pulse)))))),(er*2,er*2),er*2)
        surf.blit(gs7,(ex-er*2,skull_y-er*2),special_flags=pygame.BLEND_RGBA_ADD)
    # Grinning skull jaw
    jaw_w=max(10,hr); jaw_h=max(5,hr//3)
    pygame.draw.arc(surf,dark,(cx-jaw_w//2,skull_y+hr//3,jaw_w,jaw_h),
                    math.pi,2*math.pi,max(2,s//32))
    tw2=max(1,s//48)
    for tx3 in range(cx-hr//2+2,cx+hr//2-2,max(2,s//20)):
        pygame.draw.rect(surf,bone,(tx3,skull_y+hr//3,tw2,max(4,s//16)))