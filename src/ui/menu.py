import pygame
import sys
import math


class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
        self._hover_progress = 0.0  # 0.0 = idle, 1.0 = fully hovered

    def update(self, mouse_pos, dt):
        self.hovered = self.rect.collidepoint(mouse_pos)
        target = 1.0 if self.hovered else 0.0
        speed = 8.0
        self._hover_progress += (target - self._hover_progress) * speed * dt
        self._hover_progress = max(0.0, min(1.0, self._hover_progress))

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def draw(self, surface, font):
        t = self._hover_progress

        # Colours
        border_idle   = (90,  70,  50)
        border_hover  = (220, 180, 100)
        fill_idle     = (20,  15,  10,  180)
        fill_hover    = (60,  45,  25,  220)
        text_idle     = (160, 130, 90)
        text_hover    = (240, 210, 140)

        def lerp_color(a, b, t):
            return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

        border_col = lerp_color(border_idle, border_hover, t)
        text_col   = lerp_color(text_idle,   text_hover,   t)

        # Fill (semi-transparent)
        fill_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        alpha = int(fill_idle[3] + (fill_hover[3] - fill_idle[3]) * t)
        r = int(fill_idle[0] + (fill_hover[0] - fill_idle[0]) * t)
        g = int(fill_idle[1] + (fill_hover[1] - fill_idle[1]) * t)
        b_ = int(fill_idle[2] + (fill_hover[2] - fill_idle[2]) * t)
        fill_surf.fill((r, g, b_, alpha))
        surface.blit(fill_surf, self.rect.topleft)

        # Border — two rectangles for a slightly inset look
        pygame.draw.rect(surface, border_col, self.rect, 2)
        inner = self.rect.inflate(-6, -6)
        dim_border = lerp_color((30, 22, 14), (120, 90, 40), t)
        pygame.draw.rect(surface, dim_border, inner, 1)

        # Corner accents
        c = border_col
        cx, cy, cw, ch = self.rect.x, self.rect.y, self.rect.width, self.rect.height
        size = 8
        for px, py, dx, dy in [
            (cx, cy, 1, 1), (cx + cw, cy, -1, 1),
            (cx, cy + ch, 1, -1), (cx + cw, cy + ch, -1, -1),
        ]:
            pygame.draw.line(surface, c, (px, py), (px + dx * size, py), 1)
            pygame.draw.line(surface, c, (px, py), (px, py + dy * size), 1)

        # Text
        label = font.render(self.text, True, text_col)
        lx = self.rect.centerx - label.get_width() // 2
        ly = self.rect.centery - label.get_height() // 2
        surface.blit(label, (lx, ly))


class MenuScene:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W, self.H = screen.get_size()
        self.clock = pygame.time.Clock()
        self.time = 0.0

        # Fonts — fallback to system monospace if custom not available
        try:
            self.font_title  = pygame.font.SysFont("courier new", 64, bold=True)
            self.font_sub    = pygame.font.SysFont("courier new", 18)
            self.font_button = pygame.font.SysFont("courier new", 22, bold=True)
        except Exception:
            self.font_title  = pygame.font.SysFont("monospace", 64, bold=True)
            self.font_sub    = pygame.font.SysFont("monospace", 18)
            self.font_button = pygame.font.SysFont("monospace", 22, bold=True)

        bw, bh = 260, 56
        cx = self.W // 2 - bw // 2
        self.btn_start = Button(cx, self.H // 2 + 20,  bw, bh, "[ START ]")
        self.btn_exit  = Button(cx, self.H // 2 + 100, bw, bh, "[ EXIT  ]")

        # Pre-build a starfield / dust layer
        import random
        rng = random.Random(42)
        self.particles = [
            {
                "x": rng.uniform(0, self.W),
                "y": rng.uniform(0, self.H),
                "speed": rng.uniform(0.04, 0.18),
                "size": rng.choice([1, 1, 1, 2]),
                "phase": rng.uniform(0, math.tau),
            }
            for _ in range(90)
        ]

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    def _draw_background(self):
        """Dark stone gradient + animated vignette."""
        self.screen.fill((8, 6, 4))

        # Subtle scanline texture (every other row dimmed)
        dim = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for y in range(0, self.H, 3):
            pygame.draw.line(dim, (0, 0, 0, 18), (0, y), (self.W, y))
        self.screen.blit(dim, (0, 0))

        # Floating dust motes
        for p in self.particles:
            flicker = 0.5 + 0.5 * math.sin(self.time * p["speed"] * 6 + p["phase"])
            alpha = int(30 + 70 * flicker)
            col = (int(160 * flicker), int(120 * flicker), int(60 * flicker), alpha)
            s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, col, (p["size"], p["size"]), p["size"])
            self.screen.blit(s, (int(p["x"]), int(p["y"])))

        # Central warm glow behind title
        glow = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pulse = 0.85 + 0.15 * math.sin(self.time * 0.7)
        for r, a in [(340, 40), (220, 55), (120, 35)]:
            alpha_val = int(a * pulse)
            pygame.draw.circle(glow, (80, 50, 20, alpha_val),
                               (self.W // 2, self.H // 2 - 60), r)
        self.screen.blit(glow, (0, 0))

    def _draw_title(self):
        title_text = "DUNGEON"
        sub_text   = "a roguelike"

        # Flicker effect on title
        flicker = 0.92 + 0.08 * math.sin(self.time * 3.1 + 0.5)
        base_r, base_g, base_b = 220, 175, 90
        col = (int(base_r * flicker), int(base_g * flicker), int(base_b * flicker))

        # Shadow
        shadow = self.font_title.render(title_text, True, (20, 14, 6))
        sx = self.W // 2 - shadow.get_width() // 2
        sy = self.H // 2 - 200
        self.screen.blit(shadow, (sx + 3, sy + 4))

        # Main title
        label = self.font_title.render(title_text, True, col)
        self.screen.blit(label, (sx, sy))

        # Decorative rule lines either side of subtitle
        sub   = self.font_sub.render(sub_text, True, (100, 80, 45))
        sub_x = self.W // 2 - sub.get_width() // 2
        sub_y = sy + label.get_height() + 4
        line_col = (70, 52, 28)
        margin = 24
        pygame.draw.line(self.screen, line_col,
                         (sub_x - margin - 60, sub_y + sub.get_height() // 2),
                         (sub_x - margin,      sub_y + sub.get_height() // 2), 1)
        pygame.draw.line(self.screen, line_col,
                         (sub_x + sub.get_width() + margin,      sub_y + sub.get_height() // 2),
                         (sub_x + sub.get_width() + margin + 60, sub_y + sub.get_height() // 2), 1)
        self.screen.blit(sub, (sub_x, sub_y))

    def _draw_footer(self):
        hint = self.font_sub.render("use mouse to navigate", True, (55, 44, 28))
        self.screen.blit(hint, (self.W // 2 - hint.get_width() // 2, self.H - 36))

    # ------------------------------------------------------------------ #
    #  Main loop
    # ------------------------------------------------------------------ #
    def run(self) -> str:
        """
        Runs the menu loop.
        Returns 'start' when the player clicks Start,
        or 'exit' when the player clicks Exit / closes the window.
        """
        while True:
            dt = self.clock.tick(60) / 1000.0
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


# ------------------------------------------------------------------ #
#  Standalone test — python src/ui/menu.py
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Dungeon")
    result = MenuScene(screen).run()
    if result == "exit":
        pygame.quit()
        sys.exit()