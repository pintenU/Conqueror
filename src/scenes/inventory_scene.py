import pygame
import math


class InventoryScene:
    def __init__(self, screen, inventory):
        self.screen    = screen
        self.W, self.H = screen.get_size()
        self.clock     = pygame.time.Clock()
        self.time      = 0.0
        self.inventory = inventory

        self.font_title  = pygame.font.SysFont("courier new", 30, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 18, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 15)
        self.font_desc   = pygame.font.SysFont("courier new", 14)

        self.panel_w = int(self.W * 0.52)
        self.panel_h = int(self.H * 0.70)
        self.panel_x = (self.W - self.panel_w) // 2
        self.panel_y = (self.H - self.panel_h) // 2

        self.selected   = 0
        self.row_h      = 52
        self.icon_size  = 36
        self.open_anim  = 0.0
        self.OPEN_DUR   = 0.35

        self.dim_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.dim_surf.fill((0, 0, 0, 185))

    # ------------------------------------------------------------------ #

    def _visible_rows(self):
        """How many item rows fit in the panel content area."""
        content_y = self.panel_y + 70
        content_h = self.panel_h - 70 - 60   # leave space for footer
        return content_h // self.row_h

    def _draw_panel(self, t):
        ease = 1 - (1-t)**3
        w = int(self.panel_w * ease)
        h = int(self.panel_h * ease)
        x = self.W//2 - w//2
        y = self.H//2 - h//2
        if w < 4 or h < 4:
            return

        sh = pygame.Surface((w+14,h+14), pygame.SRCALPHA)
        sh.fill((0,0,0,90))
        self.screen.blit(sh,(x-7,y-7))

        panel = pygame.Surface((w,h), pygame.SRCALPHA)
        panel.fill((12,9,6,250))
        self.screen.blit(panel,(x,y))

        pygame.draw.rect(self.screen,(105,82,50),(x,y,w,h),2)
        pygame.draw.rect(self.screen,(62,48,28),(x+5,y+5,w-10,h-10),1)

        c  = (145,112,64)
        sz = 14
        for px2,py2,dx,dy in [(x,y,1,1),(x+w,y,-1,1),(x,y+h,1,-1),(x+w,y+h,-1,-1)]:
            pygame.draw.line(self.screen,c,(px2,py2),(px2+dx*sz,py2),2)
            pygame.draw.line(self.screen,c,(px2,py2),(px2,py2+dy*sz),2)
            pygame.draw.circle(self.screen,c,(px2,py2),3)

        if t > 0.8:
            title = self.font_title.render("INVENTORY", True, (215,180,105))
            self.screen.blit(title,(self.W//2-title.get_width()//2, y+14))
            rule_y = y + 14 + title.get_height() + 4
            pygame.draw.line(self.screen,(80,62,36),
                             (x+20,rule_y),(x+w-20,rule_y),1)

    def _draw_items(self, t):
        if t < 0.85:
            return

        items      = self.inventory.items
        content_x  = self.panel_x + 24
        content_y  = self.panel_y + 72
        row_w      = self.panel_w - 48
        max_rows   = self._visible_rows()

        if not items:
            empty = self.font_small.render(
                "Your inventory is empty.", True, (80,64,40))
            self.screen.blit(empty,(self.W//2-empty.get_width()//2,
                                    content_y + 40))
            return

        # Clamp selection
        self.selected = max(0, min(self.selected, len(items)-1))

        for i, item in enumerate(items):
            if i >= max_rows:
                break

            row_y  = content_y + i * self.row_h
            is_sel = (i == self.selected)

            # Row background
            row_bg = pygame.Surface((row_w, self.row_h - 4), pygame.SRCALPHA)
            if is_sel:
                row_bg.fill((35,26,16,220))
            else:
                row_bg.fill((18,13,8,160))
            self.screen.blit(row_bg,(content_x, row_y))

            # Selected highlight border
            if is_sel:
                pygame.draw.rect(self.screen,(160,128,68),
                                 (content_x, row_y, row_w, self.row_h-4), 2)
                # Arrow indicator
                arr = self.font_medium.render("▶", True, (200,165,80))
                self.screen.blit(arr,(content_x+4,
                                      row_y + self.row_h//2 - arr.get_height()//2 - 2))
            else:
                pygame.draw.rect(self.screen,(55,42,26),
                                 (content_x, row_y, row_w, self.row_h-4), 1)

            # Icon
            icon_x = content_x + 30
            icon_y = row_y + self.row_h//2 - 4
            item.draw_icon(self.screen, icon_x, icon_y, self.icon_size)

            # Name
            name_col = (220,192,130) if is_sel else (170,145,95)
            name_s = self.font_medium.render(item.name, True, name_col)
            self.screen.blit(name_s,(content_x + 60,
                                     row_y + 8))

            # Description (only for selected)
            if is_sel:
                desc_s = self.font_desc.render(
                    item.description, True, (145,120,75))
                self.screen.blit(desc_s,(content_x + 60,
                                         row_y + 8 + name_s.get_height() + 3))

            # Item count if stackable (potions)
            from src.scenes.chest_scene import PotionItem
            if isinstance(item, PotionItem):
                count = self.inventory.count(PotionItem)
                # Only show count on first occurrence
                first_idx = next(
                    j for j,it in enumerate(items) if isinstance(it,PotionItem))
                if i == first_idx:
                    cnt_s = self.font_small.render(
                        f"x{count}", True, (120,180,210))
                    self.screen.blit(cnt_s,(content_x+row_w-cnt_s.get_width()-12,
                                            row_y+self.row_h//2-cnt_s.get_height()//2-2))

        # Footer hint
        footer_y = self.panel_y + self.panel_h - 40
        hints = self.font_desc.render(
            "↑ ↓  navigate    I / ESC  close", True, (70,56,34))
        self.screen.blit(hints,(self.W//2-hints.get_width()//2, footer_y))

        # Item count summary
        total_s = self.font_desc.render(
            f"{len(items)} item{'s' if len(items)!=1 else ''}", True, (80,64,38))
        self.screen.blit(total_s,(self.panel_x+self.panel_w-total_s.get_width()-20,
                                   self.panel_y+18))

    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while True:
            dt         = self.clock.tick(60)/1000.0
            self.time += dt
            self.open_anim += dt
            t          = min(1.0, self.open_anim/self.OPEN_DUR)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_i, pygame.K_ESCAPE):
                        return "game"
                    if event.key == pygame.K_UP:
                        self.selected = max(0, self.selected-1)
                    if event.key == pygame.K_DOWN:
                        self.selected = min(
                            len(self.inventory.items)-1, self.selected+1)

            # --- Draw ---
            self.screen.blit(self.dim_surf,(0,0))
            self._draw_panel(t)
            self._draw_items(t)

            pygame.display.flip()