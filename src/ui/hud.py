import pygame
import math


class HUD:
    """
    Bottom-of-screen HUD for the dungeon.
    Shows: level, HP bar, EXP bar, gold, location, enemy count.
    """

    HEIGHT = 52   # pixel height of the HUD strip

    def __init__(self, screen):
        self.screen = screen
        self.W, self.H = screen.get_size()

        self.font_medium = pygame.font.SysFont("courier new", 14, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 12)
        self.font_tiny   = pygame.font.SysFont("courier new", 11)

        # Animated bar targets (smooth fill)
        self._hp_fill  = 1.0
        self._exp_fill = 0.0

        # Pre-build the background strip once
        self._bg = self._build_bg()

    def _build_bg(self):
        surf = pygame.Surface((self.W, self.HEIGHT), pygame.SRCALPHA)
        # Dark gradient — more opaque at bottom
        for y in range(self.HEIGHT):
            t = y / self.HEIGHT
            a = int(180 + 60*t)
            pygame.draw.line(surf, (6, 4, 2, a), (0, y), (self.W, y))
        # Top border line
        pygame.draw.line(surf, (90, 68, 38), (0, 0), (self.W, 0), 1)
        pygame.draw.line(surf, (55, 40, 20), (0, 1), (self.W, 1), 1)
        return surf

    # ------------------------------------------------------------------ #

    def _draw_bar(self, x, y, w, h, fill, col_full, col_empty=(35,25,14),
                  border=(70,52,28), label=None, label_right=None):
        # Background
        pygame.draw.rect(self.screen, col_empty, (x, y, w, h))
        # Fill
        fw = max(0, int(w * fill))
        if fw > 0:
            pygame.draw.rect(self.screen, col_full, (x, y, fw, h))
        # Shine
        if fw > 4:
            shine = pygame.Surface((fw, h//2), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 18))
            self.screen.blit(shine, (x, y))
        # Border
        pygame.draw.rect(self.screen, border, (x, y, w, h), 1)
        # Labels
        if label:
            ls = self.font_tiny.render(label, True, (200, 170, 100))
            self.screen.blit(ls, (x + 3, y + h//2 - ls.get_height()//2))
        if label_right:
            rs = self.font_tiny.render(label_right, True, (180, 150, 85))
            self.screen.blit(rs, (x + w - rs.get_width() - 3,
                                   y + h//2 - rs.get_height()//2))

    def _draw_section_divider(self, x, y, h):
        pygame.draw.line(self.screen, (55, 40, 20), (x, y+4), (x, y+h-4), 1)

    def update(self, dt, player_stats, game_state):
        """Smooth bar animations."""
        target_hp  = (game_state.player_hp / player_stats.max_hp
                      if player_stats.max_hp > 0 else 1.0)
        target_exp = player_stats.exp_progress()

        self._hp_fill  += (target_hp  - self._hp_fill)  * 6 * dt
        self._exp_fill += (target_exp - self._exp_fill)  * 6 * dt

    def draw(self, player_stats, game_state, goblins_remaining,
             location_name="Dungeon", boss_alive=False):
        y0 = self.H - self.HEIGHT

        # Background strip
        self.screen.blit(self._bg, (0, y0))

        W  = self.W
        pad = 10
        cx  = y0 + self.HEIGHT//2   # vertical centre of HUD

        # ---- SECTION 1: Level badge (far left) ----
        lv_text = f"LV{player_stats.level}"
        lv_s    = self.font_medium.render(lv_text, True, (220, 185, 80))
        lv_x    = pad + 4
        lv_y    = y0 + self.HEIGHT//2 - lv_s.get_height()//2
        # Badge background
        badge_w = lv_s.get_width() + 14
        badge_h = lv_s.get_height() + 6
        badge_x = lv_x - 7
        badge_y = lv_y - 3
        pygame.draw.rect(self.screen, (35,26,12),
                         (badge_x, badge_y, badge_w, badge_h))
        pygame.draw.rect(self.screen, (120,90,38),
                         (badge_x, badge_y, badge_w, badge_h), 1)
        self.screen.blit(lv_s, (lv_x, lv_y))

        section_x = badge_x + badge_w + 10
        self._draw_section_divider(section_x, y0, self.HEIGHT)
        section_x += 8

        # ---- SECTION 2: HP bar ----
        hp_label_s = self.font_small.render("HP", True, (180, 60, 60))
        self.screen.blit(hp_label_s, (section_x, y0+6))

        hp_bar_x = section_x + hp_label_s.get_width() + 5
        hp_bar_w = 130
        hp_val   = game_state.player_hp
        hp_max   = player_stats.max_hp

        # Colour shifts red as HP drops
        t_hp = self._hp_fill
        if t_hp > 0.5:
            hp_col = (int(60+60*(1-t_hp)), int(160+40*t_hp), 60)
        elif t_hp > 0.25:
            hp_col = (200, int(160*t_hp*2), 40)
        else:
            hp_col = (210, 40, 40)
        # Clamp all colour channels to valid range
        hp_col = tuple(max(0, min(255, c)) for c in hp_col)

        self._draw_bar(hp_bar_x, y0+8, hp_bar_w, 14,
                       self._hp_fill, hp_col,
                       label_right=f"{hp_val}/{hp_max}")

        section_x = hp_bar_x + hp_bar_w + 10
        self._draw_section_divider(section_x, y0, self.HEIGHT)
        section_x += 8

        # ---- SECTION 3: EXP bar ----
        exp_label_s = self.font_small.render("EXP", True, (80, 180, 140))
        self.screen.blit(exp_label_s, (section_x, y0+6))

        exp_bar_x = section_x + exp_label_s.get_width() + 5
        exp_bar_w = 120
        exp_needed = player_stats.exp_needed()

        self._draw_bar(exp_bar_x, y0+8, exp_bar_w, 14,
                       self._exp_fill, (60, 185, 140),
                       border=(40,120,90),
                       label_right=f"{player_stats.exp}/{exp_needed}")

        section_x = exp_bar_x + exp_bar_w + 10
        self._draw_section_divider(section_x, y0, self.HEIGHT)
        section_x += 8

        # ---- SECTION 4: Gold ----
        from src.scenes.chest_scene import GoldItem
        gold_val = 0
        try:
            gold_item = next((it for it in game_state.inventory_items
                              if isinstance(it, GoldItem)), None)
        except Exception:
            gold_item = None
        # Simpler — read from game_state.gold_collected for display
        gold_val = game_state.gold_collected

        gold_icon = self.font_medium.render("◆", True, (220,185,50))
        self.screen.blit(gold_icon, (section_x, y0+self.HEIGHT//2
                                      -gold_icon.get_height()//2))
        gold_s = self.font_small.render(str(gold_val), True, (200,168,75))
        self.screen.blit(gold_s, (section_x+gold_icon.get_width()+3,
                                   y0+self.HEIGHT//2-gold_s.get_height()//2))

        section_x += gold_icon.get_width() + gold_s.get_width() + 16
        self._draw_section_divider(section_x, y0, self.HEIGHT)
        section_x += 8

        # ---- SECTION 5: Enemy count ----
        skull = self.font_medium.render("☠", True, (180,80,80))
        self.screen.blit(skull, (section_x,
                                  y0+self.HEIGHT//2-skull.get_height()//2))
        enemy_txt = f"{goblins_remaining} left"
        if boss_alive:
            enemy_txt += " + BOSS"
        en_s = self.font_small.render(enemy_txt, True,
                                       (180,80,80) if goblins_remaining > 0
                                       else (80,160,80))
        self.screen.blit(en_s, (section_x+skull.get_width()+3,
                                  y0+self.HEIGHT//2-en_s.get_height()//2))

        # ---- SECTION 6: Location (far right) ----
        loc_s = self.font_small.render(location_name, True, (130,105,55))
        lx = W - loc_s.get_width() - pad
        self.screen.blit(loc_s, (lx, y0+self.HEIGHT//2-loc_s.get_height()//2))
        # Small sword icon before it
        sw_s = self.font_tiny.render("⚔", True, (90,72,38))
        self.screen.blit(sw_s, (lx-sw_s.get_width()-4,
                                  y0+self.HEIGHT//2-sw_s.get_height()//2))

        # ---- BOTTOM ROW: second line of info ----
        # Stat summary tiny text
        stat_txt = (f"STR:{player_stats.strength}  "
                    f"DEX:{player_stats.dexterity}  "
                    f"MAG:{player_stats.magic_mastery}")
        if player_stats.stat_points > 0:
            stat_txt += f"   [{player_stats.stat_points} point{'s' if player_stats.stat_points!=1 else ''} unspent!]"
        st_s = self.font_tiny.render(stat_txt, True,
                                      (160,130,60) if player_stats.stat_points == 0
                                      else (220,185,60))
        self.screen.blit(st_s, (hp_bar_x, y0+self.HEIGHT-st_s.get_height()-3))