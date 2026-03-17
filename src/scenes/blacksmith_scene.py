import pygame
import math
import random


def _lerp_col(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))


# ---------------------------------------------------------------------------
# Upgrade definitions
# ---------------------------------------------------------------------------

WEAPON_UPGRADE_COSTS = [10, 15, 20, 25, 30]
ARMOUR_UPGRADE_COSTS = [10, 15, 20, 25, 30]

GORIN_DIALOGUES = [
    "Hmph. What d'ye want.",
    "I don't talk. I forge.",
    "That weapon needs work.\nBring me ingots.",
    "Iron ingots. Dungeon's\nfull of 'em.",
    "Finest work in Ashenvale.\nDon't argue.",
    "Get out of m'light.",
    "Upgraded it m'self.\nYou're welcome.",
    "A stick? Really?\nLet me fix that.",
]

RUMOURS = [
    "They say the dungeon goes deeper than any map shows.",
    "Old Berin lost three good swords down there. Never came back for 'em.",
    "Iron ingots fetch a fine price if you know where to look.",
    "The goblins have been restless. Something's stirring them up.",
    "A traveller passed through last week. Wouldn't say where he'd been.",
    "Heard a knight went in with full plate. Found the armour. Not the knight.",
    "The iron veins in that dungeon are ancient. Pre-kingdom old.",
    "There's a locked door deep in the dungeon. Nobody knows what's behind it.",
]

ARMOUR_SLOTS = ["helmet","chestplate","leggings","boots"]
ARMOUR_NAMES = {
    "helmet":     "Iron Helmet",
    "chestplate": "Iron Chestplate",
    "leggings":   "Iron Leggings",
    "boots":      "Iron Boots",
}


class BlacksmithScene:
    def __init__(self, screen, inventory, armour=None):
        self.screen    = screen
        self.W, self.H = screen.get_size()
        self.clock     = pygame.time.Clock()
        self.time      = 0.0
        self.inventory = inventory
        self.armour    = armour

        self.font_title  = pygame.font.SysFont("courier new", 24, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 16, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 13)
        self.font_tiny   = pygame.font.SysFont("courier new", 11)

        self.tab      = 0
        self.selected = 0
        self.open_anim = 0.0
        self._msg      = ""
        self._msg_t    = 0.0
        self._msg_good = True
        self._sparks   = []
        self._hammer_t = 0.0
        self._hammering = False

        # Cached panel coords for mouse hit-testing
        self._px = self._py = self._pw = self._ph = 0

        self.shop_color   = (180, 100, 30)
        self.keeper_color = (165, 120, 80)

        # Extra rumours added dynamically (e.g. from quests)
        self._extra_rumours: list[str] = []

        import random as _r
        self._dialogue = _r.choice(GORIN_DIALOGUES)

        for _ in range(20):
            self._sparks.append(self._new_spark())

    def _new_spark(self):
        import random as _r
        return {
            "x": self.W*3//4 + _r.randint(-30,30),
            "y": self.H//2 + _r.randint(-20,20),
            "vx": _r.uniform(-80,80),
            "vy": _r.uniform(-120,-40),
            "life": _r.uniform(0.2,0.8),
            "max_life": 0.8,
            "size": _r.choice([2,2,3]),
            "col": _r.choice([(255,200,50),(255,150,30),(255,240,100)]),
        }

    def _update_sparks(self, dt):
        import random as _r
        for sp in self._sparks:
            sp["x"] += sp["vx"]*dt
            sp["y"] += sp["vy"]*dt
            sp["vy"] += 200*dt
            sp["life"] -= dt
            if sp["life"] <= 0:
                sp.update(self._new_spark())

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _gold(self):
        from src.scenes.chest_scene import GoldItem
        return sum(self.inventory.stack_count(it)
                   for it in self.inventory.items
                   if isinstance(it, GoldItem))

    def _ingots(self):
        from src.scenes.chest_scene import IronIngotItem
        total = 0
        for it in self.inventory.items:
            if isinstance(it, IronIngotItem):
                total += self.inventory.stack_count(it)
        return total

    def _spend_gold(self, amount):
        from src.scenes.chest_scene import GoldItem
        gi = next((it for it in self.inventory.items if isinstance(it,GoldItem)),None)
        if not gi: return False
        total = self.inventory.stack_count(gi)
        if total < amount: return False
        self.inventory.remove(gi)
        if total-amount > 0:
            self.inventory.add(GoldItem(total-amount))
        return True

    def _spend_ingot(self):
        from src.scenes.chest_scene import IronIngotItem
        gi = next((it for it in self.inventory.items if isinstance(it,IronIngotItem)),None)
        if not gi: return False
        self.inventory.remove_one(IronIngotItem)
        return True

    def _get_weapon(self):
        from src.scenes.chest_scene import StickItem
        for it in self.inventory.items:
            if isinstance(it, StickItem):
                return it
        return None

    def _get_armour_item(self, slot):
        if not self.armour: return None
        return self.armour.equipped.get(slot)

    # ------------------------------------------------------------------ #
    # Hit-test helpers (use cached panel coords)
    # ------------------------------------------------------------------ #

    def _tab_rects(self):
        px,py,pw,ph = self._px,self._py,self._pw,self._ph
        tw = pw // 2
        return [pygame.Rect(px+i*tw+2, py+38, tw-4, 30) for i in range(2)]

    def _upgrade_btn_rect(self):
        px,py,pw,ph = self._px,self._py,self._pw,self._ph
        cy2 = py+80; cw = int(pw*0.58); ch = 130
        return pygame.Rect(px+20, cy2+ch+16, cw, 54)

    def _armour_row_rects(self):
        px,py,pw,ph = self._px,self._py,self._pw,self._ph
        cy2 = py+80; rw = int(pw*0.55)
        return [pygame.Rect(px+20, cy2+i*90, rw, 80) for i in range(len(ARMOUR_SLOTS))]

    # ------------------------------------------------------------------ #
    # Upgrade actions
    # ------------------------------------------------------------------ #

    def _do_upgrade_weapon(self):
        weapon = self._get_weapon()
        if not weapon:
            self._msg = "No upgradeable weapon found!"; self._msg_good=False
            self._msg_t=2.5; return
        lvl = getattr(weapon,'upgrade_level',0)
        if lvl >= 5:
            self._msg = "Already at max level!"; self._msg_good=False
            self._msg_t=2.5; return
        cost_g = WEAPON_UPGRADE_COSTS[lvl]
        if self._gold() < cost_g:
            self._msg = f"Need {cost_g}g!"; self._msg_good=False
            self._msg_t=2.5; return
        if self._ingots() < 1:
            self._msg = "Need 1 Iron Ingot!"; self._msg_good=False
            self._msg_t=2.5; return
        self._spend_gold(cost_g)
        self._spend_ingot()
        weapon.upgrade_level = lvl+1
        new_name = weapon.WEAPON_NAMES[weapon.upgrade_level]
        new_dmg  = weapon.DAMAGE_VALUES[weapon.upgrade_level]
        self._msg = f"Forged: {new_name}! Damage: {new_dmg}"
        self._msg_good = True; self._msg_t = 3.0
        self._hammering = True; self._hammer_t = 0.0
        import random as _r; self._dialogue = _r.choice(GORIN_DIALOGUES)

    def _do_upgrade_armour(self, slot):
        piece = self._get_armour_item(slot)
        if not piece:
            self._msg = f"No {ARMOUR_NAMES[slot]} equipped!"; self._msg_good=False
            self._msg_t=2.5; return
        lvl = getattr(piece,'upgrade_level',0)
        if lvl >= 5:
            self._msg = "Already at max level!"; self._msg_good=False
            self._msg_t=2.5; return
        cost_g = ARMOUR_UPGRADE_COSTS[lvl]
        if self._gold() < cost_g:
            self._msg = f"Need {cost_g}g!"; self._msg_good=False
            self._msg_t=2.5; return
        if self._ingots() < 1:
            self._msg = "Need 1 Iron Ingot!"; self._msg_good=False
            self._msg_t=2.5; return
        self._spend_gold(cost_g)
        self._spend_ingot()
        piece.upgrade_level = getattr(piece,'upgrade_level',0)+1
        base_def = abs(piece.defence_value) if hasattr(piece,'defence_value') else 1
        piece.defence_value = -(base_def+1)
        self._msg = f"{ARMOUR_NAMES[slot]} upgraded! Defence +{base_def+1}"
        self._msg_good=True; self._msg_t=3.0
        self._hammering=True; self._hammer_t=0.0
        import random as _r; self._dialogue=_r.choice(GORIN_DIALOGUES)

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #

    def _draw_background(self):
        for y in range(self.H):
            t = y/self.H
            r = int(20+15*t); g = int(14+10*t); b = int(8+6*t)
            pygame.draw.line(self.screen,(r,g,b),(0,y),(self.W,y))

        rng = random.Random(55)
        for row in range(8):
            for col in range(12):
                sx = col*(self.W//12)+rng.randint(-2,2)
                sy = row*(self.H//8)+rng.randint(-2,2)
                sw = self.W//12-2; sh2 = self.H//8-2
                v  = rng.randint(-6,6)
                pygame.draw.rect(self.screen,(45+v,35+v,22+v),(sx,sy,sw,sh2),1)

        pulse  = 0.5+0.5*math.sin(self.time*2.5)
        flicker= 0.6+0.4*math.sin(self.time*6.3+0.8)
        fx = self.W*3//4; fy = self.H*2//3
        fw,fh = 140,90

        pygame.draw.rect(self.screen,(90,72,50),(fx-fw//2,fy-fh,fw,fh))
        pygame.draw.rect(self.screen,(65,50,32),(fx-fw//2,fy-fh,fw,fh),3)
        pygame.draw.rect(self.screen,(15,10,6),(fx-38,fy-fh+16,76,52))
        pygame.draw.ellipse(self.screen,(15,10,6),(fx-38,fy-fh+8,76,24))

        for fi in range(6):
            fa = math.radians(fi*30+self.time*80)
            ffx = fx+int(math.cos(fa)*18)
            ffy = fy-fh+40+int(math.sin(fa)*10)
            flen= 14+int(12*math.sin(self.time*4+fi))
            col2=(int(255*flicker),int(150*pulse*flicker),15)
            pygame.draw.polygon(self.screen,col2,[
                (ffx-4,ffy+4),(ffx,ffy-flen),(ffx+4,ffy+4)])

        gs=pygame.Surface((fw*2,fh*2),pygame.SRCALPHA)
        pygame.draw.ellipse(gs,(int(200*pulse),int(100*pulse),20,int(55*pulse)),
                            (0,0,fw*2,fh*2))
        self.screen.blit(gs,(fx-fw,fy-fh*2+20),special_flags=pygame.BLEND_RGBA_ADD)

        pygame.draw.polygon(self.screen,(60,45,28),
                            [(fx-fw//2-10,fy-fh),(fx-20,fy-fh-40),
                             (fx+20,fy-fh-40),(fx+fw//2+10,fy-fh)])
        pygame.draw.polygon(self.screen,(45,32,18),
                            [(fx-fw//2-10,fy-fh),(fx-20,fy-fh-40),
                             (fx+20,fy-fh-40),(fx+fw//2+10,fy-fh)],2)

        ax = fx-40; ay = fy-20
        pygame.draw.rect(self.screen,(80,72,65),(ax,ay,48,14))
        pygame.draw.rect(self.screen,(65,58,50),(ax-4,ay+14,56,10))
        pygame.draw.rect(self.screen,(75,68,60),(ax+8,ay+24,32,12))
        pygame.draw.rect(self.screen,(55,48,42),(ax,ay,48,14),1)

        if self._hammering:
            hangle = math.sin(self._hammer_t*15)*0.6
            hx2 = ax+24+int(math.cos(hangle)*30)
            hy2 = ay-10+int(math.sin(hangle)*30)
            pygame.draw.line(self.screen,(120,100,70),(ax+24,ay-5),(hx2,hy2),5)
            pygame.draw.rect(self.screen,(140,130,115),(hx2-8,hy2-6,16,10))

        for sp in self._sparks:
            if sp["life"]>0:
                alpha = sp["life"]/sp["max_life"]
                r2,g2,b2 = sp["col"]
                pygame.draw.circle(self.screen,
                    (int(r2*alpha),int(g2*alpha),int(b2*alpha)),
                    (int(sp["x"]),int(sp["y"])),sp["size"])

        for ti,(tx2,ty2,tc) in enumerate([
            (self.W*3//4-90,self.H//4,(120,110,100)),
            (self.W*3//4-65,self.H//4-15,(130,120,108)),
            (self.W*3//4-40,self.H//4+5,(115,105,95)),
        ]):
            pygame.draw.circle(self.screen,(90,68,40),(tx2,ty2-2),4)
            pygame.draw.line(self.screen,tc,(tx2,ty2),(tx2+rng.randint(-5,5),ty2+40),3)

    def _draw_gorin(self, cx, cy):
        c = self.keeper_color
        dark = tuple(max(0,v-50) for v in c)
        apron=(80,60,35); leather=(100,72,40)

        bw=55; bh=65
        pygame.draw.ellipse(self.screen,c,(cx-bw//2,cy-bh//3,bw,bh))
        pygame.draw.ellipse(self.screen,dark,(cx-bw//2,cy-bh//3,bw,bh),2)
        pygame.draw.polygon(self.screen,apron,[
            (cx-20,cy-bh//3+8),(cx+20,cy-bh//3+8),
            (cx+24,cy+bh//2),(cx-24,cy+bh//2)])
        pygame.draw.line(self.screen,leather,(cx-18,cy-bh//3+8),(cx-bw//2,cy-bh//2),2)
        pygame.draw.line(self.screen,leather,(cx+18,cy-bh//3+8),(cx+bw//2,cy-bh//2),2)
        aw=8
        pygame.draw.line(self.screen,c,(cx-bw//2,cy-bh//4),(cx-bw//2-20,cy-bh//2-10),aw)
        pygame.draw.line(self.screen,(110,95,75),(cx-bw//2-20,cy-bh//2-10),(cx-bw//2-28,cy-bh//2-28),5)
        pygame.draw.rect(self.screen,(130,120,108),(cx-bw//2-36,cy-bh//2-34,16,10))
        pygame.draw.line(self.screen,c,(cx+bw//2,cy-bh//4),(cx+bw//2+18,cy+bh//4),aw)

        hr=22
        pygame.draw.circle(self.screen,c,(cx,cy-bh//3-hr),hr)
        pygame.draw.circle(self.screen,dark,(cx,cy-bh//3-hr),hr,2)
        for bi in range(7):
            bx2=cx-18+bi*6; by2=cy-bh//3-hr+hr//2
            blen=8+abs(bi-3)*3
            pygame.draw.line(self.screen,(165,158,148),(bx2,by2),(bx2,by2+blen),3)
        for ex,edir in [(cx-10,-1),(cx+4,1)]:
            pygame.draw.line(self.screen,(80,62,35),(ex,cy-bh//3-hr+6),(ex+edir*8,cy-bh//3-hr+3),3)
        for ex in [cx-7,cx+7]:
            pygame.draw.line(self.screen,(45,30,15),(ex-3,cy-bh//3-hr+9),(ex+3,cy-bh//3-hr+9),2)
        pygame.draw.circle(self.screen,tuple(max(0,v-20) for v in c),(cx,cy-bh//3-hr+14),5)
        for hi in [-8,-2,4]:
            pygame.draw.line(self.screen,(100,82,55),(cx+hi,cy-bh//3-hr*2+4),(cx+hi+2,cy-bh//3-hr*2-4),2)

    def _draw_dialogue_bubble(self, cx, cy):
        lines = self._dialogue.split("\n")
        max_w = max(self.font_small.size(l)[0] for l in lines)+20
        bh2   = len(lines)*18+14
        bx    = cx-max_w//2; by = cy-bh2-18
        pygame.draw.rect(self.screen,(235,220,190),(bx,by,max_w,bh2),border_radius=5)
        pygame.draw.rect(self.screen,(160,128,68),(bx,by,max_w,bh2),2,border_radius=5)
        pygame.draw.polygon(self.screen,(235,220,190),[(cx-7,by+bh2),(cx+7,by+bh2),(cx,by+bh2+12)])
        pygame.draw.line(self.screen,(160,128,68),(cx-7,by+bh2),(cx,by+bh2+12),2)
        pygame.draw.line(self.screen,(160,128,68),(cx+7,by+bh2),(cx,by+bh2+12),2)
        for li,line in enumerate(lines):
            ls=self.font_small.render(line,True,(50,35,15))
            self.screen.blit(ls,(bx+10,by+7+li*18))

    def _draw_panel(self, ease):
        pw=int(self.W*0.86); ph=int(self.H*0.84)
        px=self.W//2-pw//2; py=self.H//2-ph//2
        w2=int(pw*ease); h2=int(ph*ease)
        x=self.W//2-w2//2; y=self.H//2-h2//2
        if w2<4: return px,py,pw,ph
        bg=pygame.Surface((w2,h2),pygame.SRCALPHA)
        bg.fill((16,11,7,245))
        self.screen.blit(bg,(x,y))
        pygame.draw.rect(self.screen,self.shop_color,(x,y,w2,h2),2)
        pygame.draw.rect(self.screen,tuple(max(0,v-50) for v in self.shop_color),(x+5,y+5,w2-10,h2-10),1)
        sz=13
        for bx2,by2,dx,dy in [(x,y,1,1),(x+w2,y,-1,1),(x,y+h2,1,-1),(x+w2,y+h2,-1,-1)]:
            pygame.draw.line(self.screen,(200,140,50),(bx2,by2),(bx2+dx*sz,by2),2)
            pygame.draw.line(self.screen,(200,140,50),(bx2,by2),(bx2,by2+dy*sz),2)
        return px,py,pw,ph

    def _draw_tabs(self, px, py, pw):
        tabs=["WEAPONS","ARMOUR"]
        tw=pw//2
        mouse = pygame.mouse.get_pos()
        for i,label in enumerate(tabs):
            tx=px+i*tw; ty=py+38
            is_sel=(i==self.tab)
            tab_rect = pygame.Rect(tx+2, ty, tw-4, 30)
            is_hover = tab_rect.collidepoint(mouse) and not is_sel

            bg=pygame.Surface((tw-4,30),pygame.SRCALPHA)
            if is_sel:
                bg.fill((35,22,10,220))
            elif is_hover:
                bg.fill((28,18,8,200))
            else:
                bg.fill((20,12,6,160))
            self.screen.blit(bg,(tx+2,ty))

            bc=(200,140,50) if is_sel else (140,95,35) if is_hover else (80,55,22)
            pygame.draw.rect(self.screen,bc,(tx+2,ty,tw-4,30),2 if is_sel else 1)
            ls=self.screen.blit(
                self.font_medium.render(label,True,
                    (220,165,70) if is_sel else (170,125,55) if is_hover else (100,70,30)),
                (tx+tw//2 - self.font_medium.size(label)[0]//2, ty+6))
        pygame.draw.line(self.screen,self.shop_color,(px+self.tab*tw+2,py+68),(px+(self.tab+1)*tw-2,py+68),2)

    def _draw_weapon_tab(self, px, py, pw, ph):
        weapon = self._get_weapon()
        cy2 = py+80

        if not weapon:
            ns=self.font_medium.render("No upgradeable weapon in inventory.",True,(80,55,22))
            self.screen.blit(ns,(px+20,cy2+20))
            hint=self.font_tiny.render("TAB  switch tab    ESC  leave",True,(80,58,25))
            self.screen.blit(hint,(self.W//2-hint.get_width()//2,py+ph-hint.get_height()-10))
            self._draw_rumours(px, py, pw, ph)
            return

        lvl  = getattr(weapon,'upgrade_level',0)
        name = weapon.WEAPON_NAMES[min(lvl,5)]
        dmg  = weapon.DAMAGE_VALUES[min(lvl,5)]

        cw=int(pw*0.58); ch=130
        pygame.draw.rect(self.screen,(22,14,8),(px+20,cy2,cw,ch))
        pygame.draw.rect(self.screen,self.shop_color,(px+20,cy2,cw,ch),2)

        wn=self.font_medium.render(f"{name}",True,(220,185,100))
        self.screen.blit(wn,(px+32,cy2+10))
        stars="".join(["★" if i<lvl else "☆" for i in range(5)])
        ss=self.font_small.render(stars,True,(220,170,50))
        self.screen.blit(ss,(px+32,cy2+32))
        ds=self.font_small.render(f"Damage: {dmg}",True,(200,160,80))
        self.screen.blit(ds,(px+32,cy2+52))

        # Draw weapon icon
        weapon.draw_icon(self.screen, px+cw-30, cy2+ch//2, 40)

        # Upgrade path bar
        for wi in range(6):
            col=(100,80,40) if wi>lvl else self.shop_color
            pygame.draw.rect(self.screen,col,(px+32+wi*28,cy2+72,22,16))
            pygame.draw.rect(self.screen,(40,28,12),(px+32+wi*28,cy2+72,22,16),1)
            wl=self.font_tiny.render(weapon.WEAPON_NAMES[wi][:3],True,
                                     (200,160,60) if wi<=lvl else (60,44,20))
            self.screen.blit(wl,(px+33+wi*28,cy2+75))

        # Upgrade button
        if lvl < 5:
            cost_g=WEAPON_UPGRADE_COSTS[lvl]
            next_name=weapon.WEAPON_NAMES[lvl+1]
            next_dmg =weapon.DAMAGE_VALUES[lvl+1]
            can = self._gold()>=cost_g and self._ingots()>=1

            ub_x=px+20; ub_y=cy2+ch+16; ub_w=cw; ub_h=54
            mouse = pygame.mouse.get_pos()
            is_hover_ub = pygame.Rect(ub_x,ub_y,ub_w,ub_h).collidepoint(mouse) and can

            pygame.draw.rect(self.screen,(18,11,6),(ub_x,ub_y,ub_w,ub_h))
            bc=(220,160,60) if is_hover_ub else (200,140,50) if can else (55,38,18)
            pygame.draw.rect(self.screen,bc,(ub_x,ub_y,ub_w,ub_h),2)

            ul=self.font_medium.render(f"Upgrade → {next_name}  (dmg {next_dmg})",
                                        True,(235,190,80) if is_hover_ub else (220,175,70) if can else (80,58,28))
            self.screen.blit(ul,(ub_x+12,ub_y+8))
            cost_s=self.font_small.render(f"Cost: {cost_g}g + 1 Iron Ingot",
                                           True,(180,145,55) if can else (65,48,22))
            self.screen.blit(cost_s,(ub_x+12,ub_y+28))

            # Click hint
            if can:
                ck=self.font_tiny.render("click or ENTER to upgrade",True,(120,90,40))
                self.screen.blit(ck,(ub_x+ub_w+10,ub_y+ub_h//2-ck.get_height()//2))
        else:
            ms=self.font_medium.render("✓ MAX LEVEL — Legendary Blade!",True,(220,170,50))
            self.screen.blit(ms,(px+32,cy2+ch+20))

        # Resources panel
        rx=px+cw+40
        self.screen.blit(self.font_medium.render("Resources:",True,(160,120,50)),(rx,py+80))
        self.screen.blit(self.font_small.render(f"Gold:        {self._gold()}g",True,(220,185,60)),(rx,py+104))
        self.screen.blit(self.font_small.render(f"Iron Ingots: {self._ingots()}",True,(180,165,140)),(rx,py+124))

        hint=self.font_tiny.render("ENTER / click  upgrade    TAB  switch tab    ESC  leave",True,(80,58,25))
        self.screen.blit(hint,(self.W//2-hint.get_width()//2,py+ph-hint.get_height()-10))
        self._draw_rumours(px, py, pw, ph)

    def _draw_armour_tab(self, px, py, pw, ph):
        cy2=py+80; rw=int(pw*0.55)
        mouse = pygame.mouse.get_pos()

        for i,slot in enumerate(ARMOUR_SLOTS):
            piece=self._get_armour_item(slot)
            ry=cy2+i*90
            is_sel=(i==self.selected and self.tab==1)
            row_rect = pygame.Rect(px+20,ry,rw,80)
            is_hover = row_rect.collidepoint(mouse) and not is_sel

            bg=pygame.Surface((rw,80),pygame.SRCALPHA)
            if is_sel:
                bg.fill((40,25,10,230))
            elif is_hover:
                bg.fill((30,18,8,200))
            else:
                bg.fill((22,14,8,220))
            self.screen.blit(bg,(px+20,ry))
            bc=(200,140,50) if is_sel else (140,95,35) if is_hover else (65,45,18)
            pygame.draw.rect(self.screen,bc,(px+20,ry,rw,80),2 if is_sel else 1)

            if is_sel:
                arr=self.font_small.render("▶",True,self.shop_color)
                self.screen.blit(arr,(px+6,ry+32))

            name=ARMOUR_NAMES[slot]
            if not piece:
                ns=self.font_medium.render(f"{name}  [not equipped]",True,(65,48,22))
                self.screen.blit(ns,(px+32,ry+10))
                ns2=self.font_tiny.render("Equip this armour via the Inventory (I) first.",True,(50,38,16))
                self.screen.blit(ns2,(px+32,ry+30))
                continue

            lvl=getattr(piece,'upgrade_level',0)
            base_def=abs(getattr(piece,'defence_value',1))
            stars="".join(["★" if j<lvl else "☆" for j in range(5)])

            ns=self.font_medium.render(f"{name}  {stars}",True,(220,185,100))
            self.screen.blit(ns,(px+32,ry+8))
            ds=self.font_small.render(f"Defence: {base_def}",True,(180,150,75))
            self.screen.blit(ds,(px+32,ry+28))

            if lvl<5:
                cost_g=ARMOUR_UPGRADE_COSTS[lvl]
                can=self._gold()>=cost_g and self._ingots()>=1
                action_hint = "click again to upgrade" if is_sel and can else ""
                cs=self.font_small.render(
                    f"Upgrade: {cost_g}g + 1 ingot → +{base_def+1} def  {action_hint}",
                    True,(200,160,60) if can else (65,48,22))
                self.screen.blit(cs,(px+32,ry+48))
            else:
                ms=self.font_tiny.render("✓ MAX",True,(220,170,50))
                self.screen.blit(ms,(px+32,ry+50))

        # Resources
        rx=px+rw+40
        self.screen.blit(self.font_medium.render("Resources:",True,(160,120,50)),(rx,py+80))
        self.screen.blit(self.font_small.render(f"Gold:        {self._gold()}g",True,(220,185,60)),(rx,py+104))
        self.screen.blit(self.font_small.render(f"Iron Ingots: {self._ingots()}",True,(180,165,140)),(rx,py+124))

        hint=self.font_tiny.render("↑ ↓ / click  select    ENTER / click  upgrade    TAB  switch tab    ESC  leave",True,(80,58,25))
        self.screen.blit(hint,(self.W//2-hint.get_width()//2,py+ph-hint.get_height()-10))
        self._draw_rumours(px, py, pw, ph)

    def _draw_rumours(self, px, py, pw, ph):
        """Rumour board — right column, below resources."""
        # Panel sits in the right column, below resources block
        rx  = px + int(pw * 0.60)
        ry  = py + 150
        rw  = pw - int(pw * 0.60) - 20
        rh  = ph - 150 - 60   # leave room for hint at bottom

        # Board background
        bg = pygame.Surface((rw, rh), pygame.SRCALPHA)
        bg.fill((18, 12, 6, 200))
        self.screen.blit(bg, (rx, ry))
        pygame.draw.rect(self.screen, (100, 72, 30), (rx, ry, rw, rh), 1)

        # Header
        hdr = self.font_small.render("— RUMOURS —", True, (180, 138, 55))
        self.screen.blit(hdr, (rx + rw//2 - hdr.get_width()//2, ry + 8))
        pygame.draw.line(self.screen, (80, 58, 24),
                         (rx + 8, ry + 24), (rx + rw - 8, ry + 24), 1)

        # Rumour entries — scrolled by self._rumour_scroll
        entry_y = ry + 32
        pad     = 8
        visible_h = rh - 40
        line_h  = self.font_tiny.get_height() + 3

        rumours = RUMOURS + self._extra_rumours   # base + quest-added rumours

        for i, rumour in enumerate(rumours):
            # Word-wrap each rumour into lines
            words = rumour.split()
            lines_out = []
            cur = ""
            for w in words:
                test = cur + (" " if cur else "") + w
                if self.font_tiny.size(test)[0] < rw - pad*2:
                    cur = test
                else:
                    lines_out.append(cur)
                    cur = w
            if cur:
                lines_out.append(cur)

            block_h = len(lines_out) * line_h + 6
            by2 = entry_y

            # Clip to panel
            if by2 + block_h < ry + 32:
                entry_y += block_h + 4
                continue
            if by2 > ry + rh - 12:
                break

            # Bullet dot
            dot_col = (160, 120, 45) if i < len(RUMOURS) else (100, 160, 120)
            pygame.draw.circle(self.screen, dot_col, (rx + pad + 3, by2 + line_h//2), 3)

            for li, line in enumerate(lines_out):
                col = (170, 145, 95) if i < len(RUMOURS) else (120, 190, 140)
                ls  = self.font_tiny.render(line, True, col)
                self.screen.blit(ls, (rx + pad + 10, by2 + li * line_h))

            entry_y += block_h + 4

        # Scroll hint if content overflows
        if entry_y > ry + rh - 12:
            more = self.font_tiny.render("▼ more", True, (80, 60, 28))
            self.screen.blit(more, (rx + rw//2 - more.get_width()//2, ry + rh - 14))

    def _draw_message(self):
        if not self._msg or self._msg_t<=0: return
        alpha=min(1.0,self._msg_t/0.4)
        col=(120,200,120) if self._msg_good else (200,100,80)
        ms=self.font_small.render(self._msg,True,col)
        bg=pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
        bg.fill((12,8,4,int(210*alpha)))
        bx=self.W//2-bg.get_width()//2; by=80
        self.screen.blit(bg,(bx,by))
        pygame.draw.rect(self.screen,col,(bx,by,bg.get_width(),bg.get_height()),1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms,(bx+10,by+4))

    # ------------------------------------------------------------------ #

    def run(self) -> str:
        _leave_hover = 0.0
        while True:
            dt=self.clock.tick(60)/1000.0
            self.time+=dt
            self.open_anim=min(self.open_anim+dt,0.4)
            ease=1-(1-min(1.0,self.open_anim/0.4))**3
            self._msg_t=max(0.0,self._msg_t-dt)
            self._update_sparks(dt)
            if self._hammering:
                self._hammer_t+=dt
                if self._hammer_t>1.2: self._hammering=False

            mouse = pygame.mouse.get_pos()

            # Compute panel rect for leave button position
            pw=int(self.W*0.86); ph=int(self.H*0.84)
            px=self.W//2-pw//2; py=self.H//2-ph//2
            leave_rect = pygame.Rect(px+pw-116, py+10, 100, 28)
            _leave_hover += ((1.0 if leave_rect.collidepoint(mouse) else 0.0) - _leave_hover)*10*dt
            _leave_hover = max(0.0, min(1.0, _leave_hover))

            for event in pygame.event.get():
                if event.type==pygame.QUIT: return "exit"

                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: return "town"
                    if event.key==pygame.K_TAB:
                        self.tab=(self.tab+1)%2; self.selected=0
                    if event.key==pygame.K_UP:
                        self.selected=max(0,self.selected-1)
                    if event.key==pygame.K_DOWN:
                        maxs=0 if self.tab==0 else len(ARMOUR_SLOTS)-1
                        self.selected=min(maxs,self.selected+1)
                    if event.key in (pygame.K_RETURN,pygame.K_SPACE):
                        if self.tab==0:
                            self._do_upgrade_weapon()
                        else:
                            self._do_upgrade_armour(ARMOUR_SLOTS[self.selected])

                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    # Leave button
                    if leave_rect.collidepoint(mouse): return "town"

                    # Only handle other clicks once panel is fully open
                    if self._pw == 0:
                        continue

                    # Tab clicks
                    for i, rect in enumerate(self._tab_rects()):
                        if rect.collidepoint(mouse):
                            self.tab = i
                            self.selected = 0
                            break

                    # Weapons tab: upgrade button click
                    if self.tab == 0:
                        if self._upgrade_btn_rect().collidepoint(mouse):
                            self._do_upgrade_weapon()

                    # Armour tab: row clicks
                    elif self.tab == 1:
                        for i, rect in enumerate(self._armour_row_rects()):
                            if rect.collidepoint(mouse):
                                if self.selected == i:
                                    self._do_upgrade_armour(ARMOUR_SLOTS[i])
                                else:
                                    self.selected = i
                                break

            # Draw
            self._draw_background()
            px,py,pw,ph = self._draw_panel(ease)
            # Cache panel coords for mouse hit-testing
            self._px,self._py,self._pw,self._ph = px,py,pw,ph

            if ease>0.7:
                title=self.font_title.render("Gorin's Forge",True,(210,155,60))
                self.screen.blit(title,(self.W//2-title.get_width()//2,py+10))
                pygame.draw.line(self.screen,self.shop_color,(px+20,py+32),(px+pw-20,py+32),1)
                self._draw_tabs(px,py,pw)
                if self.tab==0: self._draw_weapon_tab(px,py,pw,ph)
                else:           self._draw_armour_tab(px,py,pw,ph)

                gcx=px+pw-110; gcy=py+ph*2//3
                self._draw_gorin(gcx,gcy)
                self._draw_dialogue_bubble(gcx,gcy-45)
                kn=self.font_tiny.render("Gorin, Master Smith",True,(110,78,30))
                self.screen.blit(kn,(gcx-kn.get_width()//2,gcy+80))

                # LEAVE button — top right, consistent with other scenes
                leave_rect = pygame.Rect(px+pw-116, py+10, 100, 28)
                lbg = pygame.Surface((100,28), pygame.SRCALPHA)
                lbg.fill((int(18+30*_leave_hover),int(12+22*_leave_hover),int(7+14*_leave_hover),200))
                self.screen.blit(lbg, leave_rect.topleft)
                def _lc(a,b,h=_leave_hover): return tuple(int(a[j]+(b[j]-a[j])*h) for j in range(3))
                pygame.draw.rect(self.screen,_lc((60,44,24),(160,125,60)),leave_rect,2)
                lbl=self.font_small.render("LEAVE",True,_lc((120,90,45),(210,175,90)))
                self.screen.blit(lbl,(leave_rect.centerx-lbl.get_width()//2,leave_rect.centery-lbl.get_height()//2))

            self._draw_message()
            pygame.display.flip()