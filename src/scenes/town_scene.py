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
        "action":   "notice_board",
        "action_label": "[ E ]  Read notices",
        "action_key":   "notice_board",
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
    # Build gradient as a tiny 1-pixel-wide strip then scale — much faster than per-line draws
    half = H // 2
    sky_strip = pygame.Surface((1, half))
    for y in range(half):
        t = y / half
        c = _lerp_col(sky_top, sky_bot, t)
        sky_strip.set_at((0, y), c)
    surf.blit(pygame.transform.scale(sky_strip, (W, half)), (0, 0))

    ground_dark = tuple(max(0, v-15) for v in ground_col)
    gnd_strip = pygame.Surface((1, H - half))
    for y in range(H - half):
        t = y / max(1, H - half)
        c = _lerp_col(ground_col, ground_dark, t)
        gnd_strip.set_at((0, y), c)
    surf.blit(pygame.transform.scale(gnd_strip, (W, H - half)), (0, half))


def _draw_stone_road(surf, W, H, rng):
    ry = H*2//3
    # Fill road base with a flat colour then add cobble rects — no per-pixel lines
    pygame.draw.rect(surf, (118, 103, 83), (0, ry, W, H - ry))
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
    _draw_sky(surf,W,H,(88,128,178),(148,188,215),(55,82,42))
    _draw_stone_road(surf,W,H,rng)

    ground = H*2//3

    # Distant rolling hills
    for hx2,hw2,hh2,hc in [(W//5,280,90,(48,78,38)),(W*4//5,260,80,(44,72,34)),
                             (W//2-60,200,60,(52,84,42))]:
        pygame.draw.ellipse(surf,hc,(hx2-hw2//2,ground-hh2,hw2,hh2*2))

    # Town wall extending left and right from gate — crenellated
    wall_h = 55; wall_y = ground - wall_h
    # Left wall section
    pygame.draw.rect(surf,(118,98,70),(0, wall_y, W//2-82, wall_h))
    pygame.draw.rect(surf,(88,70,48),(0, wall_y, W//2-82, wall_h), 2)
    for bx2 in range(0, W//2-82, 20):
        pygame.draw.rect(surf,(118,98,70),(bx2, wall_y-16, 14, 18))
        pygame.draw.rect(surf,(88,70,48),(bx2, wall_y-16, 14, 18), 1)
    # Right wall section
    pygame.draw.rect(surf,(118,98,70),(W//2+82, wall_y, W-W//2-82, wall_h))
    pygame.draw.rect(surf,(88,70,48),(W//2+82, wall_y, W-W//2-82, wall_h), 2)
    for bx2 in range(W//2+82, W, 20):
        pygame.draw.rect(surf,(118,98,70),(bx2, wall_y-16, 14, 18))
        pygame.draw.rect(surf,(88,70,48),(bx2, wall_y-16, 14, 18), 1)

    # LEFT tower — tall, wide, battlemented
    tx1 = W//2 - 105; tw = 68; th = 185
    ty1 = ground - th
    # Tower body
    pygame.draw.rect(surf,(108,88,62),(tx1, ty1, tw, th))
    pygame.draw.rect(surf,(75,60,40),(tx1, ty1, tw, th), 3)
    # Stone block texture
    blk_rng = random.Random(12)
    for row in range(8):
        for col in range(3):
            bsx=tx1+2+col*(tw//3); bsy=ty1+4+row*(th//8)
            v=blk_rng.randint(-5,5)
            pygame.draw.rect(surf,(100+v,82+v,58+v),(bsx,bsy,tw//3-3,th//8-3),1)
    # Tower top platform
    pygame.draw.rect(surf,(122,102,72),(tx1-6, ty1-12, tw+12, 14))
    pygame.draw.rect(surf,(88,70,48),(tx1-6, ty1-12, tw+12, 14), 2)
    # Battlements
    for bx2 in range(tx1-6, tx1+tw+6, 16):
        pygame.draw.rect(surf,(122,102,72),(bx2, ty1-28, 11, 18))
        pygame.draw.rect(surf,(88,70,48),(bx2, ty1-28, 11, 18), 1)
    # Arrow slit windows
    for wy2 in [ty1+30, ty1+70, ty1+110]:
        pygame.draw.rect(surf,(35,22,12),(tx1+tw//2-4, wy2, 8, 20))
        pygame.draw.polygon(surf,(35,22,12),[(tx1+tw//2-4,wy2),(tx1+tw//2+4,wy2),(tx1+tw//2,wy2-8)])
    # Tower flag — left
    pygame.draw.line(surf,(88,70,48),(tx1+tw//2, ty1-28),(tx1+tw//2, ty1-60), 3)
    pygame.draw.polygon(surf,(165,45,45),[(tx1+tw//2,ty1-60),(tx1+tw//2+22,ty1-52),(tx1+tw//2,ty1-44)])

    # RIGHT tower — mirror
    tx2 = W//2 + 37
    pygame.draw.rect(surf,(108,88,62),(tx2, ty1, tw, th))
    pygame.draw.rect(surf,(75,60,40),(tx2, ty1, tw, th), 3)
    for row in range(8):
        for col in range(3):
            bsx=tx2+2+col*(tw//3); bsy=ty1+4+row*(th//8)
            v=blk_rng.randint(-5,5)
            pygame.draw.rect(surf,(100+v,82+v,58+v),(bsx,bsy,tw//3-3,th//8-3),1)
    pygame.draw.rect(surf,(122,102,72),(tx2-6, ty1-12, tw+12, 14))
    pygame.draw.rect(surf,(88,70,48),(tx2-6, ty1-12, tw+12, 14), 2)
    for bx2 in range(tx2-6, tx2+tw+6, 16):
        pygame.draw.rect(surf,(122,102,72),(bx2, ty1-28, 11, 18))
        pygame.draw.rect(surf,(88,70,48),(bx2, ty1-28, 11, 18), 1)
    for wy2 in [ty1+30, ty1+70, ty1+110]:
        pygame.draw.rect(surf,(35,22,12),(tx2+tw//2-4, wy2, 8, 20))
        pygame.draw.polygon(surf,(35,22,12),[(tx2+tw//2-4,wy2),(tx2+tw//2+4,wy2),(tx2+tw//2,wy2-8)])
    pygame.draw.line(surf,(88,70,48),(tx2+tw//2, ty1-28),(tx2+tw//2, ty1-60), 3)
    pygame.draw.polygon(surf,(165,45,45),[(tx2+tw//2,ty1-60),(tx2+tw//2-22,ty1-52),(tx2+tw//2,ty1-44)])

    # Gate arch — spanning between towers
    arch_x = tx1+tw; arch_w = tx2-tx1-tw; arch_cx = W//2
    arch_top = ty1+40
    # Arch fill (dark passage)
    pygame.draw.rect(surf,(22,14,8),(arch_x, arch_top, arch_w, ground-arch_top))
    # Arch curve
    arch_r = arch_w//2
    pygame.draw.arc(surf,(22,14,8),(arch_cx-arch_r, arch_top-arch_r, arch_r*2, arch_r*2),
                    0, math.pi, arch_r)
    # Arch stone surround — thick decorative border
    pygame.draw.arc(surf,(128,105,72),(arch_cx-arch_r-6, arch_top-arch_r-6, arch_r*2+12, arch_r*2+12),
                    0, math.pi, 8)
    pygame.draw.arc(surf,(88,70,48),(arch_cx-arch_r-10, arch_top-arch_r-10, arch_r*2+20, arch_r*2+20),
                    0, math.pi, 4)
    # Keystone
    pygame.draw.polygon(surf,(148,120,82),[
        (arch_cx-10, arch_top-arch_r-8),(arch_cx+10, arch_top-arch_r-8),
        (arch_cx+7, arch_top-arch_r+14),(arch_cx-7, arch_top-arch_r+14)])
    pygame.draw.polygon(surf,(88,70,48),[
        (arch_cx-10, arch_top-arch_r-8),(arch_cx+10, arch_top-arch_r-8),
        (arch_cx+7, arch_top-arch_r+14),(arch_cx-7, arch_top-arch_r+14)], 2)
    # Portcullis bars visible in shadow
    for bar_x in range(arch_x+4, arch_x+arch_w-4, 8):
        pygame.draw.line(surf,(38,28,18),(bar_x, arch_top),(bar_x, ground), 2)
    for bar_y in [arch_top+20, arch_top+40, arch_top+60]:
        pygame.draw.line(surf,(38,28,18),(arch_x+2, bar_y),(arch_x+arch_w-2, bar_y), 2)
    # Gate arch side walls
    pygame.draw.rect(surf,(108,88,62),(arch_x, arch_top, 8, ground-arch_top))
    pygame.draw.rect(surf,(108,88,62),(arch_x+arch_w-8, arch_top, 8, ground-arch_top))

    # Town name sign above gate
    sign_y = ty1 - 8
    pygame.draw.rect(surf,(88,62,30),(arch_cx-52, sign_y-26, 104, 28))
    pygame.draw.rect(surf,(120,90,48),(arch_cx-52, sign_y-26, 104, 28), 2)
    for cx2 in [arch_cx-44, arch_cx+40]:
        pygame.draw.line(surf,(88,62,30),(cx2, sign_y-28),(cx2, ty1-30), 2)
    sf = pygame.font.SysFont("courier new",12,bold=True)
    ss = sf.render("ASHENVALE",True,(220,190,130))
    surf.blit(ss,(arch_cx-ss.get_width()//2, sign_y-22))

    # Torch brackets on towers — flanking the gate
    for tcx,tside in [(tx1+tw-4,-1),(tx2+4,1)]:
        tcy = ty1+45
        pygame.draw.line(surf,(80,58,28),(tcx,tcy),(tcx+tside*14,tcy-8),3)
        pygame.draw.rect(surf,(85,62,28),(tcx+tside*10,tcy-22,6,14))
        tp=0.7+0.3*math.sin(time*3.8+tcx*0.02)
        pygame.draw.polygon(surf,(int(230*tp),int(130*tp),20),[
            (tcx+tside*13,tcy-22),(tcx+tside*13,tcy-34),(tcx+tside*17,tcy-26)])
        tgs=pygame.Surface((28,28),pygame.SRCALPHA)
        pygame.draw.circle(tgs,(int(200*tp),int(110*tp),20,int(55*tp)),(14,14),12)
        surf.blit(tgs,(tcx+tside*13-14,tcy-34-6),special_flags=pygame.BLEND_RGBA_ADD)

    # Road perspective leading through gate
    pygame.draw.polygon(surf,(95,82,62),[
        (W//2-28,ground),(W//2+28,ground),(W//2+14,H),(W//2-14,H)])

    # Flanking trees — large, stately
    _draw_tree(surf,tx1-80,ground+2,rng,1.4)
    _draw_tree(surf,tx2+tw+60,ground+2,rng,1.3)


def _bg_house(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(108,148,192),(162,200,225),(60,88,47))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)
    hx,hy,hw,hh = W//2-90, H//2-80, 180, 130
    pygame.draw.rect(surf,(148,120,85),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(110,88,60),(hx,hy,hw,hh),2)
    pygame.draw.polygon(surf,(100,68,42),[(hx-10,hy),(hx+hw//2,hy-70),(hx+hw+10,hy)])
    pygame.draw.polygon(surf,(72,48,28),[(hx-10,hy),(hx+hw//2,hy-70),(hx+hw+10,hy)],2)
    pygame.draw.rect(surf,(75,52,28),(W//2-18,hy+hh-60,36,60))
    pygame.draw.circle(surf,(160,130,60),(W//2+14,hy+hh-32),5)
    for wx in [hx+20,hx+hw-56]:
        pygame.draw.rect(surf,(180,215,235),(wx,hy+30,36,30))
        pygame.draw.rect(surf,(90,68,45),(wx,hy+30,36,30),2)
        pygame.draw.line(surf,(90,68,45),(wx+18,hy+30),(wx+18,hy+60),1)
    pygame.draw.rect(surf,(110,88,60),(hx+hw-40,hy-40,16,45))
    for i in range(3):
        smoke = pygame.Surface((18,18),pygame.SRCALPHA)
        pygame.draw.circle(smoke,(180,180,180,50),(9,9),5+i*2)
        surf.blit(smoke,(hx+hw-38+i*5,hy-50-i*12))
    for fx in range(hx-30,hx+hw+30,16):
        pygame.draw.line(surf,(100,78,48),(fx,H*2//3-8),(fx,H*2//3+12),3)
    pygame.draw.line(surf,(110,85,52),(hx-30,H*2//3+2),(hx+hw+30,H*2//3+2),2)
    _draw_tree(surf,hx-50,H//2,rng)


def _bg_inn(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(55,72,105),(110,140,180),(45,68,38))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)

    pulse  = 0.6+0.4*math.sin(time*1.5)
    ground = H*2//3

    hw,hh = 260,140
    hx = W//2-hw//2
    hy = ground-hh

    pygame.draw.rect(surf,(78,65,48),(hx-4,ground-8,hw+8,12))
    pygame.draw.rect(surf,(145,110,62),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(98,72,38),(hx,hy,hw,hh),2)

    beam=(82,58,28)
    for bx2 in [hx+hw//3, hx+hw*2//3]:
        pygame.draw.line(surf,beam,(bx2,hy),(bx2,ground-8),3)
    pygame.draw.line(surf,beam,(hx,hy+hh//2),(hx+hw,hy+hh//2),2)
    pygame.draw.line(surf,beam,(hx,hy),(hx+hw//3,hy+hh//2),2)
    pygame.draw.line(surf,beam,(hx+hw,hy),(hx+hw*2//3,hy+hh//2),2)

    apex=(W//2,hy-95)
    roof_l=(hx-10,hy); roof_r=(hx+hw+10,hy)
    pygame.draw.polygon(surf,(88,65,30),[roof_l,apex,roof_r])
    pygame.draw.polygon(surf,(62,44,18),[roof_l,apex,roof_r],2)
    for i in range(1,7):
        frac=i/7
        xl=int(roof_l[0]+(apex[0]-roof_l[0])*frac)
        xr=int(roof_r[0]+(apex[0]-roof_r[0])*frac)
        ty2=int(roof_l[1]+(apex[1]-roof_l[1])*frac)
        pygame.draw.line(surf,(72,52,22),(xl,ty2),(xr,ty2),1)

    for chx in [hx+50,hx+hw-62]:
        pygame.draw.rect(surf,(108,82,48),(chx,hy-55,16,58))
        pygame.draw.rect(surf,(82,62,32),(chx,hy-55,16,58),1)
        pygame.draw.rect(surf,(122,95,55),(chx-3,hy-60,22,8))
        for si in range(3):
            sa=0.3+0.25*math.sin(time*1.8+si*1.5+chx*0.01)
            sm=pygame.Surface((18,18),pygame.SRCALPHA)
            pygame.draw.circle(sm,(158,148,135,int(45*sa)),(9,9),4+si*2)
            surf.blit(sm,(chx-1+si*2,hy-66-si*10))

    win_cols=[(hx+18,hy+18,46,32),(hx+hw-64,hy+18,46,32),
              (hx+20,hy+hh//2+8,38,26),(hx+hw-58,hy+hh//2+8,38,26)]
    for wx,wy,ww2,wh2 in win_cols:
        pygame.draw.rect(surf,(72,50,22),(wx-2,wy-2,ww2+4,wh2+4))
        wsurf=pygame.Surface((ww2,wh2),pygame.SRCALPHA)
        wsurf.fill((int(220*pulse),int(155*pulse),int(50*pulse),185))
        surf.blit(wsurf,(wx,wy))
        pygame.draw.rect(surf,(72,50,22),(wx,wy,ww2,wh2),2)
        pygame.draw.line(surf,(72,50,22),(wx+ww2//2,wy),(wx+ww2//2,wy+wh2),1)
        pygame.draw.line(surf,(72,50,22),(wx,wy+wh2//2),(wx+ww2,wy+wh2//2),1)

    dx=W//2-22; dh=68; dw=44
    pygame.draw.rect(surf,(58,36,14),(dx,ground-dh,dw,dh-8))
    pygame.draw.ellipse(surf,(58,36,14),(dx,ground-dh-18,dw,36))
    pygame.draw.ellipse(surf,(42,26,8),(dx,ground-dh-18,dw,36),2)
    for pi in range(3):
        pygame.draw.line(surf,(46,28,10),(dx+4+pi*14,ground-dh),(dx+4+pi*14,ground-10),1)
    pygame.draw.circle(surf,(155,125,50),(dx+dw-8,ground-dh//2),3)

    for tx2 in [dx-22, dx+dw+8]:
        pygame.draw.line(surf,(70,50,25),(tx2,ground-dh-5),(tx2,ground-dh+10),3)
        pygame.draw.line(surf,(70,50,25),(tx2,ground-dh-5),(tx2+6,ground-dh-15),2)
        pygame.draw.rect(surf,(80,58,28),(tx2+2,ground-dh-20,4,14))
        fp=0.65+0.35*math.sin(time*4+tx2)
        pygame.draw.polygon(surf,(int(220*fp),int(110*fp),15),[
            (tx2+4,ground-dh-20),(tx2+4,ground-dh-30),(tx2+8,ground-dh-22)])

    sx=W//2; sy=hy+10
    pygame.draw.line(surf,(75,55,25),(sx,sy),(sx,sy+22),3)
    pygame.draw.line(surf,(75,55,25),(sx-30,sy),(sx+30,sy),3)
    pygame.draw.rect(surf,(150,112,52),(sx-42,sy+22,84,24))
    pygame.draw.rect(surf,(105,75,32),(sx-42,sy+22,84,24),2)
    for cx2 in [sx-36,sx+36]:
        pygame.draw.line(surf,(90,65,30),(cx2,sy),(cx2,sy+22),1)
    sf=pygame.font.SysFont("courier new",10,bold=True)
    ss=sf.render("THE RUSTY FLAGON",True,(230,195,105))
    surf.blit(ss,(sx-ss.get_width()//2,sy+26))

    for bx2 in [dx-36,dx+dw+10]:
        bw2=26; bh2=32
        pygame.draw.rect(surf,(85,62,30),(bx2,ground-bh2,bw2,bh2))
        pygame.draw.ellipse(surf,(100,75,38),(bx2,ground-bh2-5,bw2,12))
        pygame.draw.ellipse(surf,(100,75,38),(bx2,ground-8,bw2,12))
        for bi in [ground-bh2+8,ground-bh2+18]:
            pygame.draw.line(surf,(65,48,22),(bx2,bi),(bx2+bw2,bi),2)

    nb_x=hx-90; nb_y=ground-70
    for px2 in [nb_x+2,nb_x+58]:
        pygame.draw.rect(surf,(82,60,28),(px2,nb_y+10,5,58))
    pygame.draw.rect(surf,(138,105,55),(nb_x,nb_y,65,48))
    pygame.draw.rect(surf,(100,72,36),(nb_x,nb_y,65,48),2)
    for pi,(ppx,ppy) in enumerate([(nb_x+4,nb_y+4),(nb_x+32,nb_y+6),(nb_x+8,nb_y+26)]):
        pygame.draw.rect(surf,(212,198,170),(ppx,ppy,22,15))
        pygame.draw.circle(surf,(175,50,40),(ppx+11,ppy),3)
        for li in range(3):
            pygame.draw.line(surf,(145,128,100),(ppx+2,ppy+5+li*4),(ppx+18,ppy+5+li*4),1)

    _draw_tree(surf,hx-160,ground+2,rng)
    _draw_tree(surf,hx+hw+80,ground+2,rng)


def _bg_market(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(105,148,195),(165,202,228),(60,88,47))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)

    ground = H*2//3
    pulse  = 0.6+0.4*math.sin(time*1.2)

    bw=110; bh=90
    bx=W//2-bw//2; by=ground-bh-30
    for px2 in [bx+8, bx+bw-14]:
        pygame.draw.rect(surf,(75,52,28),(px2,by+bh-8,6,45))
        pygame.draw.rect(surf,(58,40,18),(px2,by+bh-8,6,45),1)
    pygame.draw.rect(surf,(100,72,38),(bx,by,bw,bh))
    pygame.draw.rect(surf,(72,50,24),(bx,by,bw,bh),3)
    for gi in range(1,5):
        pygame.draw.line(surf,(88,62,30),(bx,by+gi*(bh//5)),(bx+bw,by+gi*(bh//5)),1)
    pygame.draw.rect(surf,(130,95,48),(bx+3,by+3,bw-6,bh-6),2)
    for nx2,ny2 in [(bx+8,by+8),(bx+bw-8,by+8),(bx+8,by+bh-8),(bx+bw-8,by+bh-8)]:
        pygame.draw.circle(surf,(160,130,60),(nx2,ny2),4)
        pygame.draw.circle(surf,(120,95,40),(nx2,ny2),4,1)

    papers = [
        (bx+8,  by+10, 38, 26, (215,202,172), (185,50,40)),
        (bx+52, by+8,  40, 28, (210,198,168), (50,120,185)),
        (bx+14, by+44, 44, 30, (218,206,176), (185,50,40)),
    ]
    for ppx,ppy,pw2,ph2,pc,pin_c in papers:
        pygame.draw.rect(surf,pc,(ppx,ppy,pw2,ph2))
        pygame.draw.rect(surf,(160,145,118),(ppx,ppy,pw2,ph2),1)
        for li in range(3):
            lc=(140,125,95) if li>0 else (80,60,30)
            lw2=pw2-8 if li==0 else pw2-4-li*4
            pygame.draw.line(surf,lc,(ppx+4,ppy+6+li*7),(ppx+4+lw2,ppy+6+li*7),1)
        pygame.draw.circle(surf,pin_c,(ppx+pw2//2,ppy),(4))
        pygame.draw.circle(surf,(255,255,255),(ppx+pw2//2,ppy),2)

    f_small=pygame.font.SysFont("courier new",9,bold=True)
    ns=f_small.render("NOTICES",True,(225,198,120))
    surf.blit(ns,(W//2-ns.get_width()//2,by+bh-16))

    gw=pygame.Surface((bw+40,bh+40),pygame.SRCALPHA)
    pygame.draw.rect(gw,(int(180*pulse),int(145*pulse),int(60*pulse),
                         int(30*pulse)),(0,0,bw+40,bh+40),border_radius=4)
    surf.blit(gw,(bx-20,by-20),special_flags=pygame.BLEND_RGBA_ADD)

    for sx,sc,ac in [(W//2-220,(115,88,50),(185,65,65)),
                      (W//2+110,(100,75,42),(65,155,185))]:
        pygame.draw.rect(surf,sc,(sx,ground-55,88,55))
        pygame.draw.rect(surf,(75,55,28),(sx,ground-55,88,55),2)
        for ai in range(5):
            col2 = ac if ai%2==0 else (235,230,215)
            pygame.draw.rect(surf,col2,(sx+ai*(88//5),ground-68,88//5,16))
        pygame.draw.rect(surf,(65,48,22),(sx,ground-68,88,16),1)
        for gi,gc in enumerate([(180,60,60),(60,160,80),(220,185,60)]):
            pygame.draw.circle(surf,gc,(sx+18+gi*22,ground-38),7)

    wx2=W//2+165; wy2=ground-30
    pygame.draw.ellipse(surf,(108,85,58),(wx2-28,wy2,56,18))
    pygame.draw.rect(surf,(95,75,48),(wx2-24,wy2-28,48,30))
    pygame.draw.ellipse(surf,(108,85,58),(wx2-24,wy2-32,48,14))
    pygame.draw.rect(surf,(75,58,32),(wx2-24,wy2-28,48,30),2)
    pygame.draw.polygon(surf,(85,62,30),[(wx2-32,wy2-28),(wx2,wy2-52),(wx2+32,wy2-28)])
    pygame.draw.line(surf,(65,48,22),(wx2-12,wy2-28),(wx2-12,wy2),2)
    pygame.draw.line(surf,(65,48,22),(wx2+12,wy2-28),(wx2+12,wy2),2)

    for fx2 in [W//2-185, W//2+85]:
        pygame.draw.rect(surf,(110,80,45),(fx2,ground-18,32,18))
        pygame.draw.rect(surf,(85,60,30),(fx2,ground-18,32,18),1)
        for fi in range(4):
            pygame.draw.circle(surf,(195,65,85),(fx2+4+fi*8,ground-22),5)
            pygame.draw.line(surf,(55,110,45),(fx2+4+fi*8,ground-17),(fx2+4+fi*8,ground-10),1)


def _bg_blacksmith(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(45,55,78),(88,112,148),(38,56,30))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)

    pulse  = 0.5+0.5*math.sin(time*3.5)
    flicker= 0.7+0.3*math.sin(time*7.1+0.4)
    ground = H*2//3

    hw,hh = 260,150
    hx = W//2-hw//2; hy = ground-hh

    # Stone foundation ledge
    pygame.draw.rect(surf,(55,44,28),(hx-6,ground-8,hw+12,12))
    pygame.draw.rect(surf,(40,32,18),(hx-6,ground-8,hw+12,12),1)

    # Main stone walls
    pygame.draw.rect(surf,(98,82,58),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(68,52,32),(hx,hy,hw,hh),3)
    # Stone block texture — use fixed offsets, not rng (avoids shimmer on redraw)
    for row in range(6):
        for col in range(7):
            sx=hx+4+col*(hw//7)
            sy=hy+4+row*(hh//6)
            v = ((row*7+col)*13+42) % 9 - 4   # deterministic "random"
            pygame.draw.rect(surf,(90+v,74+v,52+v),(sx,sy,hw//7-4,hh//6-4),1)

    # Flat roof parapet
    pygame.draw.rect(surf,(80,64,42),(hx-10,hy-16,hw+20,18))
    pygame.draw.rect(surf,(58,44,26),(hx-10,hy-16,hw+20,18),2)
    # Battlement merlons — evenly spaced
    for bx2 in range(hx-8, hx+hw+10, 20):
        pygame.draw.rect(surf,(80,64,42),(bx2,hy-30,13,16))
        pygame.draw.rect(surf,(58,44,26),(bx2,hy-30,13,16),1)

    # Two chimneys
    for chx in [hx+48, hx+hw-62]:
        pygame.draw.rect(surf,(88,70,46),(chx,hy-60,20,46))
        pygame.draw.rect(surf,(62,46,28),(chx,hy-60,20,46),2)
        pygame.draw.rect(surf,(100,80,52),(chx-3,hy-64,26,8))
        pygame.draw.rect(surf,(70,52,30),(chx-3,hy-64,26,8),1)
        # Smoke — small, contained puffs
        for si in range(4):
            sa = 0.3+0.2*math.sin(time*1.8+si*1.2+chx*0.01)
            sm = pygame.Surface((14,14),pygame.SRCALPHA)
            pygame.draw.circle(sm,(125,115,102,int(48*sa)),(7,7),3+si*2)
            surf.blit(sm,(chx+3+si,hy-68-si*10))

    # LEFT side: two smaller windows with orange glow
    for wx,wy,ww2,wh2 in [(hx+18,hy+22,38,26),(hx+18,hy+hh//2+12,34,22)]:
        pygame.draw.rect(surf,(52,36,16),(wx-3,wy-3,ww2+6,wh2+6))
        wsurf=pygame.Surface((ww2,wh2),pygame.SRCALPHA)
        wsurf.fill((int(205*pulse),int(125*pulse*flicker),int(18*pulse),200))
        surf.blit(wsurf,(wx,wy))
        pygame.draw.rect(surf,(42,28,10),(wx,wy,ww2,wh2),2)
        pygame.draw.line(surf,(42,28,10),(wx+ww2//2,wy),(wx+ww2//2,wy+wh2),1)
        pygame.draw.line(surf,(42,28,10),(wx,wy+wh2//2),(wx+ww2,wy+wh2//2),1)
        # Tiny contained glow — max 16px radius
        gw = pygame.Surface((32,32),pygame.SRCALPHA)
        pygame.draw.ellipse(gw,(int(150*pulse),int(70*pulse),8,int(22*pulse)),(0,0,32,32))
        surf.blit(gw,(wx+ww2//2-16,wy+wh2//2-16),special_flags=pygame.BLEND_RGBA_ADD)

    # RIGHT side: large forge window — the main glowing feature
    gx = hx+hw-78; gy = hy+24; gw2 = 60; gh = 44
    pygame.draw.rect(surf,(48,32,12),(gx-4,gy-4,gw2+8,gh+8))
    gsurf=pygame.Surface((gw2,gh),pygame.SRCALPHA)
    gsurf.fill((int(248*pulse),int(130*pulse*flicker),int(12*pulse),220))
    surf.blit(gsurf,(gx,gy))
    pygame.draw.rect(surf,(40,26,8),(gx,gy,gw2,gh),2)
    pygame.draw.line(surf,(40,26,8),(gx+gw2//2,gy),(gx+gw2//2,gy+gh),2)
    pygame.draw.line(surf,(40,26,8),(gx,gy+gh//2),(gx+gw2,gy+gh//2),2)
    # Contained glow spill — small ellipse, low alpha, won't bleed
    gs2=pygame.Surface((gw2+20,30),pygame.SRCALPHA)
    pygame.draw.ellipse(gs2,(int(180*pulse),int(88*pulse),8,int(32*pulse)),(0,0,gw2+20,30))
    surf.blit(gs2,(gx-10,gy+gh-6),special_flags=pygame.BLEND_RGBA_ADD)

    # Second smaller window on right
    wx2=hx+hw-76; wy2=hy+hh//2+12
    pygame.draw.rect(surf,(52,36,16),(wx2-3,wy2-3,37,25))
    sw=pygame.Surface((34,22),pygame.SRCALPHA)
    sw.fill((int(200*pulse),int(115*pulse),10,190))
    surf.blit(sw,(wx2,wy2))
    pygame.draw.rect(surf,(42,28,10),(wx2,wy2,34,22),2)

    # Arched door — centred, well-proportioned
    dx = W//2-24; dw = 48; dh = 74
    # Door surround stone
    pygame.draw.rect(surf,(52,36,14),(dx-4,ground-dh,dw+8,dh))
    pygame.draw.ellipse(surf,(52,36,14),(dx-4,ground-dh-22,dw+8,44))
    # Door fill
    pygame.draw.rect(surf,(40,25,8),(dx,ground-dh,dw,dh))
    pygame.draw.ellipse(surf,(40,25,8),(dx,ground-dh-20,dw,40))
    pygame.draw.ellipse(surf,(30,18,4),(dx,ground-dh-20,dw,40),2)
    # Plank lines
    for pi in range(4):
        pygame.draw.line(surf,(34,20,5),(dx+5+pi*11,ground-dh),(dx+5+pi*11,ground-4),1)
    # Cross brace
    pygame.draw.line(surf,(48,30,8),(dx+2,ground-dh+18),(dx+dw-2,ground-dh+38),2)
    pygame.draw.line(surf,(48,30,8),(dx+2,ground-dh+38),(dx+dw-2,ground-dh+18),2)
    # Handle
    pygame.draw.circle(surf,(128,110,78),(dx+dw-8,ground-dh//2),4)
    pygame.draw.circle(surf,(92,76,52),(dx+dw-8,ground-dh//2),4,1)

    # Wall torch brackets either side of door — no large glow surfaces
    for tx2 in [dx-18, dx+dw+5]:
        pygame.draw.line(surf,(72,52,26),(tx2+4,ground-dh+6),(tx2+4,ground-dh+18),3)
        pygame.draw.line(surf,(72,52,26),(tx2+4,ground-dh+6),(tx2+10,ground-dh-5),2)
        pygame.draw.rect(surf,(82,60,28),(tx2+6,ground-dh-18,5,14))
        fp = 0.7+0.3*math.sin(time*5+tx2)
        pygame.draw.polygon(surf,(int(228*fp),int(115*fp),18),[
            (tx2+8,ground-dh-18),(tx2+5,ground-dh-27),(tx2+11,ground-dh-22)])
        pygame.draw.polygon(surf,(255,int(195*fp),55),[
            (tx2+8,ground-dh-18),(tx2+7,ground-dh-23),(tx2+10,ground-dh-20)])

    # Hanging sign — properly above door, not overlapping windows
    sx = W//2; sy = hy+6
    pygame.draw.line(surf,(72,52,24),(sx-30,sy+2),(sx+30,sy+2),3)   # horizontal bar
    pygame.draw.line(surf,(72,52,24),(sx,hy-2),(sx,sy+2),3)           # vertical drop
    for cx2 in [sx-22, sx+22]:
        pygame.draw.line(surf,(92,72,38),(cx2,sy+2),(cx2,sy+18),2)   # chains
    # Sign board
    pygame.draw.rect(surf,(138,102,46),(sx-40,sy+18,80,26))
    pygame.draw.rect(surf,(92,65,25),(sx-40,sy+18,80,26),2)
    # Rivets
    for rx,ry in [(sx-36,sy+21),(sx+32,sy+21),(sx-36,sy+38),(sx+32,sy+38)]:
        pygame.draw.circle(surf,(155,125,62),(rx,ry),2)
    sf = pygame.font.SysFont("courier new",10,bold=True)
    ss = sf.render("GORIN'S FORGE",True,(212,172,72))
    surf.blit(ss,(sx-ss.get_width()//2, sy+22))

    # Anvil to the right of door
    ax = dx+dw+26; ay = ground-30
    pygame.draw.rect(surf,(76,68,60),(ax,ay,42,13))
    pygame.draw.rect(surf,(56,50,44),(ax-4,ay+13,50,9))
    pygame.draw.rect(surf,(66,58,50),(ax+7,ay+22,28,9))
    pygame.draw.rect(surf,(48,42,36),(ax,ay,42,13),1)
    pygame.draw.line(surf,(102,84,50),(ax+21,ay-2),(ax+36,ay-16),4)
    pygame.draw.rect(surf,(126,112,98),(ax+33,ay-20,14,8))

    # Water barrel left of door
    bx2 = dx-42
    pygame.draw.rect(surf,(76,54,24),(bx2,ground-38,26,36))
    pygame.draw.ellipse(surf,(90,66,30),(bx2,ground-43,26,12))
    pygame.draw.ellipse(surf,(90,66,30),(bx2,ground-6,26,12))
    for bi in [ground-32, ground-20]:
        pygame.draw.line(surf,(56,40,16),(bx2,bi),(bx2+26,bi),2)

    _draw_tree(surf,hx-108,ground+2,rng)


def _bg_shop(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(108,155,200),(165,205,228),(58,88,46))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)

    ground = H*2//3
    hw,hh = 255,145
    hx = W//2-hw//2; hy = ground-hh

    # Foundation ledge
    pygame.draw.rect(surf,(80,100,68),(hx-6,ground-8,hw+12,12))
    pygame.draw.rect(surf,(55,75,46),(hx-6,ground-8,hw+12,12),1)

    # Main walls — warm green
    pygame.draw.rect(surf,(72,118,68),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(48,88,44),(hx,hy,hw,hh),3)
    # Wall plank texture — horizontal lines
    for row in range(6):
        sy = hy + row*(hh//6)
        pygame.draw.line(surf,(60,100,56),(hx+2,sy),(hx+hw-2,sy),1)

    # Peaked roof — larger and well-proportioned
    roof_pts = [(hx-10,hy),(hx+hw//2,hy-88),(hx+hw+10,hy)]
    pygame.draw.polygon(surf,(48,82,42),roof_pts)
    pygame.draw.polygon(surf,(32,60,28),roof_pts,2)
    # Roof shingles — diagonal lines
    for i in range(1,7):
        frac = i/7
        xl = int(hx-10 + (hx+hw//2-(hx-10))*frac)
        xr = int(hx+hw+10 + (hx+hw//2-(hx+hw+10))*frac)
        ty2 = int(hy + (hy-88-hy)*frac)
        pygame.draw.line(surf,(38,68,32),(xl,ty2),(xr,ty2),1)

    # Chimney — left side
    chx = hx+38; chy = hy-70
    pygame.draw.rect(surf,(88,118,76),(chx,chy,20,55))
    pygame.draw.rect(surf,(62,92,52),(chx,chy,20,55),2)
    pygame.draw.rect(surf,(100,132,86),(chx-3,chy-7,26,9))
    pygame.draw.rect(surf,(68,98,58),(chx-3,chy-7,26,9),1)
    # Chimney smoke
    for si in range(4):
        sa = 0.3+0.2*math.sin(time*1.6+si*1.3)
        sm = pygame.Surface((14,14),pygame.SRCALPHA)
        pygame.draw.circle(sm,(155,168,148,int(48*sa)),(7,7),3+si*2)
        surf.blit(sm,(chx+3+si,chy-12-si*10))

    # Striped canvas awning — wide, colourful
    aw_y = hy+hh//3; aw_h = 18
    for i in range(8):
        c = (215,55,55) if i%2==0 else (245,245,245)
        pygame.draw.rect(surf,c,(hx+i*(hw//8),aw_y-2,hw//8,aw_h))
    pygame.draw.rect(surf,(38,65,32),(hx,aw_y-2,hw,aw_h),2)
    # Awning scalloped bottom edge
    for i in range(8):
        ax2 = hx + i*(hw//8) + hw//16
        pygame.draw.circle(surf,(38,65,32),(ax2, aw_y+aw_h-2),6)

    # Large display window — centred
    wx = W//2-52; wy = hy+18; ww = 104; wh = hy+hh//3-hy-24
    pygame.draw.rect(surf,(52,88,46),(wx-4,wy-4,ww+8,wh+8))
    pygame.draw.rect(surf,(185,220,215),(wx,wy,ww,wh))
    pygame.draw.rect(surf,(38,70,34),(wx,wy,ww,wh),2)
    # Window cross bars
    pygame.draw.line(surf,(38,70,34),(wx+ww//2,wy),(wx+ww//2,wy+wh),2)
    pygame.draw.line(surf,(38,70,34),(wx,wy+wh//2),(wx+ww,wy+wh//2),2)
    # Items in window — decorative shapes
    pygame.draw.circle(surf,(180,55,55),(wx+22,wy+wh//2-4),7)   # red potion
    pygame.draw.rect(surf,(155,130,65),(wx+ww//2+8,wy+wh//2-10,14,18))  # key/chest
    pygame.draw.circle(surf,(200,175,60),(wx+ww//2+15,wy+wh//2-12),5)   # coin

    # Two side windows — smaller
    for swx in [hx+12, hx+hw-52]:
        pygame.draw.rect(surf,(52,88,46),(swx-3,wy-3,40,32))
        pygame.draw.rect(surf,(185,220,215),(swx,wy,36,28))
        pygame.draw.rect(surf,(38,70,34),(swx,wy,36,28),2)
        pygame.draw.line(surf,(38,70,34),(swx+18,wy),(swx+18,wy+28),1)
        pygame.draw.line(surf,(38,70,34),(swx,wy+14),(swx+36,wy+14),1)

    # Arched door — centred
    dx = W//2-22; dw = 44; dh = 62
    pygame.draw.rect(surf,(52,36,14),(dx-3,ground-dh,dw+6,dh))
    pygame.draw.ellipse(surf,(52,36,14),(dx-3,ground-dh-18,dw+6,36))
    pygame.draw.rect(surf,(42,26,8),(dx,ground-dh,dw,dh))
    pygame.draw.ellipse(surf,(42,26,8),(dx,ground-dh-16,dw,32))
    pygame.draw.ellipse(surf,(32,18,4),(dx,ground-dh-16,dw,32),2)
    # Door planks
    for pi in range(3):
        pygame.draw.line(surf,(36,22,6),(dx+5+pi*13,ground-dh),(dx+5+pi*13,ground-4),1)
    # Door handle
    pygame.draw.circle(surf,(165,135,58),(dx+dw-8,ground-dh//2),4)
    pygame.draw.circle(surf,(120,95,38),(dx+dw-8,ground-dh//2),4,1)

    # Hanging sign — above door on bracket
    sx = W//2; sy = hy+8
    pygame.draw.line(surf,(68,95,55),(sx-28,sy+2),(sx+28,sy+2),3)
    pygame.draw.line(surf,(68,95,55),(sx,hy-2),(sx,sy+2),3)
    for cx2 in [sx-20,sx+20]:
        pygame.draw.line(surf,(88,118,72),(cx2,sy+2),(cx2,sy+18),2)
    pygame.draw.rect(surf,(58,95,52),(sx-40,sy+18,80,26))
    pygame.draw.rect(surf,(38,70,32),(sx-40,sy+18,80,26),2)
    for rx,ry in [(sx-36,sy+21),(sx+32,sy+21),(sx-36,sy+38),(sx+32,sy+38)]:
        pygame.draw.circle(surf,(120,185,100),(rx,ry),2)
    sf=pygame.font.SysFont("courier new",10,bold=True)
    ss=sf.render("MIRA'S SUNDRIES",True,(195,235,170))
    surf.blit(ss,(sx-ss.get_width()//2, sy+22))

    # Flower boxes under side windows
    for fbx in [hx+10, hx+hw-52]:
        pygame.draw.rect(surf,(72,50,24),(fbx,wy+28,38,12))
        pygame.draw.rect(surf,(52,36,14),(fbx,wy+28,38,12),1)
        for fi in range(5):
            fc = (195+fi*5,55+fi*10,75) if fi%2==0 else (255,210,60)
            pygame.draw.circle(surf,fc,(fbx+4+fi*8,wy+26),5)

    # Barrel and crate outside — left of door
    bx2 = dx-42
    pygame.draw.rect(surf,(85,60,26),(bx2,ground-36,26,34))
    pygame.draw.ellipse(surf,(100,72,32),(bx2,ground-40,26,12))
    pygame.draw.ellipse(surf,(100,72,32),(bx2,ground-6,26,12))
    for bi in [ground-30,ground-18]:
        pygame.draw.line(surf,(62,44,18),(bx2,bi),(bx2+26,bi),2)
    # Crate right of door
    crx = dx+dw+10; cry = ground-28
    pygame.draw.rect(surf,(105,80,40),(crx,cry,28,26))
    pygame.draw.rect(surf,(75,55,22),(crx,cry,28,26),2)
    pygame.draw.line(surf,(75,55,22),(crx+14,cry),(crx+14,cry+26),1)
    pygame.draw.line(surf,(75,55,22),(crx,cry+13),(crx+28,cry+13),1)

    # Two trees flanking
    _draw_tree(surf,hx-90,ground+2,rng,1.1)
    _draw_tree(surf,hx+hw+70,ground+2,rng,0.9)


def _bg_antiquity(surf, W, H, rng, time):
    _draw_sky(surf,W,H,(38,30,58),(82,65,118),(42,58,36))
    _draw_town_backdrop(surf,W,H,rng)
    _draw_stone_road(surf,W,H,rng)

    pulse  = 0.5+0.5*math.sin(time*1.8)
    pulse2 = 0.5+0.5*math.sin(time*2.4+1.0)
    ground = H*2//3
    hw,hh  = 248,152
    hx = W//2-hw//2; hy = ground-hh

    # Foundation — dark stone
    pygame.draw.rect(surf,(52,38,65),(hx-6,ground-8,hw+12,12))
    pygame.draw.rect(surf,(35,24,48),(hx-6,ground-8,hw+12,12),1)

    # Main walls — deep purple stone
    pygame.draw.rect(surf,(72,48,98),(hx,hy,hw,hh))
    pygame.draw.rect(surf,(48,30,68),(hx,hy,hw,hh),3)
    # Stone block texture
    for row in range(6):
        for col in range(6):
            sx2=hx+4+col*(hw//6)
            sy2=hy+4+row*(hh//6)
            v=((row*6+col)*11+7)%9-4
            pygame.draw.rect(surf,(68+v,44+v,92+v),(sx2,sy2,hw//6-4,hh//6-4),1)

    # Ornate dome roof — the signature feature
    dome_cx = W//2; dome_cy = hy
    dome_w = hw+24; dome_h = 110
    # Outer dome
    pygame.draw.ellipse(surf,(58,38,82),(dome_cx-dome_w//2, dome_cy-dome_h, dome_w, dome_h*2))
    pygame.draw.ellipse(surf,(38,22,58),(dome_cx-dome_w//2, dome_cy-dome_h, dome_w, dome_h*2),3)
    # Dome highlight — lighter upper arc
    pygame.draw.arc(surf,(88,58,118),(dome_cx-dome_w//2+8,dome_cy-dome_h+8,dome_w-16,dome_h*2-16),
                    math.pi*0.6,math.pi*1.4,3)
    # Dome ribbing lines
    for ri in range(-2,3):
        ra = math.pi/2 + ri*0.28
        rx1 = dome_cx + int(math.cos(ra)*(dome_w//2-4))
        ry1 = dome_cy + int(math.sin(ra)*(dome_h-4)) - dome_h//2
        pygame.draw.line(surf,(48,30,68),(dome_cx,dome_cy-dome_h+4),(rx1,ry1),1)
    # Dome finial (spire on top)
    pygame.draw.line(surf,(120,85,158),(dome_cx,dome_cy-dome_h),(dome_cx,dome_cy-dome_h-22),3)
    pygame.draw.polygon(surf,(140,100,180),[(dome_cx-5,dome_cy-dome_h-18),(dome_cx+5,dome_cy-dome_h-18),
                                             (dome_cx,dome_cy-dome_h-32)])
    pygame.draw.circle(surf,(int(180*pulse),int(120*pulse),int(255*pulse)),(dome_cx,dome_cy-dome_h-32),4)

    # Mystical orb window — centred on dome, animated glow
    orb_x=W//2; orb_y=hy+32; orb_r=26
    # Glow halo
    gsurf=pygame.Surface((orb_r*4,orb_r*4),pygame.SRCALPHA)
    pygame.draw.circle(gsurf,(int(140*pulse),int(80*pulse),int(220*pulse),int(60*pulse)),
                       (orb_r*2,orb_r*2),orb_r*2)
    surf.blit(gsurf,(orb_x-orb_r*2,orb_y-orb_r*2),special_flags=pygame.BLEND_RGBA_ADD)
    # Window frame
    pygame.draw.circle(surf,(48,28,68),(orb_x,orb_y),orb_r+4)
    # Orb glass
    wsurf=pygame.Surface((orb_r*2,orb_r*2),pygame.SRCALPHA)
    pygame.draw.circle(wsurf,(int(160*pulse),int(100*pulse),int(240*pulse),200),(orb_r,orb_r),orb_r)
    surf.blit(wsurf,(orb_x-orb_r,orb_y-orb_r))
    pygame.draw.circle(surf,(80,45,110),(orb_x,orb_y),orb_r,2)
    # Star spokes radiating from orb
    for a in range(0,360,45):
        ra=math.radians(a+time*12)
        r1=orb_r+6; r2=orb_r+14
        pygame.draw.line(surf,(int(140*pulse),int(85*pulse),int(200*pulse)),
                         (orb_x+int(math.cos(ra)*r1),orb_y+int(math.sin(ra)*r1)),
                         (orb_x+int(math.cos(ra)*r2),orb_y+int(math.sin(ra)*r2)),2)
    # Inner shimmer
    pygame.draw.circle(surf,(int(220*pulse),int(160*pulse),int(255*pulse2)),
                       (orb_x-8,orb_y-8),orb_r//3)

    # Two side windows — tall arched, glowing purple
    for swx in [hx+16, hx+hw-58]:
        sww=42; swh=52; swy=hy+hh//2-8
        # Frame
        pygame.draw.rect(surf,(48,28,68),(swx-3,swy-3,sww+6,swh+6))
        pygame.draw.ellipse(surf,(48,28,68),(swx-3,swy-sww//2-3,sww+6,sww+6))
        # Glass
        wsf=pygame.Surface((sww,swh),pygame.SRCALPHA)
        wsf.fill((int(100*pulse2),int(60*pulse2),int(160*pulse2),185))
        surf.blit(wsf,(swx,swy))
        pygame.draw.ellipse(surf,(int(100*pulse2),int(60*pulse2),int(160*pulse2),185),
                            (swx,swy-sww//2,sww,sww))
        pygame.draw.rect(surf,(38,20,55),(swx,swy,sww,swh),2)
        pygame.draw.ellipse(surf,(38,20,55),(swx,swy-sww//2,sww,sww),2)
        # Cross bar
        pygame.draw.line(surf,(38,20,55),(swx+sww//2,swy),(swx+sww//2,swy+swh),1)
        pygame.draw.line(surf,(38,20,55),(swx,swy+swh//2),(swx+sww,swy+swh//2),1)
        # Small contained glow
        sg=pygame.Surface((30,30),pygame.SRCALPHA)
        pygame.draw.ellipse(sg,(int(120*pulse2),int(60*pulse2),int(180*pulse2),int(30*pulse2)),(0,0,30,30))
        surf.blit(sg,(swx+sww//2-15,swy+swh//2-15),special_flags=pygame.BLEND_RGBA_ADD)

    # Arched door — narrow and tall, mysterious
    dx=W//2-20; dw=40; dh=70
    pygame.draw.rect(surf,(30,16,44),(dx-3,ground-dh,dw+6,dh))
    pygame.draw.ellipse(surf,(30,16,44),(dx-3,ground-dh-22,dw+6,44))
    pygame.draw.rect(surf,(22,10,32),(dx,ground-dh,dw,dh))
    pygame.draw.ellipse(surf,(22,10,32),(dx,ground-dh-20,dw,40))
    pygame.draw.ellipse(surf,(15,6,22),(dx,ground-dh-20,dw,40),2)
    # Door symbol — arcane circle
    pygame.draw.circle(surf,(75,45,105),(dx+dw//2,ground-dh//2),10,1)
    for a in range(0,360,60):
        ra2=math.radians(a)
        pygame.draw.circle(surf,(75,45,105),
                           (dx+dw//2+int(math.cos(ra2)*10),ground-dh//2+int(math.sin(ra2)*10)),2)
    # Door handle
    pygame.draw.circle(surf,(145,105,185),(dx+dw-7,ground-dh//2),4)
    pygame.draw.circle(surf,(100,68,135),(dx+dw-7,ground-dh//2),4,1)

    # Hanging sign — ornate, with chains
    sx=W//2; sy=hy+10
    pygame.draw.line(surf,(88,55,118),(sx-26,sy+2),(sx+26,sy+2),3)
    pygame.draw.line(surf,(88,55,118),(sx,hy-2),(sx,sy+2),3)
    for cx2 in [sx-20,sx+20]:
        pygame.draw.line(surf,(108,72,145),(cx2,sy+2),(cx2,sy+20),2)
    pygame.draw.rect(surf,(55,32,78),(sx-44,sy+20,88,28))
    pygame.draw.rect(surf,(80,50,110),(sx-44,sy+20,88,28),2)
    # Rivets
    for rx,ry in [(sx-40,sy+23),(sx+36,sy+23),(sx-40,sy+42),(sx+36,sy+42)]:
        pygame.draw.circle(surf,(155,110,200),(rx,ry),2)
    sf=pygame.font.SysFont("courier new",9,bold=True)
    ss=sf.render("THE CURIO CABINET",True,(195,155,235))
    surf.blit(ss,(sx-ss.get_width()//2, sy+25))

    # Mysterious display items outside — pedestal with glowing artefact
    ped_x = dx-52; ped_y = ground-36
    pygame.draw.rect(surf,(52,34,70),(ped_x,ped_y,28,34))
    pygame.draw.rect(surf,(38,22,52),(ped_x,ped_y,28,34),1)
    pygame.draw.rect(surf,(62,42,82),(ped_x-4,ped_y,36,8))   # pedestal top
    # Orb on pedestal
    osurf=pygame.Surface((22,22),pygame.SRCALPHA)
    pygame.draw.circle(osurf,(int(160*pulse2),int(100*pulse2),int(230*pulse2),210),(11,11),10)
    surf.blit(osurf,(ped_x+3,ped_y-14))
    pygame.draw.circle(surf,(int(200*pulse2),int(140*pulse2),255),(ped_x+9,ped_y-10),3)

    # Lamp post left side — arcane lantern
    lx=hx-55; ly=ground-85
    pygame.draw.line(surf,(65,42,88),(lx,ground),(lx,ly),4)
    pygame.draw.circle(surf,(72,48,95),(lx,ly),12)
    pygame.draw.circle(surf,(50,30,70),(lx,ly),12,2)
    lp=0.6+0.4*math.sin(time*2.8)
    ls2=pygame.Surface((28,28),pygame.SRCALPHA)
    pygame.draw.circle(ls2,(int(180*lp),int(100*lp),int(255*lp),int(80*lp)),(14,14),12)
    surf.blit(ls2,(lx-14,ly-14),special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.circle(surf,(int(220*lp),int(140*lp),255),(lx,ly),5)

    _draw_tree(surf,hx+hw+80,ground+2,rng,0.9)


def _bg_dungeon(surf, W, H, rng, time):
    ground = H*2//3

    # Dark foreboding sky — gradient from near-black to deep bruised purple at horizon
    for y in range(H):
        t = y/H
        if t < 0.55:
            r = int(12+16*t); g = int(8+10*t); b = int(16+14*t)
        else:
            r = int(20+28*(t-0.55)); g = int(13+10*(t-0.55)); b = int(22+12*(t-0.55))
        pygame.draw.line(surf,(r,g,b),(0,y),(W,y))

    # Distant blighted mountains — slightly lighter than sky so they read
    mountain_pts_l = [(0,ground),(0,ground-70),(W//10,ground-105),(W//6,ground-85),
                      (W//4,ground-130),(W*3//10,ground-95),(W//3,ground-60),(W//3,ground)]
    pygame.draw.polygon(surf,(32,22,18),mountain_pts_l)
    mountain_pts_r = [(W,ground),(W,ground-70),(W*9//10,ground-100),(W*5//6,ground-82),
                      (W*3//4,ground-128),(W*7//10,ground-92),(W*2//3,ground-58),(W*2//3,ground)]
    pygame.draw.polygon(surf,(28,18,14),mountain_pts_r)

    # Dark ground — draw BEFORE trees so trees sit on top
    for y in range(ground, H):
        t=(y-ground)/(H-ground)
        pygame.draw.line(surf,(int(28+10*t),int(20+6*t),int(14+4*t)),(0,y),(W,y))
    _draw_stone_road(surf,W,H,rng)

    # Dead leafless trees — drawn AFTER ground so they're visible
    def _dead_tree(sx, sy, seed, flip=False):
        trng = random.Random(seed)
        # Trunk
        pygame.draw.line(surf,(52,38,24),(sx,sy),(sx,sy-100),6)
        pygame.draw.line(surf,(52,38,24),(sx,sy-100),(sx,sy-130),4)
        # Main branches
        branches = [(-32,-60,20,-88),(-18,-80,26,-108),(22,-52,-20,-80),(14,-74,-26,-98)]
        for bx1,by1,bx2,by2 in branches:
            if flip: bx1,bx2=-bx1,-bx2
            pygame.draw.line(surf,(45,32,18),(sx+bx1,sy+by1),(sx+bx2,sy+by2),3)
            mx=(bx1+bx2)//2; my=(by1+by2)//2
            ox=trng.randint(-16,16); oy=trng.randint(-24,-6)
            pygame.draw.line(surf,(40,28,14),(sx+mx,sy+my),(sx+mx+ox,sy+my+oy),2)

    _dead_tree(W//2-240, ground, 11)
    _dead_tree(W//2+210, ground, 22, flip=True)
    _dead_tree(W//2-400, ground+8, 33)
    _dead_tree(W//2+370, ground+8, 44, flip=True)

    # Main dungeon entrance structure
    # Central tower — tall and wide
    tw2=110; th2=235; tx3=W//2-tw2//2; ty3=ground-th2
    pygame.draw.rect(surf,(52,40,26),(tx3,ty3,tw2,th2))
    pygame.draw.rect(surf,(35,26,14),(tx3,ty3,tw2,th2),3)
    blk_rng=random.Random(77)
    for row in range(11):
        for col in range(4):
            bsx=tx3+3+col*(tw2//4); bsy=ty3+4+row*(th2//11)
            v2=blk_rng.randint(-6,6)
            pygame.draw.rect(surf,(46+v2,35+v2,22+v2),(bsx,bsy,tw2//4-4,th2//11-3),1)
    # Battlements
    for i,intact in enumerate([True,False,True,True,False,True]):
        if intact:
            pygame.draw.rect(surf,(52,40,26),(tx3+i*18,ty3-18,14,20))
            pygame.draw.rect(surf,(35,26,14),(tx3+i*18,ty3-18,14,20),1)
    # Tower cracks
    pygame.draw.line(surf,(26,16,8),(tx3+tw2//3,ty3+20),(tx3+tw2//3-10,ty3+th2//3),2)

    # Ruined wall wings — taller, framing the tower properly
    wing_h_base = 95
    for col in range(7):
        bw2=38
        # Left wing — gets shorter as it goes left
        height_l = max(40, wing_h_base - col*8 + blk_rng.randint(-10,10))
        bx3=tx3-14-(col+1)*bw2; by3=ground-height_l
        v=blk_rng.randint(-8,8)
        pygame.draw.rect(surf,(52+v,40+v,26+v),(bx3,by3,bw2,height_l))
        pygame.draw.rect(surf,(36+v,26+v,14+v),(bx3,by3,bw2,height_l),2)
        for row in range(height_l//18):
            pygame.draw.line(surf,(30,20,10),(bx3,by3+row*18),(bx3+bw2,by3+row*18),1)
        # Right wing — mirror
        bx3r=tx3+tw2+14+col*bw2; by3r=ground-height_l
        pygame.draw.rect(surf,(52+v,40+v,26+v),(bx3r,by3r,bw2,height_l))
        pygame.draw.rect(surf,(36+v,26+v,14+v),(bx3r,by3r,bw2,height_l),2)
        for row in range(height_l//18):
            pygame.draw.line(surf,(30,20,10),(bx3r,by3r+row*18),(bx3r+bw2,by3r+row*18),1)

    # Arch gateway — centred in tower, large and prominent
    aw2=78; ax2=W//2-aw2//2; arch_top=ground-158
    # Pure void inside arch
    pygame.draw.rect(surf,(3,2,1),(ax2,arch_top,aw2,ground-arch_top))
    pygame.draw.arc(surf,(3,2,1),(ax2,arch_top-aw2//2,aw2,aw2),0,math.pi,aw2//2)
    # Thick stone surround
    pygame.draw.arc(surf,(62,48,30),(ax2-8,arch_top-aw2//2-8,aw2+16,aw2+16),0,math.pi,9)
    pygame.draw.arc(surf,(44,32,16),(ax2-13,arch_top-aw2//2-13,aw2+26,aw2+26),0,math.pi,4)
    # Arch side pillars
    for px4,pw2 in [(ax2-16,16),(ax2+aw2,16)]:
        pygame.draw.rect(surf,(50,38,24),(px4,arch_top,pw2,ground-arch_top))
        pygame.draw.rect(surf,(34,24,12),(px4,arch_top,pw2,ground-arch_top),2)

    # Keystone skull
    kx=W//2; ky=arch_top-aw2//2-6
    pygame.draw.polygon(surf,(68,52,32),[(kx-11,ky-8),(kx+11,ky-8),(kx+7,ky+14),(kx-7,ky+14)])
    pygame.draw.polygon(surf,(38,28,14),[(kx-11,ky-8),(kx+11,ky-8),(kx+7,ky+14),(kx-7,ky+14)],2)
    pygame.draw.circle(surf,(160,145,125),(kx,ky+2),6)
    for ex2 in [kx-3,kx+3]:
        pygame.draw.circle(surf,(14,8,4),(ex2,ky+1),2)

    # Subtle red glow — contained inside/near the arch, NOT a giant ellipse
    pulse=0.4+0.35*math.sin(time*1.8)
    # Inner glow — small, close to arch base
    inner=pygame.Surface((aw2-10,50),pygame.SRCALPHA)
    pygame.draw.ellipse(inner,(int(200*pulse),int(22*pulse),int(16*pulse),int(130*pulse)),
                        (0,0,aw2-10,50))
    surf.blit(inner,(ax2+5,ground-55),special_flags=pygame.BLEND_RGBA_ADD)
    # Floor glow — very faint bleed onto road
    floor_g=pygame.Surface((aw2+30,30),pygame.SRCALPHA)
    pygame.draw.ellipse(floor_g,(int(120*pulse),int(14*pulse),10,int(60*pulse)),
                        (0,0,aw2+30,30))
    surf.blit(floor_g,(ax2-15,ground-20),special_flags=pygame.BLEND_RGBA_ADD)

    # Steps down into entrance
    for i in range(4):
        sw2=aw2-i*8+6; sx2=W//2-sw2//2; sy2=ground-8-i*11
        pygame.draw.rect(surf,(40+i*3,28+i*2,16+i),(sx2,sy2,sw2,12))
        pygame.draw.rect(surf,(26,16,8),(sx2,sy2,sw2,12),1)

    # Hanging chains on arch
    for chx in [ax2+8, ax2+aw2-8]:
        for ci in range(4):
            cy3=arch_top+ci*20
            pygame.draw.ellipse(surf,(52,40,22),(chx-3,cy3,7,11))
            pygame.draw.ellipse(surf,(36,26,12),(chx-3,cy3,7,11),1)

    # Skull pile — base of arch, left side
    for skx2,sky2,skr in [(ax2-22,ground-8,7),(ax2-33,ground-18,6),(ax2-14,ground-20,8)]:
        pygame.draw.circle(surf,(148,135,118),(skx2,sky2),skr)
        pygame.draw.circle(surf,(28,18,8),(skx2,sky2),skr,1)
        for ex2 in [skx2-skr//3,skx2+skr//3]:
            pygame.draw.circle(surf,(14,8,4),(ex2,sky2-1),max(2,skr//3))

    # Wall torches — animated, flanking the arch
    for tcx2,tside2 in [(ax2-28,-1),(ax2+aw2+10,1)]:
        tcy2=arch_top+35
        pygame.draw.line(surf,(60,42,22),(tcx2,tcy2),(tcx2+tside2*10,tcy2+10),3)
        pygame.draw.rect(surf,(68,48,24),(tcx2-3,tcy2-20,6,22))
        tp=0.65+0.35*math.sin(time*4.0+tcx2*0.03)
        pygame.draw.polygon(surf,(int(235*tp),int(115*tp),18),[
            (tcx2-5,tcy2-20),(tcx2,tcy2-38),(tcx2+5,tcy2-20)])
        pygame.draw.polygon(surf,(255,int(190*tp),45),[
            (tcx2-2,tcy2-20),(tcx2,tcy2-32),(tcx2+2,tcy2-20)])
        tgs=pygame.Surface((30,30),pygame.SRCALPHA)
        pygame.draw.circle(tgs,(int(195*tp),int(88*tp),14,int(65*tp)),(15,15),13)
        surf.blit(tgs,(tcx2-15,tcy2-38),special_flags=pygame.BLEND_RGBA_ADD)

    # Warning plaque — above arch, clearly readable
    pw3=124; ph3=22; px5=W//2-pw3//2; py5=arch_top-aw2//2-38
    pygame.draw.rect(surf,(50,38,22),(px5,py5,pw3,ph3))
    pygame.draw.rect(surf,(34,24,10),(px5,py5,pw3,ph3),2)
    sf=pygame.font.SysFont("courier new",10,bold=True)
    ws=sf.render("ENTER AT YOUR PERIL",True,(148,95,40))
    surf.blit(ws,(W//2-ws.get_width()//2,py5+5))

    # Distant blighted mountains — jagged silhouettes
    mountain_pts_l = [(0,ground),(0,ground-80),(W//8,ground-120),(W//5,ground-95),
                      (W//4,ground-145),(W//3,ground-105),(W//3,ground)]
    pygame.draw.polygon(surf,(28,18,14),mountain_pts_l)
    mountain_pts_r = [(W,ground),(W,ground-80),(W*7//8,ground-115),(W*3//4,ground-90),
                      (W*2//3,ground-140),(W*3//5,ground-100),(W*3//5,ground)]
    pygame.draw.polygon(surf,(22,14,10),mountain_pts_r)

    # Dead leafless trees — left and right, large and twisted
    def _dead_tree(sx, sy, seed, flip=False):
        trng = random.Random(seed)
        pygame.draw.line(surf,(48,36,22),(sx,sy),(sx,sy-95),5)
        branches = [(-28,-65,18,-90),(-14,-80,22,-105),
                    (20,-50,-18,-78),(12,-72,-24,-95)]
        for bx1,by1,bx2,by2 in branches:
            if flip: bx1,bx2=-bx1,-bx2
            pygame.draw.line(surf,(42,30,18),(sx+bx1,sy+by1),(sx+bx2,sy+by2),3)
            # Smaller sub-branches
            mx=(bx1+bx2)//2; my=(by1+by2)//2
            pygame.draw.line(surf,(38,26,14),(sx+mx,sy+my),
                             (sx+mx+trng.randint(-14,14),sy+my+trng.randint(-22,-8)),2)

    _dead_tree(W//2-220, ground, 11)
    _dead_tree(W//2+200, ground, 22, flip=True)
    _dead_tree(W//2-370, ground+8, 33)
    _dead_tree(W//2+350, ground+8, 44, flip=True)

    # Dark ground
    for y in range(ground, H):
        t=(y-ground)/(H-ground)
        pygame.draw.line(surf,(int(28+10*t),int(20+6*t),int(14+4*t)),(0,y),(W,y))
    # Cracked earth texture
    crack_rng = random.Random(99)
    for _ in range(18):
        cx2=crack_rng.randint(0,W); cy2=crack_rng.randint(ground,H)
        pygame.draw.line(surf,(22,14,8),(cx2,cy2),
                         (cx2+crack_rng.randint(-30,30),cy2+crack_rng.randint(-12,12)),1)

    # Stone road — darker, more worn
    _draw_stone_road(surf,W,H,rng)
    # Road grime overlay
    for y in range(ground, H):
        v=rng.randint(-6,6)
        pygame.draw.line(surf,(28+v,20+v,14+v),(0,y),(W,y))
    _draw_stone_road(surf,W,H,rng)

    # Main dungeon entrance structure — large ruined stone facade
    fw = 320; fh = 210
    fx = W//2-fw//2; fy = ground-fh

    # Ruined wall left wing
    for col in range(6):
        bw2=44; bh2=rng.randint(55,90)
        bx3=fx+col*(bw2+2); by3=fy+fh-bh2
        v=rng.randint(-8,8)
        pygame.draw.rect(surf,(55+v,42+v,28+v),(bx3,by3,bw2,bh2))
        pygame.draw.rect(surf,(38+v,28+v,16+v),(bx3,by3,bw2,bh2),2)
        # Stone row lines
        for row in range(bh2//18):
            pygame.draw.line(surf,(32,22,12),(bx3,by3+row*18),(bx3+bw2,by3+row*18),1)
    # Ruined wall right wing
    for col in range(6):
        bw2=44; bh2=rng.randint(55,90)
        bx3=W//2+44+col*(bw2+2); by3=fy+fh-bh2
        v=rng.randint(-8,8)
        pygame.draw.rect(surf,(55+v,42+v,28+v),(bx3,by3,bw2,bh2))
        pygame.draw.rect(surf,(38+v,28+v,16+v),(bx3,by3,bw2,bh2),2)
        for row in range(bh2//18):
            pygame.draw.line(surf,(32,22,12),(bx3,by3+row*18),(bx3+bw2,by3+row*18),1)

    # Central tower — tall, imposing, partially intact
    tw2=110; th2=fh+55; tx3=W//2-tw2//2; ty3=fy-55
    pygame.draw.rect(surf,(52,40,26),(tx3,ty3,tw2,th2))
    pygame.draw.rect(surf,(35,26,14),(tx3,ty3,tw2,th2),3)
    # Block texture
    blk_rng=random.Random(77)
    for row in range(12):
        for col in range(4):
            bsx=tx3+3+col*(tw2//4); bsy=ty3+4+row*(th2//12)
            v2=blk_rng.randint(-6,6)
            pygame.draw.rect(surf,(46+v2,35+v2,22+v2),(bsx,bsy,tw2//4-4,th2//12-3),1)
    # Tower top — partially collapsed battlements
    for i,intact in enumerate([True,False,True,True,False,True]):
        if intact:
            pygame.draw.rect(surf,(52,40,26),(tx3+i*18,ty3-18,14,20))
            pygame.draw.rect(surf,(35,26,14),(tx3+i*18,ty3-18,14,20),1)
    # Tower cracks
    pygame.draw.line(surf,(28,18,8),(tx3+tw2//3,ty3),(tx3+tw2//3-8,ty3+th2//3),2)
    pygame.draw.line(surf,(28,18,8),(tx3+tw2*2//3,ty3+20),(tx3+tw2*2//3+6,ty3+80),1)

    # Arch gateway — grand and ominous
    aw2=96; ax2=W//2-aw2//2; arch_top=fy+fh-160
    # Absolute void inside
    pygame.draw.rect(surf,(2,1,1),(ax2,arch_top,aw2,ground-arch_top))
    pygame.draw.arc(surf,(2,1,1),(ax2,arch_top-aw2//2,aw2,aw2),0,math.pi,aw2//2)
    # Stone arch surround — thick, decorative
    pygame.draw.arc(surf,(58,44,28),(ax2-8,arch_top-aw2//2-8,aw2+16,aw2+16),0,math.pi,10)
    pygame.draw.arc(surf,(42,30,16),(ax2-14,arch_top-aw2//2-14,aw2+28,aw2+28),0,math.pi,4)
    # Carved warning runes above arch
    rune_y=arch_top-aw2//2-22
    for rx2 in range(ax2-6,ax2+aw2+6,12):
        rv=blk_rng.randint(0,2)
        if rv==0:   pygame.draw.line(surf,(80,55,30),(rx2,rune_y),(rx2,rune_y+10),2)
        elif rv==1: pygame.draw.line(surf,(80,55,30),(rx2,rune_y+2),(rx2+8,rune_y+8),1)
        else:       pygame.draw.rect(surf,(80,55,30),(rx2,rune_y+3,6,6),1)
    # Keystone with skull motif
    kx=W//2; ky=arch_top-aw2//2-8
    pygame.draw.polygon(surf,(68,52,32),[(kx-12,ky-10),(kx+12,ky-10),(kx+8,ky+16),(kx-8,ky+16)])
    pygame.draw.polygon(surf,(38,28,14),[(kx-12,ky-10),(kx+12,ky-10),(kx+8,ky+16),(kx-8,ky+16)],2)
    pygame.draw.circle(surf,(165,148,128),(kx,ky+2),7)
    pygame.draw.circle(surf,(32,22,10),(kx,ky+2),7,1)
    for ex2 in [kx-3,kx+3]:
        pygame.draw.circle(surf,(16,10,6),(ex2,ky+1),2)

    # Arch side pillars — carved stone
    for px4,pw2 in [(ax2-18,18),(ax2+aw2,18)]:
        pygame.draw.rect(surf,(48,36,22),(px4,arch_top,pw2,ground-arch_top))
        pygame.draw.rect(surf,(34,24,12),(px4,arch_top,pw2,ground-arch_top),2)
        for row in range((ground-arch_top)//22):
            pygame.draw.line(surf,(28,18,8),(px4,arch_top+row*22),(px4+pw2,arch_top+row*22),1)

    # Red ominous glow from inside — pulsing
    pulse=0.4+0.4*math.sin(time*1.8)
    pulse2=0.3+0.3*math.sin(time*2.6+1.0)
    gsurf=pygame.Surface((aw2+40,100),pygame.SRCALPHA)
    pygame.draw.ellipse(gsurf,(int(180*pulse),int(18*pulse),int(14*pulse),int(100*pulse)),
                        (0,0,aw2+40,100))
    surf.blit(gsurf,(ax2-20,ground-100),special_flags=pygame.BLEND_RGBA_ADD)
    # Flickering secondary glow
    gsurf2=pygame.Surface((aw2,60),pygame.SRCALPHA)
    pygame.draw.ellipse(gsurf2,(int(220*pulse2),int(30*pulse2),20,int(70*pulse2)),(0,0,aw2,60))
    surf.blit(gsurf2,(ax2,ground-80),special_flags=pygame.BLEND_RGBA_ADD)

    # Steps descending into darkness
    for i in range(5):
        sw2=aw2-i*10+10; sx2=W//2-sw2//2; sy2=ground-i*12
        pygame.draw.rect(surf,(42+i*2,30+i,18+i),(sx2,sy2,sw2,11))
        pygame.draw.rect(surf,(28,18,8),(sx2,sy2,sw2,11),1)

    # Hanging chains on arch sides
    for chx in [ax2+10, ax2+aw2-10]:
        for ci in range(5):
            cy3=arch_top+ci*18
            pygame.draw.ellipse(surf,(55,42,25),(chx-4,cy3,8,12))
            pygame.draw.ellipse(surf,(38,28,14),(chx-4,cy3,8,12),1)

    # Skull pile at base of entrance — left side
    for sk_i,(skx2,sky2,skr) in enumerate([(ax2-28,ground-10,8),(ax2-40,ground-20,7),
                                              (ax2-18,ground-22,9)]):
        pygame.draw.circle(surf,(155,142,125),(skx2,sky2),skr)
        pygame.draw.circle(surf,(30,20,10),(skx2,sky2),skr,1)
        for ex2 in [skx2-skr//3,skx2+skr//3]:
            pygame.draw.circle(surf,(18,10,6),(ex2,sky2-1),max(2,skr//3))

    # Wall-mounted torches flanking entrance — with animated flames
    for tcx2,tside2 in [(ax2-32,-1),(ax2+aw2+14,1)]:
        tcy2=arch_top+30
        pygame.draw.line(surf,(62,44,24),(tcx2,tcy2+2),(tcx2+tside2*10,tcy2+12),3)
        pygame.draw.rect(surf,(70,50,26),(tcx2-3,tcy2-18,6,20))
        tp=0.65+0.35*math.sin(time*4.2+tcx2*0.03)
        pygame.draw.polygon(surf,(int(230*tp),int(110*tp),15),[
            (tcx2-5,tcy2-18),(tcx2,tcy2-34),(tcx2+5,tcy2-18)])
        pygame.draw.polygon(surf,(255,int(180*tp),40),[
            (tcx2-2,tcy2-18),(tcx2,tcy2-28),(tcx2+2,tcy2-18)])
        tgs=pygame.Surface((32,32),pygame.SRCALPHA)
        pygame.draw.circle(tgs,(int(200*tp),int(90*tp),15,int(60*tp)),(16,16),14)
        surf.blit(tgs,(tcx2-16,tcy2-36),special_flags=pygame.BLEND_RGBA_ADD)

    # "WARNING" carved stone plaque
    pw3=110; ph3=26; px5=W//2-pw3//2; py5=fy+fh-195
    pygame.draw.rect(surf,(48,36,22),(px5,py5,pw3,ph3))
    pygame.draw.rect(surf,(32,22,10),(px5,py5,pw3,ph3),2)
    sf=pygame.font.SysFont("courier new",11,bold=True)
    ws=sf.render("ENTER AT YOUR PERIL",True,(155,100,45))
    surf.blit(ws,(W//2-ws.get_width()//2,py5+6))


def _draw_town_backdrop(surf, W, H, rng, exclude_self=True):
    ground_y = H * 2 // 3
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
        pygame.draw.rect(surf, col,  (bx2-bw2//2, by2, bw2, bh2))
        pygame.draw.rect(surf, dark, (bx2-bw2//2, by2, bw2, bh2), 2)
        rh = bh2 // 3
        pygame.draw.polygon(surf, (82+v, 58+v, 32+v), [
            (bx2-bw2//2-5, by2),(bx2, by2-rh),(bx2+bw2//2+5, by2)])
        pygame.draw.polygon(surf, (58+v, 40+v, 20+v), [
            (bx2-bw2//2-5, by2),(bx2, by2-rh),(bx2+bw2//2+5, by2)], 2)
        ww2 = bw2 // 5; wh2 = bh2 // 5
        wy2 = by2 + bh2 // 4
        for wx_off in [-bw2//4, bw2//4 - ww2//2]:
            pygame.draw.rect(surf, (175, 210, 225),(bx2+wx_off-ww2//2, wy2, ww2, wh2))
            pygame.draw.rect(surf, (65, 50, 30),(bx2+wx_off-ww2//2, wy2, ww2, wh2), 1)
            pygame.draw.line(surf, (65, 50, 30),(bx2+wx_off, wy2),(bx2+wx_off, wy2+wh2), 1)
        if bw2 >= 130:
            dw2 = bw2 // 5; dh2 = bh2 // 3
            pygame.draw.rect(surf, (58, 40, 18),(bx2-dw2//2, by2+bh2-dh2, dw2, dh2))
        pygame.draw.rect(surf, dark,(bx2+bw2//4-5, by2-rh-18, 10, 22))

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

        self.idx     = start_idx
        self.sliding = False
        self.slide_t = 0.0
        self.slide_dir = 1
        self.next_idx  = 0

        self._bgs = self._build_bgs()
        self._static_bases = self._build_static_bases()
        self._rng = random.Random(42)

        self._show_notice = False
        self._notice_idx  = 0

        self.open_anim = 0.0
        self.OPEN_DUR  = 0.4

        self._left_hover  = 0.0
        self._right_hover = 0.0

        # Pre-bake overlay gradients (expensive per-pixel ops done once)
        self._bot_grad = self._make_gradient(self.W, 100, bottom=True)
        self._top_grad = self._make_gradient(self.W, 80,  bottom=False)

        # Pre-render per-area text surfaces
        self._area_text = []
        for area in AREAS:
            name_s = self.font_title.render(area["name"], True, (225,195,130))
            sh_s   = self.font_title.render(area["name"], True, (20,14,6))
            sub_s  = self.font_sub.render(area["subtitle"], True, (150,120,68))
            ap_surf = None
            if area["action_label"]:
                ap = self.font_small.render(area["action_label"], True,(210,185,110))
                ap_bg = pygame.Surface((ap.get_width()+20, ap.get_height()+8), pygame.SRCALPHA)
                ap_bg.fill((10,8,5,180))
                ap_bg.blit(ap, (10, 4))
                pygame.draw.rect(ap_bg,(100,80,42),(0,0,ap_bg.get_width(),ap_bg.get_height()),1)
                ap_surf = ap_bg
            self._area_text.append((name_s, sh_s, sub_s, ap_surf))

    def _make_gradient(self, W, H, bottom=True):
        """Build a cached SRCALPHA gradient surface using a scaled 1px strip."""
        strip = pygame.Surface((1, H), pygame.SRCALPHA)
        for y in range(H):
            if bottom:
                a = int(180 * (y/H)**0.6)
            else:
                a = int(140 * ((H-y)/H)**1.2)
            strip.set_at((0, y), (0, 0, 0, a))
        return pygame.transform.scale(strip, (W, H))

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

    def _build_static_bases(self):
        """Pre-bake the static (non-animated) layer of each animated BG."""
        bases = {}
        rng = random.Random(77)
        for i, area in enumerate(AREAS):
            if area["bg"] in self.ANIMATED_BGS:
                surf = pygame.Surface((self.W, self.H))
                fn   = BG_FUNCS.get(area["bg"])
                if fn:
                    fn(surf, self.W, self.H, random.Random(i*100), 0.0)
                bases[i] = surf
        return bases

    ANIMATED_BGS = {"inn", "blacksmith", "antiquity", "dungeon", "market", "shop", "gate"}

    def _redraw_bg(self, idx):
        if AREAS[idx]["bg"] in self.ANIMATED_BGS:
            surf = self._bgs[idx]
            fn   = BG_FUNCS.get(AREAS[idx]["bg"])
            if fn:
                # Restore static base (sky, road, building structure) first
                # so animated functions only need to redraw glows/flames/smoke
                if idx in self._static_bases:
                    surf.blit(self._static_bases[idx], (0, 0))
                fn(surf, self.W, self.H, random.Random(idx*100), self.time)

    def _draw_area(self, surf_idx, x_offset):
        self.screen.blit(self._bgs[surf_idx], (x_offset, 0))
        self._draw_overlay(surf_idx, x_offset)

    def _draw_overlay(self, area_idx, ox):
        area = AREAS[area_idx]

        # Use pre-baked gradients — no per-frame surface allocation
        self.screen.blit(self._bot_grad, (ox, self.H-100))
        self.screen.blit(self._top_grad, (ox, 0))

        name_s, sh_s, sub_s, ap_surf = self._area_text[area_idx]
        self.screen.blit(sh_s,   (ox+self.W//2-name_s.get_width()//2+2, self.H-78))
        self.screen.blit(name_s, (ox+self.W//2-name_s.get_width()//2,   self.H-80))
        self.screen.blit(sub_s,  (ox+self.W//2-sub_s.get_width()//2,    self.H-48))

        if ap_surf:
            bx = ox + self.W//2 - ap_surf.get_width()//2
            by = self.H*2//3+18
            self.screen.blit(ap_surf, (bx, by))

    def _draw_arrows(self, ease):
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

    def _start_slide(self, direction):
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

    def run(self) -> str:
        while True:
            dt          = self.clock.tick(60)/1000.0
            self.time  += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            ease        = 1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            mouse       = pygame.mouse.get_pos()
            left_r, right_r = self._arrow_rects()

            tl = 1.0 if left_r.collidepoint(mouse)  and self.idx>0             else 0.0
            tr = 1.0 if right_r.collidepoint(mouse) and self.idx<len(AREAS)-1  else 0.0
            self._left_hover  += (tl-self._left_hover)*10*dt
            self._right_hover += (tr-self._right_hover)*10*dt
            self._left_hover   = max(0.0,min(1.0,self._left_hover))
            self._right_hover  = max(0.0,min(1.0,self._right_hover))

            if self.sliding:
                self.slide_t += dt
                if self.slide_t >= self.SLIDE_DUR:
                    self.sliding = False
                    self.idx     = self.next_idx

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ("exit", self.idx)

                if event.type == pygame.KEYDOWN:
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
                        if area["action_key"] == "notice_board":
                            return (area["action_key"], self.idx)
                        elif area["action_key"]:
                            return (area["action_key"], self.idx)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                    if left_r.collidepoint(mouse) and not self.sliding:
                        self._start_slide(-1)
                    elif right_r.collidepoint(mouse) and not self.sliding:
                        self._start_slide(1)

            if self.sliding:
                raw  = self.slide_t/self.SLIDE_DUR
                prog = 1-(1-raw)**3
                offset = int(self.W * prog * -self.slide_dir)
                self._redraw_bg(self.idx)
                self._draw_area(self.idx, offset)
                self._redraw_bg(self.next_idx)
                self._draw_area(self.next_idx, offset + self.W*self.slide_dir)
            else:
                self._redraw_bg(self.idx)
                self._draw_area(self.idx, 0)

            self._draw_arrows(ease)
            self._draw_position_dots(ease)
            self._draw_hints(ease)
            pygame.display.flip()