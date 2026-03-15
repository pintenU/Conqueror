import pygame
import math


class LootScene:
    """Small popup shown after killing a goblin."""

    def __init__(self, screen, items: list, inventory):
        self.screen    = screen
        self.W, self.H = screen.get_size()
        self.clock     = pygame.time.Clock()
        self.time      = 0.0
        self.items     = items
        self.inventory = inventory

        self.font_title  = pygame.font.SysFont("courier new", 24, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 17, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 14)

        # Panel dimensions — must be set BEFORE _build_slots
        self.panel_w = int(self.W * 0.38)
        self.panel_h = int(self.H * 0.42)
        self.panel_x = (self.W - self.panel_w) // 2
        self.panel_y = (self.H - self.panel_h) // 2
        self.slot_size = int(self.panel_w * 0.20)

        # Now safe to build slots
        self.slots = self._build_slots()
        for i, item in enumerate(items[:len(self.slots)]):
            self.slots[i].item = item
        self.taken = [False] * len(self.slots)

        # Buttons
        bw, bh = 150, 38
        cx = self.panel_x + self.panel_w // 2
        self.take_all_rect = pygame.Rect(cx - bw - 8,
                                         self.panel_y + self.panel_h - bh - 12,
                                         bw, bh)
        self.close_rect    = pygame.Rect(cx + 8,
                                         self.panel_y + self.panel_h - bh - 12,
                                         bw, bh)
        self._ta_hover = 0.0
        self._cl_hover = 0.0

        self.open_anim = 0.0
        self.OPEN_DUR  = 0.3

        self.dim_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.dim_surf.fill((0, 0, 0, 160))

    def _build_slots(self):
        from src.scenes.chest_scene import ItemSlot
        slots   = []
        n       = max(len(self.items), 1)
        pad     = 12
        total_w = n * self.slot_size + (n - 1) * pad
        sx      = self.panel_x + (self.panel_w - total_w) // 2
        sy      = self.panel_y + 70
        for i in range(n):
            slots.append(ItemSlot(sx + i * (self.slot_size + pad), sy, self.slot_size))
        return slots

    def _draw_panel(self, t):
        ease = 1 - (1 - t) ** 3
        w = int(self.panel_w * ease)
        h = int(self.panel_h * ease)
        x = self.W // 2 - w // 2
        y = self.H // 2 - h // 2
        if w < 4 or h < 4:
            return

        sh = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 90))
        self.screen.blit(sh, (x - 6, y - 6))

        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((14, 10, 7, 248))
        self.screen.blit(panel, (x, y))

        pygame.draw.rect(self.screen, (105, 82, 50), (x, y, w, h), 2)
        pygame.draw.rect(self.screen, (62, 48, 28), (x + 5, y + 5, w - 10, h - 10), 1)

        c  = (145, 112, 64)
        sz = 12
        for px2, py2, dx, dy in [(x, y, 1, 1), (x+w, y, -1, 1),
                                   (x, y+h, 1, -1), (x+w, y+h, -1, -1)]:
            pygame.draw.line(self.screen, c, (px2, py2), (px2 + dx*sz, py2), 2)
            pygame.draw.line(self.screen, c, (px2, py2), (px2, py2 + dy*sz), 2)

        if t > 0.8:
            title = self.font_title.render("GOBLIN DEFEATED!", True, (215, 175, 90))
            self.screen.blit(title, (self.W//2 - title.get_width()//2, y + 12))
            sub = self.font_small.render("dropped:", True, (130, 105, 60))
            self.screen.blit(sub, (self.W//2 - sub.get_width()//2,
                                   y + 12 + title.get_height() + 2))
            pygame.draw.line(self.screen, (80, 62, 36),
                             (x + 16, y + 12 + title.get_height() + sub.get_height() + 8),
                             (x + w - 16, y + 12 + title.get_height() + sub.get_height() + 8), 1)

    def _btn(self, surface, rect, label, hover, col_idle, col_hover):
        t    = hover
        fill = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        fill.fill((int(18+35*t), int(14+28*t), int(10+18*t), 215))
        surface.blit(fill, rect.topleft)
        def lc(a, b): return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))
        pygame.draw.rect(surface, lc(col_idle, col_hover), rect, 2)
        lbl = self.font_medium.render(label, True, lc((140, 112, 65), (225, 195, 120)))
        surface.blit(lbl, (rect.centerx - lbl.get_width()//2,
                           rect.centery - lbl.get_height()//2))

    def run(self) -> str:
        while True:
            dt         = self.clock.tick(60) / 1000.0
            self.time += dt
            self.open_anim = min(self.open_anim + dt, self.OPEN_DUR)
            t          = min(1.0, self.open_anim / self.OPEN_DUR)
            mouse      = pygame.mouse.get_pos()

            def upd(h, rect):
                tgt = 1.0 if rect.collidepoint(mouse) else 0.0
                return h + (tgt - h) * 10 * dt
            self._ta_hover = max(0.0, min(1.0, upd(self._ta_hover, self.take_all_rect)))
            self._cl_hover = max(0.0, min(1.0, upd(self._cl_hover, self.close_rect)))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "game"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.take_all_rect.collidepoint(event.pos):
                        for i, slot in enumerate(self.slots):
                            if slot.item and not self.taken[i]:
                                self.inventory.add(slot.item)
                                self.taken[i] = True
                        return "game"
                    if self.close_rect.collidepoint(event.pos):
                        return "game"
                    for i, slot in enumerate(self.slots):
                        if (slot.item and not self.taken[i]
                                and slot.rect.collidepoint(event.pos)):
                            self.inventory.add(slot.item)
                            self.taken[i] = True

            self.screen.blit(self.dim_surf, (0, 0))
            self._draw_panel(t)

            if t > 0.8:
                for i, slot in enumerate(self.slots):
                    if t > 0.9:
                        slot.update(mouse, dt)
                    slot.draw(self.screen, self.font_small, self.taken[i])

                self._btn(self.screen, self.take_all_rect,
                          "TAKE ALL", self._ta_hover,
                          (70, 100, 55), (120, 170, 80))
                self._btn(self.screen, self.close_rect,
                          "LEAVE", self._cl_hover,
                          (70, 54, 34), (180, 148, 70))

            pygame.display.flip()