import pygame
import math
import random


# ---------------------------------------------------------------------------
# Shop item definition
# ---------------------------------------------------------------------------

class ShopItem:
    def __init__(self, item_factory, price, stock=-1, description=None):
        """
        item_factory — callable that returns a fresh Item instance
        price        — gold cost
        stock        — -1 = unlimited, otherwise depletes
        """
        self.item_factory = item_factory
        self.price        = price
        self.stock        = stock
        self._instance    = item_factory()   # for display
        self.description  = description or self._instance.description

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
# Base ShopScene (Dredge-style)
# ---------------------------------------------------------------------------

class ShopScene:
    """
    Base class for all shop interiors.
    Subclasses set self.shop_items, self.shop_name, self.shop_color,
    self.bg_draw_fn and optionally self.sell_enabled.
    """

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

        # Overridden by subclass
        self.shop_name    = "Shop"
        self.shop_color   = (140, 110, 60)
        self.shop_items   = []
        self.sell_enabled = True
        self.flavor_text  = "What can I do for you?"
        self.keeper_color = (180, 150, 100)

        # State
        self.mode          = "buy"    # "buy" or "sell"
        self.selected_buy  = 0
        self.selected_sell = 0
        self.message       = ""
        self.message_timer = 0.0
        self.open_anim     = 0.0
        self.OPEN_DUR      = 0.4

        # Hover states for mode buttons
        self._buy_hover  = 0.0
        self._sell_hover = 0.0
        self._back_hover = 0.0

        self._setup()

    def _setup(self):
        """Called after __init__ — subclasses populate shop_items here."""
        pass

    # ------------------------------------------------------------------ #
    # Gold helper
    # ------------------------------------------------------------------ #

    def _gold(self):
        from src.scenes.chest_scene import GoldItem
        return self.inventory.stack_count(
            next((it for it in self.inventory.items
                  if isinstance(it, GoldItem)), None)) if \
            any(isinstance(it, GoldItem) for it in self.inventory.items) else 0

    def _spend_gold(self, amount):
        from src.scenes.chest_scene import GoldItem
        gold_item = next((it for it in self.inventory.items
                         if isinstance(it, GoldItem)), None)
        if gold_item is None:
            return False
        total = self.inventory.stack_count(gold_item)
        if total < amount:
            return False
        # Remove entire gold stack then add back remainder
        remaining = total - amount
        self.inventory.remove(gold_item)
        if remaining > 0:
            self.inventory.add(GoldItem(remaining))
        return True

    def _sell_item(self, item):
        """Sell an item for half its value."""
        from src.scenes.chest_scene import GoldItem, SwordItem, SunSwordItem
        sell_prices = {
            "Healing Potion": 4,
            "Dungeon Key":    8,
            "Candle":         1,
            "Iron Shield":    18,
            "Sun Sword":      25,
            "Sword":          10,
            "Gold":           0,   # can't sell gold
            "Exit Key":       0,
        }
        price = sell_prices.get(item.name, 2)
        if price == 0:
            return False, "Can't sell that here."
        # For stackables sell one unit at a time
        if getattr(item,'stackable',False):
            self.inventory.remove_one(type(item))
        else:
            self.inventory.remove(item)
        gold = GoldItem(price)
        self.inventory.add(gold)
        return True, f"Sold {item.name} for {price} gold!"

    # ------------------------------------------------------------------ #
    # Background — overridden per shop
    # ------------------------------------------------------------------ #

    def _draw_background(self):
        self.screen.fill((20, 15, 10))

    # ------------------------------------------------------------------ #
    # Shopkeeper illustration
    # ------------------------------------------------------------------ #

    def _draw_keeper(self, cx, cy, color):
        """Simple keeper silhouette."""
        c = color
        dark = tuple(max(0,v-40) for v in c)
        # Body
        pygame.draw.ellipse(self.screen, c,
                            (cx-30, cy-20, 60, 80))
        pygame.draw.ellipse(self.screen, dark,
                            (cx-30, cy-20, 60, 80), 2)
        # Head
        pygame.draw.circle(self.screen, c, (cx, cy-35), 28)
        pygame.draw.circle(self.screen, dark, (cx, cy-35), 28, 2)
        # Eyes
        pygame.draw.circle(self.screen, (40,30,15), (cx-9, cy-38), 5)
        pygame.draw.circle(self.screen, (40,30,15), (cx+9, cy-38), 5)
        pygame.draw.circle(self.screen, (220,200,160),(cx-9,cy-38),2)
        pygame.draw.circle(self.screen, (220,200,160),(cx+9,cy-38),2)
        # Smile
        pygame.draw.arc(self.screen, dark,
                        (cx-10, cy-32, 20, 12), math.pi, 2*math.pi, 2)

    # ------------------------------------------------------------------ #
    # Layout constants
    # ------------------------------------------------------------------ #

    def _panel_rect(self):
        pw = int(self.W * 0.72)
        ph = int(self.H * 0.78)
        px = (self.W - pw) // 2
        py = (self.H - ph) // 2
        return px, py, pw, ph

    # ------------------------------------------------------------------ #
    # Draw panel
    # ------------------------------------------------------------------ #

    def _draw_panel(self, t):
        px, py, pw, ph = self._panel_rect()
        ease = 1-(1-t)**3
        w = int(pw*ease); h = int(ph*ease)
        x = self.W//2 - w//2
        y = self.H//2 - h//2
        if w < 4: return

        sh = pygame.Surface((w+14,h+14),pygame.SRCALPHA)
        sh.fill((0,0,0,100))
        self.screen.blit(sh,(x-7,y-7))

        panel = pygame.Surface((w,h),pygame.SRCALPHA)
        panel.fill((16,12,8,248))
        self.screen.blit(panel,(x,y))

        pygame.draw.rect(self.screen,self.shop_color,(x,y,w,h),2)
        pygame.draw.rect(self.screen,
                         tuple(max(0,c-40) for c in self.shop_color),
                         (x+5,y+5,w-10,h-10),1)

        c2 = tuple(min(255,c+30) for c in self.shop_color)
        sz = 14
        for bx,by,dx,dy in [(x,y,1,1),(x+w,y,-1,1),
                              (x,y+h,1,-1),(x+w,y+h,-1,-1)]:
            pygame.draw.line(self.screen,c2,(bx,by),(bx+dx*sz,by),2)
            pygame.draw.line(self.screen,c2,(bx,by),(bx,by+dy*sz),2)
            pygame.draw.circle(self.screen,c2,(bx,by),3)

        if t > 0.8:
            title = self.font_title.render(self.shop_name,True,
                                           tuple(min(255,c+80) for c in self.shop_color))
            self.screen.blit(title,(self.W//2-title.get_width()//2,y+12))
            rule_y = y+12+title.get_height()+4
            pygame.draw.line(self.screen,self.shop_color,
                             (x+20,rule_y),(x+w-20,rule_y),1)

            # Gold display
            gold = self._gold()
            gs = self.font_medium.render(f"Gold: {gold}",True,(220,185,60))
            self.screen.blit(gs,(x+w-gs.get_width()-16, y+12))

    # ------------------------------------------------------------------ #
    # Mode tabs
    # ------------------------------------------------------------------ #

    def _draw_tabs(self, t, x, y, w, h):
        if t < 0.8: return
        tab_y = y + 55
        tab_w = 100
        tab_h = 32

        for i,(label,mode) in enumerate([("BUY","buy"),("SELL","sell")]):
            if not self.sell_enabled and mode == "sell":
                continue
            tx2 = x + 20 + i*110
            is_sel = self.mode == mode
            col = self.shop_color if is_sel else (50,38,22)
            fill = pygame.Surface((tab_w,tab_h),pygame.SRCALPHA)
            fill.fill((*col,220) if is_sel else (25,18,10,180))
            self.screen.blit(fill,(tx2,tab_y))
            pygame.draw.rect(self.screen,col,(tx2,tab_y,tab_w,tab_h),2)
            lbl = self.font_small.render(label,True,
                (220,190,110) if is_sel else (100,78,45))
            self.screen.blit(lbl,(tx2+tab_w//2-lbl.get_width()//2,
                                  tab_y+tab_h//2-lbl.get_height()//2))

        # Back button
        bx2 = x + w - 120
        bt = self._back_hover
        fill = pygame.Surface((100,32),pygame.SRCALPHA)
        fill.fill((int(18+30*bt),int(14+24*bt),int(8+14*bt),200))
        self.screen.blit(fill,(bx2,tab_y))
        def lc(a,b): return tuple(int(a[i]+(b[i]-a[i])*bt) for i in range(3))
        pygame.draw.rect(self.screen,lc((60,45,25),(160,125,60)),
                         (bx2,tab_y,100,32),2)
        bl = self.font_small.render("LEAVE",True,lc((120,92,48),(210,175,90)))
        self.screen.blit(bl,(bx2+50-bl.get_width()//2,tab_y+16-bl.get_height()//2))

    # ------------------------------------------------------------------ #
    # Item list
    # ------------------------------------------------------------------ #

    def _draw_buy_list(self, x, y, w, h):
        items    = self.shop_items
        if not items:
            ns = self.font_small.render("Nothing for sale.",True,(100,78,45))
            self.screen.blit(ns,(x+20,y+100))
            return

        list_y   = y + 100
        row_h    = 58
        icon_s   = 36
        row_w    = w - 40
        gold     = self._gold()

        for i, si in enumerate(items):
            ry      = list_y + i*row_h
            is_sel  = (i == self.selected_buy)
            can_buy = gold >= si.price and si.in_stock()

            row_bg = pygame.Surface((row_w,row_h-4),pygame.SRCALPHA)
            if is_sel:
                row_bg.fill((35,26,14,220))
            else:
                row_bg.fill((18,13,7,160))
            self.screen.blit(row_bg,(x+20,ry))

            bc = self.shop_color if (is_sel and can_buy) else \
                 (80,60,30) if is_sel else (40,30,15)
            pygame.draw.rect(self.screen,bc,(x+20,ry,row_w,row_h-4),
                             2 if is_sel else 1)

            # Icon
            si.draw_icon(self.screen, x+50, ry+row_h//2-2, icon_s)

            # Name
            nc = (220,190,120) if (is_sel and can_buy) else \
                 (150,115,65) if can_buy else (80,62,40)
            ns2 = self.font_medium.render(si.name,True,nc)
            self.screen.blit(ns2,(x+80,ry+8))

            # Description
            ds = self.font_tiny.render(si.description,True,(100,78,45))
            self.screen.blit(ds,(x+80,ry+8+ns2.get_height()+2))

            # Price
            pc = (220,185,50) if can_buy else (100,75,35)
            ps = self.font_medium.render(f"{si.price}g",True,pc)
            self.screen.blit(ps,(x+20+row_w-ps.get_width()-8,
                                  ry+row_h//2-ps.get_height()//2-2))

            # Stock
            if si.stock > 0:
                ss2 = self.font_tiny.render(f"x{si.stock}",True,(120,95,50))
                self.screen.blit(ss2,(x+20+row_w-ss2.get_width()-8,
                                      ry+row_h//2+6))
            elif si.stock == 0:
                oos = self.font_tiny.render("OUT OF STOCK",True,(120,60,40))
                self.screen.blit(oos,(x+20+row_w-oos.get_width()-8,
                                       ry+row_h//2-oos.get_height()//2-2))

            # Selector arrow
            if is_sel:
                arr = self.font_small.render("▶",True,self.shop_color)
                self.screen.blit(arr,(x+22,ry+row_h//2-arr.get_height()//2-2))

        # Buy hint
        hint = self.font_tiny.render(
            "↑ ↓  select    ENTER  buy    ESC  leave",True,(70,54,28))
        self.screen.blit(hint,(x+20,y+h-hint.get_height()-10))

    def _draw_sell_list(self, x, y, w, h):
        # Only show sellable items
        from src.scenes.chest_scene import GoldItem, ExitKeyItem
        items = [it for it in self.inventory.items
                 if not isinstance(it,(GoldItem,ExitKeyItem))]

        list_y = y + 100
        row_h  = 58
        icon_s = 36
        row_w  = w - 40

        if not items:
            ns = self.font_small.render("Nothing to sell.",True,(100,78,45))
            self.screen.blit(ns,(x+20,y+100))
        else:
            sell_prices = {
                "Healing Potion":4,"Dungeon Key":8,"Candle":1,
                "Iron Shield":18,"Sun Sword":25,"Sword":10,
            }
            for i,item in enumerate(items):
                ry     = list_y + i*row_h
                is_sel = (i == self.selected_sell)
                price  = sell_prices.get(item.name,2)

                row_bg = pygame.Surface((row_w,row_h-4),pygame.SRCALPHA)
                row_bg.fill((35,26,14,220) if is_sel else (18,13,7,160))
                self.screen.blit(row_bg,(x+20,ry))
                bc = self.shop_color if is_sel else (40,30,15)
                pygame.draw.rect(self.screen,bc,(x+20,ry,row_w,row_h-4),
                                 2 if is_sel else 1)

                item.draw_icon(self.screen,x+50,ry+row_h//2-2,icon_s)
                nc = (220,190,120) if is_sel else (150,115,65)
                # Show stack count if stackable
                stack_n = self.inventory.stack_count(item)
                name_label = item.name
                if getattr(item,'stackable',False) and stack_n > 1:
                    name_label = f"{item.name}  (x{stack_n})"
                ns2 = self.font_medium.render(name_label,True,nc)
                self.screen.blit(ns2,(x+80,ry+8))
                ds = self.font_tiny.render(item.description,True,(100,78,45))
                self.screen.blit(ds,(x+80,ry+8+ns2.get_height()+2))

                ps = self.font_medium.render(f"{price}g each",True,(180,155,45))
                self.screen.blit(ps,(x+20+row_w-ps.get_width()-8,
                                      ry+row_h//2-ps.get_height()//2-2))
                if is_sel:
                    arr = self.font_small.render("▶",True,self.shop_color)
                    self.screen.blit(arr,(x+22,ry+row_h//2-arr.get_height()//2-2))

        hint = self.font_tiny.render(
            "↑ ↓  select    ENTER  sell    ESC  leave",True,(70,54,28))
        self.screen.blit(hint,(x+20,y+h-hint.get_height()-10))

    # ------------------------------------------------------------------ #
    # Message banner
    # ------------------------------------------------------------------ #

    def _draw_message(self, x, y, w):
        if not self.message or self.message_timer <= 0:
            return
        alpha = min(1.0, self.message_timer/0.4)
        ms  = self.font_small.render(self.message,True,(220,195,120))
        bg  = pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
        bg.fill((14,10,6,int(220*alpha)))
        bx2 = self.W//2 - bg.get_width()//2
        by2 = y - bg.get_height() - 8
        self.screen.blit(bg,(bx2,by2))
        pygame.draw.rect(self.screen,self.shop_color,
                         (bx2,by2,bg.get_width(),bg.get_height()),1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms,(bx2+10,by2+4))

    # ------------------------------------------------------------------ #
    # Flavor / keeper
    # ------------------------------------------------------------------ #

    def _draw_keeper_area(self, x, y, w, t):
        if t < 0.8: return
        kx = x + w - 90
        ky = y + 45
        self._draw_keeper(kx, ky, self.keeper_color)
        fs = self.font_tiny.render(f'"{self.flavor_text}"',True,(160,135,85))
        self.screen.blit(fs,(kx-fs.get_width()//2, ky+65))

    # ------------------------------------------------------------------ #
    # Input handling
    # ------------------------------------------------------------------ #

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
                self.message = "Out of stock!"
                self.message_timer = 2.0
            elif self._gold() < si.price:
                self.message = f"Need {si.price} gold — you have {self._gold()}!"
                self.message_timer = 2.5
            else:
                if self._spend_gold(si.price):
                    item = si.buy()
                    self.inventory.add(item)
                    self.message = f"Bought {si.name} for {si.price} gold!"
                    self.message_timer = 2.0

    def _handle_sell(self, key):
        from src.scenes.chest_scene import GoldItem, ExitKeyItem
        items = [it for it in self.inventory.items
                 if not isinstance(it,(GoldItem,ExitKeyItem))]
        if not items: return
        if key == pygame.K_UP:
            self.selected_sell = max(0, self.selected_sell-1)
        elif key == pygame.K_DOWN:
            self.selected_sell = min(len(items)-1, self.selected_sell+1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            item = items[self.selected_sell]
            ok, msg = self._sell_item(item)
            self.message = msg
            self.message_timer = 2.0
            # Only move selector up if item is now fully gone
            from src.scenes.chest_scene import GoldItem, ExitKeyItem
            remaining = [it for it in self.inventory.items
                         if not isinstance(it,(GoldItem,ExitKeyItem))]
            self.selected_sell = max(0, min(self.selected_sell,
                                            len(remaining)-1))

    # ------------------------------------------------------------------ #
    # Tab / back hit test
    # ------------------------------------------------------------------ #

    def _tab_rects(self, x, y, w, h):
        tab_y = y + 55
        rects = {}
        for i,(label,mode) in enumerate([("BUY","buy"),("SELL","sell")]):
            rects[mode] = pygame.Rect(x+20+i*110, tab_y, 100, 32)
        rects["back"] = pygame.Rect(x+w-120, tab_y, 100, 32)
        return rects

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while True:
            dt         = self.clock.tick(60)/1000.0
            self.time += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            t          = min(1.0, self.open_anim/self.OPEN_DUR)
            self.message_timer = max(0.0, self.message_timer-dt)
            mouse      = pygame.mouse.get_pos()

            px,py,pw,ph = self._panel_rect()
            tabs = self._tab_rects(px,py,pw,ph)

            # Hover updates
            self._back_hover += (
                (1.0 if tabs["back"].collidepoint(mouse) else 0.0)
                - self._back_hover) * 10*dt
            self._back_hover = max(0.0,min(1.0,self._back_hover))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "town"
                    if event.key == pygame.K_TAB:
                        if self.sell_enabled:
                            self.mode = "sell" if self.mode=="buy" else "buy"
                    if self.mode == "buy":
                        self._handle_buy(event.key)
                    else:
                        self._handle_sell(event.key)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if tabs["back"].collidepoint(mouse):
                        return "town"
                    if tabs.get("buy") and tabs["buy"].collidepoint(mouse):
                        self.mode = "buy"
                    if self.sell_enabled and tabs.get("sell") and \
                            tabs["sell"].collidepoint(mouse):
                        self.mode = "sell"

            # Draw
            self._draw_background()

            ease = 1-(1-t)**3
            if ease > 0.1:
                self._draw_panel(t)
                self._draw_tabs(t, px, py, pw, ph)
                self._draw_keeper_area(px, py, pw, t)
                if t > 0.85:
                    if self.mode == "buy":
                        self._draw_buy_list(px,py,pw,ph)
                    else:
                        self._draw_sell_list(px,py,pw,ph)
                    self._draw_message(px,py,pw)

            pygame.display.flip()


# ===========================================================================
# Individual shop subclasses
# ===========================================================================

class InnScene(ShopScene):
    def _setup(self):
        from src.scenes.chest_scene import PotionItem
        self.shop_name    = "The Rusty Flagon"
        self.shop_color   = (140, 95, 45)
        self.keeper_color = (190, 155, 100)
        self.flavor_text  = "Rest up, friend."
        self.sell_enabled = False
        self.shop_items   = [
            ShopItem(PotionItem,  6, -1, "Restores 5 HP in combat."),
            ShopItem(PotionItem, 10, -1, "Buy 2 potions at once."),   # placeholder
        ]
        # Rest option — heals to full for gold
        self._rest_cost = 15

    def _draw_background(self):
        for y in range(self.H):
            t2 = y/self.H
            r  = int(25+15*t2); g2 = int(16+10*t2); b = int(8+5*t2)
            pygame.draw.line(self.screen,(r,g2,b),(0,y),(self.W,y))
        # Fireplace glow
        pulse = 0.6+0.4*math.sin(self.time*2)
        glow  = pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        pygame.draw.ellipse(glow,(160,80,20,int(35*pulse)),
                            (self.W//2-200,self.H-200,400,300))
        self.screen.blit(glow,(0,0))

    def _draw_keeper_area(self, x, y, w, t):
        if t < 0.8: return
        kx = x+w-90; ky = y+45
        self._draw_keeper(kx, ky, self.keeper_color)
        pygame.draw.rect(self.screen,(100,70,35),(kx+18,ky+10,16,18))
        pygame.draw.arc(self.screen,(80,55,25),(kx+30,ky+12,10,12),
                        -math.pi/2,math.pi/2,3)
        fs = self.font_tiny.render(f'"{self.flavor_text}"',True,(160,135,85))
        self.screen.blit(fs,(kx-fs.get_width()//2,ky+65))


class GeneralShopScene(ShopScene):
    def _setup(self):
        from src.scenes.chest_scene import PotionItem, KeyItem
        self.shop_name    = "Mira's Sundries"
        self.shop_color   = (70, 130, 80)
        self.keeper_color = (160, 190, 150)
        self.flavor_text  = "Fine goods, fair prices!"
        self.sell_enabled = True
        self.shop_items   = [
            ShopItem(PotionItem,           6,  -1, "Restores 5 HP in combat."),
            ShopItem(lambda: KeyItem("key_ab"), 20, 3, "Opens a locked dungeon door."),
            ShopItem(lambda: KeyItem("key_ad"), 20, 3, "Opens a locked dungeon door."),
            ShopItem(lambda: KeyItem("key_ef"), 20, 3, "Opens a locked dungeon door."),
            ShopItem(lambda: KeyItem("key_dg"), 20, 3, "Opens a locked dungeon door."),
        ]

    def _draw_background(self):
        for y in range(self.H):
            t2 = y/self.H
            r  = int(18+12*t2); g2 = int(22+15*t2); b = int(12+8*t2)
            pygame.draw.line(self.screen,(r,g2,b),(0,y),(self.W,y))


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
            stackable = True
            amount    = 10
            name      = "Arrows (x10)"
            description = "A bundle of arrows. For future use."
            icon_color  = (160, 130, 70)
            def draw_icon(self, surface, cx, cy, size):
                s = size
                for i in range(3):
                    ox2 = (i-1)*6
                    pygame.draw.line(surface,(160,130,70),
                                     (cx+ox2,cy+s//3),(cx+ox2,cy-s//3),3)
                    pygame.draw.polygon(surface,(200,170,80),[
                        (cx+ox2,cy-s//3-6),(cx+ox2-4,cy-s//3),
                        (cx+ox2+4,cy-s//3)])

        from src.scenes.chest_scene import (IronHelmet, IronChestplate,
                                               IronLeggings, IronBoots)
        self.shop_items = [
            ShopItem(IronHelmet,      18, 3, "Reduces damage by 1."),
            ShopItem(IronChestplate,  32, 2, "Reduces damage by 3."),
            ShopItem(IronLeggings,    24, 2, "Reduces damage by 2."),
            ShopItem(IronBoots,       18, 3, "Reduces damage by 1."),
            ShopItem(HeavySwordItem,  25, 2, "Deals 10 damage. Two-handed."),
            ShopItem(ShieldItem,       22, 2, "Blocks one hit entirely."),
            ShopItem(ChainmailItem,    18, 3, "Reduces damage by 2 per hit."),
            ShopItem(ArrowBundleItem,   8,-1, "10 arrows. For future use."),
            ShopItem(SunSwordItem,     50, 1, "The legendary Sun Sword. Deals 12 damage."),
        ]

    def _draw_background(self):
        for y in range(self.H):
            t2 = y/self.H
            r  = int(22+18*t2); g2 = int(14+10*t2); b = int(8+5*t2)
            pygame.draw.line(self.screen,(r,g2,b),(0,y),(self.W,y))
        # Forge glow bottom
        pulse = 0.5+0.5*math.sin(self.time*3)
        glow  = pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        pygame.draw.ellipse(glow,(180,80,10,int(40*pulse)),
                            (self.W//2-180,self.H-180,360,260))
        self.screen.blit(glow,(0,0))


class AntiquityScene(ShopScene):
    def _setup(self):
        from src.scenes.chest_scene import SunSwordItem, ShieldItem
        self.shop_name    = "The Curio Cabinet"
        self.shop_color   = (120, 80, 170)
        self.keeper_color = (170, 140, 210)
        self.flavor_text  = "Every relic has a story..."
        self.sell_enabled = True

        class MysticOrbItem:
            stackable   = False
            name        = "Mystic Orb"
            description = "Swirling with power. Future relic."
            icon_color  = (160, 100, 220)
            def draw_icon(self, surface, cx, cy, size):
                s = size
                pygame.draw.circle(surface,(100,60,180),(cx,cy),s//2)
                pygame.draw.circle(surface,(160,100,220),(cx,cy),s//2,2)
                for a in range(0,360,60):
                    ra = math.radians(a)
                    pygame.draw.line(surface,(200,160,255),
                                     (cx,cy),
                                     (cx+int(math.cos(ra)*s//3),
                                      cy+int(math.sin(ra)*s//3)),1)

        self.shop_items = [
            ShopItem(SunSwordItem,  55, 1, "Blazing solar relic. Deals 12 damage."),
            ShopItem(ShieldItem,    40, 2, "Blocks one hit entirely."),
            ShopItem(MysticOrbItem, 35, 2, "A mysterious relic. Power unknown."),
        ]

    def _draw_background(self):
        for y in range(self.H):
            t2 = y/self.H
            r  = int(12+10*t2); g2 = int(8+6*t2); b = int(18+15*t2)
            pygame.draw.line(self.screen,(r,g2,b),(0,y),(self.W,y))
        # Mystical glow
        pulse = 0.5+0.5*math.sin(self.time*1.5)
        glow  = pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        pygame.draw.ellipse(glow,(80,30,140,int(30*pulse)),
                            (self.W//2-220,self.H//2-180,440,360))
        self.screen.blit(glow,(0,0))