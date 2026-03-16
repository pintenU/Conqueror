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

class InnScene:
    """
    The Rusty Flagon — full inn scene with innkeeper NPC,
    rumour board, rest options and potion buying.
    """

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

        # Rumour cycling
        import random as _r
        self._rumour_idx   = _r.randint(0, len(self.RUMOURS)-1)
        self._rumour_timer = 0.0
        self.RUMOUR_DUR    = 6.0

        # Dialogue state
        self._dialogue_idx = 0
        self._show_dialogue = False
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

    # ------------------------------------------------------------------ #

    def _gold(self):
        from src.scenes.chest_scene import GoldItem
        return sum(self.inventory.stack_count(it)
                   for it in self.inventory.items
                   if isinstance(it, GoldItem))

    def _spend_gold(self, amount):
        from src.scenes.chest_scene import GoldItem
        gold_item = next((it for it in self.inventory.items
                          if isinstance(it, GoldItem)), None)
        if gold_item is None: return False
        total = self.inventory.stack_count(gold_item)
        if total < amount: return False
        remaining = total - amount
        self.inventory.remove(gold_item)
        if remaining > 0:
            self.inventory.add(GoldItem(remaining))
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

    # ------------------------------------------------------------------ #

    def _draw_background(self):
        # Warm dark interior
        for y in range(self.H):
            t2 = y/self.H
            r  = int(28+18*t2); g2 = int(18+12*t2); b = int(10+6*t2)
            pygame.draw.line(self.screen,(r,g2,b),(0,y),(self.W,y))

        # Fireplace on the right wall
        pulse = 0.55+0.45*math.sin(self.time*2.2)
        flicker = 0.6+0.4*math.sin(self.time*5.1+0.8)
        fw,fh = 120,90
        fx = self.W-fw-40; fy = self.H-fh-30
        # Mantle
        pygame.draw.rect(self.screen,(100,80,50),(fx-12,fy-18,fw+24,18))
        pygame.draw.rect(self.screen,(75,58,32),(fx-12,fy-18,fw+24,18),2)
        # Firebox
        pygame.draw.rect(self.screen,(40,28,15),(fx,fy,fw,fh))
        pygame.draw.rect(self.screen,(65,45,22),(fx,fy,fw,fh),2)
        # Arch
        pygame.draw.ellipse(self.screen,(40,28,15),(fx,fy-fh//3,fw,fh//2))
        # Fire glow
        for fi,(fr,fg2,fb2,fa) in enumerate([
            (int(200*pulse*flicker),int(100*pulse),20,int(120*pulse)),
            (int(240*pulse),int(140*pulse*flicker),30,int(80*pulse)),
            (255,int(200*flicker),50,int(60*pulse))]):
            gs2=pygame.Surface((fw-fi*20,fh-fi*15),pygame.SRCALPHA)
            pygame.draw.ellipse(gs2,(fr,fg2,fb2,fa),(0,0,fw-fi*20,fh-fi*15))
            self.screen.blit(gs2,(fx+fi*10,fy+fi*8),special_flags=pygame.BLEND_RGBA_ADD)
        # Flame tips
        for fli in range(5):
            flx=fx+15+fli*18; fly=fy+fh//3
            fla=math.radians(-20+fli*10)+math.sin(self.time*4+fli)*0.3
            flen=20+int(15*math.sin(self.time*3+fli))
            pygame.draw.polygon(self.screen,(int(255*flicker),int(160*pulse),20),[
                (flx-5,fly),(flx+int(math.sin(fla)*flen),fly-flen),(flx+5,fly)])

        # Fireplace glow spilling onto floor
        gs3=pygame.Surface((300,200),pygame.SRCALPHA)
        pygame.draw.ellipse(gs3,(int(160*pulse),int(80*pulse),20,int(40*pulse)),(0,0,300,200))
        self.screen.blit(gs3,(fx-90,fy+40),special_flags=pygame.BLEND_RGBA_ADD)

        # Wooden beams on ceiling
        for bx2 in range(0,self.W,90):
            pygame.draw.rect(self.screen,(55,38,20),(bx2,0,22,35))
            pygame.draw.rect(self.screen,(42,28,12),(bx2,0,22,35),1)

        # Wall-mounted torch left side
        tx=60; ty=self.H//3
        pygame.draw.rect(self.screen,(80,60,30),(tx-3,ty,6,20))
        tp=0.7+0.3*math.sin(self.time*3.8+1.2)
        pygame.draw.polygon(self.screen,(int(220*tp),int(120*tp),20),[
            (tx-5,ty),(tx,ty-18),(tx+5,ty)])
        tgs=pygame.Surface((50,50),pygame.SRCALPHA)
        pygame.draw.circle(tgs,(int(200*tp),int(110*tp),20,int(50*tp)),(25,25),22)
        self.screen.blit(tgs,(tx-25,ty-28),special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_keeper(self, cx, cy):
        """Draw Borin the innkeeper — portly, friendly, holding a mug."""
        c = self.keeper_color
        dark = tuple(max(0,v-50) for v in c)
        apron = (210,195,165)

        # Body — portly
        pygame.draw.ellipse(self.screen,c,(cx-38,cy-15,76,95))
        pygame.draw.ellipse(self.screen,dark,(cx-38,cy-15,76,95),2)
        # Apron
        pygame.draw.polygon(self.screen,apron,[
            (cx-22,cy-10),(cx+22,cy-10),(cx+28,cy+75),(cx-28,cy+75)])
        pygame.draw.polygon(self.screen,(180,165,140),[
            (cx-22,cy-10),(cx+22,cy-10),(cx+28,cy+75),(cx-28,cy+75)],1)
        # Apron strings
        pygame.draw.line(self.screen,(180,165,140),(cx-22,cy-10),(cx-38,cy-18),2)
        pygame.draw.line(self.screen,(180,165,140),(cx+22,cy-10),(cx+38,cy-18),2)
        # Head — round and jovial
        pygame.draw.circle(self.screen,c,(cx,cy-35),32)
        pygame.draw.circle(self.screen,dark,(cx,cy-35),32,2)
        # Rosy cheeks
        for chx in [cx-15,cx+15]:
            chsurf=pygame.Surface((18,12),pygame.SRCALPHA)
            pygame.draw.ellipse(chsurf,(220,120,100,80),(0,0,18,12))
            self.screen.blit(chsurf,(chx-9,cy-30))
        # Eyes — friendly squint
        for ex in [cx-10,cx+10]:
            pygame.draw.circle(self.screen,(45,30,15),(ex,cy-38),5)
            pygame.draw.circle(self.screen,(255,220,180),(ex,cy-38),2)
        # Big smile
        pygame.draw.arc(self.screen,dark,(cx-12,cy-32,24,16),math.pi,2*math.pi,3)
        # Bushy eyebrows
        for ex,edir in [(cx-14,-1),(cx+6,1)]:
            pygame.draw.line(self.screen,(100,70,35),(ex,cy-46),(ex+edir*10,cy-43),3)
        # Moustache
        pygame.draw.arc(self.screen,(110,80,40),(cx-14,cy-34,14,10),0,math.pi,3)
        pygame.draw.arc(self.screen,(110,80,40),(cx+0,cy-34,14,10),0,math.pi,3)
        # Ale mug in right hand
        mx=cx+42; my=cy+10
        pygame.draw.rect(self.screen,(110,80,40),(mx,my,22,28))
        pygame.draw.rect(self.screen,(80,55,22),(mx,my,22,28),2)
        pygame.draw.arc(self.screen,(80,55,22),(mx+18,my+4,14,16),-math.pi/2,math.pi/2,3)
        # Foam on top
        foam_s=pygame.Surface((22,10),pygame.SRCALPHA)
        pygame.draw.ellipse(foam_s,(235,228,215,200),(0,0,22,10))
        self.screen.blit(foam_s,(mx,my-4))
        # Arm holding mug
        pygame.draw.line(self.screen,c,(cx+36,cy+5),(mx,my+10),8)

    def _draw_rumour_board(self, x, y, w):
        """Notice board with current rumour."""
        bh = 65
        pygame.draw.rect(self.screen,(100,75,40),(x,y,w,bh))
        pygame.draw.rect(self.screen,(75,55,25),(x,y,w,bh),2)
        # Corner nails
        for nx2,ny2 in [(x+5,y+5),(x+w-5,y+5),(x+5,y+bh-5),(x+w-5,y+bh-5)]:
            pygame.draw.circle(self.screen,(160,130,55),(nx2,ny2),3)
        # Paper
        pygame.draw.rect(self.screen,(215,202,175),(x+8,y+8,w-16,bh-16))
        pygame.draw.rect(self.screen,(180,165,140),(x+8,y+8,w-16,bh-16),1)
        # Header
        hdr=self.font_tiny.render("NOTICE BOARD",True,(100,78,38))
        self.screen.blit(hdr,(x+w//2-hdr.get_width()//2,y+10))
        # Rumour text — word wrap
        rumour = self.RUMOURS[self._rumour_idx]
        words = rumour.split()
        lines = []; cur = ""
        for word in words:
            test = cur+(" " if cur else "")+word
            if self.font_tiny.size(test)[0] < w-24:
                cur = test
            else:
                lines.append(cur); cur = word
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
        """Speech bubble above innkeeper."""
        lines = self._current_dialogue.split("\n")
        max_w = max(self.font_small.size(l)[0] for l in lines)+20
        bh2 = len(lines)*18+14
        bx = cx-max_w//2; by = cy-bh2-20
        # Bubble
        pygame.draw.rect(self.screen,(240,228,200),(bx,by,max_w,bh2),border_radius=6)
        pygame.draw.rect(self.screen,(180,150,90),(bx,by,max_w,bh2),2,border_radius=6)
        # Tail
        pygame.draw.polygon(self.screen,(240,228,200),[
            (cx-8,by+bh2),(cx+8,by+bh2),(cx,by+bh2+14)])
        pygame.draw.line(self.screen,(180,150,90),(cx-8,by+bh2),(cx,by+bh2+14),2)
        pygame.draw.line(self.screen,(180,150,90),(cx+8,by+bh2),(cx,by+bh2+14),2)
        for li,line in enumerate(lines):
            ls=self.font_small.render(line,True,(55,40,20))
            self.screen.blit(ls,(bx+10,by+7+li*18))

    def _draw_options(self, x, y, w, h, ease):
        if ease < 0.8: return
        hp=self._player_hp(); mhp=self._player_max_hp(); gold=self._gold()
        options=[
            {"label":"Light Rest",   "detail":f"Restore {self.PARTIAL_HEAL} HP",
             "cost":self.PARTIAL_COST,"afford":gold>=self.PARTIAL_COST,
             "useful":hp<mhp,"icon":(80,160,120)},
            {"label":"Full Rest",    "detail":"Restore all HP",
             "cost":self.FULL_COST,  "afford":gold>=self.FULL_COST,
             "useful":hp<mhp,"icon":(60,140,200)},
            {"label":"Buy Potion",   "detail":"Restores 5 HP in combat",
             "cost":self.POTION_COST,"afford":gold>=self.POTION_COST,
             "useful":True,"icon":(180,60,60)},
            {"label":"Leave",        "detail":"Head back outside",
             "cost":0,"afford":True,"useful":True,"icon":(120,95,55)},
        ]
        row_h=52; row_w=int(w*0.88)
        rx=x+20; start_y=y+55
        for i,opt in enumerate(options):
            ry=start_y+i*row_h; is_sel=(i==self.selected)
            tv=1.0 if is_sel else 0.0
            can=opt["afford"] and opt["useful"]
            bg=pygame.Surface((row_w,row_h-6),pygame.SRCALPHA)
            bg.fill((int(28+20*tv),int(20+15*tv),int(12+8*tv),210))
            self.screen.blit(bg,(rx,ry))
            bc=tuple(int(a+(b-a)*tv) for a,b in
                     zip((55,42,26),(180,145,70))) if can else (35,26,14)
            pygame.draw.rect(self.screen,bc,(rx,ry,row_w,row_h-6),2 if is_sel else 1)
            pygame.draw.circle(self.screen,opt["icon"],(rx+20,ry+(row_h-6)//2),9)
            nc=(220,190,120) if (is_sel and can) else (140,110,65) if can else (75,58,35)
            ns=self.font_medium.render(opt["label"],True,nc)
            self.screen.blit(ns,(rx+38,ry+7))
            ds=self.font_tiny.render(opt["detail"],True,(100,78,45))
            self.screen.blit(ds,(rx+38,ry+7+ns.get_height()+2))
            if opt["cost"]>0:
                cs=self.font_medium.render(f"{opt['cost']}g",True,
                    (220,185,50) if opt["afford"] else (120,70,40))
                self.screen.blit(cs,(rx+row_w-cs.get_width()-10,
                                     ry+(row_h-6)//2-cs.get_height()//2))
            elif opt["label"]=="Leave":
                es=self.font_tiny.render("free",True,(80,62,34))
                self.screen.blit(es,(rx+row_w-es.get_width()-10,
                                     ry+(row_h-6)//2-es.get_height()//2))
            if is_sel:
                arr=self.font_small.render("▶",True,self.shop_color)
                self.screen.blit(arr,(rx+2,ry+(row_h-6)//2-arr.get_height()//2))
        self._draw_hp_bar(rx,start_y+len(options)*row_h+6,row_w)
        hint=self.font_tiny.render("↑ ↓  select    ENTER  confirm    ESC  leave",
                                    True,(70,54,28))
        self.screen.blit(hint,(self.W//2-hint.get_width()//2,y+h-hint.get_height()-10))

    def _draw_message(self):
        if not self._message or self._message_timer<=0: return
        alpha=min(1.0,self._message_timer/0.4)
        col=(120,200,120) if self._msg_good else (200,100,80)
        ms=self.font_small.render(self._message,True,col)
        bg=pygame.Surface((ms.get_width()+20,ms.get_height()+8),pygame.SRCALPHA)
        bg.fill((14,10,6,int(210*alpha)))
        bx=self.W//2-bg.get_width()//2; by=80
        self.screen.blit(bg,(bx,by))
        pygame.draw.rect(self.screen,col,(bx,by,bg.get_width(),bg.get_height()),1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms,(bx+10,by+4))

    def _do_action(self, idx):
        hp=self._player_hp(); mhp=self._player_max_hp(); gold=self._gold()
        if idx==0:
            if hp>=mhp:
                self._message="You are already at full health!"; self._msg_good=False
            elif gold<self.PARTIAL_COST:
                self._message=f"Need {self.PARTIAL_COST} gold!"; self._msg_good=False
            else:
                self._spend_gold(self.PARTIAL_COST)
                healed=min(self.PARTIAL_HEAL,mhp-hp)
                self._play_rest_animation(full_rest=False)
                self._set_hp(hp+healed)
                self._message=f"You rest briefly. +{healed} HP  ({self._player_hp()}/{mhp})"
                self._msg_good=True
                import random as _r; self._current_dialogue=_r.choice(self._dialogues)
        elif idx==1:
            if hp>=mhp:
                self._message="You are already at full health!"; self._msg_good=False
            elif gold<self.FULL_COST:
                self._message=f"Need {self.FULL_COST} gold!"; self._msg_good=False
            else:
                self._spend_gold(self.FULL_COST)
                self._play_rest_animation(full_rest=True)
                self._set_hp(mhp)
                self._message=f"You sleep soundly. Full HP restored!  ({mhp}/{mhp})"
                self._msg_good=True
                import random as _r; self._current_dialogue=_r.choice(self._dialogues)
        elif idx==2:
            if gold<self.POTION_COST:
                self._message=f"Need {self.POTION_COST} gold!"; self._msg_good=False
            else:
                from src.scenes.chest_scene import PotionItem
                self._spend_gold(self.POTION_COST)
                self.inventory.add(PotionItem())
                self._message="Bought a Healing Potion!"; self._msg_good=True
        elif idx==3:
            return "town"
        self._message_timer=2.5
        return None

    def _play_rest_animation(self, full_rest=False):
        """Fade to black with Zzz, then fade back in."""
        import math
        W,H = self.W, self.H
        clock = pygame.time.Clock()
        font_big  = pygame.font.SysFont("courier new", 42, bold=True)
        font_med  = pygame.font.SysFont("courier new", 22, bold=True)

        # Capture current screen
        snapshot = self.screen.copy()

        zzz_positions = [
            (W//2-20, H//2+20,  28, 0.0),
            (W//2+10, H//2,     36, 0.4),
            (W//2+40, H//2-30, 44, 0.8),
        ]

        total = 2.2 if not full_rest else 3.0
        t = 0.0
        while t < total:
            dt = clock.tick(60)/1000.0
            t += dt

            # Phase: 0-0.6 fade out, 0.6-1.4 black hold with zzz, 1.4-2.2 fade in
            if t < 0.6:
                alpha = int(255 * (t/0.6))
            elif t < total-0.6:
                alpha = 255
            else:
                alpha = int(255 * ((total-t)/0.6))

            self.screen.blit(snapshot,(0,0))

            # Dark overlay
            overlay = pygame.Surface((W,H))
            overlay.fill((8,5,3))
            overlay.set_alpha(alpha)
            self.screen.blit(overlay,(0,0))

            # Zzz letters during hold phase
            if 0.5 < t < total-0.4:
                hold_t = t - 0.5
                for i,(zx,zy,zsize,zdelay) in enumerate(zzz_positions):
                    age = hold_t - zdelay
                    if age < 0: continue
                    # Float upward and fade out over 1.2s, then loop
                    cycle = age % 1.4
                    if cycle > 1.2: continue
                    a2 = int(255 * min(1.0, (1.0 - cycle/1.2)))
                    rise = int(cycle * 40)
                    zf = pygame.font.SysFont("courier new", zsize, bold=True)
                    zs = zf.render("Z", True, (180,220,255))
                    zs.set_alpha(a2)
                    self.screen.blit(zs,(zx, zy-rise))

            # "Resting..." or "Sleeping deeply..." text
            if 0.7 < t < total-0.3:
                fade_in = min(1.0,(t-0.7)/0.3)
                fade_out = min(1.0,(total-0.3-t)/0.3)
                ta = int(255*min(fade_in,fade_out))
                msg = "Sleeping deeply..." if full_rest else "Resting..."
                ms = font_med.render(msg, True, (160,185,220))
                ms.set_alpha(ta)
                self.screen.blit(ms,(W//2-ms.get_width()//2, H//2+60))

            pygame.display.flip()

    def run(self)->str:
        while True:
            dt=self.clock.tick(60)/1000.0
            self.time+=dt
            self.open_anim=min(self.open_anim+dt,self.OPEN_DUR)
            ease=1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            self._message_timer=max(0.0,self._message_timer-dt)
            self._rumour_timer+=dt
            if self._rumour_timer>=self.RUMOUR_DUR:
                self._rumour_timer=0.0
                self._rumour_idx=(self._rumour_idx+1)%len(self.RUMOURS)

            for event in pygame.event.get():
                if event.type==pygame.QUIT: return "exit"
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: return "town"
                    if event.key==pygame.K_UP:   self.selected=max(0,self.selected-1)
                    if event.key==pygame.K_DOWN: self.selected=min(3,self.selected+1)
                    if event.key in (pygame.K_RETURN,pygame.K_SPACE):
                        result=self._do_action(self.selected)
                        if result: return result

            self._draw_background()

            # Full-screen panel
            pw = int(self.W*0.88); ph = int(self.H*0.86)
            px = self.W//2-pw//2;  py = self.H//2-ph//2

            w2=int(pw*ease); h2=int(ph*ease)
            px2=self.W//2-w2//2; py2=self.H//2-h2//2
            if w2>4:
                bg=pygame.Surface((w2,h2),pygame.SRCALPHA)
                bg.fill((18,12,7,245))
                self.screen.blit(bg,(px2,py2))
                pygame.draw.rect(self.screen,self.shop_color,(px2,py2,w2,h2),2)
                pygame.draw.rect(self.screen,tuple(max(0,v-40) for v in self.shop_color),
                                 (px2+5,py2+5,w2-10,h2-10),1)
                sz=14
                for bx2,by2,dx,dy in [(px2,py2,1,1),(px2+w2,py2,-1,1),
                                       (px2,py2+h2,1,-1),(px2+w2,py2+h2,-1,-1)]:
                    pygame.draw.line(self.screen,(185,150,68),(bx2,by2),(bx2+dx*sz,by2),2)
                    pygame.draw.line(self.screen,(185,150,68),(bx2,by2),(bx2,by2+dy*sz),2)

            if ease>0.7:
                # Title — centred at top
                title=self.font_title.render("The Rusty Flagon",True,(215,180,105))
                self.screen.blit(title,(self.W//2-title.get_width()//2, py+14))
                pygame.draw.line(self.screen,self.shop_color,
                                 (px+24,py+14+title.get_height()+6),
                                 (px+pw-24,py+14+title.get_height()+6),1)

                # Gold — top right
                gold_s=self.font_medium.render(f"Gold: {self._gold()}",True,(220,185,60))
                self.screen.blit(gold_s,(px+pw-gold_s.get_width()-18,py+16))

                # Left column — menu options (takes 55% of width)
                left_w = int(pw*0.55)
                self._draw_options(px, py, left_w, ph, ease)

                # Divider between columns
                div_x = px + left_w
                pygame.draw.line(self.screen,
                                 tuple(max(0,v-30) for v in self.shop_color),
                                 (div_x, py+40),(div_x, py+ph-20),1)

                # Right column — innkeeper + rumour board
                right_cx = div_x + (pw - left_w)//2

                # Innkeeper — centred in right column, lower half
                keeper_cx = right_cx
                keeper_cy = py + ph*2//3
                self._draw_keeper(keeper_cx, keeper_cy)
                # Keeper name
                kn=self.font_tiny.render("Borin, Innkeeper",True,(130,100,55))
                self.screen.blit(kn,(keeper_cx-kn.get_width()//2, keeper_cy+95))
                # Speech bubble above keeper
                self._draw_dialogue_bubble(keeper_cx, keeper_cy-45)

                # Rumour board — top of right column
                board_x = div_x+12
                board_w  = pw - left_w - 24
                self._draw_rumour_board(board_x, py+48, board_w)

            self._draw_message()
            pygame.display.flip()


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