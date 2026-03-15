import pygame
import math
import random


# ---------------------------------------------------------------------------
# Town data
# ---------------------------------------------------------------------------

TOWNS = [
    # Index 0 — starting hub in the rough centre
    {"name": "Dungeon",      "x": 0.50, "y": 0.52, "type": "dungeon",  "desc": "The dungeon you just escaped from. Dark and foreboding."},
    # Surrounding towns — deliberately uneven distances and angles
    {"name": "Ashenvale",    "x": 0.24, "y": 0.30, "type": "capital",  "desc": "A grand walled city, seat of the kingdom."},
    {"name": "Millhaven",    "x": 0.58, "y": 0.20, "type": "town",     "desc": "A prosperous market town by the river."},
    {"name": "Duskport",     "x": 0.82, "y": 0.28, "type": "port",     "desc": "A foggy harbour town, sailors and smugglers."},
    {"name": "Ironhold",     "x": 0.78, "y": 0.58, "type": "fortress", "desc": "A dwarven fortress carved into the mountain."},
    {"name": "Grimhaven",    "x": 0.66, "y": 0.78, "type": "dungeon",  "desc": "A cursed town bordering the dark marshes."},
    {"name": "Emberveil",    "x": 0.32, "y": 0.82, "type": "town",     "desc": "Famous for its fire festivals and spiced mead."},
    {"name": "Crestfall",    "x": 0.14, "y": 0.62, "type": "town",     "desc": "Built on the ruins of an older civilisation."},
    {"name": "Thornwick",    "x": 0.20, "y": 0.46, "type": "town",     "desc": "A sleepy village surrounded by thorned hedgerows."},
    {"name": "Veldmoor",     "x": 0.44, "y": 0.36, "type": "town",     "desc": "A muddy crossroads town, busy with travellers."},
]

# Road connections — spider-web from centre, with some cross-links
# All outer towns connect to the dungeon hub, plus some neighbour links
ROADS = [
    # Hub spokes (dungeon to each town)
    (0, 1), (0, 2), (0, 3), (0, 4),
    (0, 5), (0, 6), (0, 7), (0, 8),
    (0, 9),
    # Outer ring partial connections (not all — keeps it asymmetric)
    (1, 2), (2, 3), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (8, 1), (9, 2), (9, 8),
    (4, 5),
]

# Town type colours (parchment palette)
TYPE_COLS = {
    "capital":  (160,  80,  30),
    "town":     (100,  75,  40),
    "port":     ( 50,  90, 120),
    "fortress": ( 80,  70,  60),
    "dungeon":  ( 90,  40,  40),
}


# ---------------------------------------------------------------------------
# WorldMapScene
# ---------------------------------------------------------------------------

class WorldMapScene:
    def __init__(self, screen, current_location: str = "dungeon"):
        self.screen           = screen
        self.W, self.H        = screen.get_size()
        self.clock            = pygame.time.Clock()
        self.time             = 0.0
        self.current_location = current_location

        self.font_title  = pygame.font.SysFont("courier new", 32, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 18, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 14)
        self.font_tiny   = pygame.font.SysFont("courier new", 12)

        # Map area (leave margin for border/title)
        self.mx = int(self.W * 0.06)
        self.my = int(self.H * 0.10)
        self.mw = int(self.W * 0.88)
        self.mh = int(self.H * 0.76)

        self.selected   = None   # hovered town index
        self.confirmed  = None   # clicked town index
        self._hover_t   = [0.0] * len(TOWNS)

        # Confirm button
        bw, bh = 200, 48
        self.confirm_rect = pygame.Rect(
            self.W//2 - bw//2,
            self.my + self.mh + 14,
            bw, bh)
        self._confirm_hover = 0.0

        self.open_anim = 0.0
        self.OPEN_DUR  = 0.6

        # Pre-build parchment + static map elements
        self.paper   = self._build_paper()
        self.map_sur = self._build_map_surface()

    # ------------------------------------------------------------------ #
    # Parchment background
    # ------------------------------------------------------------------ #

    def _build_paper(self):
        surf = pygame.Surface((self.W, self.H))
        rng  = random.Random(55)
        surf.fill((188, 162, 105))

        # Noise
        noise = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for _ in range(22000):
            nx = rng.randint(0, self.W-1)
            ny = rng.randint(0, self.H-1)
            v  = rng.randint(-20, 20)
            a  = rng.randint(15, 55)
            pygame.draw.circle(noise, (max(0,min(255,125+v)),
                                       max(0,min(255,100+v)),
                                       max(0,min(255,55+v)), a),
                               (nx, ny), rng.randint(1,4))
        surf.blit(noise, (0,0))

        # Water stains
        stain = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for _ in range(14):
            sx = rng.randint(0, self.W)
            sy = rng.randint(0, self.H)
            sr = rng.randint(50, 200)
            sa = rng.randint(10, 28)
            pygame.draw.ellipse(stain, (70,48,18,sa),
                                (sx-sr, sy-sr//2, sr*2, int(sr*1.4)))
        surf.blit(stain, (0,0))

        # Vignette
        vig = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        cx, cy = self.W//2, self.H//2
        max_r  = int(math.hypot(cx, cy))
        for i in range(60, 0, -1):
            r = int(max_r * i/60)
            a = int(120 * (i/60)**1.8)
            pygame.draw.circle(vig, (45,28,8,a), (cx,cy), r)
        surf.blit(vig, (0,0))

        # Torn border
        border = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        rng2   = random.Random(66)
        for side in range(4):
            for i in range(0, max(self.W,self.H), 5):
                jag = rng2.randint(6, 28)
                al  = rng2.randint(130, 210)
                if side==0:   pygame.draw.rect(border,(18,10,3,al),(i,0,6,jag))
                elif side==1: pygame.draw.rect(border,(18,10,3,al),(i,self.H-jag,6,jag))
                elif side==2: pygame.draw.rect(border,(18,10,3,al),(0,i,jag,6))
                else:         pygame.draw.rect(border,(18,10,3,al),(self.W-jag,i,jag,6))
        surf.blit(border, (0,0))

        return surf

    # ------------------------------------------------------------------ #
    # Static map surface (terrain, roads)
    # ------------------------------------------------------------------ #

    def _build_map_surface(self):
        surf = pygame.Surface((self.mw, self.mh), pygame.SRCALPHA)
        rng  = random.Random(77)

        # Terrain patches — hills, forests
        for _ in range(40):
            tx = rng.randint(20, self.mw-20)
            ty = rng.randint(20, self.mh-20)
            tr = rng.randint(18, 55)
            tc = rng.choice([
                (90, 110, 60, 35),   # green hill
                (70,  95, 50, 28),   # dark forest
                (110,130, 75, 22),   # light meadow
                (140,120, 80, 20),   # sandy plain
            ])
            pygame.draw.ellipse(surf, tc, (tx-tr, ty-tr//2, tr*2, tr))

        # Mountain symbols (top right area)
        for mx2, my2 in [(int(self.mw*0.70), int(self.mh*0.25)),
                          (int(self.mw*0.76), int(self.mh*0.18)),
                          (int(self.mw*0.80), int(self.mh*0.30))]:
            h2 = rng.randint(18, 30)
            w2 = rng.randint(14, 22)
            pygame.draw.polygon(surf, (100,88,70,140), [
                (mx2, my2-h2), (mx2-w2, my2+8), (mx2+w2, my2+8)])
            pygame.draw.polygon(surf, (160,148,130,100), [
                (mx2, my2-h2), (mx2-4, my2-h2+10), (mx2+4, my2-h2+10)])

        # River (wavy path)
        riv_pts = []
        for i in range(20):
            rx = int(self.mw * (0.30 + 0.02 * math.sin(i*0.8)) * (i/19))
            ry = int(self.mh * (0.10 + i * 0.042))
            riv_pts.append((rx, ry))
        if len(riv_pts) > 1:
            pygame.draw.lines(surf, (80,120,160,120), False, riv_pts, 3)
            pygame.draw.lines(surf, (100,150,190,60), False, riv_pts, 1)

        # Roads between towns
        def town_px(t):
            return (int(t["x"] * self.mw), int(t["y"] * self.mh))

        for i, j in ROADS:
            ax, ay = town_px(TOWNS[i])
            bx, by = town_px(TOWNS[j])
            # Slightly curved road using midpoint offset
            mx2 = (ax+bx)//2 + rng.randint(-20, 20)
            my2 = (ay+by)//2 + rng.randint(-20, 20)
            # Draw as series of lines approximating a curve
            pts = []
            for s in range(11):
                t2 = s / 10
                px2 = int((1-t2)**2*ax + 2*(1-t2)*t2*mx2 + t2**2*bx)
                py2 = int((1-t2)**2*ay + 2*(1-t2)*t2*my2 + t2**2*by)
                pts.append((px2, py2))
            # Road shadow
            pygame.draw.lines(surf, (80,60,30,80), False, pts, 5)
            # Road surface
            pygame.draw.lines(surf, (140,115,70,160), False, pts, 3)
            # Road highlight
            pygame.draw.lines(surf, (165,138,88,80), False, pts, 1)

        return surf

    # ------------------------------------------------------------------ #
    # Town pixel position helpers
    # ------------------------------------------------------------------ #

    def _town_screen(self, t):
        return (self.mx + int(t["x"] * self.mw),
                self.my + int(t["y"] * self.mh))

    def _town_radius(self, t):
        return 18 if t["type"] == "capital" else 13

    # ------------------------------------------------------------------ #
    # Draw towns
    # ------------------------------------------------------------------ #

    def _draw_towns(self, alpha_frac):
        for i, town in enumerate(TOWNS):
            tx, ty = self._town_screen(town)
            r      = self._town_radius(town)
            col    = TYPE_COLS[town["type"]]
            hover  = self._hover_t[i]
            is_sel = (i == self.confirmed)
            is_cur = (town["name"] == self.current_location)
            pulse  = 0.7 + 0.3 * math.sin(self.time * 3 + i)

            # Glow for selected / current
            if is_sel or is_cur:
                gr = int(r * 2.5)
                glow = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
                gc = (200,160,60,int(40*pulse)) if is_sel else (80,140,200,int(35*pulse))
                pygame.draw.circle(glow, gc, (gr,gr), gr)
                self.screen.blit(glow, (tx-gr, ty-gr),
                                 special_flags=pygame.BLEND_RGBA_ADD)

            # Town icon depending on type
            if town["type"] == "capital":
                # Castle silhouette
                pygame.draw.rect(self.screen, col,
                                 (tx-r, ty-r+4, r*2, r*2-4))
                for ox2 in [-r+2, -r//2, r//2-2]:
                    pygame.draw.rect(self.screen, col,
                                     (tx+ox2, ty-r-4, r//3, 8))
                pygame.draw.rect(self.screen,
                                 tuple(min(255,c+40) for c in col),
                                 (tx-r, ty-r+4, r*2, r*2-4), 1)
            elif town["type"] == "fortress":
                # Pentagon
                pts2 = [(int(tx+r*math.cos(math.radians(a-90))),
                         int(ty+r*math.sin(math.radians(a-90))))
                        for a in range(0,360,72)]
                pygame.draw.polygon(self.screen, col, pts2)
                pygame.draw.polygon(self.screen,
                                    tuple(min(255,c+40) for c in col), pts2, 2)
            elif town["type"] == "port":
                # Circle with anchor hint
                pygame.draw.circle(self.screen, col, (tx,ty), r)
                pygame.draw.circle(self.screen,
                                   tuple(min(255,c+40) for c in col), (tx,ty), r, 2)
                pygame.draw.line(self.screen, (200,200,220),
                                 (tx,ty-r//2),(tx,ty+r//2), 2)
                pygame.draw.line(self.screen, (200,200,220),
                                 (tx-r//2,ty),(tx+r//2,ty), 2)
            elif town["type"] == "dungeon":
                # Skull-ish — dark circle with X
                pygame.draw.circle(self.screen, col, (tx,ty), r)
                pygame.draw.circle(self.screen, (140,60,60), (tx,ty), r, 2)
                pygame.draw.line(self.screen,(160,80,80),(tx-6,ty-6),(tx+6,ty+6),2)
                pygame.draw.line(self.screen,(160,80,80),(tx+6,ty-6),(tx-6,ty+6),2)
            else:
                # House shape
                pygame.draw.rect(self.screen, col, (tx-r+2, ty-r+6, (r-2)*2, r*2-6))
                pygame.draw.polygon(self.screen, tuple(min(255,c+30) for c in col), [
                    (tx-r, ty-r+8), (tx, ty-r-4), (tx+r, ty-r+8)])
                pygame.draw.rect(self.screen,
                                 tuple(min(255,c+40) for c in col),
                                 (tx-r+2, ty-r+6, (r-2)*2, r*2-6), 1)

            # Hover ring
            if hover > 0.05:
                pygame.draw.circle(self.screen,
                                   (200,170,90,int(180*hover)),
                                   (tx,ty), int(r+4+hover*4), 2)

            # Current location marker — "YOU ARE HERE" star
            if is_cur:
                for sa in range(0, 360, 60):
                    ra = math.radians(sa + self.time*30)
                    sx2 = int(tx + math.cos(ra)*(r+7))
                    sy2 = int(ty + math.sin(ra)*(r+7))
                    pygame.draw.circle(self.screen,(200,170,60),(sx2,sy2),2)
                you = self.font_tiny.render("YOU ARE HERE", True, (140,100,30))
                self.screen.blit(you,(tx-you.get_width()//2, ty-r-20))

            # Town name label
            nc = (50,30,10) if not is_sel else (160,100,20)
            ns = self.font_tiny.render(town["name"], True, nc)
            self.screen.blit(ns, (tx - ns.get_width()//2, ty + r + 8))

    # ------------------------------------------------------------------ #
    # Description panel
    # ------------------------------------------------------------------ #

    def _draw_info_panel(self):
        town = TOWNS[self.confirmed] if self.confirmed is not None else None
        hov  = next((TOWNS[i] for i in range(len(TOWNS))
                     if self._hover_t[i] > 0.4), None)
        show = town or hov
        if not show:
            hint = self.font_small.render(
                "Click a town to select a destination", True, (70,50,22))
            self.screen.blit(hint, (self.W//2-hint.get_width()//2,
                                    self.my+self.mh+18))
            return

        name_s = self.font_medium.render(show["name"], True, (60,35,12))
        desc_s = self.font_tiny.render(show["desc"], True, (90,62,28))
        ty2 = self.my + self.mh + 12
        self.screen.blit(name_s, (self.W//2-name_s.get_width()//2, ty2))
        self.screen.blit(desc_s, (self.W//2-desc_s.get_width()//2,
                                   ty2+name_s.get_height()+3))

    # ------------------------------------------------------------------ #
    # Confirm button
    # ------------------------------------------------------------------ #

    def _draw_confirm(self):
        if self.confirmed is None:
            return
        t = self._confirm_hover
        fill = pygame.Surface((self.confirm_rect.w,self.confirm_rect.h),
                               pygame.SRCALPHA)
        fill.fill((int(18+40*t),int(14+32*t),int(8+18*t),220))
        self.screen.blit(fill, self.confirm_rect.topleft)
        def lc(a,b): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
        pygame.draw.rect(self.screen,lc((80,60,28),(200,160,70)),self.confirm_rect,2)
        name = TOWNS[self.confirmed]["name"].upper()
        lbl = self.font_medium.render(
            f"TRAVEL TO {name}",
            True, lc((140,100,45),(230,190,100)))
        self.screen.blit(lbl,(self.confirm_rect.centerx-lbl.get_width()//2,
                               self.confirm_rect.centery-lbl.get_height()//2))

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        """Returns the name of the chosen town, or 'exit'."""
        while True:
            dt         = self.clock.tick(60)/1000.0
            self.time += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            ease       = 1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            mouse      = pygame.mouse.get_pos()

            # Update hovers
            self.selected = None
            for i, town in enumerate(TOWNS):
                tx, ty = self._town_screen(town)
                r      = self._town_radius(town)
                dist   = math.hypot(mouse[0]-tx, mouse[1]-ty)
                tgt    = 1.0 if dist < r+8 else 0.0
                self._hover_t[i] += (tgt-self._hover_t[i])*10*dt
                self._hover_t[i]  = max(0.0,min(1.0,self._hover_t[i]))
                if tgt > 0:
                    self.selected = i

            # Confirm button hover
            ctgt = 1.0 if (self.confirmed is not None and
                           self.confirm_rect.collidepoint(mouse)) else 0.0
            self._confirm_hover += (ctgt-self._confirm_hover)*10*dt
            self._confirm_hover  = max(0.0,min(1.0,self._confirm_hover))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "cancelled"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Click town (can't select current location)
                    for i, town in enumerate(TOWNS):
                        tx, ty = self._town_screen(town)
                        r      = self._town_radius(town)
                        if math.hypot(mouse[0]-tx, mouse[1]-ty) < r+8:
                            if town["name"] != self.current_location:
                                self.confirmed = i
                            break
                    # Click confirm
                    if (self.confirmed is not None and
                            self.confirm_rect.collidepoint(mouse)):
                        return TOWNS[self.confirmed]["name"]

            # --- Draw ---
            self.screen.blit(self.paper, (0,0))

            # Fade in map
            ms = self.map_sur.copy()
            ms.set_alpha(int(255*ease))
            self.screen.blit(ms, (self.mx, self.my))

            # Map border
            pygame.draw.rect(self.screen,(55,35,12),
                             (self.mx-2,self.my-2,self.mw+4,self.mh+4),2)
            pygame.draw.rect(self.screen,(80,55,22),
                             (self.mx-6,self.my-6,self.mw+12,self.mh+12),1)

            if ease > 0.4:
                self._draw_towns(ease)
                self._draw_info_panel()
                self._draw_confirm()

                # Title
                title = self.font_title.render("— WORLD MAP —", True, (55,32,10))
                self.screen.blit(title,(self.W//2-title.get_width()//2,
                                        self.my-title.get_height()-8))

                # ESC hint
                esc = self.font_tiny.render("ESC  return to dungeon",
                                            True, (80,58,28))
                self.screen.blit(esc,(self.mx, self.my+self.mh+self.H//14))

            pygame.display.flip()