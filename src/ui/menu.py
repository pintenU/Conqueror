import pygame
import math
import random


class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self._hover_progress = 0.0

    def update(self, mouse_pos, dt):
        target = 1.0 if self.rect.collidepoint(mouse_pos) else 0.0
        self._hover_progress += (target - self._hover_progress) * 8.0 * dt
        self._hover_progress = max(0.0, min(1.0, self._hover_progress))

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def draw(self, surface, font):
        t = self._hover_progress

        def lerp(a, b, t):
            return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

        border_col = lerp((90, 70, 50),   (220, 180, 100), t)
        text_col   = lerp((160, 130, 90), (240, 210, 140), t)

        fill = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        r  = int(20  + 40  * t)
        g  = int(15  + 30  * t)
        b  = int(10  + 15  * t)
        a  = int(180 + 40  * t)
        fill.fill((r, g, b, a))
        surface.blit(fill, self.rect.topleft)

        pygame.draw.rect(surface, border_col, self.rect, 2)
        pygame.draw.rect(surface, lerp((30, 22, 14), (120, 90, 40), t),
                         self.rect.inflate(-6, -6), 1)

        cx, cy = self.rect.x, self.rect.y
        cw, ch = self.rect.width, self.rect.height
        s = 8
        for px, py, dx, dy in [(cx, cy, 1, 1), (cx+cw, cy, -1, 1),
                                (cx, cy+ch, 1, -1), (cx+cw, cy+ch, -1, -1)]:
            pygame.draw.line(surface, border_col, (px, py), (px + dx*s, py), 1)
            pygame.draw.line(surface, border_col, (px, py), (px, py + dy*s), 1)

        label = font.render(self.text, True, text_col)
        surface.blit(label, (self.rect.centerx - label.get_width() // 2,
                             self.rect.centery - label.get_height() // 2))


class MenuScene:
    def __init__(self, screen):
        self.screen = screen
        self.W, self.H = screen.get_size()
        self.clock = pygame.time.Clock()
        self.time  = 0.0

        self.font_title  = pygame.font.SysFont("courier new", 64, bold=True)
        self.font_sub    = pygame.font.SysFont("courier new", 18)
        self.font_button = pygame.font.SysFont("courier new", 22, bold=True)

        bw, bh = 260, 56
        cx = self.W // 2 - bw // 2
        self.btn_start = Button(cx, self.H // 2 + 20,  bw, bh, "[ START ]")
        self.btn_exit  = Button(cx, self.H // 2 + 100, bw, bh, "[ EXIT  ]")

        rng = random.Random(42)
        self.particles = [
            {
                "x":     rng.uniform(0, self.W),
                "y":     rng.uniform(0, self.H),
                "speed": rng.uniform(0.04, 0.18),
                "size":  rng.choice([1, 1, 1, 2]),
                "phase": rng.uniform(0, math.tau),
            }
            for _ in range(90)
        ]

    def _draw_background(self):
        self.screen.fill((8, 6, 4))

        dim = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for y in range(0, self.H, 3):
            pygame.draw.line(dim, (0, 0, 0, 18), (0, y), (self.W, y))
        self.screen.blit(dim, (0, 0))

        for p in self.particles:
            flicker = 0.5 + 0.5 * math.sin(self.time * p["speed"] * 6 + p["phase"])
            alpha = int(30 + 70 * flicker)
            col = (int(160 * flicker), int(120 * flicker), int(60 * flicker), alpha)
            s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, col, (p["size"], p["size"]), p["size"])
            self.screen.blit(s, (int(p["x"]), int(p["y"])))

        glow  = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pulse = 0.85 + 0.15 * math.sin(self.time * 0.7)
        for r, a in [(340, 40), (220, 55), (120, 35)]:
            pygame.draw.circle(glow, (80, 50, 20, int(a * pulse)),
                               (self.W // 2, self.H // 2 - 60), r)
        self.screen.blit(glow, (0, 0))

    def _draw_title(self):
        flicker = 0.92 + 0.08 * math.sin(self.time * 3.1 + 0.5)
        col = (int(220 * flicker), int(175 * flicker), int(90 * flicker))

        shadow = self.font_title.render("DUNGEON", True, (20, 14, 6))
        sx = self.W // 2 - shadow.get_width() // 2
        sy = self.H // 2 - 200
        self.screen.blit(shadow, (sx + 3, sy + 4))

        label = self.font_title.render("DUNGEON", True, col)
        self.screen.blit(label, (sx, sy))

        sub   = self.font_sub.render("a roguelike", True, (100, 80, 45))
        sub_x = self.W // 2 - sub.get_width() // 2
        sub_y = sy + label.get_height() + 4
        lc    = (70, 52, 28)
        mid_y = sub_y + sub.get_height() // 2
        pygame.draw.line(self.screen, lc, (sub_x - 84, mid_y), (sub_x - 24, mid_y), 1)
        pygame.draw.line(self.screen, lc, (sub_x + sub.get_width() + 24, mid_y),
                                          (sub_x + sub.get_width() + 84, mid_y), 1)
        self.screen.blit(sub, (sub_x, sub_y))

    def _draw_footer(self):
        hint = self.font_sub.render("use mouse to navigate", True, (55, 44, 28))
        self.screen.blit(hint, (self.W // 2 - hint.get_width() // 2, self.H - 36))

    def run(self):
        while True:
            dt        = self.clock.tick(60) / 1000.0
            self.time += dt
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if self.btn_start.is_clicked(event):
                    return "start"
                if self.btn_exit.is_clicked(event):
                    return "exit"

            self.btn_start.update(mouse_pos, dt)
            self.btn_exit.update(mouse_pos, dt)

            self._draw_background()
            self._draw_title()
            self.btn_start.draw(self.screen, self.font_button)
            self.btn_exit.draw(self.screen, self.font_button)
            self._draw_footer()

            pygame.display.flip()