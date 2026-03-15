import pygame
import math
import random

from src.save_system import (load_slot, save_slot, delete_slot,
                              slot_exists, format_playtime, NUM_SLOTS)


# ---------------------------------------------------------------------------
# Mini scene illustrations
# ---------------------------------------------------------------------------

def _lerp(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))


def _draw_mini_town(surf, rx, ry, rw, rh, time):
    """Small illustrated town scene."""
    rng = random.Random(42)
    # Sky
    for y in range(rh*2//3):
        t = y/(rh*2//3)
        c = _lerp((95,135,185),(155,195,220),t)
        pygame.draw.line(surf,c,(rx,ry+y),(rx+rw,ry+y))
    # Ground
    for y in range(rh*2//3, rh):
        t = (y-rh*2//3)/(rh//3)
        c = _lerp((58,88,46),(40,62,32),t)
        pygame.draw.line(surf,c,(rx,ry+y),(rx+rw,ry+y))
    # Buildings
    ground = ry + rh*2//3
    for i,(bx,bw,bh,bc) in enumerate([
        (rx+rw*0.12, rw*0.14, rh*0.38, (140,108,72)),
        (rx+rw*0.30, rw*0.18, rh*0.50, (125,95,60)),
        (rx+rw*0.52, rw*0.22, rh*0.44, (110,85,55)),
        (rx+rw*0.78, rw*0.14, rh*0.36, (130,100,65)),
    ]):
        bx=int(bx); bw=int(bw); bh=int(bh)
        by = ground-bh
        v = rng.randint(-8,8)
        pygame.draw.rect(surf,(bc[0]+v,bc[1]+v,bc[2]+v),(bx,by,bw,bh))
        rh2 = bh//3
        pygame.draw.polygon(surf,(80+v,55+v,28+v),[
            (bx-2,by),(bx+bw//2,by-rh2),(bx+bw+2,by)])
        # Lit window
        pulse = 0.7+0.3*math.sin(time*1.5+i)
        wsurf = pygame.Surface((bw//3,bh//4),pygame.SRCALPHA)
        wsurf.fill((int(220*pulse),int(160*pulse),int(50*pulse),180))
        surf.blit(wsurf,(bx+bw//3,by+bh//4))
    # Road
    for y in range(ground, ry+rh):
        v = rng.randint(-4,4)
        pygame.draw.line(surf,(118+v,102+v,82+v),(rx,y),(rx+rw,y))


def _draw_mini_dungeon(surf, rx, ry, rw, rh, time):
    """Small illustrated dungeon scene."""
    # Dark background
    for y in range(rh):
        t = y/rh
        c = _lerp((20,14,8),(8,5,3),t)
        pygame.draw.line(surf,c,(rx,ry+y),(rx+rw,ry+y))
    # Stone floor
    ground = ry+rh*3//4
    for y in range(ground, ry+rh):
        v = random.Random(y).randint(-4,4)
        pygame.draw.line(surf,(55+v,44+v,30+v),(rx,y),(rx+rw,y))
    # Archway
    aw = rw//3; ax = rx+rw//2-aw//2; ay = ry+rh//8
    pygame.draw.rect(surf,(52,42,28),(ax-12,ay,12,rh//2+10))
    pygame.draw.rect(surf,(52,42,28),(ax+aw,ay,12,rh//2+10))
    pygame.draw.arc(surf,(52,42,28),(ax-12,ay-30,aw+24,60),0,math.pi,8)
    # Void inside
    vsurf = pygame.Surface((aw,rh//2),pygame.SRCALPHA)
    vsurf.fill((3,2,1,240))
    surf.blit(vsurf,(ax,ay))
    # Red glow
    pulse = 0.4+0.4*math.sin(time*2.2)
    gs = pygame.Surface((aw,30),pygame.SRCALPHA)
    r2 = max(0,min(255,int(150*pulse)))
    g2 = max(0,min(255,int(15*pulse)))
    gs.fill((0,0,0,0))
    pygame.draw.ellipse(gs,(r2,g2,0),(0,0,aw,30))
    gs.set_alpha(int(80*pulse))
    surf.blit(gs,(ax,ay+rh//2-20))
    # Torches
    for tx in [rx+rw//6, rx+rw*5//6]:
        pygame.draw.rect(surf,(80,62,35),(tx-3,ground-28,6,18))
        fp = 0.7+0.3*math.sin(time*3.5+tx)
        pygame.draw.polygon(surf,(int(220*fp),int(120*fp),20),[
            (tx-5,ground-28),(tx,ground-44),(tx+5,ground-28)])
        # Torch glow
        gr = pygame.Surface((40,40),pygame.SRCALPHA)
        gr.fill((0,0,0,0))
        pygame.draw.circle(gr,(int(180*fp),int(100*fp),20),(20,20),20)
        gr.set_alpha(int(40*fp))
        surf.blit(gr,(tx-20,ground-48))
    # Skull decoration
    skx,sky = rx+rw//2, ry+rh//16
    pygame.draw.circle(surf,(160,148,130),(skx,sky),10)
    pygame.draw.circle(surf,(25,18,10),(skx,sky),10,1)
    for ex in [skx-4,skx+4]:
        pygame.draw.circle(surf,(12,8,5),(ex,sky-1),3)


# ---------------------------------------------------------------------------
# SavesScene
# ---------------------------------------------------------------------------

class SavesScene:
    def __init__(self, screen, game_state=None, mode="load"):
        self.screen     = screen
        self.W, self.H  = screen.get_size()
        self.clock      = pygame.time.Clock()
        self.time       = 0.0
        self.game_state = game_state
        self.mode       = mode

        self.font_title  = pygame.font.SysFont("courier new", 32, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 16, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 13)
        self.font_tiny   = pygame.font.SysFont("courier new", 11)

        self.slots   = [load_slot(i) for i in range(NUM_SLOTS)]
        self.selected = 0
        self._hover   = [0.0]*NUM_SLOTS

        self._confirm_delete = None
        self._message        = ""
        self._message_timer  = 0.0

        self.open_anim = 0.0
        self.OPEN_DUR  = 0.4

        # Card layout — 3 side by side
        pad       = 40
        total_gap = pad * (NUM_SLOTS+1)
        self.CARD_W = (self.W - total_gap) // NUM_SLOTS
        self.CARD_H = int(self.H * 0.72)
        self.CARD_Y = (self.H - self.CARD_H) // 2 + 20
        self.MINI_H = int(self.CARD_H * 0.42)   # illustration height

        self._card_rects = []
        for i in range(NUM_SLOTS):
            x = pad + i*(self.CARD_W+pad)
            self._card_rects.append(pygame.Rect(x, self.CARD_Y,
                                                self.CARD_W, self.CARD_H))

        # Find most recent slot
        self._latest_slot = self._find_latest()

        # Pre-render mini scenes per slot (redrawn each frame for animation)
        self._mini_surfs = [
            pygame.Surface((self.CARD_W, self.MINI_H))
            for _ in range(NUM_SLOTS)
        ]

    def _find_latest(self):
        latest = None
        latest_slot = None
        for i, s in enumerate(self.slots):
            if s and (latest is None or s.save_time > latest):
                latest = s.save_time
                latest_slot = i
        return latest_slot

    # ------------------------------------------------------------------ #
    # Mini scene rendering
    # ------------------------------------------------------------------ #

    def _render_mini(self, slot_idx):
        surf = self._mini_surfs[slot_idx]
        data = self.slots[slot_idx]
        if data is None:
            surf.fill((12, 9, 6))
            # Empty pattern — subtle stone texture
            rng = random.Random(slot_idx*7)
            for _ in range(60):
                x = rng.randint(0, self.CARD_W-4)
                y = rng.randint(0, self.MINI_H-4)
                v = rng.randint(-6,6)
                pygame.draw.rect(surf,(22+v,16+v,10+v),(x,y,4,4))
            # "Empty" text
            f = pygame.font.SysFont("courier new",14)
            es = f.render("— Empty —",True,(55,42,25))
            surf.blit(es,(self.CARD_W//2-es.get_width()//2,
                          self.MINI_H//2-es.get_height()//2))
        elif data.current_location == "town":
            _draw_mini_town(surf,0,0,self.CARD_W,self.MINI_H,self.time)
        else:
            _draw_mini_dungeon(surf,0,0,self.CARD_W,self.MINI_H,self.time)

    # ------------------------------------------------------------------ #
    # Card drawing
    # ------------------------------------------------------------------ #

    def _draw_card(self, i, alpha):
        rect  = self._card_rects[i]
        data  = self.slots[i]
        t     = self._hover[i]
        is_sel = (i == self.selected)
        is_latest = (i == self._latest_slot and data is not None)

        def lc(a,b): return tuple(int(a[j]+(b[j]-a[j])*t) for j in range(3))

        # Shadow
        sh = pygame.Surface((rect.w+10,rect.h+10),pygame.SRCALPHA)
        sh.fill((0,0,0,int(80*alpha/255)))
        self.screen.blit(sh,(rect.x-5,rect.y+5))

        # Card background
        bg = pygame.Surface((rect.w,rect.h),pygame.SRCALPHA)
        bg.fill((int(20+18*t),int(14+12*t),int(8+8*t),int(235*alpha/255)))
        self.screen.blit(bg,rect.topleft)

        # Border — gold for selected, dimmer otherwise
        if is_sel:
            border = lc((120,92,45),(200,165,80))
        else:
            border = lc((55,42,24),(130,100,48))
        pygame.draw.rect(self.screen,border,rect,2)
        pygame.draw.rect(self.screen,
                         tuple(max(0,c-40) for c in border),
                         rect.inflate(-6,-6),1)

        # Corner accents
        sz = 12
        for bx,by,dx,dy in [(rect.x,rect.y,1,1),(rect.x+rect.w,rect.y,-1,1),
                             (rect.x,rect.y+rect.h,1,-1),(rect.x+rect.w,rect.y+rect.h,-1,-1)]:
            pygame.draw.line(self.screen,border,(bx,by),(bx+dx*sz,by),2)
            pygame.draw.line(self.screen,border,(bx,by),(bx,by+dy*sz),2)

        # Slot number badge
        badge_col = lc((80,60,28),(148,115,50))
        badge_rect = pygame.Rect(rect.x+10,rect.y+10,32,32)
        pygame.draw.rect(self.screen,badge_col,badge_rect)
        pygame.draw.rect(self.screen,lc((110,85,38),(180,145,65)),badge_rect,1)
        sn = self.font_medium.render(str(i+1),True,lc((180,145,70),(235,200,120)))
        self.screen.blit(sn,(badge_rect.centerx-sn.get_width()//2,
                              badge_rect.centery-sn.get_height()//2))

        # "Latest" badge
        if is_latest:
            lb = self.font_tiny.render("LATEST",True,(80,160,80))
            lbg = pygame.Surface((lb.get_width()+10,lb.get_height()+4),pygame.SRCALPHA)
            lbg.fill((20,50,20,180))
            lx = rect.right-lb.get_width()-16
            self.screen.blit(lbg,(lx-5,rect.y+14))
            pygame.draw.rect(self.screen,(50,120,50),(lx-5,rect.y+14,
                             lb.get_width()+10,lb.get_height()+4),1)
            self.screen.blit(lb,(lx,rect.y+16))

        # Mini illustration
        self._render_mini(i)
        mini_rect = pygame.Rect(rect.x, rect.y, rect.w, self.MINI_H)
        # Clip mini surf to card width
        clip = pygame.Rect(0,0,rect.w,self.MINI_H)
        self.screen.blit(self._mini_surfs[i],mini_rect.topleft,clip)
        # Bottom fade on illustration
        fade = pygame.Surface((rect.w,40),pygame.SRCALPHA)
        for fy in range(40):
            a2 = int(200*(fy/40)**1.5)
            pygame.draw.line(fade,(int(20+18*t),int(14+12*t),int(8+8*t),a2),
                             (0,fy),(rect.w,fy))
        self.screen.blit(fade,(rect.x,rect.y+self.MINI_H-40))
        # Illustration border
        pygame.draw.rect(self.screen,border,mini_rect,1)

        content_y = rect.y + self.MINI_H + 10

        if data is None:
            # Empty slot
            es = self.font_medium.render("Empty Slot",True,lc((55,42,22),(105,82,40)))
            self.screen.blit(es,(rect.centerx-es.get_width()//2, content_y+20))
            if self.mode in ("save","both") and self.game_state:
                hint = self.font_tiny.render("Click to save here",True,lc((55,42,22),(90,70,35)))
                self.screen.blit(hint,(rect.centerx-hint.get_width()//2,content_y+44))
        else:
            # Location — big
            loc = data.current_location.replace("_"," ").title()
            loc_col = lc((80,130,180),(120,180,230)) if "dungeon" in loc.lower() \
                      else lc((70,145,90),(110,195,130))
            loc_s = self.font_medium.render(loc.upper(),True,loc_col)
            self.screen.blit(loc_s,(rect.centerx-loc_s.get_width()//2, content_y+6))

            # Playtime — prominent
            pt = format_playtime(data.playtime_seconds)
            pt_s = self.font_medium.render(pt,True,lc((160,130,70),(215,180,100)))
            self.screen.blit(pt_s,(rect.centerx-pt_s.get_width()//2,
                                    content_y+6+loc_s.get_height()+4))

            # Divider
            dy = content_y+6+loc_s.get_height()+pt_s.get_height()+10
            pygame.draw.line(self.screen,lc((45,34,18),(90,70,34)),
                             (rect.x+16,dy),(rect.right-16,dy),1)

            # Stats grid
            stats = [
                ("Enemies",  str(data.enemies_defeated)),
                ("Quests",   str(data.quests_cleared)),
                ("Gold",     str(data.gold_collected)),
            ]
            sy = dy + 8
            col_w = rect.w // len(stats)
            for j,(label,val) in enumerate(stats):
                sx = rect.x + j*col_w + col_w//2
                val_s   = self.font_medium.render(val,True,lc((175,145,75),(225,192,110)))
                label_s = self.font_tiny.render(label,True,lc((85,65,30),(130,102,48)))
                self.screen.blit(val_s,(sx-val_s.get_width()//2,sy))
                self.screen.blit(label_s,(sx-label_s.get_width()//2,
                                           sy+val_s.get_height()+1))

            # Timestamp
            ts_s = self.font_tiny.render(data.save_time,True,lc((65,50,24),(100,78,38)))
            self.screen.blit(ts_s,(rect.centerx-ts_s.get_width()//2,
                                    rect.bottom-ts_s.get_height()-42))

            # Action buttons
            self._draw_card_buttons(i, rect, data, lc, alpha)

    def _draw_card_buttons(self, i, rect, data, lc, alpha):
        bh2 = 28; bw2 = (rect.w-30)//2; gap = 10
        by2 = rect.bottom - bh2 - 8
        bx_left  = rect.x + 10
        bx_right = rect.x + rect.w//2 + gap//2

        buttons = []
        if self.mode in ("save","both") and self.game_state:
            buttons.append(("SAVE",   bx_left,  (70,110,55),(120,185,80)))
        if self.mode in ("load","both") and data:
            bx = bx_left if not buttons else bx_right
            buttons.append(("LOAD",   bx,       (55,80,120),(80,130,200)))
        if data:
            bx = bx_right if len(buttons)==1 else bx_left + bw2 + gap
            buttons.append(("DELETE", bx_right, (110,45,35),(200,70,50)))

        # If only save+load, space them evenly
        if len(buttons) == 2:
            buttons[0] = (buttons[0][0], bx_left,  buttons[0][2], buttons[0][3])
            buttons[1] = (buttons[1][0], bx_right, buttons[1][2], buttons[1][3])

        mouse = pygame.mouse.get_pos()
        for label, bx, ci, ch in buttons:
            brect = pygame.Rect(bx, by2, bw2, bh2)
            hov   = 1.0 if brect.collidepoint(mouse) else 0.0
            def lc2(a,b): return tuple(int(a[j]+(b[j]-a[j])*hov) for j in range(3))
            fill  = pygame.Surface((bw2,bh2),pygame.SRCALPHA)
            fill.fill((int(12+18*hov),int(8+12*hov),int(5+8*hov),int(200*alpha/255)))
            self.screen.blit(fill,brect.topleft)
            pygame.draw.rect(self.screen,lc2(ci,ch),brect,2)
            ls = self.font_tiny.render(label,True,lc2(ci,ch))
            self.screen.blit(ls,(brect.centerx-ls.get_width()//2,
                                  brect.centery-ls.get_height()//2))

    # ------------------------------------------------------------------ #
    # Confirm delete overlay
    # ------------------------------------------------------------------ #

    def _draw_confirm_delete(self):
        i    = self._confirm_delete
        rect = self._card_rects[i]
        pw,ph = 340,120
        px = self.W//2-pw//2; py = self.H//2-ph//2

        overlay = pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        self.screen.blit(overlay,(0,0))

        bg = pygame.Surface((pw,ph),pygame.SRCALPHA)
        bg.fill((20,13,8,248))
        self.screen.blit(bg,(px,py))
        pygame.draw.rect(self.screen,(160,55,35),(px,py,pw,ph),2)

        t2 = self.font_medium.render(f"Delete slot {i+1}?",True,(220,90,65))
        self.screen.blit(t2,(self.W//2-t2.get_width()//2,py+14))
        sub = self.font_tiny.render("This cannot be undone.",True,(130,60,40))
        self.screen.blit(sub,(self.W//2-sub.get_width()//2,py+36))

        mouse = pygame.mouse.get_pos()
        for label,bx2,ci,ch in [
            ("YES, DELETE", px+pw//4-60,  (160,55,35),(220,85,60)),
            ("CANCEL",      px+pw*3//4-50,(55,90,50), (80,160,70)),
        ]:
            brect = pygame.Rect(bx2,py+ph-44,120,30)
            hov   = 1.0 if brect.collidepoint(mouse) else 0.0
            def lc2(a,b): return tuple(int(a[j]+(b[j]-a[j])*hov) for j in range(3))
            fill  = pygame.Surface((120,30),pygame.SRCALPHA)
            fill.fill((int(12+18*hov),int(8+12*hov),int(5+8*hov),200))
            self.screen.blit(fill,brect.topleft)
            pygame.draw.rect(self.screen,lc2(ci,ch),brect,2)
            ls = self.font_small.render(label,True,lc2(ci,ch))
            self.screen.blit(ls,(brect.centerx-ls.get_width()//2,
                                  brect.centery-ls.get_height()//2))

    def _draw_message(self):
        if not self._message or self._message_timer <= 0: return
        alpha = min(1.0,self._message_timer/0.5)
        ms  = self.font_small.render(self._message,True,(220,195,110))
        bg  = pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
        bg.fill((14,10,6,int(200*alpha)))
        bx  = self.W//2-bg.get_width()//2
        by  = self.CARD_Y-bg.get_height()-10
        self.screen.blit(bg,(bx,by))
        pygame.draw.rect(self.screen,(120,95,45),(bx,by,bg.get_width(),bg.get_height()),1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms,(bx+10,by+4))

    # ------------------------------------------------------------------ #
    # Hit testing
    # ------------------------------------------------------------------ #

    def _card_button_hit(self, pos, i):
        rect = self._card_rects[i]
        data = self.slots[i]
        bh2  = 28; bw2 = (rect.w-30)//2; gap = 10
        by2  = rect.bottom - bh2 - 8

        buttons = []
        if self.mode in ("save","both") and self.game_state:
            buttons.append(("SAVE",   rect.x+10))
        if self.mode in ("load","both") and data:
            bx = rect.x+10 if not buttons else rect.x+rect.w//2+gap//2
            buttons.append(("LOAD",   bx))
        if data:
            buttons.append(("DELETE", rect.x+rect.w//2+gap//2))

        if len(buttons)==2:
            buttons[0] = (buttons[0][0], rect.x+10)
            buttons[1] = (buttons[1][0], rect.x+rect.w//2+gap//2)

        for label,bx in buttons:
            if pygame.Rect(bx,by2,bw2,bh2).collidepoint(pos):
                return label
        return None

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _do_save(self, i):
        if self.game_state:
            save_slot(i, self.game_state)
            self.slots[i]      = load_slot(i)
            self._latest_slot  = self._find_latest()
            self._message       = f"Saved to slot {i+1}!"
            self._message_timer = 2.5

    def _do_delete(self, i):
        delete_slot(i)
        self.slots[i]      = None
        self._confirm_delete = None
        self._latest_slot  = self._find_latest()
        self._message       = f"Slot {i+1} deleted."
        self._message_timer = 2.0

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self):
        while True:
            dt          = self.clock.tick(60)/1000.0
            self.time  += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            t           = min(1.0,self.open_anim/self.OPEN_DUR)
            ease        = 1-(1-t)**3
            alpha       = int(255*ease)
            self._message_timer = max(0.0,self._message_timer-dt)
            mouse       = pygame.mouse.get_pos()

            # Hover
            for i,rect in enumerate(self._card_rects):
                tgt = 1.0 if rect.collidepoint(mouse) else 0.0
                self._hover[i] += (tgt-self._hover[i])*8*dt
                self._hover[i]  = max(0.0,min(1.0,self._hover[i]))

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
                        if event.key == pygame.K_LEFT:
                            self.selected = max(0,self.selected-1)
                        if event.key == pygame.K_RIGHT:
                            self.selected = min(NUM_SLOTS-1,self.selected+1)
                        if event.key in (pygame.K_RETURN,pygame.K_SPACE):
                            i = self.selected
                            data = self.slots[i]
                            if self.mode in ("save","both") and self.game_state:
                                self._do_save(i)
                            elif data and self.mode in ("load","both"):
                                return ("loaded", data)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                    if self._confirm_delete is not None:
                        pw,ph = 340,120
                        px = self.W//2-pw//2; py = self.H//2-ph//2
                        yes = pygame.Rect(px+pw//4-60,  py+ph-44,120,30)
                        no  = pygame.Rect(px+pw*3//4-50,py+ph-44,120,30)
                        if yes.collidepoint(mouse):
                            self._do_delete(self._confirm_delete)
                        elif no.collidepoint(mouse):
                            self._confirm_delete = None
                        continue

                    for i,rect in enumerate(self._card_rects):
                        if not rect.collidepoint(mouse): continue
                        self.selected = i
                        action = self._card_button_hit(mouse,i)
                        if action == "SAVE":
                            self._do_save(i)
                        elif action == "LOAD":
                            data = self.slots[i]
                            if data: return ("loaded",data)
                        elif action == "DELETE":
                            self._confirm_delete = i
                        elif self.slots[i] is None:
                            # Click on empty card — save here if in save mode
                            if self.mode in ("save","both") and self.game_state:
                                self._do_save(i)

            # Draw
            self.screen.fill((8,6,4))

            # Background vignette
            vx,vy = self.W//2,self.H//2
            mr = int(math.hypot(vx,vy))
            for step in range(0,mr,6):
                r2 = max(0,min(255,int(40*(step/mr)**1.5)))
                pygame.draw.circle(self.screen,(r2,r2,r2),(vx,vy),mr-step)

            # Title
            title = self.font_title.render("— SAVES —",True,
                                            (int(210*ease),int(178*ease),int(100*ease)))
            self.screen.blit(title,(self.W//2-title.get_width()//2,
                                     self.CARD_Y-title.get_height()-18))

            # Cards
            for i in range(NUM_SLOTS):
                self._draw_card(i, alpha)

            # Hint
            mode_hint = "ENTER  save    ←→  select    ESC  back" if self.mode in ("save","both") \
                        else "ENTER  load    ←→  select    ESC  back"
            hs = self.font_tiny.render(mode_hint,True,
                                        (int(70*ease),int(54*ease),int(28*ease)))
            self.screen.blit(hs,(self.W//2-hs.get_width()//2,
                                  self.CARD_Y+self.CARD_H+12))

            self._draw_message()
            if self._confirm_delete is not None:
                self._draw_confirm_delete()

            pygame.display.flip()