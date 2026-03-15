import pygame
import math
import random

from src.player_stats import PlayerStats, exp_to_next


STATS = [
    {
        "key":   "dexterity",
        "name":  "Dexterity",
        "icon":  (60, 200, 120),
        "desc":  "+5 max HP per point",
        "attr":  "dexterity",
    },
    {
        "key":   "strength",
        "name":  "Strength",
        "icon":  (220, 100, 60),
        "desc":  "+1 attack damage per point",
        "attr":  "strength",
    },
    {
        "key":   "magic_mastery",
        "name":  "Magic Mastery",
        "icon":  (160, 100, 240),
        "desc":  "Increases relic effectiveness",
        "attr":  "magic_mastery",
    },
]


def _lerp(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))


class LevelUpScene:
    """
    Shown after gaining enough EXP to level up.
    Player picks one stat to increase.
    Can be called once per level gained.
    """

    def __init__(self, screen, stats: PlayerStats, new_level: int):
        self.screen    = screen
        self.W, self.H = screen.get_size()
        self.clock     = pygame.time.Clock()
        self.time      = 0.0
        self.stats     = stats
        self.new_level = new_level

        self.font_huge   = pygame.font.SysFont("courier new", 52, bold=True)
        self.font_title  = pygame.font.SysFont("courier new", 28, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 18, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 14)
        self.font_tiny   = pygame.font.SysFont("courier new", 12)

        self.selected  = 0
        self._hover    = [0.0]*len(STATS)
        self.confirmed = False
        self.confirm_t = 0.0

        self.open_anim = 0.0
        self.OPEN_DUR  = 0.5

        # Particles
        rng = random.Random()
        self.particles = [
            {
                "x":  rng.uniform(0,self.W),
                "y":  rng.uniform(0,self.H),
                "vx": rng.uniform(-30,30),
                "vy": rng.uniform(-60,-20),
                "life": rng.uniform(0.8,2.0),
                "max_life": 2.0,
                "size": rng.choice([2,2,3,4]),
                "col": rng.choice([(220,185,60),(180,220,80),(100,180,255),(200,100,255)]),
            }
            for _ in range(60)
        ]

    # ------------------------------------------------------------------ #

    def _update_particles(self, dt):
        for p in self.particles:
            p["x"]   += p["vx"]*dt
            p["y"]   += p["vy"]*dt
            p["vy"]  += 30*dt   # gravity
            p["life"] -= dt
            if p["life"] <= 0:
                rng = random.Random()
                p["x"]    = rng.uniform(0,self.W)
                p["y"]    = self.H + 10
                p["vx"]   = rng.uniform(-40,40)
                p["vy"]   = rng.uniform(-80,-30)
                p["life"] = rng.uniform(0.8,2.0)

    def _draw_bg(self, ease):
        self.screen.fill((8,6,12))
        # Gold radial glow
        cx,cy = self.W//2, self.H//2
        for r in range(300,0,-8):
            t2 = 1-(r/300)
            col = _lerp((8,6,12),(40,30,8),t2**2)
            pygame.draw.circle(self.screen,col,(cx,cy),r)
        # Particles
        for p in self.particles:
            alpha = max(0,min(1,p["life"]/p["max_life"]))
            r2,g2,b2 = p["col"]
            pygame.draw.circle(self.screen,
                               (int(r2*alpha),int(g2*alpha),int(b2*alpha)),
                               (int(p["x"]),int(p["y"])), p["size"])

    def _draw_level_banner(self, ease):
        # "LEVEL UP!" text
        pulse = 0.9+0.1*math.sin(self.time*4)
        col   = (int(220*pulse),int(185*pulse),int(60*pulse))
        label = self.font_huge.render("LEVEL UP!", True, col)
        sh    = self.font_huge.render("LEVEL UP!", True, (30,22,6))
        sx    = self.W//2 - label.get_width()//2
        sy    = int(self.H*0.10)

        ss = pygame.Surface(sh.get_size(),pygame.SRCALPHA)
        ss.blit(sh,(0,0)); ss.set_alpha(int(255*ease))
        ls = pygame.Surface(label.get_size(),pygame.SRCALPHA)
        ls.blit(label,(0,0)); ls.set_alpha(int(255*ease))
        self.screen.blit(ss,(sx+3,sy+4))
        self.screen.blit(ls,(sx,sy))

        # Level number
        lv = self.font_title.render(f"You reached level {self.new_level}!",
                                     True,(180,150,80))
        lvs = pygame.Surface(lv.get_size(),pygame.SRCALPHA)
        lvs.blit(lv,(0,0)); lvs.set_alpha(int(230*ease))
        self.screen.blit(lvs,(self.W//2-lv.get_width()//2,
                               sy+label.get_height()+8))

        # Stat points reminder
        pts = self.font_small.render(
            f"{self.stats.stat_points} stat point{'s' if self.stats.stat_points!=1 else ''} to spend",
            True,(140,115,55))
        ps = pygame.Surface(pts.get_size(),pygame.SRCALPHA)
        ps.blit(pts,(0,0)); ps.set_alpha(int(180*ease))
        self.screen.blit(ps,(self.W//2-pts.get_width()//2,
                              sy+label.get_height()+8+lv.get_height()+6))

    def _draw_stat_cards(self, ease):
        n    = len(STATS)
        pad  = 30
        cw   = (self.W - pad*(n+1)) // n
        ch   = int(self.H*0.42)
        cy   = int(self.H*0.38)

        for i,stat in enumerate(STATS):
            cx  = pad + i*(cw+pad)
            is_sel = (i == self.selected)
            t   = self._hover[i]

            # Slide in from below
            slide = 1-(1-min(1.0,(ease-i*0.08)))**3 if ease > i*0.08 else 0
            draw_y = cy + int((1-slide)*60)
            alpha  = int(255*slide)

            card = pygame.Surface((cw,ch),pygame.SRCALPHA)
            bg_col = (int(22+22*t),int(16+16*t),int(28+28*t),220)
            card.fill(bg_col)
            self.screen.blit(card,(cx,draw_y))

            # Border — glows for selected
            if is_sel:
                bc = _lerp((100,78,140),(200,160,255),t)
                pygame.draw.rect(self.screen,bc,(cx,draw_y,cw,ch),2)
                pygame.draw.rect(self.screen,tuple(max(0,c-60) for c in bc),
                                 (cx+5,draw_y+5,cw-10,ch-10),1)
            else:
                bc = _lerp((42,32,58),(90,70,120),t)
                pygame.draw.rect(self.screen,bc,(cx,draw_y,cw,ch),1)

            # Corner accents
            sz = 10
            for bx,by,dx,dy in [(cx,draw_y,1,1),(cx+cw,draw_y,-1,1),
                                  (cx,draw_y+ch,1,-1),(cx+cw,draw_y+ch,-1,-1)]:
                pygame.draw.line(self.screen,bc,(bx,by),(bx+dx*sz,by),2)
                pygame.draw.line(self.screen,bc,(bx,by),(bx,by+dy*sz),2)

            # Icon circle
            pulse = 0.7+0.3*math.sin(self.time*2+i) if is_sel else 0.6
            ic    = stat["icon"]
            icol  = (int(ic[0]*pulse),int(ic[1]*pulse),int(ic[2]*pulse))
            icx   = cx+cw//2; icy = draw_y+50
            pygame.draw.circle(self.screen,icol,(icx,icy),28)
            pygame.draw.circle(self.screen,tuple(min(255,c+60) for c in icol),
                               (icx,icy),28,2)

            # Glow on selected
            if is_sel:
                gs = pygame.Surface((80,80))
                gs.fill((8,6,12))
                pygame.draw.circle(gs,icol,(40,40),40)
                gs.set_colorkey((8,6,12))
                gs.set_alpha(int(60*pulse))
                self.screen.blit(gs,(icx-40,icy-40))

            # Stat name
            nc  = _lerp((150,120,200),(220,190,255),t) if is_sel \
                  else _lerp((100,80,130),(170,145,200),t)
            ns  = self.font_medium.render(stat["name"],True,nc)
            nss = pygame.Surface(ns.get_size(),pygame.SRCALPHA)
            nss.blit(ns,(0,0)); nss.set_alpha(alpha)
            self.screen.blit(nss,(cx+cw//2-ns.get_width()//2,draw_y+88))

            # Current value
            val    = getattr(self.stats, stat["attr"])
            val_s  = self.font_small.render(f"Current: {val}",True,
                                             _lerp((80,65,100),(140,115,170),t))
            vss    = pygame.Surface(val_s.get_size(),pygame.SRCALPHA)
            vss.blit(val_s,(0,0)); vss.set_alpha(alpha)
            self.screen.blit(vss,(cx+cw//2-val_s.get_width()//2,draw_y+114))

            # Description
            ds  = self.font_tiny.render(stat["desc"],True,
                                         _lerp((70,55,90),(120,96,150),t))
            dss = pygame.Surface(ds.get_size(),pygame.SRCALPHA)
            dss.blit(ds,(0,0)); dss.set_alpha(alpha)
            self.screen.blit(dss,(cx+cw//2-ds.get_width()//2,draw_y+134))

            # Divider
            pygame.draw.line(self.screen,bc,
                             (cx+20,draw_y+ch-75),(cx+cw-20,draw_y+ch-75),1)

            # What you get
            bonus = "+5 max HP" if stat["key"]=="dexterity" else \
                    "+1 ATK dmg" if stat["key"]=="strength" else \
                    "+1 relic power"
            bs  = self.font_small.render(f"→  {bonus}",True,
                                          _lerp((100,80,140),(180,155,220),t))
            bss = pygame.Surface(bs.get_size(),pygame.SRCALPHA)
            bss.blit(bs,(0,0)); bss.set_alpha(alpha)
            self.screen.blit(bss,(cx+cw//2-bs.get_width()//2,draw_y+ch-55))

            # CHOOSE button on selected
            if is_sel:
                btn_col = _lerp((80,60,110),(160,130,210),t)
                btn_rect = pygame.Rect(cx+cw//4, draw_y+ch-30, cw//2, 24)
                bf = pygame.Surface((cw//2,24),pygame.SRCALPHA)
                bf.fill((int(18+20*t),int(14+16*t),int(24+28*t),210))
                bfs = pygame.Surface((cw//2,24),pygame.SRCALPHA)
                bfs.blit(bf,(0,0)); bfs.set_alpha(alpha)
                self.screen.blit(bfs,btn_rect.topleft)
                pygame.draw.rect(self.screen,btn_col,btn_rect,2)
                cl = self.font_tiny.render("ENTER  choose",True,btn_col)
                self.screen.blit(cl,(btn_rect.centerx-cl.get_width()//2,
                                     btn_rect.centery-cl.get_height()//2))

    def _draw_hint(self, ease):
        hint = self.font_tiny.render(
            "← →  select stat    ENTER  confirm",True,(80,65,100))
        hs = pygame.Surface(hint.get_size(),pygame.SRCALPHA)
        hs.blit(hint,(0,0)); hs.set_alpha(int(180*ease))
        self.screen.blit(hs,(self.W//2-hint.get_width()//2,self.H-28))

    def _draw_confirm_flash(self):
        stat_name = STATS[self.selected]["name"]
        t  = min(1.0,self.confirm_t/0.3)
        label = self.font_title.render(
            f"{stat_name} increased!", True,
            STATS[self.selected]["icon"])
        ls = pygame.Surface(label.get_size(),pygame.SRCALPHA)
        ls.blit(label,(0,0)); ls.set_alpha(int(255*(1-t)))
        self.screen.blit(ls,(self.W//2-label.get_width()//2,
                              self.H//2-label.get_height()//2))

    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while True:
            dt          = self.clock.tick(60)/1000.0
            self.time  += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            ease        = 1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            mouse       = pygame.mouse.get_pos()
            self._update_particles(dt)

            # Hover
            n   = len(STATS)
            pad = 30
            cw  = (self.W-pad*(n+1))//n
            ch  = int(self.H*0.42)
            cy  = int(self.H*0.38)
            for i in range(n):
                cx  = pad+i*(cw+pad)
                tgt = 1.0 if pygame.Rect(cx,cy,cw,ch).collidepoint(mouse) else 0.0
                self._hover[i] += (tgt-self._hover[i])*10*dt
                self._hover[i]  = max(0.0,min(1.0,self._hover[i]))
                if tgt > 0: self.selected = i

            if self.confirmed:
                self.confirm_t += dt
                if self.confirm_t >= 0.6:
                    return "done"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "done"
                if not self.confirmed and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.selected = max(0,self.selected-1)
                    if event.key == pygame.K_RIGHT:
                        self.selected = min(len(STATS)-1,self.selected+1)
                    if event.key in (pygame.K_RETURN,pygame.K_SPACE):
                        stat = STATS[self.selected]["key"]
                        if self.stats.spend_point(stat):
                            self.confirmed = True
                            self.confirm_t = 0.0
                if not self.confirmed and event.type==pygame.MOUSEBUTTONDOWN \
                        and event.button==1:
                    for i in range(n):
                        cx = pad+i*(cw+pad)
                        if pygame.Rect(cx,cy,cw,ch).collidepoint(mouse):
                            self.selected = i
                            stat = STATS[i]["key"]
                            if self.stats.spend_point(stat):
                                self.confirmed = True
                                self.confirm_t = 0.0

            self._draw_bg(ease)
            self._draw_level_banner(ease)
            self._draw_stat_cards(ease)
            self._draw_hint(ease)
            if self.confirmed:
                self._draw_confirm_flash()

            pygame.display.flip()