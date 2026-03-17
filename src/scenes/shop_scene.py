import pygame
import math
import random


# ---------------------------------------------------------------------------
# Shop item definition
# ---------------------------------------------------------------------------

class ShopItem:
    def __init__(self, item_factory, price, stock=-1, description=None, category="misc"):
        self.item_factory = item_factory
        self.price        = price
        self.stock        = stock
        self._instance    = item_factory()
        self.description  = description or self._instance.description
        self.category     = category   # "consumables" | "equipment" | "keys" | "misc"
        self.is_new       = False      # set True on restock

    @property
    def name(self):
        return self._instance.name

    @property
    def icon_color(self):
        return self._instance.icon_color

    def draw_icon(self, surface, cx, cy, size):
        self._instance.draw_icon(surface, cx, cy, size)

    def in_stock(self):
        return self.stock != 0

    def buy(self):
        if self.stock > 0:
            self.stock -= 1
        return self.item_factory()


# ---------------------------------------------------------------------------
# Base ShopScene
# ---------------------------------------------------------------------------

class ShopScene:
    def __init__(self, screen, inventory):
        self.screen    = screen
        self.W, self.H = screen.get_size()
        self.clock     = pygame.time.Clock()
        self.time      = 0.0
        self.inventory = inventory

        self.font_title  = pygame.font.SysFont("courier new", 30, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 18, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 14)
        self.font_tiny   = pygame.font.SysFont("courier new", 12)

        self.shop_name    = "Shop"
        self.shop_color   = (140, 110, 60)
        self.shop_items   = []
        self.sell_enabled = True
        self.flavor_text  = "What can I do for you?"
        self.keeper_color = (180, 150, 100)

        self.mode          = "buy"
        self.selected_buy  = 0
        self.selected_sell = 0
        self.message       = ""
        self.message_timer = 0.0
        self.open_anim     = 0.0
        self.OPEN_DUR      = 0.4

        self._buy_hover  = 0.0
        self._sell_hover = 0.0
        self._back_hover = 0.0

        self._setup()

    def _setup(self):
        pass

    def _gold(self):
        from src.scenes.chest_scene import GoldItem
        return sum(self.inventory.stack_count(it)
                   for it in self.inventory.items if isinstance(it, GoldItem))

    def _spend_gold(self, amount):
        from src.scenes.chest_scene import GoldItem
        gold_item = next((it for it in self.inventory.items if isinstance(it, GoldItem)), None)
        if gold_item is None: return False
        total = self.inventory.stack_count(gold_item)
        if total < amount: return False
        remaining = total - amount
        self.inventory.remove(gold_item)
        if remaining > 0:
            self.inventory.add(GoldItem(remaining))
        return True

    def _sell_item(self, item):
        from src.scenes.chest_scene import GoldItem
        sell_prices = {
            "Healing Potion": 4, "Dungeon Key": 8, "Candle": 1,
            "Iron Shield": 18, "Sun Sword": 25, "Sword": 10,
            "Gold": 0, "Exit Key": 0,
        }
        price = sell_prices.get(item.name, 2)
        if price == 0:
            return False, "Can't sell that here."
        if getattr(item, 'stackable', False):
            self.inventory.remove_one(type(item))
        else:
            self.inventory.remove(item)
        self.inventory.add(GoldItem(price))
        return True, f"Sold {item.name} for {price} gold!"

    def _draw_background(self):
        self.screen.fill((20, 15, 10))

    def _draw_keeper(self, cx, cy, color):
        c = color
        dark = tuple(max(0, v-40) for v in c)
        pygame.draw.ellipse(self.screen, c, (cx-30, cy-20, 60, 80))
        pygame.draw.ellipse(self.screen, dark, (cx-30, cy-20, 60, 80), 2)
        pygame.draw.circle(self.screen, c, (cx, cy-35), 28)
        pygame.draw.circle(self.screen, dark, (cx, cy-35), 28, 2)
        pygame.draw.circle(self.screen, (40,30,15), (cx-9, cy-38), 5)
        pygame.draw.circle(self.screen, (40,30,15), (cx+9, cy-38), 5)
        pygame.draw.circle(self.screen, (220,200,160), (cx-9, cy-38), 2)
        pygame.draw.circle(self.screen, (220,200,160), (cx+9, cy-38), 2)
        pygame.draw.arc(self.screen, dark, (cx-10, cy-32, 20, 12), math.pi, 2*math.pi, 2)

    def _panel_rect(self):
        pw = int(self.W * 0.72)
        ph = int(self.H * 0.78)
        px = (self.W - pw) // 2
        py = (self.H - ph) // 2
        return px, py, pw, ph

    def _draw_panel(self, t):
        px, py, pw, ph = self._panel_rect()
        ease = 1-(1-t)**3
        w = int(pw*ease); h = int(ph*ease)
        x = self.W//2 - w//2; y = self.H//2 - h//2
        if w < 4: return
        sh = pygame.Surface((w+14, h+14), pygame.SRCALPHA)
        sh.fill((0,0,0,100))
        self.screen.blit(sh, (x-7, y-7))
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((16,12,8,248))
        self.screen.blit(panel, (x, y))
        pygame.draw.rect(self.screen, self.shop_color, (x, y, w, h), 2)
        pygame.draw.rect(self.screen, tuple(max(0,c-40) for c in self.shop_color), (x+5, y+5, w-10, h-10), 1)
        c2 = tuple(min(255, c+30) for c in self.shop_color)
        sz = 14
        for bx, by, dx, dy in [(x,y,1,1),(x+w,y,-1,1),(x,y+h,1,-1),(x+w,y+h,-1,-1)]:
            pygame.draw.line(self.screen, c2, (bx, by), (bx+dx*sz, by), 2)
            pygame.draw.line(self.screen, c2, (bx, by), (bx, by+dy*sz), 2)
            pygame.draw.circle(self.screen, c2, (bx, by), 3)
        if t > 0.8:
            title = self.font_title.render(self.shop_name, True, tuple(min(255,c+80) for c in self.shop_color))
            self.screen.blit(title, (self.W//2-title.get_width()//2, y+12))
            rule_y = y+12+title.get_height()+4
            pygame.draw.line(self.screen, self.shop_color, (x+20, rule_y), (x+w-20, rule_y), 1)
            gold = self._gold()
            gs = self.font_medium.render(f"Gold: {gold}", True, (220,185,60))
            self.screen.blit(gs, (x+w-gs.get_width()-16, y+12))

    def _draw_tabs(self, t, x, y, w, h):
        if t < 0.8: return
        tab_y = y + 55
        tab_w = 100; tab_h = 32
        for i, (label, mode) in enumerate([("BUY","buy"),("SELL","sell")]):
            if not self.sell_enabled and mode == "sell": continue
            tx2 = x + 20 + i*110
            is_sel = self.mode == mode
            col = self.shop_color if is_sel else (50,38,22)
            fill = pygame.Surface((tab_w, tab_h), pygame.SRCALPHA)
            fill.fill((*col, 220) if is_sel else (25,18,10,180))
            self.screen.blit(fill, (tx2, tab_y))
            pygame.draw.rect(self.screen, col, (tx2, tab_y, tab_w, tab_h), 2)
            lbl = self.font_small.render(label, True, (220,190,110) if is_sel else (100,78,45))
            self.screen.blit(lbl, (tx2+tab_w//2-lbl.get_width()//2, tab_y+tab_h//2-lbl.get_height()//2))
        bx2 = x + w - 120
        bt = self._back_hover
        fill = pygame.Surface((100, 32), pygame.SRCALPHA)
        fill.fill((int(18+30*bt), int(14+24*bt), int(8+14*bt), 200))
        self.screen.blit(fill, (bx2, tab_y))
        def lc(a, b): return tuple(int(a[i]+(b[i]-a[i])*bt) for i in range(3))
        pygame.draw.rect(self.screen, lc((60,45,25),(160,125,60)), (bx2, tab_y, 100, 32), 2)
        bl = self.font_small.render("LEAVE", True, lc((120,92,48),(210,175,90)))
        self.screen.blit(bl, (bx2+50-bl.get_width()//2, tab_y+16-bl.get_height()//2))

    def _draw_buy_list(self, x, y, w, h):
        items = self.shop_items
        if not items:
            ns = self.font_small.render("Nothing for sale.", True, (100,78,45))
            self.screen.blit(ns, (x+20, y+100))
            return
        list_y = y + 100; row_h = 58; icon_s = 36; row_w = w - 40; gold = self._gold()
        for i, si in enumerate(items):
            ry = list_y + i*row_h; is_sel = (i == self.selected_buy)
            can_buy = gold >= si.price and si.in_stock()
            row_bg = pygame.Surface((row_w, row_h-4), pygame.SRCALPHA)
            row_bg.fill((35,26,14,220) if is_sel else (18,13,7,160))
            self.screen.blit(row_bg, (x+20, ry))
            bc = self.shop_color if (is_sel and can_buy) else (80,60,30) if is_sel else (40,30,15)
            pygame.draw.rect(self.screen, bc, (x+20, ry, row_w, row_h-4), 2 if is_sel else 1)
            si.draw_icon(self.screen, x+50, ry+row_h//2-2, icon_s)
            nc = (220,190,120) if (is_sel and can_buy) else (150,115,65) if can_buy else (80,62,40)
            ns2 = self.font_medium.render(si.name, True, nc)
            self.screen.blit(ns2, (x+80, ry+8))
            ds = self.font_tiny.render(si.description, True, (100,78,45))
            self.screen.blit(ds, (x+80, ry+8+ns2.get_height()+2))
            pc = (220,185,50) if can_buy else (100,75,35)
            ps = self.font_medium.render(f"{si.price}g", True, pc)
            self.screen.blit(ps, (x+20+row_w-ps.get_width()-8, ry+row_h//2-ps.get_height()//2-2))
            if si.stock > 0:
                ss2 = self.font_tiny.render(f"x{si.stock}", True, (120,95,50))
                self.screen.blit(ss2, (x+20+row_w-ss2.get_width()-8, ry+row_h//2+6))
            elif si.stock == 0:
                oos = self.font_tiny.render("OUT OF STOCK", True, (120,60,40))
                self.screen.blit(oos, (x+20+row_w-oos.get_width()-8, ry+row_h//2-oos.get_height()//2-2))
            if is_sel:
                arr = self.font_small.render("▶", True, self.shop_color)
                self.screen.blit(arr, (x+22, ry+row_h//2-arr.get_height()//2-2))
        hint = self.font_tiny.render("↑ ↓  select    ENTER  buy    ESC  leave", True, (70,54,28))
        self.screen.blit(hint, (x+20, y+h-hint.get_height()-10))

    def _draw_sell_list(self, x, y, w, h):
        from src.scenes.chest_scene import GoldItem, ExitKeyItem
        items = [it for it in self.inventory.items if not isinstance(it,(GoldItem,ExitKeyItem))]
        list_y = y + 100; row_h = 58; icon_s = 36; row_w = w - 40
        if not items:
            ns = self.font_small.render("Nothing to sell.", True, (100,78,45))
            self.screen.blit(ns, (x+20, y+100))
        else:
            sell_prices = {"Healing Potion":4,"Dungeon Key":8,"Candle":1,"Iron Shield":18,"Sun Sword":25,"Sword":10}
            for i, item in enumerate(items):
                ry = list_y + i*row_h; is_sel = (i == self.selected_sell)
                price = sell_prices.get(item.name, 2)
                row_bg = pygame.Surface((row_w, row_h-4), pygame.SRCALPHA)
                row_bg.fill((35,26,14,220) if is_sel else (18,13,7,160))
                self.screen.blit(row_bg, (x+20, ry))
                bc = self.shop_color if is_sel else (40,30,15)
                pygame.draw.rect(self.screen, bc, (x+20, ry, row_w, row_h-4), 2 if is_sel else 1)
                item.draw_icon(self.screen, x+50, ry+row_h//2-2, icon_s)
                nc = (220,190,120) if is_sel else (150,115,65)
                stack_n = self.inventory.stack_count(item)
                name_label = f"{item.name}  (x{stack_n})" if getattr(item,'stackable',False) and stack_n>1 else item.name
                ns2 = self.font_medium.render(name_label, True, nc)
                self.screen.blit(ns2, (x+80, ry+8))
                ds = self.font_tiny.render(item.description, True, (100,78,45))
                self.screen.blit(ds, (x+80, ry+8+ns2.get_height()+2))
                ps = self.font_medium.render(f"{price}g each", True, (180,155,45))
                self.screen.blit(ps, (x+20+row_w-ps.get_width()-8, ry+row_h//2-ps.get_height()//2-2))
                if is_sel:
                    arr = self.font_small.render("▶", True, self.shop_color)
                    self.screen.blit(arr, (x+22, ry+row_h//2-arr.get_height()//2-2))
        hint = self.font_tiny.render("↑ ↓  select    ENTER  sell    ESC  leave", True, (70,54,28))
        self.screen.blit(hint, (x+20, y+h-hint.get_height()-10))

    def _draw_message(self, x, y, w):
        if not self.message or self.message_timer <= 0: return
        alpha = min(1.0, self.message_timer/0.4)
        ms = self.font_small.render(self.message, True, (220,195,120))
        bg = pygame.Surface((ms.get_width()+20, ms.get_height()+8), pygame.SRCALPHA)
        bg.fill((14,10,6,int(220*alpha)))
        bx2 = self.W//2 - bg.get_width()//2; by2 = y - bg.get_height() - 8
        self.screen.blit(bg, (bx2, by2))
        pygame.draw.rect(self.screen, self.shop_color, (bx2, by2, bg.get_width(), bg.get_height()), 1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms, (bx2+10, by2+4))

    def _draw_keeper_area(self, x, y, w, t):
        if t < 0.8: return
        kx = x + w - 90; ky = y + 45
        self._draw_keeper(kx, ky, self.keeper_color)
        fs = self.font_tiny.render(f'"{self.flavor_text}"', True, (160,135,85))
        self.screen.blit(fs, (kx-fs.get_width()//2, ky+65))

    def _handle_buy(self, key):
        items = self.shop_items
        if not items: return
        if key == pygame.K_UP:
            self.selected_buy = max(0, self.selected_buy-1)
        elif key == pygame.K_DOWN:
            self.selected_buy = min(len(items)-1, self.selected_buy+1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            si = items[self.selected_buy]
            if not si.in_stock():
                self.message = "Out of stock!"; self.message_timer = 2.0
            elif self._gold() < si.price:
                self.message = f"Need {si.price} gold — you have {self._gold()}!"; self.message_timer = 2.5
            else:
                if self._spend_gold(si.price):
                    self.inventory.add(si.buy())
                    self.message = f"Bought {si.name} for {si.price} gold!"; self.message_timer = 2.0

    def _handle_sell(self, key):
        from src.scenes.chest_scene import GoldItem, ExitKeyItem
        items = [it for it in self.inventory.items if not isinstance(it,(GoldItem,ExitKeyItem))]
        if not items: return
        if key == pygame.K_UP:
            self.selected_sell = max(0, self.selected_sell-1)
        elif key == pygame.K_DOWN:
            self.selected_sell = min(len(items)-1, self.selected_sell+1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            item = items[self.selected_sell]
            ok, msg = self._sell_item(item)
            self.message = msg; self.message_timer = 2.0
            from src.scenes.chest_scene import GoldItem, ExitKeyItem
            remaining = [it for it in self.inventory.items if not isinstance(it,(GoldItem,ExitKeyItem))]
            self.selected_sell = max(0, min(self.selected_sell, len(remaining)-1))

    def _tab_rects(self, x, y, w, h):
        tab_y = y + 55
        rects = {}
        for i, (label, mode) in enumerate([("BUY","buy"),("SELL","sell")]):
            rects[mode] = pygame.Rect(x+20+i*110, tab_y, 100, 32)
        rects["back"] = pygame.Rect(x+w-120, tab_y, 100, 32)
        return rects

    def run(self) -> str:
        while True:
            dt = self.clock.tick(60)/1000.0
            self.time += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            t = min(1.0, self.open_anim/self.OPEN_DUR)
            self.message_timer = max(0.0, self.message_timer-dt)
            mouse = pygame.mouse.get_pos()
            px, py, pw, ph = self._panel_rect()
            tabs = self._tab_rects(px, py, pw, ph)
            self._back_hover += ((1.0 if tabs["back"].collidepoint(mouse) else 0.0) - self._back_hover) * 10*dt
            self._back_hover = max(0.0, min(1.0, self._back_hover))
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: return "town"
                    if event.key == pygame.K_TAB and self.sell_enabled:
                        self.mode = "sell" if self.mode=="buy" else "buy"
                    if self.mode == "buy": self._handle_buy(event.key)
                    else: self._handle_sell(event.key)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if tabs["back"].collidepoint(mouse): return "town"
                    if tabs.get("buy") and tabs["buy"].collidepoint(mouse): self.mode = "buy"
                    if self.sell_enabled and tabs.get("sell") and tabs["sell"].collidepoint(mouse): self.mode = "sell"
            self._draw_background()
            ease = 1-(1-t)**3
            if ease > 0.1:
                self._draw_panel(t)
                self._draw_tabs(t, px, py, pw, ph)
                self._draw_keeper_area(px, py, pw, t)
                if t > 0.85:
                    if self.mode == "buy": self._draw_buy_list(px, py, pw, ph)
                    else: self._draw_sell_list(px, py, pw, ph)
                    self._draw_message(px, py, pw)
            pygame.display.flip()


# ===========================================================================
# InnScene — unchanged
# ===========================================================================

class InnScene:
    PARTIAL_COST = 7
    PARTIAL_HEAL = 15
    FULL_COST    = 15
    POTION_COST  = 6

    RUMOURS = [
        "They say the Goblin King wears a crown made from adventurer bones...",
        "Old Mira found strange tracks near the dungeon entrance last week.",
        "A troll was spotted near the eastern gate. Best travel in daylight.",
        "The chest in the final room hasn't been opened in thirty years.",
        "Word is there's a blade down there that glows like the sun itself.",
        "Three adventurers went in last month. Only one came back — won't say a word.",
        "The skeletons down there used to be the king's own soldiers, they say.",
        "Bring potions. Lots of them. You'll thank me later.",
        "The rats in that dungeon are the size of dogs. I've seen them myself.",
        "Someone sold a gold ingot at the market claiming it came from the dungeon.",
        "The Goblin King heals himself. Don't let the fight drag on.",
        "There's a locked door or two down there. Keys are hidden in side rooms.",
    ]

    def __init__(self, screen, inventory, game_state=None):
        self.screen     = screen
        self.W, self.H  = screen.get_size()
        self.clock      = pygame.time.Clock()
        self.time       = 0.0
        self.inventory  = inventory
        self.game_state = game_state

        self.font_title  = pygame.font.SysFont("courier new", 26, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 17, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 13)
        self.font_tiny   = pygame.font.SysFont("courier new", 11)

        self._message       = ""
        self._message_timer = 0.0
        self._msg_good      = True
        self.open_anim      = 0.0
        self.OPEN_DUR       = 0.4
        self.selected       = 0

        import random as _r
        self._rumour_idx   = _r.randint(0, len(self.RUMOURS)-1)
        self._rumour_timer = 0.0
        self.RUMOUR_DUR    = 6.0

        self._dialogues = [
            "Welcome to the Rusty Flagon!\nRest your weary bones.",
            "Heading into the dungeon?\nMake sure you're well rested first.",
            "The name's Borin. I've kept\nthis inn for thirty years.",
            "Heard something howling down\nthere last night. Nasty business.",
            "Another round? Ha! You adventurers\nare good for business, I'll say that.",
        ]
        import random as _r2
        self._current_dialogue = _r2.choice(self._dialogues)

        self.shop_color   = (140, 95, 45)
        self.keeper_color = (195, 160, 110)

    def _gold(self):
        from src.scenes.chest_scene import GoldItem
        return sum(self.inventory.stack_count(it) for it in self.inventory.items if isinstance(it, GoldItem))

    def _spend_gold(self, amount):
        from src.scenes.chest_scene import GoldItem
        gold_item = next((it for it in self.inventory.items if isinstance(it, GoldItem)), None)
        if gold_item is None: return False
        total = self.inventory.stack_count(gold_item)
        if total < amount: return False
        remaining = total - amount
        self.inventory.remove(gold_item)
        if remaining > 0: self.inventory.add(GoldItem(remaining))
        return True

    def _player_hp(self):
        if self.game_state: return self.game_state.player_hp
        from src.scenes.combat_scene import PLAYER_MAX_HP
        return PLAYER_MAX_HP

    def _player_max_hp(self):
        if self.game_state: return self.game_state.player_max_hp
        from src.scenes.combat_scene import PLAYER_MAX_HP
        return PLAYER_MAX_HP

    def _set_hp(self, hp):
        if self.game_state:
            self.game_state.player_hp = min(hp, self._player_max_hp())

    def _draw_background(self):
        for y in range(self.H):
            t2 = y/self.H
            r = int(28+18*t2); g2 = int(18+12*t2); b = int(10+6*t2)
            pygame.draw.line(self.screen,(r,g2,b),(0,y),(self.W,y))
        pulse = 0.55+0.45*math.sin(self.time*2.2)
        flicker = 0.6+0.4*math.sin(self.time*5.1+0.8)
        fw,fh = 120,90; fx = self.W-fw-40; fy = self.H-fh-30
        pygame.draw.rect(self.screen,(100,80,50),(fx-12,fy-18,fw+24,18))
        pygame.draw.rect(self.screen,(75,58,32),(fx-12,fy-18,fw+24,18),2)
        pygame.draw.rect(self.screen,(40,28,15),(fx,fy,fw,fh))
        pygame.draw.rect(self.screen,(65,45,22),(fx,fy,fw,fh),2)
        pygame.draw.ellipse(self.screen,(40,28,15),(fx,fy-fh//3,fw,fh//2))
        for fi,(fr,fg2,fb2,fa) in enumerate([
            (int(200*pulse*flicker),int(100*pulse),20,int(120*pulse)),
            (int(240*pulse),int(140*pulse*flicker),30,int(80*pulse)),
            (255,int(200*flicker),50,int(60*pulse))]):
            gs2=pygame.Surface((fw-fi*20,fh-fi*15),pygame.SRCALPHA)
            pygame.draw.ellipse(gs2,(fr,fg2,fb2,fa),(0,0,fw-fi*20,fh-fi*15))
            self.screen.blit(gs2,(fx+fi*10,fy+fi*8),special_flags=pygame.BLEND_RGBA_ADD)
        for fli in range(5):
            flx=fx+15+fli*18; fly=fy+fh//3
            fla=math.radians(-20+fli*10)+math.sin(self.time*4+fli)*0.3
            flen=20+int(15*math.sin(self.time*3+fli))
            pygame.draw.polygon(self.screen,(int(255*flicker),int(160*pulse),20),
                [(flx-5,fly),(flx+int(math.sin(fla)*flen),fly-flen),(flx+5,fly)])
        gs3=pygame.Surface((300,200),pygame.SRCALPHA)
        pygame.draw.ellipse(gs3,(int(160*pulse),int(80*pulse),20,int(40*pulse)),(0,0,300,200))
        self.screen.blit(gs3,(fx-90,fy+40),special_flags=pygame.BLEND_RGBA_ADD)
        for bx2 in range(0,self.W,90):
            pygame.draw.rect(self.screen,(55,38,20),(bx2,0,22,35))
            pygame.draw.rect(self.screen,(42,28,12),(bx2,0,22,35),1)
        tx=60; ty=self.H//3
        pygame.draw.rect(self.screen,(80,60,30),(tx-3,ty,6,20))
        tp=0.7+0.3*math.sin(self.time*3.8+1.2)
        pygame.draw.polygon(self.screen,(int(220*tp),int(120*tp),20),[(tx-5,ty),(tx,ty-18),(tx+5,ty)])
        tgs=pygame.Surface((50,50),pygame.SRCALPHA)
        pygame.draw.circle(tgs,(int(200*tp),int(110*tp),20,int(50*tp)),(25,25),22)
        self.screen.blit(tgs,(tx-25,ty-28),special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_keeper(self, cx, cy):
        c = self.keeper_color; dark = tuple(max(0,v-50) for v in c); apron = (210,195,165)
        pygame.draw.ellipse(self.screen,c,(cx-38,cy-15,76,95))
        pygame.draw.ellipse(self.screen,dark,(cx-38,cy-15,76,95),2)
        pygame.draw.polygon(self.screen,apron,[(cx-22,cy-10),(cx+22,cy-10),(cx+28,cy+75),(cx-28,cy+75)])
        pygame.draw.polygon(self.screen,(180,165,140),[(cx-22,cy-10),(cx+22,cy-10),(cx+28,cy+75),(cx-28,cy+75)],1)
        pygame.draw.line(self.screen,(180,165,140),(cx-22,cy-10),(cx-38,cy-18),2)
        pygame.draw.line(self.screen,(180,165,140),(cx+22,cy-10),(cx+38,cy-18),2)
        pygame.draw.circle(self.screen,c,(cx,cy-35),32)
        pygame.draw.circle(self.screen,dark,(cx,cy-35),32,2)
        for chx in [cx-15,cx+15]:
            chsurf=pygame.Surface((18,12),pygame.SRCALPHA)
            pygame.draw.ellipse(chsurf,(220,120,100,80),(0,0,18,12))
            self.screen.blit(chsurf,(chx-9,cy-30))
        for ex in [cx-10,cx+10]:
            pygame.draw.circle(self.screen,(45,30,15),(ex,cy-38),5)
            pygame.draw.circle(self.screen,(255,220,180),(ex,cy-38),2)
        pygame.draw.arc(self.screen,dark,(cx-12,cy-32,24,16),math.pi,2*math.pi,3)
        for ex,edir in [(cx-14,-1),(cx+6,1)]:
            pygame.draw.line(self.screen,(100,70,35),(ex,cy-46),(ex+edir*10,cy-43),3)
        pygame.draw.arc(self.screen,(110,80,40),(cx-14,cy-34,14,10),0,math.pi,3)
        pygame.draw.arc(self.screen,(110,80,40),(cx+0,cy-34,14,10),0,math.pi,3)
        mx=cx+42; my=cy+10
        pygame.draw.rect(self.screen,(110,80,40),(mx,my,22,28))
        pygame.draw.rect(self.screen,(80,55,22),(mx,my,22,28),2)
        pygame.draw.arc(self.screen,(80,55,22),(mx+18,my+4,14,16),-math.pi/2,math.pi/2,3)
        foam_s=pygame.Surface((22,10),pygame.SRCALPHA)
        pygame.draw.ellipse(foam_s,(235,228,215,200),(0,0,22,10))
        self.screen.blit(foam_s,(mx,my-4))
        pygame.draw.line(self.screen,c,(cx+36,cy+5),(mx,my+10),8)

    def _draw_rumour_board(self, x, y, w):
        bh = 65
        pygame.draw.rect(self.screen,(100,75,40),(x,y,w,bh))
        pygame.draw.rect(self.screen,(75,55,25),(x,y,w,bh),2)
        for nx2,ny2 in [(x+5,y+5),(x+w-5,y+5),(x+5,y+bh-5),(x+w-5,y+bh-5)]:
            pygame.draw.circle(self.screen,(160,130,55),(nx2,ny2),3)
        pygame.draw.rect(self.screen,(215,202,175),(x+8,y+8,w-16,bh-16))
        pygame.draw.rect(self.screen,(180,165,140),(x+8,y+8,w-16,bh-16),1)
        hdr=self.font_tiny.render("NOTICE BOARD",True,(100,78,38))
        self.screen.blit(hdr,(x+w//2-hdr.get_width()//2,y+10))
        rumour = self.RUMOURS[self._rumour_idx]
        words = rumour.split(); lines = []; cur = ""
        for word in words:
            test = cur+(" " if cur else "")+word
            if self.font_tiny.size(test)[0] < w-24: cur = test
            else: lines.append(cur); cur = word
        if cur: lines.append(cur)
        for li,line in enumerate(lines[:2]):
            ls=self.font_tiny.render(line,True,(65,50,28))
            self.screen.blit(ls,(x+12,y+22+li*14))

    def _draw_hp_bar(self, x, y, w):
        hp=self._player_hp(); mhp=self._player_max_hp()
        lab=self.font_small.render(f"HP: {hp}/{mhp}",True,(200,165,90))
        self.screen.blit(lab,(x,y))
        bw=w-lab.get_width()-12; bx=x+lab.get_width()+12; by=y+3; bh=13
        pygame.draw.rect(self.screen,(35,22,14),(bx,by,bw,bh))
        pygame.draw.rect(self.screen,(65,42,24),(bx,by,bw,bh),1)
        fill=max(0,int(bw*(hp/mhp)))
        if fill>0:
            col=(60,180,60) if hp/mhp>0.5 else (200,160,40) if hp/mhp>0.25 else (200,50,40)
            pygame.draw.rect(self.screen,col,(bx,by,fill,bh))

    def _draw_dialogue_bubble(self, cx, cy):
        lines = self._current_dialogue.split("\n")
        max_w = max(self.font_small.size(l)[0] for l in lines)+20
        bh2 = len(lines)*18+14; bx = cx-max_w//2; by = cy-bh2-20
        pygame.draw.rect(self.screen,(240,228,200),(bx,by,max_w,bh2),border_radius=6)
        pygame.draw.rect(self.screen,(180,150,90),(bx,by,max_w,bh2),2,border_radius=6)
        pygame.draw.polygon(self.screen,(240,228,200),[(cx-8,by+bh2),(cx+8,by+bh2),(cx,by+bh2+14)])
        pygame.draw.line(self.screen,(180,150,90),(cx-8,by+bh2),(cx,by+bh2+14),2)
        pygame.draw.line(self.screen,(180,150,90),(cx+8,by+bh2),(cx,by+bh2+14),2)
        for li,line in enumerate(lines):
            ls=self.font_small.render(line,True,(55,40,20))
            self.screen.blit(ls,(bx+10,by+7+li*18))

    def _draw_options(self, x, y, w, h, ease):
        if ease < 0.8: return
        hp=self._player_hp(); mhp=self._player_max_hp(); gold=self._gold()
        options=[
            {"label":"Light Rest","detail":f"Restore {self.PARTIAL_HEAL} HP","cost":self.PARTIAL_COST,"afford":gold>=self.PARTIAL_COST,"useful":hp<mhp,"icon":(80,160,120)},
            {"label":"Full Rest","detail":"Restore all HP","cost":self.FULL_COST,"afford":gold>=self.FULL_COST,"useful":hp<mhp,"icon":(60,140,200)},
            {"label":"Buy Potion","detail":"Restores 5 HP in combat","cost":self.POTION_COST,"afford":gold>=self.POTION_COST,"useful":True,"icon":(180,60,60)},
            {"label":"Leave","detail":"Head back outside","cost":0,"afford":True,"useful":True,"icon":(120,95,55)},
        ]
        row_h=52; row_w=int(w*0.88); rx=x+20; start_y=y+55
        for i,opt in enumerate(options):
            ry=start_y+i*row_h; is_sel=(i==self.selected); tv=1.0 if is_sel else 0.0
            can=opt["afford"] and opt["useful"]
            bg=pygame.Surface((row_w,row_h-6),pygame.SRCALPHA)
            bg.fill((int(28+20*tv),int(20+15*tv),int(12+8*tv),210))
            self.screen.blit(bg,(rx,ry))
            bc=tuple(int(a+(b-a)*tv) for a,b in zip((55,42,26),(180,145,70))) if can else (35,26,14)
            pygame.draw.rect(self.screen,bc,(rx,ry,row_w,row_h-6),2 if is_sel else 1)
            pygame.draw.circle(self.screen,opt["icon"],(rx+20,ry+(row_h-6)//2),9)
            nc=(220,190,120) if (is_sel and can) else (140,110,65) if can else (75,58,35)
            ns=self.font_medium.render(opt["label"],True,nc)
            self.screen.blit(ns,(rx+38,ry+7))
            ds=self.font_tiny.render(opt["detail"],True,(100,78,45))
            self.screen.blit(ds,(rx+38,ry+7+ns.get_height()+2))
            if opt["cost"]>0:
                cs=self.font_medium.render(f"{opt['cost']}g",True,(220,185,50) if opt["afford"] else (120,70,40))
                self.screen.blit(cs,(rx+row_w-cs.get_width()-10,ry+(row_h-6)//2-cs.get_height()//2))
            elif opt["label"]=="Leave":
                es=self.font_tiny.render("free",True,(80,62,34))
                self.screen.blit(es,(rx+row_w-es.get_width()-10,ry+(row_h-6)//2-es.get_height()//2))
            if is_sel:
                arr=self.font_small.render("▶",True,self.shop_color)
                self.screen.blit(arr,(rx+2,ry+(row_h-6)//2-arr.get_height()//2))
        self._draw_hp_bar(rx,start_y+len(options)*row_h+6,row_w)
        hint=self.font_tiny.render("↑ ↓  select    ENTER  confirm    ESC  leave",True,(70,54,28))
        self.screen.blit(hint,(self.W//2-hint.get_width()//2,y+h-hint.get_height()-10))

    def _draw_message(self):
        if not self._message or self._message_timer<=0: return
        alpha=min(1.0,self._message_timer/0.4)
        col=(120,200,120) if self._msg_good else (200,100,80)
        ms=self.font_small.render(self._message,True,col)
        bg=pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
        bg.fill((14,10,6,int(210*alpha)))
        bx=self.W//2-bg.get_width()//2; by=80
        self.screen.blit(bg,(bx,by)); pygame.draw.rect(self.screen,col,(bx,by,bg.get_width(),bg.get_height()),1)
        ms.set_alpha(int(255*alpha)); self.screen.blit(ms,(bx+10,by+4))

    def _do_action(self, idx):
        hp=self._player_hp(); mhp=self._player_max_hp(); gold=self._gold()
        if idx==0:
            if hp>=mhp: self._message="You are already at full health!"; self._msg_good=False
            elif gold<self.PARTIAL_COST: self._message=f"Need {self.PARTIAL_COST} gold!"; self._msg_good=False
            else:
                self._spend_gold(self.PARTIAL_COST); healed=min(self.PARTIAL_HEAL,mhp-hp)
                self._play_rest_animation(full_rest=False); self._set_hp(hp+healed)
                self._message=f"You rest briefly. +{healed} HP  ({self._player_hp()}/{mhp})"; self._msg_good=True
                import random as _r; self._current_dialogue=_r.choice(self._dialogues)
        elif idx==1:
            if hp>=mhp: self._message="You are already at full health!"; self._msg_good=False
            elif gold<self.FULL_COST: self._message=f"Need {self.FULL_COST} gold!"; self._msg_good=False
            else:
                self._spend_gold(self.FULL_COST); self._play_rest_animation(full_rest=True)
                self._set_hp(mhp); self._message=f"You sleep soundly. Full HP restored!  ({mhp}/{mhp})"; self._msg_good=True
                import random as _r; self._current_dialogue=_r.choice(self._dialogues)
        elif idx==2:
            if gold<self.POTION_COST: self._message=f"Need {self.POTION_COST} gold!"; self._msg_good=False
            else:
                from src.scenes.chest_scene import PotionItem
                self._spend_gold(self.POTION_COST); self.inventory.add(PotionItem())
                self._message="Bought a Healing Potion!"; self._msg_good=True
        elif idx==3:
            return "town"
        self._message_timer=2.5
        return None

    def _play_rest_animation(self, full_rest=False):
        W,H = self.W,self.H; clock = pygame.time.Clock()
        font_med = pygame.font.SysFont("courier new",22,bold=True)
        snapshot = self.screen.copy()
        zzz_positions = [(W//2-20,H//2+20,28,0.0),(W//2+10,H//2,36,0.4),(W//2+40,H//2-30,44,0.8)]
        total = 3.0 if full_rest else 2.2; t = 0.0
        while t < total:
            dt = clock.tick(60)/1000.0; t += dt
            alpha = int(255*(t/0.6)) if t<0.6 else 255 if t<total-0.6 else int(255*((total-t)/0.6))
            self.screen.blit(snapshot,(0,0))
            overlay=pygame.Surface((W,H)); overlay.fill((8,5,3)); overlay.set_alpha(alpha)
            self.screen.blit(overlay,(0,0))
            if 0.5 < t < total-0.4:
                hold_t = t-0.5
                for i,(zx,zy,zsize,zdelay) in enumerate(zzz_positions):
                    age = hold_t-zdelay
                    if age<0: continue
                    cycle = age%1.4
                    if cycle>1.2: continue
                    a2=int(255*min(1.0,(1.0-cycle/1.2))); rise=int(cycle*40)
                    zf=pygame.font.SysFont("courier new",zsize,bold=True)
                    zs=zf.render("Z",True,(180,220,255)); zs.set_alpha(a2)
                    self.screen.blit(zs,(zx,zy-rise))
            if 0.7 < t < total-0.3:
                fade_in=min(1.0,(t-0.7)/0.3); fade_out=min(1.0,(total-0.3-t)/0.3)
                ta=int(255*min(fade_in,fade_out))
                msg="Sleeping deeply..." if full_rest else "Resting..."
                ms=font_med.render(msg,True,(160,185,220)); ms.set_alpha(ta)
                self.screen.blit(ms,(W//2-ms.get_width()//2,H//2+60))
            pygame.display.flip()

    def run(self)->str:
        _leave_hover = 0.0
        while True:
            dt=self.clock.tick(60)/1000.0; self.time+=dt
            self.open_anim=min(self.open_anim+dt,self.OPEN_DUR)
            ease=1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            self._message_timer=max(0.0,self._message_timer-dt)
            self._rumour_timer+=dt
            if self._rumour_timer>=self.RUMOUR_DUR:
                self._rumour_timer=0.0; self._rumour_idx=(self._rumour_idx+1)%len(self.RUMOURS)
            mouse=pygame.mouse.get_pos()
            pw=int(self.W*0.88); ph=int(self.H*0.86); px=self.W//2-pw//2; py=self.H//2-ph//2
            leave_rect = pygame.Rect(px+pw-116, py+10, 100, 28)
            _leave_hover += ((1.0 if leave_rect.collidepoint(mouse) else 0.0) - _leave_hover)*10*dt
            _leave_hover = max(0.0, min(1.0, _leave_hover))
            for event in pygame.event.get():
                if event.type==pygame.QUIT: return "exit"
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: return "town"
                    if event.key==pygame.K_UP: self.selected=max(0,self.selected-1)
                    if event.key==pygame.K_DOWN: self.selected=min(3,self.selected+1)
                    if event.key in (pygame.K_RETURN,pygame.K_SPACE):
                        result=self._do_action(self.selected)
                        if result: return result
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    if leave_rect.collidepoint(mouse): return "town"
            self._draw_background()
            w2=int(pw*ease); h2=int(ph*ease); px2=self.W//2-w2//2; py2=self.H//2-h2//2
            if w2>4:
                bg=pygame.Surface((w2,h2),pygame.SRCALPHA); bg.fill((18,12,7,245))
                self.screen.blit(bg,(px2,py2))
                pygame.draw.rect(self.screen,self.shop_color,(px2,py2,w2,h2),2)
                pygame.draw.rect(self.screen,tuple(max(0,v-40) for v in self.shop_color),(px2+5,py2+5,w2-10,h2-10),1)
                sz=14
                for bx2,by2,dx,dy in [(px2,py2,1,1),(px2+w2,py2,-1,1),(px2,py2+h2,1,-1),(px2+w2,py2+h2,-1,-1)]:
                    pygame.draw.line(self.screen,(185,150,68),(bx2,by2),(bx2+dx*sz,by2),2)
                    pygame.draw.line(self.screen,(185,150,68),(bx2,by2),(bx2,by2+dy*sz),2)
            if ease>0.7:
                title=self.font_title.render("The Rusty Flagon",True,(215,180,105))
                self.screen.blit(title,(self.W//2-title.get_width()//2,py+14))
                pygame.draw.line(self.screen,self.shop_color,(px+24,py+14+title.get_height()+6),(px+pw-24,py+14+title.get_height()+6),1)
                gold_s=self.font_medium.render(f"Gold: {self._gold()}",True,(220,185,60))
                # Gold sits left of LEAVE button
                self.screen.blit(gold_s,(px+pw-gold_s.get_width()-128,py+16))
                # LEAVE button — top right, smithy style
                def _lc(a,b,h=_leave_hover): return tuple(int(a[j]+(b[j]-a[j])*h) for j in range(3))
                lbg=pygame.Surface((100,28),pygame.SRCALPHA)
                lbg.fill((int(18+30*_leave_hover),int(12+22*_leave_hover),int(7+14*_leave_hover),200))
                self.screen.blit(lbg,leave_rect.topleft)
                pygame.draw.rect(self.screen,_lc((60,44,24),(160,125,60)),leave_rect,2)
                lbl=self.font_small.render("LEAVE",True,_lc((120,90,45),(210,175,90)))
                self.screen.blit(lbl,(leave_rect.centerx-lbl.get_width()//2,leave_rect.centery-lbl.get_height()//2))
                left_w=int(pw*0.55)
                self._draw_options(px,py,left_w,ph,ease)
                div_x=px+left_w
                pygame.draw.line(self.screen,tuple(max(0,v-30) for v in self.shop_color),(div_x,py+40),(div_x,py+ph-20),1)
                right_cx=div_x+(pw-left_w)//2
                keeper_cx=right_cx; keeper_cy=py+ph*2//3
                self._draw_keeper(keeper_cx,keeper_cy)
                kn=self.font_tiny.render("Borin, Innkeeper",True,(130,100,55))
                self.screen.blit(kn,(keeper_cx-kn.get_width()//2,keeper_cy+95))
                self._draw_dialogue_bubble(keeper_cx,keeper_cy-45)
                board_x=div_x+12; board_w=pw-left_w-24
                self._draw_rumour_board(board_x,py+48,board_w)
            self._draw_message()
            pygame.display.flip()


# ===========================================================================
# GeneralShopScene — full rework (A + B + D + rumours)
# ===========================================================================

MIRA_RUMOURS = [
    "Heard the dungeon goes deeper than anyone's mapped. Nasty down there.",
    "Those goblins have been stealing stock from the market stalls again.",
    "A merchant from the capital stopped by — said iron's worth double up north.",
    "The dungeon keys I sell? I cast them myself. Old family trade.",
    "Don't let anyone tell you potions are overpriced. Ingredients aren't cheap.",
    "Three explorers bought out my key stock last week. Haven't seen them since.",
    "The candles I stock burn longer than the cheap ones at the market.",
    "Word from a passing ranger — there's something big and old in those lower halls.",
]

# Category tabs for the shop
SHOP_CATEGORIES = ["ALL", "CONSUMABLES", "EQUIPMENT", "KEYS"]

# Restock seed — changes each time player returns from dungeon
_SHOP_RESTOCK_SEED = [random.randint(0, 9999)]

def restock_general_shop():
    """Call this when the player returns from the dungeon to trigger a restock."""
    _SHOP_RESTOCK_SEED[0] = random.randint(0, 9999)


class GeneralShopScene:
    """
    Mira's Sundries — fully reworked general shop.
    Features:
      A) Illustrated interior with Mira NPC, counter, shelves, props
      B) Category tabs: ALL / CONSUMABLES / EQUIPMENT / KEYS
      D) Restocking system — limited stock refreshes each dungeon run
      + Rumour panel on the right side
    """

    def __init__(self, screen, inventory):
        self.screen    = screen
        self.W, self.H = screen.get_size()
        self.clock     = pygame.time.Clock()
        self.time      = 0.0
        self.inventory = inventory

        self.font_title  = pygame.font.SysFont("courier new", 26, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 16, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 13)
        self.font_tiny   = pygame.font.SysFont("courier new", 11)

        self.shop_color  = (65, 135, 80)
        self.shop_color2 = (55, 115, 68)   # darker variant

        # State
        self.mode         = "buy"   # "buy" | "sell"
        self.category_idx = 0       # index into SHOP_CATEGORIES
        self.selected     = 0
        self.open_anim    = 0.0
        self.OPEN_DUR     = 0.4
        self.message      = ""
        self.message_timer = 0.0
        self.msg_good     = True

        # Hover states
        self._cat_hovers  = [0.0] * len(SHOP_CATEGORIES)
        self._mode_hover  = [0.0, 0.0]   # buy, sell
        self._back_hover  = 0.0

        # Extra quest rumours (append to add quest hooks)
        self._extra_rumours: list[str] = []

        # Dialogue
        self._dialogues = [
            "Welcome to Mira's!\nWhat'll it be?",
            "Fair prices, good stock.\nThat's my promise.",
            "Keys are hard to come by.\nBuy while I have 'em.",
            "Running low on potions?\nI've got plenty.",
            "Everything in this shop\nI sourced myself.",
            "Stay safe out there.\nI need the business.",
        ]
        self._dialogue = random.choice(self._dialogues)

        # Rumour cycling
        self._rumour_idx   = random.randint(0, len(MIRA_RUMOURS)-1)
        self._rumour_timer = 0.0
        self.RUMOUR_DUR    = 7.0

        # Build stock using restock seed for deterministic restocking
        self._build_stock()

        # Pre-bake background (expensive gradients done once)
        self._bg_surf = self._build_background()

    # ------------------------------------------------------------------ #
    # Stock building — Option D: seed-based restocking
    # ------------------------------------------------------------------ #

    def _build_stock(self):
        from src.scenes.chest_scene import PotionItem, KeyItem, CandleItem, IronIngotItem
        rng = random.Random(_SHOP_RESTOCK_SEED[0])

        # Consumables — always available, varying stock
        potion_stock = rng.randint(3, 8)
        candle_stock = rng.randint(2, 6)
        ingot_stock  = rng.randint(1, 4)

        # Keys — limited, random availability
        key_defs = [
            ("key_ab", "Door Key (AB)", 18),
            ("key_ad", "Door Key (AD)", 18),
            ("key_ef", "Door Key (EF)", 20),
            ("key_dg", "Door Key (DG)", 20),
        ]
        # Only 2-3 key types available per restock
        available_keys = rng.sample(key_defs, rng.randint(2, 3))
        key_stock = rng.randint(1, 3)

        self.all_items = [
            ShopItem(PotionItem,  6,  potion_stock, "Restores 5 HP in combat.", "consumables"),
            ShopItem(CandleItem,  3,  candle_stock, "A wax candle. Lights your way.", "consumables"),
            ShopItem(lambda: IronIngotItem(), 12, ingot_stock, "Iron ingot. Used for upgrades.", "equipment"),
        ]

        for key_id, key_name, key_price in available_keys:
            kid = key_id  # capture for lambda
            item = ShopItem(lambda k=kid: KeyItem(k), key_price, key_stock,
                            "Opens a locked dungeon door.", "keys")
            item._instance._name = key_name
            self.all_items.append(item)

        # Mark new items (all items are "new" on a fresh restock)
        for item in self.all_items:
            item.is_new = True

    def _filtered_items(self):
        cat = SHOP_CATEGORIES[self.category_idx]
        if cat == "ALL":
            return self.all_items
        return [it for it in self.all_items if it.category == cat.lower()]

    # ------------------------------------------------------------------ #
    # Gold helpers
    # ------------------------------------------------------------------ #

    def _gold(self):
        from src.scenes.chest_scene import GoldItem
        return sum(self.inventory.stack_count(it)
                   for it in self.inventory.items if isinstance(it, GoldItem))

    def _spend_gold(self, amount):
        from src.scenes.chest_scene import GoldItem
        gi = next((it for it in self.inventory.items if isinstance(it, GoldItem)), None)
        if gi is None: return False
        total = self.inventory.stack_count(gi)
        if total < amount: return False
        self.inventory.remove(gi)
        if total-amount > 0: self.inventory.add(GoldItem(total-amount))
        return True

    def _sell_value(self, item):
        prices = {"Healing Potion":4,"Dungeon Key":8,"Candle":1,"Iron Ingot":6,
                  "Iron Shield":18,"Sun Sword":25,"Sword":10,"Gold":0,"Exit Key":0}
        return prices.get(item.name, 2)

    # ------------------------------------------------------------------ #
    # Background — pre-baked shop interior
    # ------------------------------------------------------------------ #

    def _build_background(self):
        surf = pygame.Surface((self.W, self.H))
        W, H = self.W, self.H

        # Warm green-tinted interior — gradient via 1px strip
        strip = pygame.Surface((1, H))
        for y in range(H):
            t = y/H
            r = int(14+10*t); g = int(20+14*t); b = int(12+8*t)
            strip.set_at((0, y), (r, g, b))
        surf.blit(pygame.transform.scale(strip, (W, H)), (0, 0))

        # Wooden floor planks (bottom third)
        floor_y = H*2//3
        pygame.draw.rect(surf, (62, 44, 22), (0, floor_y, W, H-floor_y))
        for fx in range(0, W, 48):
            v = ((fx // 48) * 7 + 3) % 9 - 4
            pygame.draw.rect(surf, (58+v, 40+v, 18+v), (fx, floor_y, 46, H-floor_y))
            pygame.draw.line(surf, (45, 30, 12), (fx, floor_y), (fx, H), 1)

        # Back wall shelves (behind counter)
        shelf_y = H//5
        for row in range(3):
            sy = shelf_y + row*60
            pygame.draw.rect(surf, (78, 55, 28), (W//4, sy, W//2, 10))
            pygame.draw.rect(surf, (55, 38, 16), (W//4, sy, W//2, 10), 1)
            # Items on shelf — decorative pots and bottles
            rng2 = random.Random(row*17)
            for col in range(6):
                ix = W//4 + 20 + col*(W//12)
                iy = sy - 18
                shape = rng2.choice(["pot","bottle","box"])
                col_v = rng2.choice([(140,80,60),(80,120,100),(160,140,60),(100,80,140)])
                if shape == "pot":
                    pygame.draw.ellipse(surf, col_v, (ix-7, iy-8, 14, 18))
                    pygame.draw.rect(surf, col_v, (ix-4, iy-14, 8, 8))
                elif shape == "bottle":
                    pygame.draw.rect(surf, col_v, (ix-4, iy-6, 8, 16))
                    pygame.draw.rect(surf, col_v, (ix-2, iy-14, 4, 10))
                else:
                    pygame.draw.rect(surf, col_v, (ix-7, iy-10, 14, 12))

        # Counter (horizontal bar across lower-mid screen)
        counter_y = H*3//5
        counter_h = 32
        pygame.draw.rect(surf, (88, 62, 30), (W//6, counter_y, W*2//3, counter_h))
        pygame.draw.rect(surf, (110, 80, 40), (W//6, counter_y, W*2//3, 6))   # top edge highlight
        pygame.draw.rect(surf, (60, 40, 16), (W//6, counter_y, W*2//3, counter_h), 2)
        # Counter legs
        for lx in [W//6+12, W*5//6-16]:
            pygame.draw.rect(surf, (72, 50, 22), (lx, counter_y+counter_h, 12, H-counter_y-counter_h))

        # Wall torch left side
        tx = W//8; ty = H//3
        pygame.draw.rect(surf, (80, 58, 28), (tx-3, ty, 6, 20))
        pygame.draw.circle(surf, (90, 65, 32), (tx, ty-4), 8)

        # Window right side — light coming in
        win_x = W*7//8 - 30; win_y = H//4
        pygame.draw.rect(surf, (42, 32, 16), (win_x-4, win_y-4, 68, 88))
        pygame.draw.rect(surf, (155, 200, 210), (win_x, win_y, 60, 80))
        pygame.draw.line(surf, (42, 32, 16), (win_x+30, win_y), (win_x+30, win_y+80), 3)
        pygame.draw.line(surf, (42, 32, 16), (win_x, win_y+40), (win_x+60, win_y+40), 3)

        return surf

    # ------------------------------------------------------------------ #
    # Mira NPC drawing
    # ------------------------------------------------------------------ #

    def _draw_mira(self, cx, cy):
        """Mira — slender, practical, apron, hair up."""
        skin = (210, 175, 135)
        dark = (160, 120, 85)
        dress= (75, 115, 70)    # green dress matching shop colour
        apron= (215, 205, 185)
        hair = (90, 58, 28)

        # Body
        pygame.draw.ellipse(self.screen, dress, (cx-22, cy-10, 44, 80))
        pygame.draw.ellipse(self.screen, tuple(max(0,v-20) for v in dress), (cx-22, cy-10, 44, 80), 2)

        # Apron
        pygame.draw.polygon(self.screen, apron, [
            (cx-14, cy-5), (cx+14, cy-5), (cx+18, cy+65), (cx-18, cy+65)])
        pygame.draw.polygon(self.screen, (185, 175, 155), [
            (cx-14, cy-5), (cx+14, cy-5), (cx+18, cy+65), (cx-18, cy+65)], 1)
        # Apron pocket
        pygame.draw.rect(self.screen, (185, 175, 155), (cx-10, cy+28, 20, 16))
        pygame.draw.rect(self.screen, (160, 150, 130), (cx-10, cy+28, 20, 16), 1)

        # Arms
        pygame.draw.line(self.screen, skin, (cx-22, cy+10), (cx-36, cy+40), 7)
        pygame.draw.line(self.screen, skin, (cx+22, cy+10), (cx+36, cy+35), 7)

        # Head
        pygame.draw.circle(self.screen, skin, (cx, cy-28), 24)
        pygame.draw.circle(self.screen, dark, (cx, cy-28), 24, 2)

        # Hair bun up top
        pygame.draw.circle(self.screen, hair, (cx, cy-52), 14)
        pygame.draw.circle(self.screen, hair, (cx-10, cy-50), 10)
        pygame.draw.circle(self.screen, hair, (cx+10, cy-50), 10)
        pygame.draw.circle(self.screen, tuple(min(255,v+20) for v in hair), (cx, cy-54), 6)

        # Side hair strands
        pygame.draw.line(self.screen, hair, (cx-20, cy-38), (cx-24, cy-18), 4)
        pygame.draw.line(self.screen, hair, (cx+20, cy-38), (cx+24, cy-18), 4)

        # Eyes
        for ex in [cx-8, cx+8]:
            pygame.draw.circle(self.screen, (55, 35, 18), (ex, cy-30), 4)
            pygame.draw.circle(self.screen, (220, 200, 170), (ex, cy-30), 2)
        # Eyebrows — neat
        for ex, edir in [(cx-12, 1), (cx+4, -1)]:
            pygame.draw.line(self.screen, hair, (ex, cy-38), (ex+edir*8, cy-36), 2)

        # Smile
        pygame.draw.arc(self.screen, dark, (cx-8, cy-24, 16, 10), math.pi, 2*math.pi, 2)

        # Item in hand — small potion bottle
        bx = cx+38; by = cy+30
        pygame.draw.rect(self.screen, (160, 55, 55), (bx-3, by, 6, 12))
        pygame.draw.rect(self.screen, (160, 55, 55), (bx-2, by-6, 4, 8))
        pygame.draw.circle(self.screen, (200, 80, 80), (bx, by-6), 3)

    def _draw_dialogue_bubble(self, cx, cy):
        lines = self._dialogue.split("\n")
        max_w = max(self.font_small.size(l)[0] for l in lines) + 20
        bh = len(lines)*18 + 14
        bx = cx - max_w//2; by = cy - bh - 20
        pygame.draw.rect(self.screen, (240, 232, 210), (bx, by, max_w, bh), border_radius=6)
        pygame.draw.rect(self.screen, (150, 180, 130), (bx, by, max_w, bh), 2, border_radius=6)
        pygame.draw.polygon(self.screen, (240, 232, 210),
            [(cx-8, by+bh), (cx+8, by+bh), (cx, by+bh+14)])
        pygame.draw.line(self.screen, (150, 180, 130), (cx-8, by+bh), (cx, by+bh+14), 2)
        pygame.draw.line(self.screen, (150, 180, 130), (cx+8, by+bh), (cx, by+bh+14), 2)
        for li, line in enumerate(lines):
            ls = self.font_small.render(line, True, (45, 65, 40))
            self.screen.blit(ls, (bx+10, by+7+li*18))

    # ------------------------------------------------------------------ #
    # Rumour panel — Option + quest hooks
    # ------------------------------------------------------------------ #

    def _draw_rumours(self, rx, ry, rw, rh):
        rumours = MIRA_RUMOURS + self._extra_rumours

        bg = pygame.Surface((rw, rh), pygame.SRCALPHA)
        bg.fill((14, 22, 14, 210))
        self.screen.blit(bg, (rx, ry))
        pygame.draw.rect(self.screen, (55, 100, 55), (rx, ry, rw, rh), 1)

        hdr = self.font_small.render("— RUMOURS —", True, (100, 170, 100))
        self.screen.blit(hdr, (rx + rw//2 - hdr.get_width()//2, ry + 8))
        pygame.draw.line(self.screen, (45, 80, 45),
                         (rx+8, ry+24), (rx+rw-8, ry+24), 1)

        entry_y = ry + 32
        line_h  = self.font_tiny.get_height() + 3

        for i, rumour in enumerate(rumours):
            words = rumour.split(); lines_out = []; cur = ""
            for w in words:
                test = cur + (" " if cur else "") + w
                if self.font_tiny.size(test)[0] < rw - 20: cur = test
                else: lines_out.append(cur); cur = w
            if cur: lines_out.append(cur)

            block_h = len(lines_out) * line_h + 6
            if entry_y + block_h > ry + rh - 14: break

            dot_col = (80, 160, 80) if i < len(MIRA_RUMOURS) else (100, 200, 130)
            pygame.draw.circle(self.screen, dot_col, (rx+10, entry_y + line_h//2), 3)

            for li, line in enumerate(lines_out):
                col = (155, 200, 140) if i < len(MIRA_RUMOURS) else (120, 200, 155)
                ls  = self.font_tiny.render(line, True, col)
                self.screen.blit(ls, (rx+18, entry_y + li*line_h))
            entry_y += block_h + 4

        if entry_y > ry + rh - 14:
            more = self.font_tiny.render("▼ more", True, (55, 90, 55))
            self.screen.blit(more, (rx + rw//2 - more.get_width()//2, ry+rh-14))

    # ------------------------------------------------------------------ #
    # Panel & layout
    # ------------------------------------------------------------------ #

    def _panel_rect(self):
        pw = int(self.W * 0.90)
        ph = int(self.H * 0.86)
        px = (self.W - pw) // 2
        py = (self.H - ph) // 2
        return px, py, pw, ph

    def _draw_panel(self, ease):
        px, py, pw, ph = self._panel_rect()
        w = int(pw*ease); h = int(ph*ease)
        x = self.W//2 - w//2; y = self.H//2 - h//2
        if w < 4: return
        sh = pygame.Surface((w+14, h+14), pygame.SRCALPHA)
        sh.fill((0,0,0,110))
        self.screen.blit(sh, (x-7, y-7))
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((12, 18, 12, 250))
        self.screen.blit(panel, (x, y))
        pygame.draw.rect(self.screen, self.shop_color, (x, y, w, h), 2)
        pygame.draw.rect(self.screen, self.shop_color2, (x+5, y+5, w-10, h-10), 1)
        sz = 14
        for bx, by, dx, dy in [(x,y,1,1),(x+w,y,-1,1),(x,y+h,1,-1),(x+w,y+h,-1,-1)]:
            pygame.draw.line(self.screen, (100, 180, 100), (bx, by), (bx+dx*sz, by), 2)
            pygame.draw.line(self.screen, (100, 180, 100), (bx, by), (bx, by+dy*sz), 2)

    def _draw_header(self, px, py, pw, ease):
        if ease < 0.8: return
        title = self.font_title.render("Mira's Sundries", True, (140, 210, 130))
        self.screen.blit(title, (self.W//2 - title.get_width()//2, py+10))
        pygame.draw.line(self.screen, self.shop_color,
                         (px+20, py+10+title.get_height()+4),
                         (px+pw-20, py+10+title.get_height()+4), 1)
        gs = self.font_medium.render(f"Gold: {self._gold()}", True, (220,185,60))
        self.screen.blit(gs, (px+pw-gs.get_width()-18, py+12))

    def _draw_mode_tabs(self, px, py, ease):
        """BUY / SELL mode switch."""
        if ease < 0.8: return
        tab_y = py + 46
        for i, (label, mode) in enumerate([("BUY","buy"),("SELL","sell")]):
            tx = px + 20 + i*100
            is_sel = self.mode == mode
            col = self.shop_color if is_sel else (35, 55, 35)
            bg = pygame.Surface((90, 28), pygame.SRCALPHA)
            bg.fill((*col, 220) if is_sel else (20, 32, 20, 180))
            self.screen.blit(bg, (tx, tab_y))
            pygame.draw.rect(self.screen, col, (tx, tab_y, 90, 28), 2)
            lbl = self.font_small.render(label, True,
                (210, 240, 190) if is_sel else (80, 120, 80))
            self.screen.blit(lbl, (tx+45-lbl.get_width()//2, tab_y+14-lbl.get_height()//2))

        # LEAVE button
        bx = px + self._panel_rect()[2] - 110
        bh = self._back_hover
        bg = pygame.Surface((96, 28), pygame.SRCALPHA)
        bg.fill((int(14+28*bh), int(22+36*bh), int(14+20*bh), 200))
        self.screen.blit(bg, (bx, tab_y))
        def lc(a,b): return tuple(int(a[j]+(b[j]-a[j])*bh) for j in range(3))
        pygame.draw.rect(self.screen, lc((45,70,45),(120,180,100)), (bx, tab_y, 96, 28), 2)
        bl = self.font_small.render("LEAVE", True, lc((90,130,90),(190,230,160)))
        self.screen.blit(bl, (bx+48-bl.get_width()//2, tab_y+14-bl.get_height()//2))

    def _draw_category_tabs(self, px, py, pw, ease):
        """Category filter tabs: ALL / CONSUMABLES / EQUIPMENT / KEYS."""
        if ease < 0.8: return
        tab_y = py + 82
        content_w = int(pw * 0.62)   # tabs only span the left content column
        tab_w = (content_w - 20) // len(SHOP_CATEGORIES)
        mouse = pygame.mouse.get_pos()

        for i, cat in enumerate(SHOP_CATEGORIES):
            tx = px + 20 + i * tab_w
            is_sel = (i == self.category_idx)
            hov = self._cat_hovers[i]

            col    = self.shop_color if is_sel else (30, 50, 30)
            bg     = pygame.Surface((tab_w-4, 24), pygame.SRCALPHA)
            bg.fill((*col, 220) if is_sel else (int(18+12*hov), int(28+18*hov), int(18+12*hov), 180))
            self.screen.blit(bg, (tx+2, tab_y))
            pygame.draw.rect(self.screen, col, (tx+2, tab_y, tab_w-4, 24),
                             2 if is_sel else 1)

            # Count items in this category
            count = len(self._filtered_items()) if is_sel else \
                    len([it for it in self.all_items
                         if cat=="ALL" or it.category==cat.lower()])
            label = cat if count == 0 else f"{cat} ({count})"
            lbl = self.font_tiny.render(label, True,
                (210, 240, 180) if is_sel else (80, 120, 75))
            self.screen.blit(lbl, (tx+tab_w//2-lbl.get_width()//2, tab_y+12-lbl.get_height()//2))

    # ------------------------------------------------------------------ #
    # Item grid (Option A — card-style)
    # ------------------------------------------------------------------ #

    def _draw_buy_grid(self, px, py, pw, ph):
        items  = self._filtered_items()
        gold   = self._gold()
        mouse  = pygame.mouse.get_pos()

        # Content area: left 62% of panel, below category tabs
        content_x = px + 16
        content_y = py + 114
        content_w = int(pw * 0.62)
        content_h = ph - 114 - 36

        # Card grid: 2 columns
        cols    = 2
        gap     = 10
        card_w  = (content_w - gap*(cols+1)) // cols
        card_h  = 72
        rows_visible = content_h // (card_h + gap)

        if not items:
            ns = self.font_small.render("Nothing in this category.", True, (80, 120, 75))
            self.screen.blit(ns, (content_x + gap, content_y + 20))
        else:
            for i, si in enumerate(items):
                col_i  = i % cols
                row_i  = i // cols
                if row_i >= rows_visible: break

                cx2 = content_x + gap + col_i*(card_w+gap)
                cy2 = content_y + row_i*(card_h+gap)
                is_sel   = (i == self.selected) and self.mode == "buy"
                can_buy  = gold >= si.price and si.in_stock()
                hovering = pygame.Rect(cx2, cy2, card_w, card_h).collidepoint(mouse)
                active   = is_sel or hovering

                # Card background
                card_bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                if is_sel:
                    card_bg.fill((25, 45, 25, 230))
                elif hovering:
                    card_bg.fill((20, 38, 20, 210))
                else:
                    card_bg.fill((14, 24, 14, 190))
                self.screen.blit(card_bg, (cx2, cy2))

                bc = self.shop_color if (active and can_buy) else \
                     (60, 90, 60) if active else (32, 52, 32)
                pygame.draw.rect(self.screen, bc, (cx2, cy2, card_w, card_h),
                                 2 if active else 1)

                # NEW badge
                if si.is_new and si.in_stock():
                    nb = self.font_tiny.render("NEW", True, (255, 220, 80))
                    nb_bg = pygame.Surface((nb.get_width()+6, nb.get_height()+2), pygame.SRCALPHA)
                    nb_bg.fill((100, 80, 0, 200))
                    self.screen.blit(nb_bg, (cx2+card_w-nb.get_width()-10, cy2+4))
                    self.screen.blit(nb,    (cx2+card_w-nb.get_width()-7,  cy2+5))

                # Icon
                icon_size = 40
                si.draw_icon(self.screen, cx2+28, cy2+card_h//2, icon_size)

                # Name
                nc = (210, 240, 180) if (active and can_buy) else \
                     (150, 195, 130) if can_buy else (70, 100, 65)
                ns2 = self.font_medium.render(si.name, True, nc)
                self.screen.blit(ns2, (cx2+58, cy2+10))

                # Description
                ds = self.font_tiny.render(si.description, True, (90, 130, 85))
                self.screen.blit(ds, (cx2+58, cy2+10+ns2.get_height()+2))

                # Price
                if si.stock == 0:
                    oos = self.font_tiny.render("OUT OF STOCK", True, (160, 70, 55))
                    self.screen.blit(oos, (cx2+58, cy2+card_h-oos.get_height()-8))
                else:
                    pc = (220, 190, 55) if can_buy else (110, 80, 40)
                    ps = self.font_medium.render(f"{si.price}g", True, pc)
                    self.screen.blit(ps, (cx2+card_w-ps.get_width()-10,
                                          cy2+card_h-ps.get_height()-8))
                    if si.stock > 0:
                        stk = self.font_tiny.render(f"x{si.stock}", True, (100, 150, 95))
                        self.screen.blit(stk, (cx2+card_w-stk.get_width()-10,
                                               cy2+card_h-ps.get_height()-stk.get_height()-10))

        hint = self.font_tiny.render(
            "↑ ↓ ← →  navigate    ENTER / click  buy    TAB  sell    ESC  leave",
            True, (55, 90, 55))
        self.screen.blit(hint, (content_x, py+ph-hint.get_height()-8))

    def _draw_sell_list(self, px, py, pw, ph):
        from src.scenes.chest_scene import GoldItem, ExitKeyItem
        items = [it for it in self.inventory.items
                 if not isinstance(it, (GoldItem, ExitKeyItem))]

        content_x = px + 16
        content_y = py + 114
        content_w = int(pw * 0.62)
        row_h = 58; row_w = content_w - 20

        sell_prices = {"Healing Potion":4,"Dungeon Key":8,"Candle":1,"Iron Ingot":6,
                       "Iron Shield":18,"Sun Sword":25,"Sword":10}

        if not items:
            ns = self.font_small.render("Nothing to sell.", True, (80, 120, 75))
            self.screen.blit(ns, (content_x+10, content_y+20))
        else:
            for i, item in enumerate(items):
                ry = content_y + i*row_h
                is_sel = (i == self.selected)
                price = sell_prices.get(item.name, 2)

                bg = pygame.Surface((row_w, row_h-4), pygame.SRCALPHA)
                bg.fill((25,40,25,220) if is_sel else (14,22,14,180))
                self.screen.blit(bg, (content_x+10, ry))
                bc = self.shop_color if is_sel else (35, 58, 35)
                pygame.draw.rect(self.screen, bc, (content_x+10, ry, row_w, row_h-4), 2 if is_sel else 1)

                item.draw_icon(self.screen, content_x+38, ry+row_h//2-4, 36)
                nc = (210, 240, 180) if is_sel else (140, 185, 120)
                stack_n = self.inventory.stack_count(item)
                name_l = f"{item.name} (x{stack_n})" if getattr(item,'stackable',False) and stack_n>1 else item.name
                ns2 = self.font_medium.render(name_l, True, nc)
                self.screen.blit(ns2, (content_x+66, ry+8))
                ds = self.font_tiny.render(item.description, True, (90, 130, 85))
                self.screen.blit(ds, (content_x+66, ry+8+ns2.get_height()+2))
                ps = self.font_medium.render(f"{price}g each", True, (180, 160, 50))
                self.screen.blit(ps, (content_x+10+row_w-ps.get_width()-10,
                                      ry+row_h//2-ps.get_height()//2-2))
                if is_sel:
                    arr = self.font_small.render("▶", True, self.shop_color)
                    self.screen.blit(arr, (content_x+12, ry+row_h//2-arr.get_height()//2-2))

        hint = self.font_tiny.render(
            "↑ ↓  select    ENTER / click  sell    TAB  buy    ESC  leave",
            True, (55, 90, 55))
        self.screen.blit(hint, (content_x, py+ph-hint.get_height()-8))

    # ------------------------------------------------------------------ #
    # Message
    # ------------------------------------------------------------------ #

    def _draw_message(self):
        if not self.message or self.message_timer <= 0: return
        alpha = min(1.0, self.message_timer/0.4)
        col = (100, 200, 100) if self.msg_good else (200, 90, 70)
        ms = self.font_small.render(self.message, True, col)
        bg = pygame.Surface((ms.get_width()+20, ms.get_height()+8), pygame.SRCALPHA)
        bg.fill((10, 18, 10, int(220*alpha)))
        bx = self.W//2 - bg.get_width()//2; by = 72
        self.screen.blit(bg, (bx, by))
        pygame.draw.rect(self.screen, col, (bx, by, bg.get_width(), bg.get_height()), 1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms, (bx+10, by+4))

    # ------------------------------------------------------------------ #
    # Input helpers
    # ------------------------------------------------------------------ #

    def _buy_selected(self):
        items = self._filtered_items()
        if not items: return
        si = items[self.selected]
        if not si.in_stock():
            self.message = "Out of stock!"; self.msg_good = False
        elif self._gold() < si.price:
            self.message = f"Need {si.price}g — you have {self._gold()}g!"; self.msg_good = False
        else:
            if self._spend_gold(si.price):
                self.inventory.add(si.buy())
                si.is_new = False
                self.message = f"Bought {si.name} for {si.price}g!"; self.msg_good = True
                self._dialogue = random.choice(self._dialogues)
        self.message_timer = 2.5

    def _sell_selected(self):
        from src.scenes.chest_scene import GoldItem, ExitKeyItem
        items = [it for it in self.inventory.items if not isinstance(it,(GoldItem,ExitKeyItem))]
        if not items: return
        item = items[self.selected]
        sell_prices = {"Healing Potion":4,"Dungeon Key":8,"Candle":1,"Iron Ingot":6,
                       "Iron Shield":18,"Sun Sword":25,"Sword":10,"Gold":0,"Exit Key":0}
        price = sell_prices.get(item.name, 2)
        if price == 0:
            self.message = "Can't sell that here."; self.msg_good = False
        else:
            from src.scenes.chest_scene import GoldItem
            if getattr(item,'stackable',False): self.inventory.remove_one(type(item))
            else: self.inventory.remove(item)
            self.inventory.add(GoldItem(price))
            self.message = f"Sold {item.name} for {price}g!"; self.msg_good = True
        self.message_timer = 2.5
        from src.scenes.chest_scene import GoldItem, ExitKeyItem
        remaining = [it for it in self.inventory.items if not isinstance(it,(GoldItem,ExitKeyItem))]
        self.selected = max(0, min(self.selected, len(remaining)-1))

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while True:
            dt = self.clock.tick(60)/1000.0
            self.time += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            ease = 1-(1-min(1.0, self.open_anim/self.OPEN_DUR))**3
            self.message_timer = max(0.0, self.message_timer-dt)
            self._rumour_timer += dt
            if self._rumour_timer >= self.RUMOUR_DUR:
                self._rumour_timer = 0.0
                self._rumour_idx = (self._rumour_idx+1) % len(MIRA_RUMOURS + self._extra_rumours)
            mouse = pygame.mouse.get_pos()

            px, py, pw, ph = self._panel_rect()

            # Update hovers
            self._back_hover += ((1.0 if pygame.Rect(px+pw-110, py+46, 96, 28).collidepoint(mouse) else 0.0)
                                 - self._back_hover) * 10*dt
            self._back_hover = max(0.0, min(1.0, self._back_hover))

            tab_y = py + 82; tab_w = (int(pw*0.62) - 20) // len(SHOP_CATEGORIES)
            for i in range(len(SHOP_CATEGORIES)):
                tx = px + 20 + i*tab_w
                tgt = 1.0 if pygame.Rect(tx+2, tab_y, tab_w-4, 24).collidepoint(mouse) else 0.0
                self._cat_hovers[i] += (tgt - self._cat_hovers[i]) * 10*dt
                self._cat_hovers[i] = max(0.0, min(1.0, self._cat_hovers[i]))

            items = self._filtered_items()
            cols = 2

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "exit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: return "town"
                    if event.key == pygame.K_TAB:
                        self.mode = "sell" if self.mode=="buy" else "buy"
                        self.selected = 0
                    if event.key == pygame.K_LEFT and self.mode=="buy":
                        self.category_idx = (self.category_idx-1) % len(SHOP_CATEGORIES)
                        self.selected = 0
                    if event.key == pygame.K_RIGHT and self.mode=="buy":
                        self.category_idx = (self.category_idx+1) % len(SHOP_CATEGORIES)
                        self.selected = 0
                    if self.mode == "buy":
                        if event.key == pygame.K_UP and len(items)>0:
                            self.selected = max(0, self.selected-cols)
                        if event.key == pygame.K_DOWN and len(items)>0:
                            self.selected = min(len(items)-1, self.selected+cols)
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self._buy_selected()
                    else:
                        if event.key == pygame.K_UP:
                            self.selected = max(0, self.selected-1)
                        if event.key == pygame.K_DOWN:
                            from src.scenes.chest_scene import GoldItem, ExitKeyItem
                            sell_items = [it for it in self.inventory.items if not isinstance(it,(GoldItem,ExitKeyItem))]
                            self.selected = min(len(sell_items)-1, self.selected+1)
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self._sell_selected()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Leave button
                    if pygame.Rect(px+pw-110, py+46, 96, 28).collidepoint(mouse):
                        return "town"
                    # Mode tabs
                    for i, mode in enumerate(["buy","sell"]):
                        if pygame.Rect(px+20+i*100, py+46, 90, 28).collidepoint(mouse):
                            self.mode = mode; self.selected = 0
                    # Category tabs
                    for i in range(len(SHOP_CATEGORIES)):
                        tx = px + 20 + i*tab_w
                        if pygame.Rect(tx+2, tab_y, tab_w-4, 24).collidepoint(mouse):
                            self.category_idx = i; self.selected = 0
                    # Buy grid clicks
                    if self.mode == "buy":
                        gap = 10
                        card_w = (int(pw*0.62) - gap*(cols+1)) // cols
                        card_h = 72; gap = 10
                        content_x = px+16; content_y = py+114
                        for i, si in enumerate(items):
                            col_i = i%cols; row_i = i//cols
                            cx2 = content_x+gap+col_i*(card_w+gap)
                            cy2 = content_y+row_i*(card_h+gap)
                            if pygame.Rect(cx2,cy2,card_w,card_h).collidepoint(mouse):
                                if self.selected == i:
                                    self._buy_selected()
                                else:
                                    self.selected = i
                    else:
                        from src.scenes.chest_scene import GoldItem, ExitKeyItem
                        sell_items = [it for it in self.inventory.items if not isinstance(it,(GoldItem,ExitKeyItem))]
                        content_x = px+16; content_y = py+114; row_h = 58
                        row_w = int(pw*0.62)-20
                        for i, item in enumerate(sell_items):
                            ry = content_y+i*row_h
                            if pygame.Rect(content_x+10,ry,row_w,row_h-4).collidepoint(mouse):
                                if self.selected == i:
                                    self._sell_selected()
                                else:
                                    self.selected = i

            # ── Draw ──────────────────────────────────────────────────── #
            # Background interior (pre-baked)
            self.screen.blit(self._bg_surf, (0, 0))

            # Animated torch flicker on top of static bg
            tx = self.W//8; ty = self.H//3
            tp = 0.7+0.3*math.sin(self.time*3.8+1.2)
            pygame.draw.polygon(self.screen, (int(220*tp),int(120*tp),20),
                [(tx-5, ty),(tx, ty-18),(tx+5, ty)])
            tgs = pygame.Surface((50,50), pygame.SRCALPHA)
            pygame.draw.circle(tgs,(int(200*tp),int(110*tp),20,int(50*tp)),(25,25),22)
            self.screen.blit(tgs, (tx-25, ty-28), special_flags=pygame.BLEND_RGBA_ADD)

            # Window light shimmer
            pulse = 0.7+0.3*math.sin(self.time*0.8)
            win_x = self.W*7//8-30; win_y = self.H//4
            ws = pygame.Surface((60,80), pygame.SRCALPHA)
            ws.fill((int(155*pulse),int(200*pulse),int(210*pulse),int(80*pulse)))
            self.screen.blit(ws, (win_x, win_y), special_flags=pygame.BLEND_RGBA_ADD)

            self._draw_panel(ease)
            if ease > 0.8:
                self._draw_header(px, py, pw, ease)
                self._draw_mode_tabs(px, py, ease)
                self._draw_category_tabs(px, py, pw, ease)

            if ease > 0.85:
                # Left content column
                if self.mode == "buy":
                    self._draw_buy_grid(px, py, pw, ph)
                else:
                    self._draw_sell_list(px, py, pw, ph)

                # Divider
                div_x = px + int(pw*0.63)
                pygame.draw.line(self.screen, self.shop_color2,
                                 (div_x, py+44), (div_x, py+ph-20), 1)

                # Right column — Mira NPC + rumours
                right_cx = div_x + (px+pw-div_x)//2
                mira_cy  = py + ph*2//3
                self._draw_mira(right_cx, mira_cy)
                self._draw_dialogue_bubble(right_cx, mira_cy-50)
                kn = self.font_tiny.render("Mira, Shopkeeper", True, (90, 140, 90))
                self.screen.blit(kn, (right_cx-kn.get_width()//2, mira_cy+85))

                # Rumour panel above Mira
                rum_x = div_x + 12
                rum_w = px+pw-div_x-24
                rum_y = py + 82   # start below the LEAVE button row
                rum_h = mira_cy - 65 - rum_y
                self._draw_rumours(rum_x, rum_y, rum_w, rum_h)

            self._draw_message()
            pygame.display.flip()


# ===========================================================================
# BlacksmithScene — unchanged (uses separate blacksmith_scene.py)
# ===========================================================================

class BlacksmithScene(ShopScene):
    def _setup(self):
        from src.scenes.chest_scene import SwordItem, ShieldItem, SunSwordItem
        self.shop_name    = "Gorin's Forge"
        self.shop_color   = (140, 100, 50)
        self.keeper_color = (160, 130, 100)
        self.flavor_text  = "Need something sharpened?"
        self.sell_enabled = True

        class HeavySwordItem(SwordItem):
            def __init__(self):
                super().__init__()
                self.name = "Heavy Sword"
                self.description = "A two-handed blade. Deals 10 damage."

        class ChainmailItem(ShieldItem):
            def __init__(self):
                super().__init__()
                self.name = "Chainmail"
                self.description = "Reduces incoming damage by 2."

        class ArrowBundleItem:
            stackable=True; amount=10; name="Arrows (x10)"
            description="A bundle of arrows. For future use."; icon_color=(160,130,70)
            def draw_icon(self,surface,cx,cy,size):
                s=size
                for i in range(3):
                    ox2=(i-1)*6
                    pygame.draw.line(surface,(160,130,70),(cx+ox2,cy+s//3),(cx+ox2,cy-s//3),3)
                    pygame.draw.polygon(surface,(200,170,80),[(cx+ox2,cy-s//3-6),(cx+ox2-4,cy-s//3),(cx+ox2+4,cy-s//3)])

        from src.scenes.chest_scene import IronHelmet,IronChestplate,IronLeggings,IronBoots
        self.shop_items = [
            ShopItem(IronHelmet,18,3,"Reduces damage by 1."),
            ShopItem(IronChestplate,32,2,"Reduces damage by 3."),
            ShopItem(IronLeggings,24,2,"Reduces damage by 2."),
            ShopItem(IronBoots,18,3,"Reduces damage by 1."),
            ShopItem(HeavySwordItem,25,2,"Deals 10 damage. Two-handed."),
            ShopItem(ShieldItem,22,2,"Blocks one hit entirely."),
            ShopItem(ChainmailItem,18,3,"Reduces damage by 2 per hit."),
            ShopItem(ArrowBundleItem,8,-1,"10 arrows. For future use."),
            ShopItem(SunSwordItem,50,1,"The legendary Sun Sword. Deals 12 damage."),
        ]

    def _draw_background(self):
        for y in range(self.H):
            t2=y/self.H; r=int(22+18*t2); g2=int(14+10*t2); b=int(8+5*t2)
            pygame.draw.line(self.screen,(r,g2,b),(0,y),(self.W,y))
        pulse=0.5+0.5*math.sin(self.time*3)
        glow=pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        pygame.draw.ellipse(glow,(180,80,10,int(40*pulse)),(self.W//2-180,self.H-180,360,260))
        self.screen.blit(glow,(0,0))


# ===========================================================================
# AntiquityScene — unchanged
# ===========================================================================


# ===========================================================================
# Enchantment system
# ===========================================================================

ENCHANTMENTS = {
    "flame": {
        "name":        "Flame",
        "colour":      (255, 100, 20),
        "icon_col":    (255, 140, 40),
        "cost":        40,
        "desc":        "Burns foes on hit. +3 fire damage, chance to ignite.",
        "lore":        "Forged in volcanic glass. The blade remembers the mountain's rage.",
        "bonus_dmg":   3,
        "effect":      "ignite",   # handled in combat
    },
    "vampiric": {
        "name":        "Vampiric",
        "colour":      (180, 30, 60),
        "icon_col":    (220, 50, 80),
        "cost":        50,
        "desc":        "Drain 2 HP from the enemy on every hit.",
        "lore":        "The blade thirsts. Feed it, and it feeds you in kind.",
        "bonus_dmg":   0,
        "effect":      "lifesteal",
    },
    "radiant": {
        "name":        "Radiant",
        "colour":      (255, 230, 80),
        "icon_col":    (255, 245, 140),
        "cost":        45,
        "desc":        "Holy light. Double damage vs undead enemies.",
        "lore":        "Blessed by a wandering priest who asked for nothing in return.",
        "bonus_dmg":   0,
        "effect":      "radiant",
    },
    "cursed": {
        "name":        "Cursed",
        "colour":      (80, 200, 80),
        "icon_col":    (120, 240, 120),
        "cost":        35,
        "desc":        "+8 damage per hit, but costs 2 HP to swing.",
        "lore":        "Something speaks inside the metal. Do not listen too long.",
        "bonus_dmg":   8,
        "effect":      "cursed",
    },
}

LYRA_RUMOURS = [
    "The Sun Sword was carried by a paladin who never returned from the deep.",
    "I've seen three Iron Shields this month. Someone's been looting the armoury.",
    "Relics don't choose their owners. But some owners choose poorly.",
    "A scholar once told me every artefact remembers being made. Unsettling thought.",
    "The orb in the corner has been humming. Started last Tuesday. I'm ignoring it.",
    "Enchanted blades have a cost. Always. Read the lore before you swing.",
    "Something in the lower dungeon has been collecting weapons. Not using them — collecting.",
    "I don't ask where my stock comes from. The dungeon provides. That's enough.",
]

# Relics the player can research (buy lore for)
RELIC_CATALOGUE = [
    {
        "id":       "sun_sword",
        "name":     "Sun Sword",
        "icon_col": (255, 200, 40),
        "buy_price":55,
        "lore_price": 20,
        "lore": (
            "Forged during the Solstice Wars by the smith-priests of Ashenvale. "
            "The blade channels raw solar energy, burning hotter against creatures "
            "of darkness. Said to have slain the first Lich King. One of three known to exist."
        ),
        "stat_line": "Deals 12 damage. Blazes with solar fire.",
    },
    {
        "id":       "iron_shield",
        "name":     "Iron Shield",
        "icon_col": (100, 130, 160),
        "buy_price": 40,
        "lore_price": 15,
        "lore": (
            "Standard-issue shield of the old kingdom guard. The iron was smelted with "
            "a tempering agent lost to time — modern copies shatter after a few hits. "
            "This one has stopped blades for three hundred years."
        ),
        "stat_line": "Blocks all damage from one hit.",
    },
    {
        "id":       "mystic_orb",
        "name":     "Mystic Orb",
        "icon_col": (160, 100, 220),
        "buy_price": 35,
        "lore_price": 12,
        "lore": (
            "Its origin is unknown. The glass is not glass — it doesn't scratch, "
            "chip, or react to heat. The light inside moves without a source. "
            "Three scholars have studied it. Two stopped writing about it entirely."
        ),
        "stat_line": "Power unknown. Handle with curiosity.",
    },
    {
        "id":       "flame_ench",
        "name":     "Flame Enchantment",
        "icon_col": (255, 120, 30),
        "buy_price": None,
        "lore_price": 10,
        "lore": (
            "The first flame enchantment was an accident — a smith dropped his "
            "blade into a magma vein. The sword was ruined, but the method survived. "
            "Now refined, it channels persistent heat through the metal on impact."
        ),
        "stat_line": "+3 fire damage. Chance to ignite.",
    },
    {
        "id":       "vampiric_ench",
        "name":     "Vampiric Enchantment",
        "icon_col": (200, 40, 70),
        "buy_price": None,
        "lore_price": 10,
        "lore": (
            "Not technically cursed — the distinction matters legally. "
            "The blade redirects a fraction of the wound's life-force back to the wielder. "
            "Practitioners note the blade occasionally 'resists' being sheathed."
        ),
        "stat_line": "Drain 2 HP from enemy on every hit.",
    },
    {
        "id":       "radiant_ench",
        "name":     "Radiant Enchantment",
        "icon_col": (255, 245, 140),
        "buy_price": None,
        "lore_price": 10,
        "lore": (
            "Applied during the third plague of undead by a Cleric of the Old Order. "
            "The blessing is non-denominational — it seems to work on faith in general, "
            "rather than any specific deity. Highly effective. Fades after heavy use."
        ),
        "stat_line": "Double damage vs undead. Normal vs others.",
    },
    {
        "id":       "cursed_ench",
        "name":     "Cursed Enchantment",
        "icon_col": (100, 255, 100),
        "buy_price": None,
        "lore_price": 10,
        "lore": (
            "It asked me to write this entry. I declined. It wrote it anyway. "
            "The enchantment amplifies strikes dramatically, drawing power from the wielder. "
            "Do not read this aloud. It is listening."
        ),
        "stat_line": "+8 damage per hit. Costs 2 HP to swing.",
    },
]


class AntiquityScene:
    """
    The Curio Cabinet — fully reworked antiquity shop.
    A) Arcane study interior with Lyra NPC, illustrated background
    B) Lore examination — pay gold to unlock relic lore + add to tome
    C) Tome of Relics — collectable catalogue filling up as you research
    + Enchantment system: Flame, Vampiric, Radiant, Cursed
    """

    def __init__(self, screen, inventory, player_state=None):
        self.screen    = screen
        self.W, self.H = screen.get_size()
        self.clock     = pygame.time.Clock()
        self.time      = 0.0
        self.inventory = inventory
        self.player_state = player_state  # for future enchant HP cost hook

        self.font_title  = pygame.font.SysFont("courier new", 24, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 15, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 13)
        self.font_tiny   = pygame.font.SysFont("courier new", 11)

        self.shop_color  = (110, 70, 160)
        self.shop_color2 = (80, 45, 120)

        # Tabs: RELICS | ENCHANT | TOME
        self.tab      = 0
        self.selected = 0
        self._tab_hovers = [0.0, 0.0, 0.0]
        self._leave_hover = 0.0

        # State
        self.open_anim    = 0.0
        self.OPEN_DUR     = 0.4
        self.message      = ""
        self.message_timer = 0.0
        self.msg_good     = True

        # Persistent data (survives for session — hook to save system later)
        self._unlocked_lore: set = set()   # relic ids with purchased lore
        self._enchant_on_weapon: str | None = None  # current enchant key

        # Dialogue
        self._dialogues = [
            "Every relic has a story.\nMost are tragedies.",
            "Touch nothing unless\nyou intend to buy.",
            "The orb is not for sale.\nStop asking.",
            "Enchantments are\npermanent. Choose wisely.",
            "Knowledge costs.\nIgnorance costs more.",
            "The tome grows heavier\nwith each entry. Good.",
        ]
        self._dialogue = random.choice(self._dialogues)
        self._rumour_idx   = random.randint(0, len(LYRA_RUMOURS)-1)
        self._rumour_timer = 0.0
        self.RUMOUR_DUR    = 7.0

        # Pre-bake background
        self._bg_surf = self._build_background()

        # Build shop items
        self._build_stock()

    # ------------------------------------------------------------------ #
    # Stock
    # ------------------------------------------------------------------ #

    def _build_stock(self):
        from src.scenes.chest_scene import SunSwordItem, ShieldItem
        class MysticOrbItem:
            stackable=False; name="Mystic Orb"
            description="Swirling with power. A future relic."
            icon_color=(160,100,220)
            def draw_icon(self,surface,cx,cy,size):
                s=size
                pygame.draw.circle(surface,(100,60,180),(cx,cy),s//2)
                pygame.draw.circle(surface,(160,100,220),(cx,cy),s//2,2)
                for a in range(0,360,60):
                    ra=math.radians(a)
                    pygame.draw.line(surface,(200,160,255),(cx,cy),
                                     (cx+int(math.cos(ra)*s//3),cy+int(math.sin(ra)*s//3)),1)
        self.relic_items = [
            ShopItem(SunSwordItem,  55, 1, "Blazing solar relic. Deals 12 damage."),
            ShopItem(ShieldItem,    40, 2, "Blocks one hit entirely."),
            ShopItem(MysticOrbItem, 35, 2, "A mysterious relic. Power unknown."),
        ]

    # ------------------------------------------------------------------ #
    # Gold helpers
    # ------------------------------------------------------------------ #

    def _gold(self):
        from src.scenes.chest_scene import GoldItem
        return sum(self.inventory.stack_count(it)
                   for it in self.inventory.items if isinstance(it, GoldItem))

    def _spend_gold(self, amount):
        from src.scenes.chest_scene import GoldItem
        gi = next((it for it in self.inventory.items if isinstance(it, GoldItem)), None)
        if gi is None: return False
        total = self.inventory.stack_count(gi)
        if total < amount: return False
        self.inventory.remove(gi)
        if total-amount > 0: self.inventory.add(GoldItem(total-amount))
        return True

    def _get_weapon(self):
        from src.scenes.chest_scene import StickItem, SwordItem
        for it in self.inventory.items:
            if type(it).__name__ in ("StickItem","SwordItem","SunSwordItem"):
                return it
        return None

    # ------------------------------------------------------------------ #
    # Background — arcane study interior (pre-baked)
    # ------------------------------------------------------------------ #

    def _build_background(self):
        surf = pygame.Surface((self.W, self.H))
        W, H = self.W, self.H

        # Deep purple gradient — 1px strip scaled
        strip = pygame.Surface((1, H))
        for y in range(H):
            t = y/H
            strip.set_at((0,y),(int(10+8*t), int(6+5*t), int(18+14*t)))
        surf.blit(pygame.transform.scale(strip, (W, H)), (0,0))

        # Stone floor
        floor_y = H*2//3
        pygame.draw.rect(surf,(38,28,52),(0,floor_y,W,H-floor_y))
        for fx in range(0,W,52):
            v = ((fx//52)*9+5)%11-5
            pygame.draw.rect(surf,(34+v,24+v,48+v),(fx,floor_y,50,H-floor_y))
            pygame.draw.line(surf,(28,18,40),(fx,floor_y),(fx,H),1)

        # Back wall shelves with glowing jars
        for row in range(3):
            sy = H//5 + row*58
            pygame.draw.rect(surf,(55,35,75),(W//5, sy, W*3//5, 8))
            pygame.draw.rect(surf,(38,22,55),(W//5, sy, W*3//5, 8),1)
            rng2 = random.Random(row*23)
            for col in range(7):
                jx = W//5 + 18 + col*(W*3//35)
                jy = sy - 22
                jcol = rng2.choice([(140,80,220),(80,160,220),(220,120,80),(80,220,140),(220,200,80)])
                pygame.draw.rect(surf,jcol,(jx-5,jy-10,10,18))
                pygame.draw.rect(surf,jcol,(jx-3,jy-16,6,8))
                pygame.draw.circle(surf,tuple(min(255,c+60) for c in jcol),(jx,jy-16),3)

        # Crystal ball on pedestal — centre right
        cbx = W*3//4; cby = H*2//3-30
        pygame.draw.rect(surf,(48,32,62),(cbx-12,cby,24,28))
        pygame.draw.rect(surf,(58,40,75),(cbx-16,cby,32,8))
        pygame.draw.circle(surf,(55,35,80),(cbx,cby-18),22)
        pygame.draw.circle(surf,(80,50,110),(cbx,cby-18),22,2)
        pygame.draw.circle(surf,(130,90,180),(cbx-6,cby-24),8)

        # Floating candles (static positions)
        for cx2,cy2 in [(W//6,H//3),(W*5//6-20,H//3+20),(W//2,H//4)]:
            pygame.draw.rect(surf,(80,58,28),(cx2-3,cy2,6,18))
            pygame.draw.circle(surf,(90,65,32),(cx2,cy2+2),8)

        # Star chart on left wall
        scx = W//8; scy = H//3
        pygame.draw.rect(surf,(22,14,32),(scx-30,scy-40,60,70))
        pygame.draw.rect(surf,(55,35,75),(scx-30,scy-40,60,70),1)
        rng3 = random.Random(77)
        for _ in range(12):
            sx2 = scx-28+rng3.randint(0,56); sy2 = scy-38+rng3.randint(0,66)
            pygame.draw.circle(surf,(200,180,255),(sx2,sy2),rng3.choice([1,1,2]))

        # Tome on counter
        tx2 = W//2-18; ty2 = H*2//3-22
        pygame.draw.rect(surf,(45,25,65),(tx2,ty2,36,20))
        pygame.draw.rect(surf,(80,50,110),(tx2,ty2,36,20),2)
        pygame.draw.line(surf,(80,50,110),(tx2+18,ty2),(tx2+18,ty2+20),1)

        return surf

    # ------------------------------------------------------------------ #
    # Lyra NPC
    # ------------------------------------------------------------------ #

    def _draw_lyra(self, cx, cy):
        """Lyra — tall, robed, mysterious antiquarian."""
        skin  = (195, 165, 140)
        dark  = (145, 115, 90)
        robe  = (75, 45, 105)
        robe2 = (55, 30, 80)
        hair  = (45, 28, 65)

        # Robe body — long and narrow
        pygame.draw.polygon(self.screen, robe, [
            (cx-18, cy-5),(cx+18, cy-5),(cx+22, cy+80),(cx-22, cy+80)])
        pygame.draw.polygon(self.screen, robe2, [
            (cx-18, cy-5),(cx+18, cy-5),(cx+22, cy+80),(cx-22, cy+80)], 2)
        # Robe trim — gold hem
        pygame.draw.line(self.screen,(155,118,55),(cx-22,cy+78),(cx+22,cy+78),2)
        # Star pattern on robe
        for sa in range(0,360,72):
            ra2=math.radians(sa+self.time*8)
            pygame.draw.circle(self.screen,(130,85,180),
                               (cx+int(math.cos(ra2)*8),cy+30+int(math.sin(ra2)*8)),2)

        # Arms — sleeves
        pygame.draw.line(self.screen, robe, (cx-18, cy+5),(cx-32, cy+35), 8)
        pygame.draw.line(self.screen, robe, (cx+18, cy+5),(cx+32, cy+35), 8)
        # Hands
        pygame.draw.circle(self.screen, skin, (cx-32, cy+35), 5)
        pygame.draw.circle(self.screen, skin, (cx+32, cy+35), 5)

        # Head
        pygame.draw.circle(self.screen, skin, (cx, cy-28), 22)
        pygame.draw.circle(self.screen, dark, (cx, cy-28), 22, 2)

        # Tall pointed hat
        hat_pts = [(cx-20, cy-48),(cx+20, cy-48),(cx, cy-82)]
        pygame.draw.polygon(self.screen, hair, hat_pts)
        pygame.draw.polygon(self.screen, (60,38,85), hat_pts, 2)
        pygame.draw.rect(self.screen, hair, (cx-24,cy-52,48,8))
        # Hat star
        pygame.draw.circle(self.screen,(int(180*(0.5+0.5*math.sin(self.time*2))),
                                         120,255),(cx,cy-80),4)

        # Hair — dark, flowing sides
        pygame.draw.line(self.screen, hair, (cx-18, cy-40),(cx-22, cy-15), 5)
        pygame.draw.line(self.screen, hair, (cx+18, cy-40),(cx+22, cy-15), 5)

        # Eyes — large and knowing
        for ex in [cx-8, cx+8]:
            pygame.draw.ellipse(self.screen, (38,22,55),(ex-4,cy-32,8,10))
            pygame.draw.ellipse(self.screen, (160,100,220),(ex-3,cy-31,6,8))
            pygame.draw.circle(self.screen, (220,180,255),(ex-1,cy-28),2)

        # Small smile
        pygame.draw.arc(self.screen, dark,(cx-7,cy-22,14,8),math.pi,2*math.pi,2)

        # Floating orb in hand
        ox=cx+34; oy=cy+30
        osurf=pygame.Surface((18,18),pygame.SRCALPHA)
        op=0.6+0.4*math.sin(self.time*2.5)
        pygame.draw.circle(osurf,(int(160*op),int(100*op),int(240*op),210),(9,9),8)
        self.screen.blit(osurf,(ox-9,oy-9))
        pygame.draw.circle(self.screen,(int(220*op),int(160*op),255),(ox,oy),4,1)

    def _draw_dialogue_bubble(self, cx, cy):
        lines = self._dialogue.split("\n")
        max_w = max(self.font_small.size(l)[0] for l in lines)+20
        bh = len(lines)*18+14; bx = cx-max_w//2; by = cy-bh-20
        pygame.draw.rect(self.screen,(225,210,240),(bx,by,max_w,bh),border_radius=6)
        pygame.draw.rect(self.screen,(130,80,180),(bx,by,max_w,bh),2,border_radius=6)
        pygame.draw.polygon(self.screen,(225,210,240),
            [(cx-8,by+bh),(cx+8,by+bh),(cx,by+bh+14)])
        pygame.draw.line(self.screen,(130,80,180),(cx-8,by+bh),(cx,by+bh+14),2)
        pygame.draw.line(self.screen,(130,80,180),(cx+8,by+bh),(cx,by+bh+14),2)
        for li,line in enumerate(lines):
            ls=self.font_small.render(line,True,(50,28,70))
            self.screen.blit(ls,(bx+10,by+7+li*18))

    # ------------------------------------------------------------------ #
    # Rumour panel
    # ------------------------------------------------------------------ #

    def _draw_rumours(self, rx, ry, rw, rh):
        rumours = LYRA_RUMOURS
        bg = pygame.Surface((rw,rh),pygame.SRCALPHA)
        bg.fill((16,8,28,215))
        self.screen.blit(bg,(rx,ry))
        pygame.draw.rect(self.screen,(80,45,120),(rx,ry,rw,rh),1)
        hdr=self.font_small.render("— RUMOURS —",True,(160,110,220))
        self.screen.blit(hdr,(rx+rw//2-hdr.get_width()//2,ry+8))
        pygame.draw.line(self.screen,(60,35,90),(rx+8,ry+24),(rx+rw-8,ry+24),1)
        entry_y=ry+32; line_h=self.font_tiny.get_height()+3
        for i,rumour in enumerate(rumours):
            words=rumour.split(); lines_out=[]; cur=""
            for w in words:
                test=cur+(" " if cur else "")+w
                if self.font_tiny.size(test)[0]<rw-20: cur=test
                else: lines_out.append(cur); cur=w
            if cur: lines_out.append(cur)
            block_h=len(lines_out)*line_h+6
            if entry_y+block_h>ry+rh-14: break
            pygame.draw.circle(self.screen,(140,85,200),(rx+10,entry_y+line_h//2),3)
            for li,line in enumerate(lines_out):
                ls=self.font_tiny.render(line,True,(175,135,220))
                self.screen.blit(ls,(rx+18,entry_y+li*line_h))
            entry_y+=block_h+4

    # ------------------------------------------------------------------ #
    # Panel & header
    # ------------------------------------------------------------------ #

    def _panel_rect(self):
        pw=int(self.W*0.90); ph=int(self.H*0.86)
        return (self.W-pw)//2,(self.H-ph)//2,pw,ph

    def _draw_panel(self, ease):
        px,py,pw,ph=self._panel_rect()
        w=int(pw*ease); h=int(ph*ease)
        x=self.W//2-w//2; y=self.H//2-h//2
        if w<4: return
        sh=pygame.Surface((w+14,h+14),pygame.SRCALPHA); sh.fill((0,0,0,110))
        self.screen.blit(sh,(x-7,y-7))
        panel=pygame.Surface((w,h),pygame.SRCALPHA); panel.fill((10,6,18,252))
        self.screen.blit(panel,(x,y))
        pygame.draw.rect(self.screen,self.shop_color,(x,y,w,h),2)
        pygame.draw.rect(self.screen,self.shop_color2,(x+5,y+5,w-10,h-10),1)
        sz=14
        for bx,by,dx,dy in [(x,y,1,1),(x+w,y,-1,1),(x,y+h,1,-1),(x+w,y+h,-1,-1)]:
            pygame.draw.line(self.screen,(165,100,230),(bx,by),(bx+dx*sz,by),2)
            pygame.draw.line(self.screen,(165,100,230),(bx,by),(bx,by+dy*sz),2)

    def _draw_header(self, px, py, pw, ease):
        if ease<0.8: return
        title=self.font_title.render("The Curio Cabinet",True,(195,145,255))
        self.screen.blit(title,(self.W//2-title.get_width()//2,py+10))
        pygame.draw.line(self.screen,self.shop_color,(px+20,py+38),(px+pw-20,py+38),1)
        gs=self.font_medium.render(f"Gold: {self._gold()}",True,(220,185,60))
        self.screen.blit(gs,(px+pw-gs.get_width()-128,py+12))

    def _draw_leave_button(self, px, py, pw):
        leave_rect=pygame.Rect(px+pw-116,py+10,100,28)
        h=self._leave_hover
        bg=pygame.Surface((100,28),pygame.SRCALPHA)
        bg.fill((int(16+28*h),int(8+18*h),int(22+36*h),200))
        self.screen.blit(bg,leave_rect.topleft)
        def lc(a,b): return tuple(int(a[j]+(b[j]-a[j])*h) for j in range(3))
        pygame.draw.rect(self.screen,lc((55,30,80),(140,90,200)),leave_rect,2)
        lbl=self.font_small.render("LEAVE",True,lc((110,70,155),(195,145,240)))
        self.screen.blit(lbl,(leave_rect.centerx-lbl.get_width()//2,leave_rect.centery-lbl.get_height()//2))
        return leave_rect

    def _draw_tab_bar(self, px, py, pw, ease):
        if ease<0.8: return
        tabs=["RELICS","EXAMINE","ENCHANT"]
        tab_area_w=pw-140; tw=tab_area_w//3
        tab_y=py+44
        for i,label in enumerate(tabs):
            tx=px+20+i*tw; is_sel=(i==self.tab); hov=self._tab_hovers[i]
            col=self.shop_color if is_sel else (40,22,58)
            bg=pygame.Surface((tw-4,26),pygame.SRCALPHA)
            bg.fill((*col,220) if is_sel else (int(16+14*hov),int(8+8*hov),int(22+18*hov),180))
            self.screen.blit(bg,(tx+2,tab_y))
            pygame.draw.rect(self.screen,col,(tx+2,tab_y,tw-4,26),2 if is_sel else 1)
            lbl=self.font_small.render(label,True,(210,165,255) if is_sel else (110,70,155))
            self.screen.blit(lbl,(tx+tw//2-lbl.get_width()//2,tab_y+13-lbl.get_height()//2))

    # ------------------------------------------------------------------ #
    # Tab A — Relics (buy)
    # ------------------------------------------------------------------ #

    def _draw_relics_tab(self, px, py, pw, ph):
        items=self.relic_items; gold=self._gold(); mouse=pygame.mouse.get_pos()
        content_x=px+16; content_y=py+82; content_w=int(pw*0.62)
        card_h=80; gap=8

        for i,si in enumerate(items):
            cy2=content_y+i*(card_h+gap); is_sel=(i==self.selected and self.tab==0)
            can=gold>=si.price and si.in_stock()
            hovering=pygame.Rect(content_x,cy2,content_w-12,card_h).collidepoint(mouse)
            active=is_sel or hovering

            card_bg=pygame.Surface((content_w-12,card_h),pygame.SRCALPHA)
            card_bg.fill((20,10,35,220) if is_sel else (14,7,24,190))
            self.screen.blit(card_bg,(content_x,cy2))
            bc=self.shop_color if (active and can) else (65,38,95) if active else (38,20,55)
            pygame.draw.rect(self.screen,bc,(content_x,cy2,content_w-12,card_h),2 if active else 1)

            # Find matching catalogue entry for lore unlock indicator
            cat = next((r for r in RELIC_CATALOGUE if r["name"]==si.name),None)
            if cat and cat["id"] in self._unlocked_lore:
                lb=self.font_tiny.render("LORE ✓",True,(140,90,200))
                self.screen.blit(lb,(content_x+content_w-lb.get_width()-20,cy2+5))

            # Icon
            si.draw_icon(self.screen,content_x+28,cy2+card_h//2,44)
            # Name
            nc=(210,170,255) if (active and can) else (155,110,200) if can else (80,50,110)
            ns=self.font_medium.render(si.name,True,nc)
            self.screen.blit(ns,(content_x+58,cy2+12))
            ds=self.font_tiny.render(si.description,True,(110,75,150))
            self.screen.blit(ds,(content_x+58,cy2+12+ns.get_height()+2))

            # Price / stock
            if si.stock==0:
                oos=self.font_tiny.render("OUT OF STOCK",True,(160,70,90))
                self.screen.blit(oos,(content_x+58,cy2+card_h-oos.get_height()-8))
            else:
                pc=(220,185,60) if can else (100,70,35)
                ps=self.font_medium.render(f"{si.price}g",True,pc)
                self.screen.blit(ps,(content_x+content_w-ps.get_width()-20,cy2+card_h-ps.get_height()-8))
                if si.stock>0:
                    stk=self.font_tiny.render(f"x{si.stock}",True,(140,95,185))
                    self.screen.blit(stk,(content_x+content_w-stk.get_width()-20,cy2+card_h-ps.get_height()-stk.get_height()-10))

        hint=self.font_tiny.render("↑ ↓  select    ENTER / click  buy    ESC  leave",True,(70,42,95))
        self.screen.blit(hint,(content_x,py+ph-hint.get_height()-8))

    # ------------------------------------------------------------------ #
    # Tab B — Lore Examination
    # ------------------------------------------------------------------ #

    def _draw_examine_tab(self, px, py, pw, ph):
        content_x=px+16; content_y=py+82; content_w=int(pw*0.62)
        mouse=pygame.mouse.get_pos()
        card_h=68; gap=6

        for i,relic in enumerate(RELIC_CATALOGUE):
            cy2=content_y+i*(card_h+gap)
            if cy2+card_h>py+ph-40: break
            unlocked=relic["id"] in self._unlocked_lore
            is_sel=(i==self.selected and self.tab==1)
            hovering=pygame.Rect(content_x,cy2,content_w-12,card_h).collidepoint(mouse)
            active=is_sel or hovering

            card_bg=pygame.Surface((content_w-12,card_h),pygame.SRCALPHA)
            card_bg.fill((20,10,35,220) if active else (14,7,24,180))
            self.screen.blit(card_bg,(content_x,cy2))
            border_col=(165,100,230) if unlocked else (self.shop_color if active else (42,22,62))
            pygame.draw.rect(self.screen,border_col,(content_x,cy2,content_w-12,card_h),2 if active else 1)

            # Icon dot
            pygame.draw.circle(self.screen,relic["icon_col"],(content_x+20,cy2+card_h//2),14)
            pygame.draw.circle(self.screen,tuple(max(0,c-60) for c in relic["icon_col"]),
                               (content_x+20,cy2+card_h//2),14,2)

            nc=(210,170,255) if active else (155,110,200)
            ns=self.font_medium.render(relic["name"],True,nc)
            self.screen.blit(ns,(content_x+42,cy2+8))

            if unlocked:
                # Show stat line + "STUDIED" badge
                sl=self.font_tiny.render(relic["stat_line"],True,(140,100,190))
                self.screen.blit(sl,(content_x+42,cy2+8+ns.get_height()+3))
                badge=self.font_tiny.render("✓ STUDIED",True,(165,100,230))
                self.screen.blit(badge,(content_x+content_w-badge.get_width()-16,cy2+10))
            else:
                ds=self.font_tiny.render("??? — pay to study this relic",True,(80,50,110))
                self.screen.blit(ds,(content_x+42,cy2+8+ns.get_height()+3))
                if relic["lore_price"]:
                    cost_col=(220,185,60) if self._gold()>=relic["lore_price"] else (100,70,35)
                    cs=self.font_small.render(f"Study: {relic['lore_price']}g",True,cost_col)
                    self.screen.blit(cs,(content_x+content_w-cs.get_width()-16,cy2+card_h//2-cs.get_height()//2))

            # Expanded lore view when selected + unlocked
            if is_sel and unlocked:
                lore_y=cy2+card_h+4
                lore_surf=pygame.Surface((content_w-12,72),pygame.SRCALPHA)
                lore_surf.fill((24,12,40,230))
                self.screen.blit(lore_surf,(content_x,lore_y))
                pygame.draw.rect(self.screen,(165,100,230),(content_x,lore_y,content_w-12,72),1)
                # Word-wrap lore text
                words=relic["lore"].split(); lines=[]; cur=""
                for w in words:
                    test=cur+(" " if cur else "")+w
                    if self.font_tiny.size(test)[0]<content_w-32: cur=test
                    else: lines.append(cur); cur=w
                if cur: lines.append(cur)
                for li,line in enumerate(lines[:4]):
                    ls=self.font_tiny.render(line,True,(190,155,230))
                    self.screen.blit(ls,(content_x+8,lore_y+5+li*16))

        hint=self.font_tiny.render("↑ ↓  select    ENTER / click  study    ESC  leave",True,(70,42,95))
        self.screen.blit(hint,(content_x,py+ph-hint.get_height()-8))

    # ------------------------------------------------------------------ #
    # Tab C — Tome of Relics
    # ------------------------------------------------------------------ #

    def _draw_tome_tab(self, px, py, pw, ph):
        content_x=px+16; content_y=py+82; content_w=int(pw*0.62)
        studied=[r for r in RELIC_CATALOGUE if r["id"] in self._unlocked_lore]
        total=len(RELIC_CATALOGUE)

        # Tome header
        prog_s=self.font_medium.render(f"Relics Studied: {len(studied)} / {total}",True,(165,120,220))
        self.screen.blit(prog_s,(content_x,content_y))
        # Progress bar
        bar_w=content_w-20; bar_h=10; bar_y=content_y+prog_s.get_height()+4
        pygame.draw.rect(self.screen,(28,14,42),(content_x,bar_y,bar_w,bar_h))
        pygame.draw.rect(self.screen,(55,30,80),(content_x,bar_y,bar_w,bar_h),1)
        if studied:
            fill=int(bar_w*(len(studied)/total))
            pygame.draw.rect(self.screen,self.shop_color,(content_x,bar_y,fill,bar_h))

        if not studied:
            ns=self.font_medium.render("No relics studied yet.",True,(75,45,105))
            ns2=self.font_small.render("Visit the EXAMINE tab and pay to study relics.",True,(60,35,85))
            self.screen.blit(ns,(content_x,content_y+50))
            self.screen.blit(ns2,(content_x,content_y+76))
        else:
            entry_y=content_y+prog_s.get_height()+28
            for relic in studied:
                if entry_y+90>py+ph-40: break
                # Entry card
                entry_bg=pygame.Surface((content_w-12,85),pygame.SRCALPHA)
                entry_bg.fill((18,8,30,210))
                self.screen.blit(entry_bg,(content_x,entry_y))
                pygame.draw.rect(self.screen,(100,60,145),(content_x,entry_y,content_w-12,85),1)
                # Icon
                pygame.draw.circle(self.screen,relic["icon_col"],(content_x+18,entry_y+42),14)
                # Name + stat
                ns=self.font_medium.render(relic["name"],True,(200,160,250))
                self.screen.blit(ns,(content_x+40,entry_y+8))
                sl=self.font_tiny.render(relic["stat_line"],True,(140,100,190))
                self.screen.blit(sl,(content_x+40,entry_y+8+ns.get_height()+2))
                # First sentence of lore
                first=relic["lore"].split(".")[0]+"."
                if self.font_tiny.size(first)[0]>content_w-56:
                    first=first[:60]+"..."
                ls=self.font_tiny.render(first,True,(155,115,200))
                self.screen.blit(ls,(content_x+40,entry_y+8+ns.get_height()+18))
                entry_y+=92

    # ------------------------------------------------------------------ #
    # Enchant tab — apply enchantments to weapon
    # ------------------------------------------------------------------ #

    def _draw_enchant_tab(self, px, py, pw, ph):
        # This tab is only accessible via keyboard shortcut or can be
        # embedded — but the scene uses 3 tabs: RELICS, ENCHANT, TOME
        content_x=px+16; content_y=py+82; content_w=int(pw*0.62)
        mouse=pygame.mouse.get_pos()

        weapon=self._get_weapon()
        if not weapon:
            ns=self.font_medium.render("No weapon in inventory to enchant.",True,(80,50,110))
            self.screen.blit(ns,(content_x,content_y+20))
            hint=self.font_tiny.render("ESC  leave",True,(70,42,95))
            self.screen.blit(hint,(content_x,py+ph-hint.get_height()-8))
            return

        # Current weapon card
        wname=getattr(weapon,"WEAPON_NAMES",[weapon.name])[min(getattr(weapon,"upgrade_level",0),5)]
        enc=getattr(weapon,"enchantment",None)
        enc_data=ENCHANTMENTS.get(enc,None)

        wcard=pygame.Surface((content_w-12,56),pygame.SRCALPHA)
        wcard.fill((20,10,35,220))
        self.screen.blit(wcard,(content_x,content_y))
        pygame.draw.rect(self.screen,self.shop_color,(content_x,content_y,content_w-12,56),2)
        ws=self.font_medium.render(f"Weapon: {wname}",True,(210,170,255))
        self.screen.blit(ws,(content_x+10,content_y+8))
        if enc_data:
            ec=self.font_small.render(f"Current enchantment: {enc_data['name']}",True,enc_data["icon_col"])
            self.screen.blit(ec,(content_x+10,content_y+8+ws.get_height()+3))
        else:
            ec=self.font_tiny.render("No enchantment applied.",True,(100,70,140))
            self.screen.blit(ec,(content_x+10,content_y+8+ws.get_height()+3))

        # Enchantment cards
        ench_list=list(ENCHANTMENTS.items())
        card_h=70; gap=7; start_y=content_y+68
        for i,(eid,edata) in enumerate(ench_list):
            cy2=start_y+i*(card_h+gap)
            is_sel=(i==self.selected and self.tab==1)
            already=(enc==eid)
            can_afford=self._gold()>=edata["cost"]
            hovering=pygame.Rect(content_x,cy2,content_w-12,card_h).collidepoint(mouse)
            active=is_sel or hovering

            card_bg=pygame.Surface((content_w-12,card_h),pygame.SRCALPHA)
            card_bg.fill((20,10,35,220) if active else (14,7,24,180))
            self.screen.blit(card_bg,(content_x,cy2))
            bc=edata["colour"] if already else (self.shop_color if active else (38,20,55))
            pygame.draw.rect(self.screen,bc,(content_x,cy2,content_w-12,card_h),2 if active else 1)

            # Colour dot
            pygame.draw.circle(self.screen,edata["icon_col"],(content_x+18,cy2+card_h//2),12)

            # Name
            nc=edata["icon_col"] if active else (140,95,180)
            ns=self.font_medium.render(edata["name"],True,nc)
            self.screen.blit(ns,(content_x+38,cy2+8))
            ds=self.font_tiny.render(edata["desc"],True,(110,75,150))
            self.screen.blit(ds,(content_x+38,cy2+8+ns.get_height()+2))

            if already:
                ab=self.font_tiny.render("[ APPLIED ]",True,edata["icon_col"])
                self.screen.blit(ab,(content_x+content_w-ab.get_width()-16,cy2+card_h//2-ab.get_height()//2))
            else:
                cost_col=(220,185,60) if can_afford else (100,70,35)
                cs=self.font_medium.render(f"{edata['cost']}g",True,cost_col)
                self.screen.blit(cs,(content_x+content_w-cs.get_width()-16,cy2+card_h-cs.get_height()-8))

        hint=self.font_tiny.render("↑ ↓  select    ENTER / click  enchant    ESC  leave",True,(70,42,95))
        self.screen.blit(hint,(content_x,py+ph-hint.get_height()-8))

    # ------------------------------------------------------------------ #
    # Message
    # ------------------------------------------------------------------ #

    def _draw_message(self):
        if not self.message or self.message_timer<=0: return
        alpha=min(1.0,self.message_timer/0.4)
        col=(130,100,200) if self.msg_good else (200,80,100)
        ms=self.font_small.render(self.message,True,col)
        bg=pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
        bg.fill((10,5,20,int(220*alpha)))
        bx=self.W//2-bg.get_width()//2; by=72
        self.screen.blit(bg,(bx,by))
        pygame.draw.rect(self.screen,col,(bx,by,bg.get_width(),bg.get_height()),1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms,(bx+10,by+4))

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _do_buy(self):
        items=self.relic_items
        if not items or self.selected>=len(items): return
        si=items[self.selected]
        if not si.in_stock():
            self.message="Out of stock!"; self.msg_good=False
        elif self._gold()<si.price:
            self.message=f"Need {si.price}g!"; self.msg_good=False
        else:
            self._spend_gold(si.price)
            self.inventory.add(si.buy())
            self.message=f"Acquired {si.name}!"; self.msg_good=True
            self._dialogue=random.choice(self._dialogues)
        self.message_timer=2.5

    def _do_study(self):
        if self.selected>=len(RELIC_CATALOGUE): return
        relic=RELIC_CATALOGUE[self.selected]
        if relic["id"] in self._unlocked_lore:
            self.message="Already studied."; self.msg_good=False
        elif self._gold()<relic["lore_price"]:
            self.message=f"Need {relic['lore_price']}g to study!"; self.msg_good=False
        else:
            self._spend_gold(relic["lore_price"])
            self._unlocked_lore.add(relic["id"])
            self.message=f"Lore unlocked: {relic['name']}!"; self.msg_good=True
            self._dialogue=random.choice(self._dialogues)
        self.message_timer=2.5

    def _do_enchant(self):
        ench_list=list(ENCHANTMENTS.items())
        if self.selected>=len(ench_list): return
        eid,edata=ench_list[self.selected]
        weapon=self._get_weapon()
        if not weapon:
            self.message="No weapon to enchant!"; self.msg_good=False
        elif getattr(weapon,"enchantment",None)==eid:
            self.message="Already applied!"; self.msg_good=False
        elif self._gold()<edata["cost"]:
            self.message=f"Need {edata['cost']}g!"; self.msg_good=False
        else:
            self._spend_gold(edata["cost"])
            weapon.enchantment=eid
            self._enchant_on_weapon=eid
            self.message=f"{edata['name']} enchantment applied!"; self.msg_good=True
            self._dialogue=random.choice(self._dialogues)
        self.message_timer=2.5

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while True:
            dt=self.clock.tick(60)/1000.0
            self.time+=dt
            self.open_anim=min(self.open_anim+dt,self.OPEN_DUR)
            ease=1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            self.message_timer=max(0.0,self.message_timer-dt)
            self._rumour_timer+=dt
            if self._rumour_timer>=self.RUMOUR_DUR:
                self._rumour_timer=0.0
                self._rumour_idx=(self._rumour_idx+1)%len(LYRA_RUMOURS)
            mouse=pygame.mouse.get_pos()

            px,py,pw,ph=self._panel_rect()
            leave_rect=pygame.Rect(px+pw-116,py+10,100,28)

            # Tab dimensions
            tab_area_w=pw-140; tw=tab_area_w//3; tab_y=py+44

            self._leave_hover+=((1.0 if leave_rect.collidepoint(mouse) else 0.0)-self._leave_hover)*10*dt
            self._leave_hover=max(0.0,min(1.0,self._leave_hover))
            for i in range(3):
                tx=px+20+i*tw
                tgt=1.0 if pygame.Rect(tx+2,tab_y,tw-4,26).collidepoint(mouse) else 0.0
                self._tab_hovers[i]+=(tgt-self._tab_hovers[i])*10*dt
                self._tab_hovers[i]=max(0.0,min(1.0,self._tab_hovers[i]))

            # Max selected indices per tab
            max_sel=[len(self.relic_items)-1, len(RELIC_CATALOGUE)-1, len(ENCHANTMENTS)-1]

            for event in pygame.event.get():
                if event.type==pygame.QUIT: return "exit"
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: return "town"
                    if event.key==pygame.K_LEFT:
                        self.tab=max(0,self.tab-1); self.selected=0
                    if event.key==pygame.K_RIGHT:
                        self.tab=min(2,self.tab+1); self.selected=0
                    if event.key==pygame.K_UP:
                        self.selected=max(0,self.selected-1)
                    if event.key==pygame.K_DOWN:
                        self.selected=min(max_sel[self.tab],self.selected+1)
                    if event.key in (pygame.K_RETURN,pygame.K_SPACE):
                        if self.tab==0: self._do_buy()
                        elif self.tab==1: self._do_study()
                        elif self.tab==2: self._do_enchant()

                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    if leave_rect.collidepoint(mouse): return "town"
                    # Tab clicks
                    for i in range(3):
                        tx=px+20+i*tw
                        if pygame.Rect(tx+2,tab_y,tw-4,26).collidepoint(mouse):
                            self.tab=i; self.selected=0
                    # Content clicks — buy/study/enchant on double-click (select first)
                    content_x=px+16; content_y=py+82; content_w=int(pw*0.62)
                    if self.tab==0:
                        for i in range(len(self.relic_items)):
                            cy2=content_y+i*(80+8)
                            if pygame.Rect(content_x,cy2,content_w-12,80).collidepoint(mouse):
                                if self.selected==i: self._do_buy()
                                else: self.selected=i
                    elif self.tab==1:
                        for i in range(len(RELIC_CATALOGUE)):
                            cy2=content_y+i*(68+6)
                            if cy2+68>py+ph-40: break
                            if pygame.Rect(content_x,cy2,content_w-12,68).collidepoint(mouse):
                                if self.selected==i: self._do_study()
                                else: self.selected=i
                    elif self.tab==2:
                        start_y=content_y+68
                        for i in range(len(ENCHANTMENTS)):
                            cy2=start_y+i*(70+7)
                            if pygame.Rect(content_x,cy2,content_w-12,70).collidepoint(mouse):
                                if self.selected==i: self._do_enchant()
                                else: self.selected=i

            # ── Draw ────────────────────────────────────────────────── #
            self.screen.blit(self._bg_surf,(0,0))

            # Animated candle flickers on top of static bg
            for cx2,cy2 in [(self.W//6,self.H//3),(self.W*5//6-20,self.H//3+20),(self.W//2,self.H//4)]:
                fp=0.65+0.35*math.sin(self.time*3.2+cx2*0.01)
                pygame.draw.polygon(self.screen,(int(220*fp),int(130*fp),25),
                    [(cx2-4,cy2),(cx2,cy2-16),(cx2+4,cy2)])
                cgs=pygame.Surface((30,30),pygame.SRCALPHA)
                pygame.draw.circle(cgs,(int(180*fp),int(100*fp),25,int(45*fp)),(15,15),13)
                self.screen.blit(cgs,(cx2-15,cy2-18),special_flags=pygame.BLEND_RGBA_ADD)

            # Animated crystal ball pulse
            cbx=self.W*3//4; cby=self.H*2//3-30
            cp=0.5+0.5*math.sin(self.time*1.8)
            cbs=pygame.Surface((60,60),pygame.SRCALPHA)
            pygame.draw.circle(cbs,(int(100*cp),int(55*cp),int(170*cp),int(80*cp)),(30,30),28)
            self.screen.blit(cbs,(cbx-30,cby-48),special_flags=pygame.BLEND_RGBA_ADD)

            self._draw_panel(ease)
            if ease>0.8:
                self._draw_header(px,py,pw,ease)
                self._draw_tab_bar(px,py,pw,ease)
                leave_rect=self._draw_leave_button(px,py,pw)

            if ease>0.85:
                if   self.tab==0: self._draw_relics_tab(px,py,pw,ph)
                elif self.tab==1: self._draw_examine_tab(px,py,pw,ph)
                elif self.tab==2: self._draw_enchant_tab(px,py,pw,ph)

                # Divider
                div_x=px+int(pw*0.63)
                pygame.draw.line(self.screen,self.shop_color2,(div_x,py+42),(div_x,py+ph-20),1)

                # Right column — Lyra + rumours
                right_cx=div_x+(px+pw-div_x)//2
                lyra_cy=py+ph*2//3
                self._draw_lyra(right_cx,lyra_cy)
                self._draw_dialogue_bubble(right_cx,lyra_cy-55)
                kn=self.font_tiny.render("Lyra, Antiquarian",True,(140,90,200))
                self.screen.blit(kn,(right_cx-kn.get_width()//2,lyra_cy+90))

                rum_x=div_x+12; rum_w=px+pw-div_x-24
                rum_y=py+82; rum_h=lyra_cy-65-rum_y
                self._draw_rumours(rum_x,rum_y,rum_w,rum_h)

            self._draw_message()
            pygame.display.flip()