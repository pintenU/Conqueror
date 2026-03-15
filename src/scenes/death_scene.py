import pygame
import math
import random


class DeathScene:
    def __init__(self, screen):
        self.screen = screen
        self.W, self.H = screen.get_size()
        self.clock  = pygame.time.Clock()
        self.time   = 0.0

        self.font_title  = pygame.font.SysFont("courier new", 64, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 22, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 16)

        bw, bh = 300, 56
        cx = self.W//2 - bw//2
        cy = self.H//2 + 60
        self.btn_load = {"label": "USE LATEST SAVE", "rect": pygame.Rect(cx, cy,       bw, bh), "hover": 0.0}
        self.btn_menu = {"label": "MAIN MENU",        "rect": pygame.Rect(cx, cy+bh+14, bw, bh), "hover": 0.0}

        rng = random.Random()
        self.particles = [
            {
                "x":     rng.uniform(0, self.W),
                "y":     rng.uniform(0, self.H),
                "speed": rng.uniform(0.02, 0.12),
                "size":  rng.choice([1, 1, 2]),
                "phase": rng.uniform(0, math.tau),
            }
            for _ in range(60)
        ]

        # Pre-build vignette once
        self.vignette = self._build_vignette()

        self.open_anim = 0.0
        self.OPEN_DUR  = 1.2

    def _build_vignette(self):
        surf   = pygame.Surface((self.W, self.H))
        surf.fill((0, 0, 0))
        cx, cy = self.W//2, self.H//2
        max_r  = int(math.hypot(cx, cy))
        # Draw from outside in — darkest at edges, reddish tint
        for i in range(max_r, 0, -4):
            t   = 1.0 - (i / max_r)
            r2  = max(0, min(255, int(80 * t * t)))
            g2  = max(0, min(255, int(2  * t * t)))
            b2  = max(0, min(255, int(2  * t * t)))
            pygame.draw.circle(surf, (r2, g2, b2), (cx, cy), i)
        surf.set_colorkey((0, 0, 0))
        return surf

    def _draw_bg(self, ease):
        self.screen.fill((4, 2, 2))
        self.screen.blit(self.vignette, (0, 0))

        # Floating red motes — draw directly, no SRCALPHA
        for p in self.particles:
            flicker = 0.4 + 0.6 * math.sin(self.time * p["speed"] * 5 + p["phase"])
            r = max(1, min(255, int(180 * flicker)))
            g = max(0, min(255, int(10  * flicker)))
            b = max(0, min(255, int(10  * flicker)))
            pygame.draw.circle(self.screen, (r, g, b),
                               (int(p["x"]), int(p["y"])), p["size"])

    def _draw_title(self, alpha):
        flicker = 0.88 + 0.12 * math.sin(self.time * 2.8)
        col     = (int(200*flicker), int(8*flicker), int(8*flicker))

        shadow = self.font_title.render("YOU DIED", True, (30, 4, 4))
        label  = self.font_title.render("YOU DIED", True, col)
        sx = self.W//2 - label.get_width()//2
        sy = self.H//2 - 180

        ss = pygame.Surface(shadow.get_size(), pygame.SRCALPHA)
        ss.blit(shadow, (0, 0)); ss.set_alpha(alpha)
        ls = pygame.Surface(label.get_size(), pygame.SRCALPHA)
        ls.blit(label, (0, 0)); ls.set_alpha(alpha)

        self.screen.blit(ss, (sx+4, sy+5))
        self.screen.blit(ls, (sx, sy))

        sub  = self.font_small.render("your body crumbles in the darkness...", True, (120, 40, 40))
        subs = pygame.Surface(sub.get_size(), pygame.SRCALPHA)
        subs.blit(sub, (0, 0)); subs.set_alpha(alpha)
        self.screen.blit(subs, (self.W//2 - sub.get_width()//2,
                                 sy + label.get_height() + 8))

    def _draw_button(self, btn, alpha):
        t     = btn["hover"]
        rect  = btn["rect"]
        label = btn["label"]

        is_load = label == "USE LATEST SAVE"
        if is_load:
            bi, bh2 = (100, 30, 30), (220, 80, 80)
            ti, th2 = (200, 80, 80), (255, 160, 160)
        else:
            bi, bh2 = (60, 40, 40), (140, 90, 90)
            ti, th2 = (140, 90, 90), (200, 150, 150)

        def lc(a, b): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

        fill = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        fill.fill((int(12+20*t), int(4+8*t), int(4+8*t), int(180+40*t)))
        fs = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        fs.blit(fill, (0, 0)); fs.set_alpha(alpha)
        self.screen.blit(fs, rect.topleft)

        pygame.draw.rect(self.screen, lc(bi, bh2), rect, 2)
        pygame.draw.rect(self.screen, lc((30, 10, 10), (80, 30, 30)),
                         rect.inflate(-6, -6), 1)

        sz = 8
        c2 = lc(bi, bh2)
        for bx, by, dx, dy in [(rect.x, rect.y, 1, 1), (rect.x+rect.w, rect.y, -1, 1),
                                (rect.x, rect.y+rect.h, 1, -1), (rect.x+rect.w, rect.y+rect.h, -1, -1)]:
            pygame.draw.line(self.screen, c2, (bx, by), (bx+dx*sz, by), 1)
            pygame.draw.line(self.screen, c2, (bx, by), (bx, by+dy*sz), 1)

        lbl = self.font_medium.render(label, True, lc(ti, th2))
        ls  = pygame.Surface(lbl.get_size(), pygame.SRCALPHA)
        ls.blit(lbl, (0, 0)); ls.set_alpha(alpha)
        self.screen.blit(ls, (rect.centerx - lbl.get_width()//2,
                               rect.centery - lbl.get_height()//2))

    def run(self) -> str:
        while True:
            dt         = self.clock.tick(60) / 1000.0
            self.time += dt
            self.open_anim = min(self.open_anim + dt, self.OPEN_DUR)
            ease       = 1 - (1 - min(1.0, self.open_anim / self.OPEN_DUR)) ** 3
            alpha      = int(255 * ease)
            mouse      = pygame.mouse.get_pos()

            for btn in [self.btn_load, self.btn_menu]:
                tgt = 1.0 if btn["rect"].collidepoint(mouse) else 0.0
                btn["hover"] += (tgt - btn["hover"]) * 10 * dt
                btn["hover"]  = max(0.0, min(1.0, btn["hover"]))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "main_menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_load["rect"].collidepoint(mouse):
                        return "load_save"
                    if self.btn_menu["rect"].collidepoint(mouse):
                        return "main_menu"

            self._draw_bg(ease)
            self._draw_title(alpha)
            if ease > 0.5:
                self._draw_button(self.btn_load, int(255 * (ease - 0.5) * 2))
                self._draw_button(self.btn_menu, int(255 * (ease - 0.5) * 2))

            pygame.display.flip()