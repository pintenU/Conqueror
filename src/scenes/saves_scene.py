import pygame
import math
import random

from src.save_system import (load_slot, save_slot, delete_slot,
                              slot_exists, format_playtime, NUM_SLOTS)


class SavesScene:
    """
    Shown from both main menu and pause menu.
    mode="save"  — can save to a slot
    mode="load"  — can load from a slot (main menu)
    mode="both"  — save and load (pause menu)
    """

    def __init__(self, screen, game_state=None, mode="load"):
        self.screen     = screen
        self.W, self.H  = screen.get_size()
        self.clock      = pygame.time.Clock()
        self.time       = 0.0
        self.game_state = game_state   # current GameState to save
        self.mode       = mode

        self.font_title  = pygame.font.SysFont("courier new", 30, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 18, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 14)
        self.font_tiny   = pygame.font.SysFont("courier new", 12)

        self.selected    = 0
        self.slots       = [load_slot(i) for i in range(NUM_SLOTS)]

        # Confirm delete state
        self._confirm_delete = None   # slot index or None
        self._message        = ""
        self._message_timer  = 0.0

        self.open_anim = 0.0
        self.OPEN_DUR  = 0.35

        self.dim_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.dim_surf.fill((0, 0, 0, 180))

        # Layout
        self.SLOT_H  = int(self.H * 0.17)
        self.SLOT_W  = int(self.W * 0.62)
        self.SLOT_X  = (self.W - self.SLOT_W) // 2
        self.SLOT_Y0 = int(self.H * 0.18)
        self.SLOT_GAP = int(self.H * 0.03)

    # ------------------------------------------------------------------ #
    # Slot rect
    # ------------------------------------------------------------------ #

    def _slot_rect(self, i):
        y = self.SLOT_Y0 + i * (self.SLOT_H + self.SLOT_GAP)
        return pygame.Rect(self.SLOT_X, y, self.SLOT_W, self.SLOT_H)

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #

    def _draw_background(self):
        self.screen.fill((8, 6, 4))
        # Subtle scanlines
        dim = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for y in range(0, self.H, 3):
            pygame.draw.line(dim, (0,0,0,14), (0,y), (self.W,y))
        self.screen.blit(dim, (0,0))

    def _draw_slot(self, i, t, alpha):
        rect  = self._slot_rect(i)
        data  = self.slots[i]
        is_sel = (i == self.selected)
        hover  = 1.0 if is_sel else 0.0

        def lc(a,b,tv=None):
            tv = tv if tv is not None else hover
            return tuple(int(a[j]+(b[j]-a[j])*tv) for j in range(3))

        # Background
        bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        if is_sel:
            bg.fill((32,24,14,230))
        else:
            bg.fill((16,12,7,180))
        bs = pygame.Surface((rect.w,rect.h),pygame.SRCALPHA)
        bs.blit(bg,(0,0)); bs.set_alpha(alpha)
        self.screen.blit(bs, rect.topleft)

        # Border
        border = lc((55,42,26),(180,145,70))
        pygame.draw.rect(self.screen, border, rect, 2)
        if is_sel:
            pygame.draw.rect(self.screen,
                             lc((30,22,12),(100,78,38)),
                             rect.inflate(-6,-6), 1)

        # Corner accents
        sz = 10
        c2 = lc((80,62,32),(200,165,80))
        for bx,by,dx,dy in [(rect.x,rect.y,1,1),(rect.x+rect.w,rect.y,-1,1),
                             (rect.x,rect.y+rect.h,1,-1),(rect.x+rect.w,rect.y+rect.h,-1,-1)]:
            pygame.draw.line(self.screen,c2,(bx,by),(bx+dx*sz,by),2)
            pygame.draw.line(self.screen,c2,(bx,by),(bx,by+dy*sz),2)

        # Slot number badge
        badge_col = lc((70,52,28),(140,105,45))
        pygame.draw.rect(self.screen, badge_col,
                         (rect.x+8, rect.y+8, 36, 36))
        pygame.draw.rect(self.screen, lc((100,75,35),(180,140,60)),
                         (rect.x+8, rect.y+8, 36, 36), 1)
        sn = self.font_medium.render(str(i+1), True,
                                      lc((180,150,80),(240,210,120)))
        self.screen.blit(sn, (rect.x+8+18-sn.get_width()//2,
                               rect.y+8+18-sn.get_height()//2))

        if data is None:
            # Empty slot
            es = self.font_medium.render("— Empty Slot —", True,
                                          lc((60,46,26),(110,85,42)))
            self.screen.blit(es, (rect.x+56,
                                   rect.centery-es.get_height()//2))
        else:
            # Location tag
            loc = data.current_location.replace("_"," ").title()
            loc_col = (80,130,180) if "dungeon" in loc.lower() else (80,160,100)
            loc_s = self.font_tiny.render(loc, True, loc_col)
            self.screen.blit(loc_s, (rect.x+56, rect.y+10))

            # Save time
            ts2 = self.font_tiny.render(data.save_time, True, (80,62,32))
            self.screen.blit(ts2, (rect.right-ts2.get_width()-10, rect.y+10))

            # Stats row
            stats = [
                ("⏱", format_playtime(data.playtime_seconds)),
                ("☠", f"{data.enemies_defeated} defeated"),
                ("✓", f"{data.quests_cleared} quests"),
                ("◆", f"{data.gold_collected} gold"),
            ]
            sx = rect.x + 56
            sy = rect.y + 10 + loc_s.get_height() + 6
            for icon, val in stats:
                ic = self.font_small.render(icon, True, (140,110,55))
                vs = self.font_small.render(val,  True, lc((120,95,48),(190,158,85)))
                self.screen.blit(ic, (sx, sy))
                self.screen.blit(vs, (sx+20, sy))
                sx += vs.get_width() + 36
                if sx > rect.right - 80:
                    sx  = rect.x + 56
                    sy += vs.get_height() + 2

        # Action buttons on selected slot
        if is_sel and t > 0.85:
            self._draw_slot_buttons(rect, data)

    def _draw_slot_buttons(self, rect, data):
        bw, bh = 100, 28
        btn_y  = rect.bottom - bh - 8
        buttons = []

        if self.mode in ("save","both") and self.game_state:
            buttons.append(("SAVE", (70,110,55), (120,185,80)))
        if data is not None and self.mode in ("load","both"):
            buttons.append(("LOAD", (55,80,120), (80,130,200)))
        if data is not None:
            buttons.append(("DELETE", (110,45,35), (200,70,50)))

        total_w = len(buttons)*(bw+8)
        bx = rect.x + rect.w//2 - total_w//2

        mouse = pygame.mouse.get_pos()
        for label, col_idle, col_hover in buttons:
            brect = pygame.Rect(bx, btn_y, bw, bh)
            hov   = 1.0 if brect.collidepoint(mouse) else 0.0
            def lc2(a,b): return tuple(int(a[j]+(b[j]-a[j])*hov) for j in range(3))
            fill = pygame.Surface((bw,bh),pygame.SRCALPHA)
            fill.fill((int(16+24*hov),int(12+18*hov),int(8+12*hov),210))
            self.screen.blit(fill,(bx,btn_y))
            pygame.draw.rect(self.screen,lc2(col_idle,col_hover),brect,2)
            ls = self.font_tiny.render(label,True,lc2(col_idle,col_hover))
            self.screen.blit(ls,(bx+bw//2-ls.get_width()//2,
                                  btn_y+bh//2-ls.get_height()//2))
            bx += bw+8

    def _draw_confirm_delete(self):
        i = self._confirm_delete
        rect = self._slot_rect(i)
        pw, ph = 360, 130
        px = self.W//2 - pw//2
        py = rect.centery - ph//2

        bg = pygame.Surface((pw,ph),pygame.SRCALPHA)
        bg.fill((20,12,8,245))
        self.screen.blit(bg,(px,py))
        pygame.draw.rect(self.screen,(160,60,40),(px,py,pw,ph),2)

        t2 = self.font_medium.render(f"Delete slot {i+1}?",True,(220,100,70))
        self.screen.blit(t2,(self.W//2-t2.get_width()//2, py+14))

        mouse = pygame.mouse.get_pos()
        for label,cx2,col in [("YES, DELETE",pw//4,(160,60,40)),
                               ("CANCEL",    pw*3//4,(60,90,55))]:
            brect = pygame.Rect(px+cx2-70, py+ph-44, 140, 30)
            hov   = 1.0 if brect.collidepoint(mouse) else 0.0
            fill  = pygame.Surface((140,30),pygame.SRCALPHA)
            fill.fill((int(20+20*hov),int(14+14*hov),int(8+8*hov),210))
            self.screen.blit(fill,brect.topleft)
            pygame.draw.rect(self.screen,col,brect,2)
            ls = self.font_small.render(label,True,col)
            self.screen.blit(ls,(brect.centerx-ls.get_width()//2,
                                  brect.centery-ls.get_height()//2))

    def _draw_message(self):
        if not self._message or self._message_timer <= 0:
            return
        alpha = min(1.0, self._message_timer/0.5)
        ms  = self.font_small.render(self._message,True,(220,195,110))
        bg  = pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
        bg.fill((14,10,6,int(220*alpha)))
        bx2 = self.W//2-bg.get_width()//2
        by2 = self.SLOT_Y0-bg.get_height()-12
        self.screen.blit(bg,(bx2,by2))
        pygame.draw.rect(self.screen,(120,95,48),(bx2,by2,bg.get_width(),bg.get_height()),1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms,(bx2+10,by2+4))

    def _draw_hints(self, alpha):
        hints = "↑ ↓  select    ENTER  action    ESC  back"
        hs = self.font_tiny.render(hints,True,(70,54,28))
        s2 = pygame.Surface(hs.get_size(),pygame.SRCALPHA)
        s2.blit(hs,(0,0)); s2.set_alpha(alpha)
        self.screen.blit(s2,(self.W//2-hs.get_width()//2, self.H-hs.get_height()-10))

    # ------------------------------------------------------------------ #
    # Action helpers
    # ------------------------------------------------------------------ #

    def _do_save(self, slot):
        if self.game_state:
            save_slot(slot, self.game_state)
            self.slots[slot]  = load_slot(slot)
            self._message     = f"Game saved to slot {slot+1}!"
            self._message_timer = 2.5

    def _do_load(self, slot):
        data = self.slots[slot]
        if data:
            return data
        return None

    def _do_delete(self, slot):
        delete_slot(slot)
        self.slots[slot]     = None
        self._confirm_delete = None
        self._message        = f"Slot {slot+1} deleted."
        self._message_timer  = 2.0

    def _get_slot_button_hit(self, pos, slot):
        rect = self._slot_rect(slot)
        data = self.slots[slot]
        bw, bh = 100, 28
        btn_y  = rect.bottom - bh - 8
        buttons = []
        if self.mode in ("save","both") and self.game_state:
            buttons.append("SAVE")
        if data is not None and self.mode in ("load","both"):
            buttons.append("LOAD")
        if data is not None:
            buttons.append("DELETE")
        total_w = len(buttons)*(bw+8)
        bx = rect.x + rect.w//2 - total_w//2
        for label in buttons:
            brect = pygame.Rect(bx, btn_y, bw, bh)
            if brect.collidepoint(pos):
                return label
            bx += bw+8
        return None

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self):
        """
        Returns:
          ("loaded", GameState) — player chose to load a slot
          "back"                — player pressed back/ESC
          "exit"                — quit
        """
        while True:
            dt         = self.clock.tick(60)/1000.0
            self.time += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            t          = min(1.0, self.open_anim/self.OPEN_DUR)
            self._message_timer = max(0.0, self._message_timer-dt)
            alpha      = int(255*(1-(1-t)**3))
            mouse      = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self._confirm_delete is not None:
                            self._confirm_delete = None
                        else:
                            return "back"
                    if self._confirm_delete is None:
                        if event.key == pygame.K_UP:
                            self.selected = max(0, self.selected-1)
                        if event.key == pygame.K_DOWN:
                            self.selected = min(NUM_SLOTS-1, self.selected+1)
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            # Default action: save if in save mode, load otherwise
                            if self.mode in ("save","both") and self.game_state:
                                self._do_save(self.selected)
                            elif self.slots[self.selected] and self.mode in ("load","both"):
                                data = self._do_load(self.selected)
                                if data: return ("loaded", data)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Click on confirm delete dialog
                    if self._confirm_delete is not None:
                        i    = self._confirm_delete
                        rect = self._slot_rect(i)
                        pw,ph = 360,130
                        px2 = self.W//2-pw//2
                        py2 = rect.centery-ph//2
                        yes = pygame.Rect(px2+pw//4-70, py2+ph-44,140,30)
                        no  = pygame.Rect(px2+pw*3//4-70, py2+ph-44,140,30)
                        if yes.collidepoint(mouse):
                            self._do_delete(self._confirm_delete)
                        elif no.collidepoint(mouse):
                            self._confirm_delete = None
                        continue

                    # Click on slot
                    for i in range(NUM_SLOTS):
                        if self._slot_rect(i).collidepoint(mouse):
                            self.selected = i
                            action = self._get_slot_button_hit(mouse, i)
                            if action == "SAVE":
                                self._do_save(i)
                            elif action == "LOAD":
                                data = self._do_load(i)
                                if data: return ("loaded", data)
                            elif action == "DELETE":
                                self._confirm_delete = i

            # Draw
            self._draw_background()
            self.screen.blit(self.dim_surf,(0,0))

            # Title
            title = self.font_title.render("— SAVES —",True,(210,178,100))
            ts2   = pygame.Surface(title.get_size(),pygame.SRCALPHA)
            ts2.blit(title,(0,0)); ts2.set_alpha(alpha)
            self.screen.blit(ts2,(self.W//2-title.get_width()//2, int(self.H*0.06)))

            for i in range(NUM_SLOTS):
                self._draw_slot(i, t, alpha)

            self._draw_message()
            self._draw_hints(alpha)

            if self._confirm_delete is not None:
                self._draw_confirm_delete()

            pygame.display.flip()