import pygame
import math
import random


# ---------------------------------------------------------------------------
# Town area definitions — each is a self-contained illustrated screen
# ---------------------------------------------------------------------------

AREAS = [
    {
        "key":      "gate",
        "name":     "Town Gate",
        "subtitle": "Ashenvale",
        "bg":       "gate",
        "action":   None,
        "action_label": "[ E ]  Leave town",
        "action_key":   "world_map",
    },
    {
        "key":      "house_a",
        "name":     "Old Miller's House",
        "subtitle": "A quiet home",
        "bg":       "house",
        "action":   None,
        "action_label": None,
        "action_key":   None,
    },
    {
        "key":      "inn",
        "name":     "The Rusty Flagon",
        "subtitle": "Inn & Tavern",
        "bg":       "inn",
        "action":   "inn",
        "action_label": "[ E ]  Enter inn",
        "action_key":   "inn",
    },
    {
        "key":      "market",
        "name":     "Market Square",
        "subtitle": "Heart of Ashenvale",
        "bg":       "market",
        "action":   "notice",
        "action_label": "[ E ]  Read notices",
        "action_key":   "notice",
    },
    {
        "key":      "blacksmith",
        "name":     "Gorin's Forge",
        "subtitle": "Blacksmith",
        "bg":       "blacksmith",
        "action":   "blacksmith",
        "action_label": "[ E ]  Enter forge",
        "action_key":   "blacksmith",
    },
    {
        "key":      "house_b",
        "name":     "Widow Hara's Cottage",
        "subtitle": "A small dwelling",
        "bg":       "house",
        "action":   None,
        "action_label": None,
        "action_key":   None,
    },
    {
        "key":      "shop",
        "name":     "Mira's Sundries",
        "subtitle": "General Shop",
        "bg":       "shop",
        "action":   "shop",
        "action_label": "[ E ]  Enter shop",
        "action_key":   "shop",
    },
    {
        "key":      "antiquity",
        "name":     "The Curio Cabinet",
        "subtitle": "Antiquities",
        "bg":       "antiquity",
        "action":   "antiquity",
        "action_label": "[ E ]  Enter shop",
        "action_key":   "antiquity",
    },
    {
        "key":      "house_c",
        "name":     "Thornwood Residence",
        "subtitle": "A tall townhouse",
        "bg":       "house",
        "action":   None,
        "action_label": None,
        "action_key":   None,
    },
    {
        "key":      "dungeon",
        "name":     "Dungeon Entrance",
        "subtitle": "Enter at your own risk",
        "bg":       "dungeon",
        "action":   "start",
        "action_label": "[ E ]  Enter dungeon",
        "action_key":   "start",
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


# ---------------------------------------------------------------------------
# Background painters — one per bg type
# ---------------------------------------------------------------------------

def _lerp_col(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))


def _draw_sky(surf, W, H, sky_top, sky_bot, ground_col):
    for y in range(H//2):
        t = y / (H//2)
        c = _lerp_col(sky_top, sky_bot, t)
        pygame.draw.line(surf, c, (0,y), (W,y))
    for y in range(H//2, H):
        t = (y-H//2)/(H//2)
        c = _lerp_col(ground_col, tuple(max(0,v-15) for v in ground_col), t)
        pygame.draw.line(surf, c, (0,y), (W,y))


def _draw_stone_road(surf, W, H, rng):
    """Cobblestone road running along the bottom third."""
    ry = H*2//3
    for y in range(ry, H):
        v = rng.randint(-6,6)
        pygame.draw.line(surf,(120+v,105+v,85+v),(0,y),(W,y))
    for row in range(5):
        for col in range(12):
            x = col*(W//12) + rng.randint(-4,4)
            y = ry + row*24 + rng.randint(-3,3)
            w = W//12 - 4
            h = 18
            v = rng.randint(-8,8)
            pygame.draw.rect(surf,(115+v,100+v,80+v),(x,y,w,h))
            pygame.draw.rect(surf,(90+v,78+v,60+v),(x,y,w,h),1)


def _draw_tree(surf, tx, ty, rng, size=1.0):
    tr = int(30*size)
    pygame.draw.rect(surf,(75,52,28),(tx-4,ty,8,tr))
    v = rng.randint(-10,10)
    pygame.draw.circle(surf,(45+v,82+v,38+v),(tx,ty-tr//2),tr)
    pygame.draw.circle(surf,(55+v,98+v,45+v),(tx,ty-tr//2-4),tr-8)


def _bg_gate(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(95,135,185),(155,195,220),(58,85,45))
    _draw_stone_road(surf,W,H,rng)
    # Distant hills
    for hx,hw,hh,hc in [(W//4,220,80,(52,82,42)),(W*3//4,200,70,(48,76,38))]:
        pygame.draw.ellipse(surf,hc,(hx-hw//2,H//2-hh,hw,hh*2))
    # Gate posts
    for gx in [W//2-80, W//2+50]:
        pygame.draw.rect(surf,(115,95,68),(gx,H//2-120,50,150))
        pygame.draw.rect(surf,(85,68,45),(gx,H//2-120,50,150),2)
        for bx in range(gx,gx+50,12):
            pygame.draw.rect(surf,(115,95,68),(bx,H//2-132,10,16))
    # Arch
    pygame.draw.arc(surf,(115,95,68),
                    (W//2-80,H//2-180,180,120),0,math.pi,10)
    # Road out
    pygame.draw.polygon(surf,(100,88,65),[
        (W//2-30,H*2//3),(W//2+30,H*2//3),
        (W//2+60,H),(W//2-60,H)])
    # Trees flanking
    for tx in [W//2-160,W//2+130]:
        _draw_tree(surf,tx,H//2-20,rng,1.2)


def _bg_house(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(108,148,192),(162,200,225),(60,88,47))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)
    # House body
    hx,hy,hw,hh = W//2-90, H//2-80, 180, 130
    pygame.draw.rect(surf,(148,120,85),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(110,88,60),(hx,hy,hw,hh),2)
    # Roof
    pygame.draw.polygon(surf,(100,68,42),[
        (hx-10,hy),(hx+hw//2,hy-70),(hx+hw+10,hy)])
    pygame.draw.polygon(surf,(72,48,28),[
        (hx-10,hy),(hx+hw//2,hy-70),(hx+hw+10,hy)],2)
    # Door
    pygame.draw.rect(surf,(75,52,28),(W//2-18,hy+hh-60,36,60))
    pygame.draw.circle(surf,(160,130,60),(W//2+14,hy+hh-32),5)
    # Windows
    for wx in [hx+20,hx+hw-56]:
        pygame.draw.rect(surf,(180,215,235),(wx,hy+30,36,30))
        pygame.draw.rect(surf,(90,68,45),(wx,hy+30,36,30),2)
        pygame.draw.line(surf,(90,68,45),(wx+18,hy+30),(wx+18,hy+60),1)
    # Chimney + smoke
    pygame.draw.rect(surf,(110,88,60),(hx+hw-40,hy-40,16,45))
    for i in range(3):
        smoke = pygame.Surface((18,18),pygame.SRCALPHA)
        pygame.draw.circle(smoke,(180,180,180,50),(9,9),5+i*2)
        surf.blit(smoke,(hx+hw-38+i*5,hy-50-i*12))
    # Garden fence
    for fx in range(hx-30,hx+hw+30,16):
        pygame.draw.line(surf,(100,78,48),(fx,H*2//3-8),(fx,H*2//3+12),3)
    pygame.draw.line(surf,(110,85,52),(hx-30,H*2//3+2),(hx+hw+30,H*2//3+2),2)
    _draw_tree(surf,hx-50,H//2,rng)


def _bg_inn(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(80,105,145),(140,175,205),(55,80,42))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)
    hx,hy,hw,hh = W//2-110,H//2-100,220,140
    # Body
    pygame.draw.rect(surf,(135,100,58),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(95,70,35),(hx,hy,hw,hh),2)
    # Steep roof
    pygame.draw.polygon(surf,(88,58,28),[
        (hx-8,hy),(hx+hw//2,hy-90),(hx+hw+8,hy)])
    pygame.draw.polygon(surf,(62,40,18),[
        (hx-8,hy),(hx+hw//2,hy-90),(hx+hw+8,hy)],2)
    # Sign hanging from bracket
    pygame.draw.line(surf,(80,58,30),(W//2-8,hy+10),(W//2-8,hy+36),3)
    pygame.draw.rect(surf,(148,108,55),(W//2-38,hy+36,76,22))
    pygame.draw.rect(surf,(100,72,32),(W//2-38,hy+36,76,22),1)
    sign_f = pygame.font.SysFont("courier new",10,bold=True)
    sign_s = sign_f.render("THE RUSTY FLAGON",True,(220,185,100))
    surf.blit(sign_s,(W//2-38+2,hy+40))
    # Door (arched)
    pygame.draw.rect(surf,(65,40,18),(W//2-22,hy+hh-70,44,70))
    pygame.draw.ellipse(surf,(65,40,18),(W//2-22,hy+hh-92,44,46))
    pygame.draw.ellipse(surf,(48,30,12),(W//2-22,hy+hh-92,44,46),2)
    # Windows with warm glow
    pulse = 0.6+0.4*math.sin(time*1.5)
    for wx in [hx+15,hx+hw-55]:
        wsurf = pygame.Surface((38,30),pygame.SRCALPHA)
        wsurf.fill((int(220*pulse),int(160*pulse),int(60*pulse),200))
        surf.blit(wsurf,(wx,hy+40))
        pygame.draw.rect(surf,(80,58,28),(wx,hy+40,38,30),2)
    # Two chimneys
    for cx in [hx+30,hx+hw-42]:
        pygame.draw.rect(surf,(105,80,45),(cx,hy-50,14,55))
        for i in range(3):
            sm = pygame.Surface((16,16),pygame.SRCALPHA)
            pygame.draw.circle(sm,(160,150,140,45),(8,8),4+i*2)
            surf.blit(sm,(cx-2+i*4,hy-62-i*10))
    _draw_tree(surf,hx-55,H//2-10,rng)
    _draw_tree(surf,hx+hw+55,H//2-10,rng)


def _bg_market(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(105,148,195),(165,202,228),(60,88,47))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)
    # Notice board centre
    bx,by = W//2-40,H//2-80
    for px in [bx,bx+64]:
        pygame.draw.rect(surf,(88,62,30),(px,by,10,100))
    pygame.draw.rect(surf,(140,105,55),(bx-6,by-6,86,58))
    pygame.draw.rect(surf,(100,72,32),(bx-6,by-6,86,58),2)
    # Pinned papers
    for i,pc in enumerate([(bx+4,by+4),(bx+30,by+8),(bx+54,by+2)]):
        pygame.draw.rect(surf,(215,200,170),(pc[0],pc[1],20,18))
        pygame.draw.rect(surf,(150,130,95),(pc[0],pc[1],20,18),1)
        pygame.draw.circle(surf,(180,60,40),(pc[0]+10,pc[1]),3)
    # Market stalls left and right
    for sx,sc in [(W//2-200,(110,85,48)),(W//2+100,(95,72,40))]:
        pygame.draw.rect(surf,sc,(sx,H//2-30,90,60))
        # Awning
        pts=[(sx-4,H//2-30),(sx+45,H//2-55),(sx+94,H//2-30)]
        pygame.draw.polygon(surf,(180,65,65),pts)
        pygame.draw.polygon(surf,(140,45,45),pts,2)
    # Cobblestone well
    pygame.draw.circle(surf,(118,95,68),(W//2+130,H//2+20),28)
    pygame.draw.circle(surf,(88,68,42),(W//2+130,H//2+20),28,3)
    pygame.draw.rect(surf,(88,68,42),(W//2+116,H//2-12,4,30))
    pygame.draw.rect(surf,(88,68,42),(W//2+140,H//2-12,4,30))


def _bg_blacksmith(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(70,88,110),(120,148,175),(50,72,40))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)
    hx,hy,hw,hh = W//2-115,H//2-95,230,135
    # Stone building
    pygame.draw.rect(surf,(105,88,65),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(72,58,40),(hx,hy,hw,hh),2)
    # Flat roof with battlements
    pygame.draw.rect(surf,(88,72,50),(hx-5,hy-14,hw+10,16))
    for bx2 in range(hx-5,hx+hw+5,14):
        pygame.draw.rect(surf,(88,72,50),(bx2,hy-26,10,16))
    # Forge window — orange glow
    pulse = 0.5+0.5*math.sin(time*3.5)
    gw=pygame.Surface((60,42),pygame.SRCALPHA)
    gw.fill((int(255*pulse),int(140*pulse),int(20*pulse),210))
    surf.blit(gw,(W//2-30,hy+35))
    pygame.draw.rect(surf,(65,50,30),(W//2-30,hy+35,60,42),2)
    # Door
    pygame.draw.rect(surf,(52,38,18),(W//2-24,hy+hh-72,48,72))
    pygame.draw.rect(surf,(38,28,12),(W//2-24,hy+hh-72,48,72),2)
    # Anvil silhouette outside
    ax,ay = W//2+90,H//2+10
    pygame.draw.rect(surf,(75,68,60),(ax-20,ay,40,12))
    pygame.draw.rect(surf,(75,68,60),(ax-14,ay+12,28,8))
    # Smoke stack
    pygame.draw.rect(surf,(82,65,42),(hx+hw-28,hy-52,18,42))
    for i in range(5):
        sm=pygame.Surface((20,20),pygame.SRCALPHA)
        pygame.draw.circle(sm,(100,90,80,40),(10,10),4+i*2)
        surf.blit(sm,(hx+hw-26+i*3,hy-62-i*14))
    _draw_tree(surf,hx-55,H//2,rng)


def _bg_shop(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(110,155,198),(168,205,228),(62,90,50))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)
    hx,hy,hw,hh = W//2-100,H//2-90,200,128
    # Green building
    pygame.draw.rect(surf,(72,118,68),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(48,85,44),(hx,hy,hw,hh),2)
    # Peaked roof
    pygame.draw.polygon(surf,(55,90,50),[
        (hx-6,hy),(hx+hw//2,hy-75),(hx+hw+6,hy)])
    pygame.draw.polygon(surf,(38,65,34),[
        (hx-6,hy),(hx+hw//2,hy-75),(hx+hw+6,hy)],2)
    # Striped awning
    for i in range(6):
        c = (210,55,55) if i%2==0 else (240,240,240)
        pygame.draw.rect(surf,c,(hx+i*(hw//6),hy-2,hw//6,12))
    # Display window
    pygame.draw.rect(surf,(195,225,218),(W//2-50,hy+38,100,42))
    pygame.draw.rect(surf,(45,78,40),(W//2-50,hy+38,100,42),2)
    # Door
    pygame.draw.rect(surf,(58,42,22),(W//2-20,hy+hh-60,40,60))
    pygame.draw.circle(surf,(165,135,60),(W//2+16,hy+hh-32),4)
    # Hanging flower baskets
    for bx2 in [hx+10,hx+hw-26]:
        pygame.draw.rect(surf,(88,62,30),(bx2,hy+8,16,12))
        pygame.draw.circle(surf,(195,65,80),(bx2+8,hy+6),8)
    _draw_tree(surf,hx+hw+60,H//2,rng)


def _bg_antiquity(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(55,45,80),(105,88,140),(48,68,40))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)
    hx,hy,hw,hh = W//2-95,H//2-105,190,140
    # Purple building
    pygame.draw.rect(surf,(88,60,118),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(60,38,85),(hx,hy,hw,hh),2)
    # Dome
    pygame.draw.ellipse(surf,(72,48,100),(hx,hy-hw//3,hw,hw//2+hw//3))
    pygame.draw.ellipse(surf,(50,32,72),(hx,hy-hw//3,hw,hw//2+hw//3),2)
    # Mystical window
    pulse = 0.5+0.5*math.sin(time*1.8)
    wsurf = pygame.Surface((48,48),pygame.SRCALPHA)
    pygame.draw.circle(wsurf,(int(180*pulse),int(120*pulse),int(255*pulse),180),(24,24),22)
    surf.blit(wsurf,(W//2-24,hy+28))
    pygame.draw.circle(surf,(55,35,75),(W//2,hy+52),22,2)
    for a in range(0,360,60):
        ra=math.radians(a)
        pygame.draw.line(surf,(int(160*pulse),int(100*pulse),int(220*pulse)),
                         (W//2+int(math.cos(ra)*14),hy+52+int(math.sin(ra)*14)),
                         (W//2+int(math.cos(ra)*22),hy+52+int(math.sin(ra)*22)),1)
    # Arched door
    pygame.draw.rect(surf,(38,22,52),(W//2-20,hy+hh-66,40,66))
    pygame.draw.ellipse(surf,(38,22,52),(W//2-20,hy+hh-88,40,44))


def _bg_dungeon(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(30,22,18),(62,48,38),(35,28,18))
    _draw_stone_road(surf,W,H,rng)
    # Stone archway
    aw = 120; ax = W//2-aw//2; ay = H//2-130
    pygame.draw.rect(surf,(62,50,35),(ax-18,ay,18,180))
    pygame.draw.rect(surf,(48,38,24),(ax-18,ay,18,180),2)
    pygame.draw.rect(surf,(62,50,35),(ax+aw,ay,18,180))
    pygame.draw.rect(surf,(48,38,24),(ax+aw,ay,18,180),2)
    # Arch
    pygame.draw.arc(surf,(62,50,35),(ax-18,ay-60,aw+36,120),0,math.pi,16)
    # Dark void
    vsurf=pygame.Surface((aw,H//3+20),pygame.SRCALPHA)
    vsurf.fill((4,3,2,245))
    surf.blit(vsurf,(ax,ay))
    # Steps down
    for i in range(4):
        sw=aw-i*12; sx=ax+i*6; sy=ay+H//3-i*12
        pygame.draw.rect(surf,(52,42,28),(sx,sy,sw,10))
    # Red glow from inside
    pulse=0.4+0.4*math.sin(time*2.2)
    gsurf=pygame.Surface((aw,80),pygame.SRCALPHA)
    pygame.draw.ellipse(gsurf,(int(160*pulse),int(20*pulse),int(20*pulse),
                                int(80*pulse)),(0,0,aw,80))
    surf.blit(gsurf,(ax,ay+H//3-50))
    # Skull above arch
    skx,sky=W//2,ay-28
    pygame.draw.circle(surf,(175,165,148),(skx,sky),18)
    pygame.draw.circle(surf,(38,28,16),(skx,sky),18,2)
    pygame.draw.line(surf,(38,28,16),(skx-6,sky),(skx+6,sky),2)
    for ex in [skx-7,skx+7]:
        pygame.draw.circle(surf,(18,12,8),(ex,sky-2),5)
    # Dead trees
    for tx,side in [(ax-80,1),(ax+aw+80,-1)]:
        pygame.draw.line(surf,(55,42,25),(tx,H*2//3),(tx,H//2-40),4)
        for i in range(3):
            bx2=tx+side*(15+i*12); by2=H//2-20-i*25
            pygame.draw.line(surf,(50,38,22),(tx,by2),(bx2,by2-10),2)



def _draw_town_backdrop(surf, W, H, rng, exclude_self=True):
    """Draw two large flanking buildings on each side."""
    ground_y = H * 2 // 3
    # (x_fraction, width, height)
    side_buildings = [
        (0.13, 130, 145),
        (0.28, 110, 125),
        (0.72, 110, 125),
        (0.87, 130, 145),
    ]
    for xf, bw2, bh2 in side_buildings:
        bx2 = int(W * xf)
        by2 = ground_y - bh2
        v   = rng.randint(-6, 6)
        col  = (105+v, 85+v, 60+v)
        dark = (72+v,  55+v, 35+v)
        # Body
        pygame.draw.rect(surf, col,  (bx2-bw2//2, by2, bw2, bh2))
        pygame.draw.rect(surf, dark, (bx2-bw2//2, by2, bw2, bh2), 2)
        # Pitched roof
        rh = bh2 // 3
        pygame.draw.polygon(surf, (82+v, 58+v, 32+v), [
            (bx2-bw2//2-5, by2),
            (bx2,           by2-rh),
            (bx2+bw2//2+5, by2)])
        pygame.draw.polygon(surf, (58+v, 40+v, 20+v), [
            (bx2-bw2//2-5, by2),
            (bx2,           by2-rh),
            (bx2+bw2//2+5, by2)], 2)
        # Two windows
        ww2 = bw2 // 5; wh2 = bh2 // 5
        wy2 = by2 + bh2 // 4
        for wx_off in [-bw2//4, bw2//4 - ww2//2]:
            pygame.draw.rect(surf, (175, 210, 225),
                             (bx2+wx_off-ww2//2, wy2, ww2, wh2))
            pygame.draw.rect(surf, (65, 50, 30),
                             (bx2+wx_off-ww2//2, wy2, ww2, wh2), 1)
            pygame.draw.line(surf, (65, 50, 30),
                             (bx2+wx_off, wy2),
                             (bx2+wx_off, wy2+wh2), 1)
        # Door on the wider buildings
        if bw2 >= 130:
            dw2 = bw2 // 5; dh2 = bh2 // 3
            pygame.draw.rect(surf, (58, 40, 18),
                             (bx2-dw2//2, by2+bh2-dh2, dw2, dh2))
        # Chimney
        pygame.draw.rect(surf, dark,
                         (bx2+bw2//4-5, by2-rh-18, 10, 22))

BG_FUNCS = {
    "gate":       _bg_gate,
    "house":      _bg_house,
    "inn":        _bg_inn,
    "market":     _bg_market,
    "blacksmith": _bg_blacksmith,
    "shop":       _bg_shop,
    "antiquity":  _bg_antiquity,
    "dungeon":    _bg_dungeon,
}


# ---------------------------------------------------------------------------
# TownScene
# ---------------------------------------------------------------------------

class TownScene:
    SLIDE_DUR = 0.32

    def __init__(self, screen, inventory, town_name="Ashenvale", start_idx=0):
        self.screen     = screen
        self.W, self.H  = screen.get_size()
        self.clock      = pygame.time.Clock()
        self.time       = 0.0
        self.inventory  = inventory
        self.town_name  = town_name

        self.font_title  = pygame.font.SysFont("courier new", 34, bold=True)
        self.font_sub    = pygame.font.SysFont("courier new", 16)
        self.font_small  = pygame.font.SysFont("courier new", 14)
        self.font_tiny   = pygame.font.SysFont("courier new", 12)

        self.idx     = start_idx  # current area index
        self.sliding = False
        self.slide_t = 0.0
        self.slide_dir = 1        # +1 = going right, -1 = going left
        self.next_idx  = 0

        # Pre-render all area backgrounds
        self._bgs = self._build_bgs()
        self._rng = random.Random(42)

        # Notice popup
        self._show_notice = False
        self._notice_idx  = 0

        self.open_anim = 0.0
        self.OPEN_DUR  = 0.4

        # Arrow button hover
        self._left_hover  = 0.0
        self._right_hover = 0.0

    # ------------------------------------------------------------------ #

    def _build_bgs(self):
        bgs = []
        rng = random.Random(77)
        for area in AREAS:
            surf = pygame.Surface((self.W, self.H))
            fn   = BG_FUNCS.get(area["bg"])
            if fn:
                fn(surf, self.W, self.H, rng, 0.0)
            else:
                surf.fill((20,15,10))
            bgs.append(surf)
        return bgs

    # BG types that have animation needing per-frame redraw
    ANIMATED_BGS = {"inn", "blacksmith", "antiquity", "dungeon"}

    def _redraw_bg(self, idx):
        """Only redraw animated bg types each frame; static ones are pre-baked."""
        if AREAS[idx]["bg"] in self.ANIMATED_BGS:
            surf = self._bgs[idx]
            fn   = BG_FUNCS.get(AREAS[idx]["bg"])
            if fn:
                # Use a fixed rng so static elements don't shimmer
                fn(surf, self.W, self.H, random.Random(idx*100), self.time)

    # ------------------------------------------------------------------ #
    # Drawing helpers
    # ------------------------------------------------------------------ #

    def _draw_area(self, surf_idx, x_offset):
        """Draw one area background at a horizontal offset."""
        self.screen.blit(self._bgs[surf_idx], (x_offset, 0))
        self._draw_overlay(surf_idx, x_offset)

    def _draw_overlay(self, area_idx, ox):
        """Draw UI overlay (name, arrows, action prompt) on top of bg."""
        area = AREAS[area_idx]

        # Bottom gradient overlay
        grad = pygame.Surface((self.W, 100), pygame.SRCALPHA)
        for y in range(100):
            a = int(180 * (y/100)**0.6)
            pygame.draw.line(grad,(0,0,0,a),(0,y),(self.W,y))
        self.screen.blit(grad,(ox, self.H-100))

        # Top gradient
        tgrad = pygame.Surface((self.W, 80), pygame.SRCALPHA)
        for y in range(80):
            a = int(140 * ((80-y)/80)**1.2)
            pygame.draw.line(tgrad,(0,0,0,a),(0,y),(self.W,y))
        self.screen.blit(tgrad,(ox,0))

        # Area name
        name_s = self.font_title.render(area["name"], True, (225,195,130))
        sh_s   = self.font_title.render(area["name"], True, (20,14,6))
        self.screen.blit(sh_s, (ox+self.W//2-name_s.get_width()//2+2, self.H-78))
        self.screen.blit(name_s,(ox+self.W//2-name_s.get_width()//2,   self.H-80))

        # Subtitle
        sub_s = self.font_sub.render(area["subtitle"], True, (150,120,68))
        self.screen.blit(sub_s,(ox+self.W//2-sub_s.get_width()//2, self.H-48))

        # Action prompt
        if area["action_label"]:
            ap = self.font_small.render(area["action_label"], True,(210,185,110))
            bg = pygame.Surface((ap.get_width()+20,ap.get_height()+8),pygame.SRCALPHA)
            bg.fill((10,8,5,180))
            bx = ox+self.W//2-bg.get_width()//2
            by = self.H//2+80
            self.screen.blit(bg,(bx,by))
            pygame.draw.rect(self.screen,(100,80,42),(bx,by,bg.get_width(),bg.get_height()),1)
            self.screen.blit(ap,(bx+10,by+4))

    def _draw_arrows(self, ease):
        """Draw left/right navigation arrows."""
        alpha = int(255*ease)
        can_left  = self.idx > 0
        can_right = self.idx < len(AREAS)-1
        cy = self.H//2

        for side, can, hover_v, label in [
            ("left",  can_left,  self._left_hover,  "◀"),
            ("right", can_right, self._right_hover, "▶"),
        ]:
            ax = 40 if side=="left" else self.W-40
            tc = _lerp_col((80,62,32),(220,185,90),hover_v) if can else (40,32,18)
            bc = _lerp_col((50,38,20),(160,130,60),hover_v) if can else (25,18,8)
            r  = int(28 + 6*hover_v)

            circ = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(circ,(18,13,7,int(180+40*hover_v)),(r,r),r)
            pygame.draw.circle(circ,bc,(r,r),r,2)
            circ.set_alpha(alpha)
            self.screen.blit(circ,(ax-r,cy-r))

            arr = self.font_title.render(label, True, tc)
            as2 = pygame.Surface(arr.get_size(),pygame.SRCALPHA)
            as2.blit(arr,(0,0)); as2.set_alpha(alpha)
            self.screen.blit(as2,(ax-arr.get_width()//2, cy-arr.get_height()//2))

    def _draw_position_dots(self, ease):
        """Row of dots showing current position."""
        n   = len(AREAS)
        dw  = 10; gap = 6
        total_w = n*(dw+gap)-gap
        sx  = self.W//2 - total_w//2
        y   = self.H - 16
        for i in range(n):
            col = (220,185,90) if i==self.idx else (60,48,25)
            r   = 5 if i==self.idx else 3
            dot = pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(dot,col,(r,r),r)
            dot.set_alpha(int(255*ease))
            self.screen.blit(dot,(sx+i*(dw+gap)+(dw//2-r),y-r))

    def _draw_hints(self, ease):
        hint = self.font_tiny.render(
            "◀ ▶  navigate    I  inventory    ESC  menu",
            True,(100,80,42))
        hs   = pygame.Surface(hint.get_size(),pygame.SRCALPHA)
        hs.blit(hint,(0,0)); hs.set_alpha(int(200*ease))
        self.screen.blit(hs,(self.W//2-hint.get_width()//2,8))

    def _draw_notice_popup(self):
        notice = NOTICES[self._notice_idx % len(NOTICES)]
        pw,ph  = int(self.W*0.48),int(self.H*0.26)
        px     = self.W//2-pw//2; py = self.H//2-ph//2

        bg = pygame.Surface((pw,ph),pygame.SRCALPHA)
        bg.fill((18,13,7,240))
        self.screen.blit(bg,(px,py))
        pygame.draw.rect(self.screen,(120,92,48),(px,py,pw,ph),2)
        pygame.draw.rect(self.screen,(70,52,26),(px+5,py+5,pw-10,ph-10),1)

        c2 = (140,108,56); sz=10
        for bx2,by2,dx,dy in [(px,py,1,1),(px+pw,py,-1,1),
                               (px,py+ph,1,-1),(px+pw,py+ph,-1,-1)]:
            pygame.draw.line(self.screen,c2,(bx2,by2),(bx2+dx*sz,by2),2)
            pygame.draw.line(self.screen,c2,(bx2,by2),(bx2,by2+dy*sz),2)

        font_m = pygame.font.SysFont("courier new",18,bold=True)
        title  = font_m.render("— NOTICE BOARD —",True,(200,165,90))
        self.screen.blit(title,(self.W//2-title.get_width()//2,py+10))

        ctr = self.font_tiny.render(
            f"{self._notice_idx+1} / {len(NOTICES)}",True,(90,68,38))
        self.screen.blit(ctr,(px+pw-ctr.get_width()-10,py+10))

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
            "← →  browse    ESC / E  close",True,(75,56,28))
        self.screen.blit(hint,(self.W//2-hint.get_width()//2,py+ph-hint.get_height()-8))

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #

    def _start_slide(self, direction):
        """Begin a slide animation. direction: +1=right, -1=left."""
        new_idx = self.idx + direction
        if new_idx < 0 or new_idx >= len(AREAS):
            return
        self.sliding   = True
        self.slide_t   = 0.0
        self.slide_dir = direction
        self.next_idx  = new_idx

    def _arrow_rects(self):
        cy = self.H//2
        left  = pygame.Rect(12,  cy-34, 56, 68)
        right = pygame.Rect(self.W-68, cy-34, 56, 68)
        return left, right

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while True:
            dt          = self.clock.tick(60)/1000.0
            self.time  += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            ease        = 1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            mouse       = pygame.mouse.get_pos()
            left_r, right_r = self._arrow_rects()

            # Hover
            tl = 1.0 if left_r.collidepoint(mouse)  and self.idx>0             else 0.0
            tr = 1.0 if right_r.collidepoint(mouse) and self.idx<len(AREAS)-1  else 0.0
            self._left_hover  += (tl-self._left_hover)*10*dt
            self._right_hover += (tr-self._right_hover)*10*dt
            self._left_hover   = max(0.0,min(1.0,self._left_hover))
            self._right_hover  = max(0.0,min(1.0,self._right_hover))

            # Slide animation
            if self.sliding:
                self.slide_t += dt
                if self.slide_t >= self.SLIDE_DUR:
                    self.sliding = False
                    self.idx     = self.next_idx

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ("exit", self.idx)

                if event.type == pygame.KEYDOWN:
                    if self._show_notice:
                        if event.key == pygame.K_RIGHT:
                            self._notice_idx = (self._notice_idx+1)%len(NOTICES)
                        if event.key == pygame.K_LEFT:
                            self._notice_idx = (self._notice_idx-1)%len(NOTICES)
                        if event.key in (pygame.K_ESCAPE,pygame.K_e):
                            self._show_notice = False
                        continue

                    if event.key == pygame.K_ESCAPE:
                        return ("pause", self.idx)
                    if event.key == pygame.K_i:
                        return ("inventory", self.idx)
                    if event.key == pygame.K_LEFT and not self.sliding:
                        self._start_slide(-1)
                    if event.key == pygame.K_RIGHT and not self.sliding:
                        self._start_slide(1)

                    if event.key == pygame.K_e and not self.sliding:
                        area = AREAS[self.idx]
                        if area["action_key"] == "notice":
                            self._show_notice = True
                            self._notice_idx  = 0
                        elif area["action_key"]:
                            return (area["action_key"], self.idx)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                    if self._show_notice:
                        self._show_notice = False
                        continue
                    if left_r.collidepoint(mouse) and not self.sliding:
                        self._start_slide(-1)
                    elif right_r.collidepoint(mouse) and not self.sliding:
                        self._start_slide(1)

            # --- Draw ---
            if self.sliding:
                # Ease: cubic out
                raw  = self.slide_t/self.SLIDE_DUR
                prog = 1-(1-raw)**3
                offset = int(self.W * prog * -self.slide_dir)
                # Current area slides out
                self._redraw_bg(self.idx)
                self._draw_area(self.idx, offset)
                # Next area slides in
                self._redraw_bg(self.next_idx)
                self._draw_area(self.next_idx,
                                offset + self.W*self.slide_dir)
            else:
                self._redraw_bg(self.idx)
                self._draw_area(self.idx, 0)

            self._draw_arrows(ease)
            self._draw_position_dots(ease)
            self._draw_hints(ease)

            if self._show_notice:
                self._draw_notice_popup()

            pygame.display.flip()