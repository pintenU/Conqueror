import pygame
import math
import random


# ---------------------------------------------------------------------------
# Building definitions
# ---------------------------------------------------------------------------

BUILDINGS = [
    {
        "key":   "inn",
        "name":  "The Rusty Flagon",
        "sub":   "Inn & Tavern",
        "x":     0.18,
        "y":     0.35,
        "color": (130, 90, 50),
        "icon":  "inn",
        "desc":  "Rest your weary bones. Hot stew and a warm bed.",
    },
    {
        "key":   "blacksmith",
        "name":  "Gorin's Forge",
        "sub":   "Blacksmith",
        "x":     0.38,
        "y":     0.28,
        "color": (100, 80, 60),
        "icon":  "anvil",
        "desc":  "Finest blades and armour in the realm.",
    },
    {
        "key":   "shop",
        "name":  "Mira's Sundries",
        "sub":   "General Shop",
        "x":     0.62,
        "y":     0.28,
        "color": (80, 110, 70),
        "icon":  "shop",
        "desc":  "Potions, provisions and everything in between.",
    },
    {
        "key":   "antiquity",
        "name":  "The Curio Cabinet",
        "sub":   "Antiquities",
        "x":     0.82,
        "y":     0.35,
        "color": (100, 70, 120),
        "icon":  "relic",
        "desc":  "Rare relics bought and sold. No questions asked.",
    },
    {
        "key":   "dungeon",
        "name":  "Dungeon Entrance",
        "sub":   "Enter at your own risk",
        "x":     0.50,
        "y":     0.68,
        "color": (60, 40, 40),
        "icon":  "dungeon",
        "desc":  "The dark dungeon beneath Ashenvale. Danger lurks within.",
    },
    {
        "key":   "notice",
        "name":  "Notice Board",
        "sub":   "",
        "x":     0.50,
        "y":     0.52,
        "color": (140, 110, 60),
        "icon":  "board",
        "desc":  "Town notices, wanted posters and local gossip.",
    },
]

NOTICES = [
    "WANTED: Goblin chief — 50 gold reward. See the mayor.",
    "Travellers beware — the road to Grimhaven is cursed.",
    "Gorin's Forge: finest blades in the realm. No credit.",
    "The Curio Cabinet: relics bought & sold. Fair prices.",
    "INN: warm beds, hot stew. Coin accepted only.",
    "WARNING: Strange lights seen near the old dungeon again.",
    "Lost: one brown mule, answers to 'Biscuit'. Reward offered.",
]

GATE_POS = (0.50, 0.82)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _lerp_col(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))


def _draw_inn(surface, cx, cy, size, t):
    s = size
    # Main building body
    col = _lerp_col((110,75,40),(160,120,70),t)
    pygame.draw.rect(surface, col,          (cx-s,    cy-s//2, s*2,   s+s//4))
    pygame.draw.rect(surface, (80,55,25),   (cx-s,    cy-s//2, s*2,   s+s//4), 2)
    # Roof (triangle)
    pygame.draw.polygon(surface, _lerp_col((90,55,25),(140,95,50),t), [
        (cx-s-6, cy-s//2), (cx, cy-s-s//2), (cx+s+6, cy-s//2)])
    pygame.draw.polygon(surface, (65,40,18), [
        (cx-s-6, cy-s//2), (cx, cy-s-s//2), (cx+s+6, cy-s//2)], 2)
    # Door
    pygame.draw.rect(surface,(60,38,16),(cx-s//4,cy,s//2,s//4+s//8))
    pygame.draw.circle(surface,(160,130,60),(cx+s//4-4,cy+s//8),4)
    # Windows
    for wx in [cx-s//2, cx+s//3]:
        pygame.draw.rect(surface,(180,210,220),(wx,cy-s//4,s//3,s//4))
        pygame.draw.rect(surface,(60,45,25),(wx,cy-s//4,s//3,s//4),2)
        pygame.draw.line(surface,(60,45,25),(wx+s//6,cy-s//4),(wx+s//6,cy),1)
    # Sign hanging
    pygame.draw.rect(surface,(140,100,45),(cx-s//3,cy-s//2-12,s//1.5,16))
    pygame.draw.rect(surface,(100,72,32),(cx-s//3,cy-s//2-12,s//1.5,16),1)
    # Chimney smoke
    for i in range(3):
        alpha = int(60*(1-i/3))
        smoke = pygame.Surface((14,14),pygame.SRCALPHA)
        pygame.draw.circle(smoke,(180,180,180,alpha),(7,7),4+i*2)
        surface.blit(smoke,(cx+s//3+i*4-7, cy-s-s//2-i*10-7))


def _draw_blacksmith(surface, cx, cy, size, t):
    s = size
    col = _lerp_col((85,65,45),(130,105,75),t)
    # Stone building
    pygame.draw.rect(surface, col, (cx-s, cy-s//2, s*2, s+s//4))
    pygame.draw.rect(surface,(55,42,28),(cx-s,cy-s//2,s*2,s+s//4),2)
    # Flat roof with battlement-style top
    pygame.draw.rect(surface,_lerp_col((75,58,38),(115,92,62),t),
                     (cx-s-4,cy-s//2-8,s*2+8,14))
    for bx in range(cx-s, cx+s, 12):
        pygame.draw.rect(surface,_lerp_col((75,58,38),(115,92,62),t),
                         (bx,cy-s//2-18,8,14))
    # Forge glow (orange window)
    glow_col = (255,int(140+80*math.sin(pygame.time.get_ticks()*0.003)),20,
                int(180+60*math.sin(pygame.time.get_ticks()*0.003)))
    gsurf = pygame.Surface((s//2,s//3),pygame.SRCALPHA)
    gsurf.fill(glow_col)
    surface.blit(gsurf,(cx-s//4,cy-s//8))
    pygame.draw.rect(surface,(45,32,18),(cx-s//4,cy-s//8,s//2,s//3),2)
    # Anvil icon above door
    pygame.draw.rect(surface,(160,140,120),(cx-10,cy-s//2+4,20,8))
    pygame.draw.rect(surface,(140,120,100),(cx-7,cy-s//2+12,14,6))
    # Door
    pygame.draw.rect(surface,(50,35,15),(cx-s//5,cy,s//2.5,s//4+s//8))


def _draw_shop(surface, cx, cy, size, t):
    s = size
    col = _lerp_col((65,95,55),(100,145,85),t)
    # Building
    pygame.draw.rect(surface, col, (cx-s,cy-s//2,s*2,s+s//4))
    pygame.draw.rect(surface,(45,70,35),(cx-s,cy-s//2,s*2,s+s//4),2)
    # Peaked roof
    pygame.draw.polygon(surface,_lerp_col((55,80,42),(85,125,65),t),[
        (cx-s-4,cy-s//2),(cx,cy-s-s//3),(cx+s+4,cy-s//2)])
    pygame.draw.polygon(surface,(38,58,28),[
        (cx-s-4,cy-s//2),(cx,cy-s-s//3),(cx+s+4,cy-s//2)],2)
    # Striped awning
    for i in range(5):
        stripe_col = (220,60,60) if i%2==0 else (240,240,240)
        pygame.draw.rect(surface,stripe_col,(cx-s+i*(s*2//5),cy-s//2,s*2//5,10))
    # Window display
    pygame.draw.rect(surface,(200,220,210),(cx-s//2,cy-s//4,s,s//3))
    pygame.draw.rect(surface,(45,70,35),(cx-s//2,cy-s//4,s,s//3),2)
    # Door
    pygame.draw.rect(surface,(55,40,20),(cx-s//5,cy,s//2.5,s//4+s//8))
    pygame.draw.circle(surface,(170,140,60),(cx+s//5-4,cy+s//8),3)


def _draw_antiquity(surface, cx, cy, size, t):
    s = size
    col = _lerp_col((80,55,100),(125,90,155),t)
    # Ornate building
    pygame.draw.rect(surface, col, (cx-s,cy-s//2,s*2,s+s//4))
    pygame.draw.rect(surface,(55,35,72),(cx-s,cy-s//2,s*2,s+s//4),2)
    # Dome roof
    pygame.draw.ellipse(surface,_lerp_col((70,45,90),(110,75,140),t),
                        (cx-s,cy-s-s//3,s*2,s+s//3))
    pygame.draw.ellipse(surface,(45,28,62),(cx-s,cy-s-s//3,s*2,s+s//3),2)
    # Mystical window (star shape hint)
    wc = (220,190,255)
    pygame.draw.circle(surface,wc,(cx,cy-s//4),s//4)
    pygame.draw.circle(surface,(55,35,72),(cx,cy-s//4),s//4,2)
    for a in range(0,360,60):
        ra = math.radians(a)
        pygame.draw.line(surface,wc,
                         (cx+int(math.cos(ra)*s//6),cy-s//4+int(math.sin(ra)*s//6)),
                         (cx+int(math.cos(ra)*s//3),cy-s//4+int(math.sin(ra)*s//3)),1)
    # Door
    # Arched door
    pygame.draw.rect(surface,(40,25,55),(cx-s//5,cy,s//2.5,s//4+s//8))
    pygame.draw.ellipse(surface,(40,25,55),(cx-s//5,cy-s//5,s//2.5,s//2.5))
    # Glow
    pulse = 0.6+0.4*math.sin(pygame.time.get_ticks()*0.002)
    glow  = pygame.Surface((s*3,s*3),pygame.SRCALPHA)
    pygame.draw.circle(glow,(160,100,220,int(18*pulse)),(s+s//2,s+s//2),s+s//2)
    surface.blit(glow,(cx-s-s//2,cy-s-s//2),special_flags=pygame.BLEND_RGBA_ADD)


def _draw_notice_board(surface, cx, cy, size, t):
    s = size
    col = _lerp_col((120,90,45),(170,135,75),t)
    # Two posts
    for px2 in [cx-s//2, cx+s//2-6]:
        pygame.draw.rect(surface,(90,62,28),(px2,cy-s//2,8,s))
    # Board
    pygame.draw.rect(surface,col,(cx-s//2-4,cy-s//2-4,s+8,s//2))
    pygame.draw.rect(surface,(85,62,28),(cx-s//2-4,cy-s//2-4,s+8,s//2),2)
    # Papers on board
    for i,(nx,ny,nw,nh) in enumerate([(cx-s//3,cy-s//2,s//3-2,s//4-2),
                                        (cx+2,cy-s//2+4,s//3-2,s//4-2),
                                        (cx-s//3+4,cy-s//4+2,s//4,s//5)]):
        nc = (220,205,175) if i%2==0 else (215,195,165)
        pygame.draw.rect(surface,nc,(nx,ny,nw,nh))
        pygame.draw.rect(surface,(160,140,100),(nx,ny,nw,nh),1)
    # Shimmer
    pulse = 0.5+0.5*math.sin(pygame.time.get_ticks()*0.002)
    glow  = pygame.Surface((s*2+8,s*2),pygame.SRCALPHA)
    pygame.draw.ellipse(glow,(180,155,80,int(20*pulse)),(0,0,s*2+8,s*2))
    surface.blit(glow,(cx-s-4,cy-s),special_flags=pygame.BLEND_RGBA_ADD)


def _draw_gate(surface, cx, cy, W, t):
    """Draw the town exit gate at bottom centre."""
    col = _lerp_col((100,80,50),(150,125,80),t)
    h   = 80
    pw  = 20

    # Gate posts
    for gx in [cx-50, cx+30]:
        pygame.draw.rect(surface, col, (gx, cy-h, pw, h+20))
        pygame.draw.rect(surface,(70,52,28),(gx,cy-h,pw,h+20),2)
        # Battlements
        for bx2 in range(gx, gx+pw, 8):
            pygame.draw.rect(surface,col,(bx2,cy-h-12,6,12))

    # Arch
    pygame.draw.arc(surface, col,
                    (cx-50, cy-h-30, 100, 80), 0, math.pi, 8)

    # Road leading out (fades down)
    road = pygame.Surface((40,60),pygame.SRCALPHA)
    for i in range(60):
        a = int(120*(1-i/60))
        pygame.draw.line(road,(140,120,90,a),(0,i),(40,i),1)
    surface.blit(road,(cx-20,cy+20))

    # Leave prompt handled separately
    pulse = 0.6+0.4*math.sin(pygame.time.get_ticks()*0.0015)
    glow  = pygame.Surface((120,80),pygame.SRCALPHA)
    pygame.draw.ellipse(glow,(140,180,120,int(22*pulse)),(0,0,120,80))
    surface.blit(glow,(cx-60,cy-40),special_flags=pygame.BLEND_RGBA_ADD)


def _draw_dungeon_entrance(surface, cx, cy, size, t):
    s = size
    # Stone archway
    col = _lerp_col((50,35,35),(85,60,60),t)
    # Left and right pillars
    for px2 in [cx-s, cx+s-s//4]:
        pygame.draw.rect(surface, col, (px2, cy-s//2, s//4+2, s+s//3))
        pygame.draw.rect(surface,(35,22,22),(px2,cy-s//2,s//4+2,s+s//3),2)
        # Pillar cap
        pygame.draw.rect(surface,_lerp_col((65,45,45),(100,72,72),t),
                         (px2-3,cy-s//2-8,s//4+8,10))
    # Arch top
    pygame.draw.arc(surface, col,
                    (cx-s, cy-s, s*2, s+s//2), 0, math.pi, s//3)
    # Dark void inside
    void = pygame.Surface((s+s//2, s+s//4), pygame.SRCALPHA)
    void.fill((5,3,3,240))
    surface.blit(void,(cx-s//2-s//8, cy-s//4))
    # Eerie glow from inside
    pulse = 0.4+0.6*math.sin(pygame.time.get_ticks()*0.002)
    glow  = pygame.Surface((s*2,s*2),pygame.SRCALPHA)
    glow.fill((0,0,0,0))
    pygame.draw.ellipse(glow,(60,20,20),(0,s//2,s*2,s))
    glow.set_alpha(int(50*pulse))
    surface.blit(glow,(cx-s,cy-s//2),special_flags=pygame.BLEND_RGBA_ADD)
    # Skull / warning above arch
    wc = _lerp_col((120,60,60),(180,100,100),t)
    pygame.draw.circle(surface,wc,(cx,cy-s-s//4),s//5)
    pygame.draw.circle(surface,(20,12,12),(cx,cy-s-s//4),s//5,2)
    pygame.draw.line(surface,(20,12,12),(cx-s//8,cy-s-s//4),(cx+s//8,cy-s-s//4),2)
    # Steps leading down
    for i in range(3):
        sw = s+s//4-i*6
        sy2 = cy+s//4+i*6
        pygame.draw.rect(surface,_lerp_col((45,30,30),(70,50,50),t),
                         (cx-sw//2,sy2,sw,6))


DRAW_FUNCS = {
    "inn":       _draw_inn,
    "anvil":     _draw_blacksmith,
    "shop":      _draw_shop,
    "relic":     _draw_antiquity,
    "board":     _draw_notice_board,
    "dungeon":   _draw_dungeon_entrance,
}


# ---------------------------------------------------------------------------
# TownScene
# ---------------------------------------------------------------------------

class TownScene:
    def __init__(self, screen, inventory, town_name="Ashenvale"):
        self.screen     = screen
        self.W, self.H  = screen.get_size()
        self.clock      = pygame.time.Clock()
        self.time       = 0.0
        self.inventory  = inventory
        self.town_name  = town_name

        self.font_title  = pygame.font.SysFont("courier new", 32, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 18, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 14)
        self.font_tiny   = pygame.font.SysFont("courier new", 12)

        # Hover state per building + gate
        self._hover      = [0.0] * (len(BUILDINGS)+1)   # last = gate
        self._selected   = None   # index of hovered building
        self._gate_hover = False

        # Notice popup
        self._show_notice = False
        self._notice_idx  = 0

        # Open animation
        self.open_anim  = 0.0
        self.OPEN_DUR   = 0.5

        # Pre-build background
        self.bg = self._build_bg()

    # ------------------------------------------------------------------ #
    # Background
    # ------------------------------------------------------------------ #

    def _build_bg(self):
        surf = pygame.Surface((self.W, self.H))
        rng  = random.Random(321)

        # Sky gradient
        for y in range(self.H//2):
            t2 = y/(self.H//2)
            r  = int(100+50*t2)
            g2 = int(140+60*t2)
            b  = int(190+40*t2)
            pygame.draw.line(surf,(r,g2,b),(0,y),(self.W,y))

        # Ground
        for y in range(self.H//2, self.H):
            t2 = (y-self.H//2)/(self.H//2)
            r  = int(55+20*t2)
            g2 = int(80+25*t2)
            b  = int(40+15*t2)
            pygame.draw.line(surf,(r,g2,b),(0,y),(self.W,y))

        # Distant hills
        for i in range(3):
            hx = int(self.W*(0.15+i*0.32))
            hw = int(self.W*0.25)
            hh = int(self.H*0.12)
            hy = self.H//2
            pygame.draw.ellipse(surf,(55+i*8,85+i*10,45+i*5),
                                (hx-hw//2,hy-hh,hw,hh*2))

        # Ground detail — grass texture
        for _ in range(2000):
            gx = rng.randint(0,self.W)
            gy = rng.randint(self.H//2,self.H)
            v  = rng.randint(-8,8)
            pygame.draw.line(surf,(52+v,80+v,40+v),(gx,gy),(gx+rng.randint(-2,2),gy-rng.randint(3,7)),1)

        # Stone path from gate upward
        path_pts = []
        for i in range(20):
            py = self.H//2 + int((self.H//2)*i/19)
            pw = int(40+i*2)
            path_pts.append((self.W//2-pw//2, py, pw))
        for px2,py,pw in path_pts:
            v = rng.randint(-5,5)
            pygame.draw.rect(surf,(130+v,115+v,90+v),(px2,py,pw,self.H//19+2))

        # Background trees
        for _ in range(12):
            tx = rng.randint(20,self.W-20)
            ty = rng.randint(self.H//2-20, self.H//2+30)
            tr = rng.randint(18,35)
            v  = rng.randint(-10,10)
            # Trunk
            pygame.draw.rect(surf,(80,55,28),(tx-4,ty,8,tr))
            # Canopy
            pygame.draw.circle(surf,(45+v,80+v,35+v),(tx,ty-tr//2),tr)
            pygame.draw.circle(surf,(55+v,95+v,42+v),(tx,ty-tr//2-4),tr-6)

        # Fence line
        fence_y = self.H//2 + 15
        for fx in range(0,self.W,24):
            pygame.draw.line(surf,(100,78,45),(fx,fence_y-12),(fx,fence_y+8),4)
        pygame.draw.line(surf,(110,85,48),(0,fence_y),(self.W,fence_y),3)
        pygame.draw.line(surf,(110,85,48),(0,fence_y-8),(self.W,fence_y-8),2)

        return surf

    # ------------------------------------------------------------------ #
    # Building pixel position
    # ------------------------------------------------------------------ #

    def _bpos(self, b):
        return (int(b["x"]*self.W), int(b["y"]*self.H))

    def _bsize(self, b):
        return 42 if b["key"] != "notice" else 28

    def _gate_pos(self):
        return (int(GATE_POS[0]*self.W), int(GATE_POS[1]*self.H))

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #

    def _draw_buildings(self):
        for i, b in enumerate(BUILDINGS):
            cx, cy = self._bpos(b)
            s      = self._bsize(b)
            t      = self._hover[i]
            fn     = DRAW_FUNCS.get(b["icon"])
            if fn:
                fn(self.screen, cx, cy, s, t)

            # Name label
            nc  = _lerp_col((160,130,80),(225,195,120),t)
            ns  = self.font_small.render(b["name"], True, nc)
            nsh = self.font_small.render(b["name"], True, (20,14,8))
            self.screen.blit(nsh,(cx-ns.get_width()//2+1,cy+s+s//4+1))
            self.screen.blit(ns, (cx-ns.get_width()//2,  cy+s+s//4))

            if b["sub"]:
                ss  = self.font_tiny.render(b["sub"], True,
                                            _lerp_col((110,88,50),(170,140,80),t))
                self.screen.blit(ss,(cx-ss.get_width()//2, cy+s+s//4+ns.get_height()+1))

    def _draw_gate(self):
        cx, cy = self._gate_pos()
        t      = self._hover[len(BUILDINGS)]
        _draw_gate(self.screen, cx, cy, self.W, t)

        label   = self.font_small.render(
            "[ CLICK ]  Leave Ashenvale",
            True, _lerp_col((140,170,120),(200,230,170),t))
        lsh = self.font_small.render("[ CLICK ]  Leave Ashenvale", True,(10,8,4))
        lx  = cx - label.get_width()//2
        ly  = cy + 45
        self.screen.blit(lsh,(lx+1,ly+1))
        self.screen.blit(label,(lx,ly))

    def _draw_description(self):
        """Show hovered building description at top."""
        if self._selected is None:
            return
        b    = BUILDINGS[self._selected]
        t    = self._hover[self._selected]
        desc = self.font_small.render(b["desc"], True,
                                      _lerp_col((120,95,55),(185,155,90),t))
        bg   = pygame.Surface((desc.get_width()+20, desc.get_height()+8),
                               pygame.SRCALPHA)
        bg.fill((10,8,4,200))
        bx   = self.W//2 - bg.get_width()//2
        by   = self.H - desc.get_height() - 32
        self.screen.blit(bg,(bx,by))
        pygame.draw.rect(self.screen,(90,68,35),(bx,by,bg.get_width(),bg.get_height()),1)
        self.screen.blit(desc,(bx+10,by+4))

        hint = self.font_tiny.render("click to enter", True,(80,62,34))
        self.screen.blit(hint,(self.W//2-hint.get_width()//2, by+bg.get_height()+2))

    def _draw_title(self, alpha):
        title  = self.font_title.render(self.town_name, True,(220,192,130))
        shadow = self.font_title.render(self.town_name, True,(30,20,8))
        ts2    = pygame.Surface(title.get_size(),pygame.SRCALPHA)
        ts2.blit(title,(0,0)); ts2.set_alpha(alpha)
        ss2    = pygame.Surface(shadow.get_size(),pygame.SRCALPHA)
        ss2.blit(shadow,(0,0)); ss2.set_alpha(alpha)
        tx = self.W//2 - title.get_width()//2
        self.screen.blit(ss2,(tx+2,14))
        self.screen.blit(ts2,(tx,12))

        hint = self.font_tiny.render("I  inventory    M  map    ESC  menu",
                                     True,(100,80,45))
        hs   = pygame.Surface(hint.get_size(),pygame.SRCALPHA)
        hs.blit(hint,(0,0)); hs.set_alpha(alpha)
        self.screen.blit(hs,(self.W//2-hint.get_width()//2, self.H-hint.get_height()-8))

    def _draw_notice_popup(self):
        notice = NOTICES[self._notice_idx % len(NOTICES)]
        pw,ph  = int(self.W*0.48), int(self.H*0.26)
        px     = self.W//2 - pw//2
        py     = self.H//2 - ph//2

        bg = pygame.Surface((pw,ph),pygame.SRCALPHA)
        bg.fill((18,13,7,240))
        self.screen.blit(bg,(px,py))
        pygame.draw.rect(self.screen,(120,92,48),(px,py,pw,ph),2)
        pygame.draw.rect(self.screen,(70,52,26),(px+5,py+5,pw-10,ph-10),1)

        c  = (140,108,56)
        sz = 10
        for bpx,bpy,dx,dy in [(px,py,1,1),(px+pw,py,-1,1),
                                (px,py+ph,1,-1),(px+pw,py+ph,-1,-1)]:
            pygame.draw.line(self.screen,c,(bpx,bpy),(bpx+dx*sz,bpy),2)
            pygame.draw.line(self.screen,c,(bpx,bpy),(bpx,bpy+dy*sz),2)

        title = self.font_medium.render("— NOTICE BOARD —",True,(200,165,90))
        self.screen.blit(title,(self.W//2-title.get_width()//2,py+10))

        # Counter
        ctr = self.font_tiny.render(
            f"{self._notice_idx+1} / {len(NOTICES)}", True,(90,68,38))
        self.screen.blit(ctr,(px+pw-ctr.get_width()-10, py+10))

        # Word wrap
        words,lines,cur = notice.split(),[],""
        for w in words:
            test = cur+(" " if cur else "")+w
            if self.font_small.size(test)[0] < pw-30:
                cur = test
            else:
                lines.append(cur); cur = w
        if cur: lines.append(cur)

        ty2 = py+42
        for line in lines:
            ls = self.font_small.render(line,True,(190,162,108))
            self.screen.blit(ls,(self.W//2-ls.get_width()//2,ty2))
            ty2 += ls.get_height()+4

        hint = self.font_tiny.render(
            "← →  browse    ESC / click  close", True,(75,56,28))
        self.screen.blit(hint,(self.W//2-hint.get_width()//2,py+ph-hint.get_height()-8))

    # ------------------------------------------------------------------ #
    # Interaction
    # ------------------------------------------------------------------ #

    def _hit_building(self, pos):
        for i,b in enumerate(BUILDINGS):
            cx,cy = self._bpos(b)
            s     = self._bsize(b)
            if abs(pos[0]-cx) < s+10 and abs(pos[1]-cy) < s+10:
                return i
        return None

    def _hit_gate(self, pos):
        cx,cy = self._gate_pos()
        return abs(pos[0]-cx)<60 and abs(pos[1]-cy)<50

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while True:
            dt         = self.clock.tick(60)/1000.0
            self.time += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            ease       = 1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            mouse      = pygame.mouse.get_pos()

            # Update hovers
            self._selected = None
            for i,b in enumerate(BUILDINGS):
                cx,cy = self._bpos(b)
                s     = self._bsize(b)
                tgt   = 1.0 if (abs(mouse[0]-cx)<s+10 and abs(mouse[1]-cy)<s+10) else 0.0
                self._hover[i] += (tgt-self._hover[i])*10*dt
                self._hover[i]  = max(0.0,min(1.0,self._hover[i]))
                if tgt > 0:
                    self._selected = i

            # Gate hover
            gi  = len(BUILDINGS)
            tgt = 1.0 if self._hit_gate(mouse) else 0.0
            self._hover[gi] += (tgt-self._hover[gi])*10*dt
            self._hover[gi]  = max(0.0,min(1.0,self._hover[gi]))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self._show_notice:
                            self._show_notice = False
                        else:
                            return "pause"
                    if event.key == pygame.K_i:
                        return "inventory"
                    if event.key == pygame.K_m:
                        return "map"
                    if self._show_notice:
                        if event.key == pygame.K_RIGHT:
                            self._notice_idx = (self._notice_idx+1) % len(NOTICES)
                        if event.key == pygame.K_LEFT:
                            self._notice_idx = (self._notice_idx-1) % len(NOTICES)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._show_notice:
                        self._show_notice = False
                        continue

                    idx = self._hit_building(mouse)
                    if idx is not None:
                        b = BUILDINGS[idx]
                        if b["key"] == "notice":
                            self._show_notice = True
                            self._notice_idx  = 0
                        elif b["key"] == "dungeon":
                            return "start"
                        else:
                            return b["key"]

                    if self._hit_gate(mouse):
                        return "world_map"

            # --- Draw ---
            self.screen.blit(self.bg,(0,0))

            if ease > 0.1:
                self._draw_gate()
                self._draw_buildings()
                self._draw_description()
                self._draw_title(int(255*ease))

            if self._show_notice:
                self._draw_notice_popup()

            pygame.display.flip()