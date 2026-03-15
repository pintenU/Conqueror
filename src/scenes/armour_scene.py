import pygame
import math


SLOTS      = ["helmet", "chestplate", "leggings", "boots"]
SLOT_ICONS = {"helmet":"⬡", "chestplate":"▣", "leggings":"▤", "boots":"▥"}

SLOT_POSITIONS = {
    "helmet":     (0, 0),
    "chestplate": (0, 1),
    "leggings":   (0, 2),
    "boots":      (0, 3),
}


def _lerp(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))


class ArmourScene:
    """
    Minecraft-inspired armour screen.
    Left column: 4 armour slots (helmet, chestplate, leggings, boots).
    Right column: inventory items that are armour pieces (equippable).
    Centre: player silhouette showing equipped pieces.
    """

    def __init__(self, screen, inventory, armour_system):
        self.screen        = screen
        self.W, self.H     = screen.get_size()
        self.clock         = pygame.time.Clock()
        self.time          = 0.0
        self.inventory     = inventory
        self.armour        = armour_system

        self.font_title  = pygame.font.SysFont("courier new", 28, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 16, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 13)
        self.font_tiny   = pygame.font.SysFont("courier new", 11)

        # Layout
        self.SLOT_SIZE  = 72
        self.SLOT_PAD   = 10
        panel_w         = int(self.W * 0.75)
        panel_h         = int(self.H * 0.82)
        self.PX         = (self.W - panel_w) // 2
        self.PY         = (self.H - panel_h) // 2
        self.PW         = panel_w
        self.PH         = panel_h

        # Armour slot rects (left column)
        self.slot_rects = {}
        slot_col_x = self.PX + 30
        slot_start_y = self.PY + 70
        for i, slot in enumerate(SLOTS):
            y = slot_start_y + i * (self.SLOT_SIZE + self.SLOT_PAD)
            self.slot_rects[slot] = pygame.Rect(slot_col_x, y,
                                                self.SLOT_SIZE, self.SLOT_SIZE)

        # Inventory list (right column) — only armour items
        self.inv_col_x  = self.PX + self.PW - 30 - int(panel_w * 0.38)
        self.inv_col_w  = int(panel_w * 0.38)
        self.inv_row_h  = 52
        self.inv_start_y = self.PY + 70

        # State
        self.selected_inv = 0
        self.hover_slot   = None
        self.message      = ""
        self.message_timer = 0.0
        self.open_anim    = 0.0
        self.OPEN_DUR     = 0.35

        self.dim_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.dim_surf.fill((0, 0, 0, 180))

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _armour_items(self):
        from src.scenes.chest_scene import ArmourItem
        return [it for it in self.inventory.items
                if isinstance(it, ArmourItem)]

    def _total_defence(self):
        return self.armour.total_defence()

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #

    def _draw_panel(self, t):
        ease = 1-(1-t)**3
        w = int(self.PW*ease); h = int(self.PH*ease)
        x = self.W//2 - w//2;  y = self.H//2 - h//2
        if w < 4: return

        sh = pygame.Surface((w+14,h+14), pygame.SRCALPHA)
        sh.fill((0,0,0,90))
        self.screen.blit(sh,(x-7,y-7))

        bg = pygame.Surface((w,h), pygame.SRCALPHA)
        bg.fill((16,12,8,248))
        self.screen.blit(bg,(x,y))

        pygame.draw.rect(self.screen,(105,82,50),(x,y,w,h),2)
        pygame.draw.rect(self.screen,(62,48,28),(x+5,y+5,w-10,h-10),1)

        sz,c2 = 14,(145,112,64)
        for bx,by,dx,dy in [(x,y,1,1),(x+w,y,-1,1),(x,y+h,1,-1),(x+w,y+h,-1,-1)]:
            pygame.draw.line(self.screen,c2,(bx,by),(bx+dx*sz,by),2)
            pygame.draw.line(self.screen,c2,(bx,by),(bx,by+dy*sz),2)

        if t > 0.8:
            title = self.font_title.render("ARMOUR", True,(215,180,105))
            self.screen.blit(title,(self.W//2-title.get_width()//2, y+12))
            pygame.draw.line(self.screen,(80,62,36),
                             (x+20,y+12+title.get_height()+4),
                             (x+w-20,y+12+title.get_height()+4),1)

    def _draw_armour_slot(self, slot, rect):
        item    = self.armour.get(slot)
        is_hov  = (self.hover_slot == slot)
        t       = 1.0 if is_hov else 0.0

        # Background
        bg = pygame.Surface((rect.w,rect.h), pygame.SRCALPHA)
        bg.fill((int(28+20*t),int(20+15*t),int(12+8*t),220))
        self.screen.blit(bg,rect.topleft)

        border = _lerp((60,46,28),(180,145,70),t)
        pygame.draw.rect(self.screen,border,rect,2)

        # Corner accents
        sz = 7; c2 = border
        for bx,by,dx,dy in [(rect.x,rect.y,1,1),(rect.x+rect.w,rect.y,-1,1),
                             (rect.x,rect.y+rect.h,1,-1),(rect.x+rect.w,rect.y+rect.h,-1,-1)]:
            pygame.draw.line(self.screen,c2,(bx,by),(bx+dx*sz,by),1)
            pygame.draw.line(self.screen,c2,(bx,by),(bx,by+dy*sz),1)

        if item:
            # Draw item icon
            item.draw_icon(self.screen, rect.centerx, rect.centery-6,
                           int(rect.w*0.52))
            # Defence label
            ds = self.font_tiny.render(f"-{item.defence} dmg",True,(140,200,140))
            self.screen.blit(ds,(rect.centerx-ds.get_width()//2,
                                  rect.bottom-ds.get_height()-3))
        else:
            # Empty slot label
            label = slot.capitalize()
            ls = self.font_small.render(label,True,_lerp((55,42,26),(100,78,45),t))
            self.screen.blit(ls,(rect.centerx-ls.get_width()//2,
                                  rect.centery-ls.get_height()//2))

        # Slot name above
        sn = self.font_tiny.render(slot.upper(),True,(80,62,34))
        self.screen.blit(sn,(rect.x,rect.y-sn.get_height()-2))

    def _draw_player_silhouette(self):
        """Minecraft-style player doll in the centre."""
        cx = self.PX + self.PW//2
        cy = self.PY + self.PH//2 + 10
        sc = 2.2   # scale

        def r(x,y,w,h,col,border=None):
            rx = int(cx+x*sc); ry = int(cy+y*sc)
            rw = int(w*sc);    rh = int(h*sc)
            pygame.draw.rect(self.screen,col,(rx,ry,rw,rh))
            if border:
                pygame.draw.rect(self.screen,border,(rx,ry,rw,rh),1)

        helm  = self.armour.get("helmet")
        chest = self.armour.get("chestplate")
        legs  = self.armour.get("leggings")
        boots = self.armour.get("boots")

        skin   = (210,170,120)
        b_col  = (45,38,28)     # base clothing
        e_col  = (50,55,65)     # iron base
        h_col  = helm.icon_color      if helm  else b_col
        c_col  = chest.icon_color     if chest else b_col
        l_col  = legs.icon_color      if legs  else b_col
        bo_col = boots.icon_color     if boots else b_col

        # Head
        head_col = _lerp(skin, h_col, 0.6) if helm else skin
        r(-8,-48,16,16,head_col,(60,50,38))
        # Eyes
        pygame.draw.rect(self.screen,(40,35,25),
                         (int(cx-4*sc),int(cy-43*sc),int(2*sc),int(2*sc)))
        pygame.draw.rect(self.screen,(40,35,25),
                         (int(cx+2*sc),int(cy-43*sc),int(2*sc),int(2*sc)))
        # Helmet overlay
        if helm:
            r(-9,-49,18,18,h_col,(100,110,120))
            r(-9,-49,18,3,(80,90,100))   # visor top
            r(-9,-46,18,2,(50,55,65))    # visor slit

        # Torso
        r(-8,-30,16,20,c_col,(60,50,38) if not chest else (90,100,115))
        if chest:
            # Armour detail lines
            for dy in [-20,-12,-4]:
                pygame.draw.line(self.screen,(80,90,105),
                                 (int(cx-7*sc),int(cy+dy*sc)),
                                 (int(cx+7*sc),int(cy+dy*sc)),1)
            pygame.draw.line(self.screen,(80,90,105),
                             (int(cx),int(cy-29*sc)),(int(cx),int(cy-11*sc)),1)

        # Arms
        arm_col = _lerp(c_col,(140,150,165),0.5) if chest else skin
        r(-14,-30,6,18,arm_col,(60,50,38))
        r( 8,-30,6,18,arm_col,(60,50,38))

        # Legs
        r(-8,-10,7,20,l_col,(60,50,38) if not legs else (85,95,110))
        r( 1,-10,7,20,l_col,(60,50,38) if not legs else (85,95,110))
        if legs:
            for leg_ox in [-8,1]:
                pygame.draw.line(self.screen,(75,85,100),
                                 (int(cx+(leg_ox+3)*sc),int(cy-9*sc)),
                                 (int(cx+(leg_ox+3)*sc),int(cy+9*sc)),1)

        # Boots
        r(-8, 10,7,8,bo_col,(60,50,38) if not boots else (85,95,110))
        r( 1, 10,7,8,bo_col,(60,50,38) if not boots else (85,95,110))
        # Toe extension
        r(-9, 15,8,3,bo_col,(60,50,38) if not boots else (85,95,110))
        r( 1, 15,8,3,bo_col,(60,50,38) if not boots else (85,95,110))

        # Defence total
        total = self._total_defence()
        def_s = self.font_medium.render(f"Defence: -{total} dmg",True,
                                         (140,200,140) if total>0 else (120,95,55))
        self.screen.blit(def_s,(self.PX+self.PW//2-def_s.get_width()//2,
                                  self.PY+self.PH-def_s.get_height()-14))

    def _draw_inv_list(self, t):
        if t < 0.8: return
        items = self._armour_items()

        # Column header
        hdr = self.font_small.render("INVENTORY",True,(90,70,38))
        self.screen.blit(hdr,(self.inv_col_x, self.PY+50))
        pygame.draw.line(self.screen,(70,54,28),
                         (self.inv_col_x,self.PY+66),
                         (self.inv_col_x+self.inv_col_w,self.PY+66),1)

        if not items:
            ns = self.font_small.render("No armour in inventory",True,(65,50,28))
            self.screen.blit(ns,(self.inv_col_x,self.inv_start_y+10))
            return

        for i,item in enumerate(items):
            ry     = self.inv_start_y + i*self.inv_row_h
            is_sel = (i == self.selected_inv)
            tv     = 1.0 if is_sel else 0.0

            bg = pygame.Surface((self.inv_col_w,self.inv_row_h-4),pygame.SRCALPHA)
            bg.fill((int(28+20*tv),int(20+15*tv),int(12+8*tv),200))
            self.screen.blit(bg,(self.inv_col_x,ry))

            bc = _lerp((55,42,26),(180,145,70),tv)
            pygame.draw.rect(self.screen,bc,
                             (self.inv_col_x,ry,self.inv_col_w,self.inv_row_h-4),
                             2 if is_sel else 1)

            # Icon
            item.draw_icon(self.screen,
                           self.inv_col_x+26, ry+(self.inv_row_h-4)//2, 32)

            # Name + slot
            nc = _lerp((150,115,65),(220,185,115),tv)
            ns2 = self.font_small.render(item.name,True,nc)
            self.screen.blit(ns2,(self.inv_col_x+52,ry+6))

            slot_s = self.font_tiny.render(
                f"{item.slot}  •  -{item.defence} dmg",True,(100,78,45))
            self.screen.blit(slot_s,(self.inv_col_x+52,
                                      ry+6+ns2.get_height()+2))

            # Equipped badge
            if self.armour.is_equipped(item):
                eq = self.font_tiny.render("EQUIPPED",True,(100,180,100))
                self.screen.blit(eq,(self.inv_col_x+self.inv_col_w
                                      -eq.get_width()-6,ry+6))

            if is_sel:
                arr = self.font_small.render("▶",True,(145,112,64))
                self.screen.blit(arr,(self.inv_col_x+2,
                                       ry+(self.inv_row_h-4)//2
                                       -arr.get_height()//2))

        hint = self.font_tiny.render(
            "↑ ↓  select    ENTER  equip    U  unequip    ESC  back",
            True,(70,54,28))
        self.screen.blit(hint,(self.PX+self.PW//2-hint.get_width()//2,
                                 self.PY+self.PH-hint.get_height()-14))

    def _draw_message(self):
        if not self.message or self.message_timer <= 0: return
        alpha = min(1.0, self.message_timer/0.4)
        ms  = self.font_small.render(self.message,True,(220,195,120))
        bg  = pygame.Surface((ms.get_width()+20,ms.get_height()+8),
                              pygame.SRCALPHA)
        bg.fill((14,10,6,int(220*alpha)))
        bx = self.W//2-bg.get_width()//2
        by = self.PY+self.PH-60
        self.screen.blit(bg,(bx,by))
        pygame.draw.rect(self.screen,(120,95,48),
                         (bx,by,bg.get_width(),bg.get_height()),1)
        ms.set_alpha(int(255*alpha))
        self.screen.blit(ms,(bx+10,by+4))

    # ------------------------------------------------------------------ #
    # Input
    # ------------------------------------------------------------------ #

    def _get_hovered_slot(self, pos):
        for slot,rect in self.slot_rects.items():
            if rect.collidepoint(pos):
                return slot
        return None

    def run(self) -> str:
        while True:
            dt          = self.clock.tick(60)/1000.0
            self.time  += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            t           = min(1.0, self.open_anim/self.OPEN_DUR)
            self.message_timer = max(0.0, self.message_timer-dt)
            mouse       = pygame.mouse.get_pos()
            self.hover_slot = self._get_hovered_slot(mouse)
            items       = self._armour_items()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "inventory"
                    if event.key == pygame.K_UP:
                        self.selected_inv = max(0, self.selected_inv-1)
                    if event.key == pygame.K_DOWN:
                        self.selected_inv = min(
                            max(0,len(items)-1), self.selected_inv+1)
                    if event.key == pygame.K_RETURN and items:
                        item = items[self.selected_inv]
                        ok   = self.armour.equip(item, self.inventory)
                        self.message       = (f"Equipped {item.name}!" if ok
                                              else "Can't equip that.")
                        self.message_timer = 2.0
                    if event.key == pygame.K_u:
                        # Unequip hovered or selected slot
                        unequipped = False
                        for slot in SLOTS:
                            if self.armour.get(slot) is not None:
                                self.armour.unequip(slot, self.inventory)
                                self.message       = f"Unequipped {slot}."
                                self.message_timer = 2.0
                                unequipped = True
                                break
                        if not unequipped:
                            self.message       = "Nothing to unequip."
                            self.message_timer = 1.5

                if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                    # Click on armour slot — unequip
                    slot = self._get_hovered_slot(mouse)
                    if slot and self.armour.get(slot):
                        self.armour.unequip(slot, self.inventory)
                        self.message       = f"Unequipped {slot}."
                        self.message_timer = 2.0
                    # Click on inventory item — equip
                    for i,item in enumerate(items):
                        ry = self.inv_start_y + i*self.inv_row_h
                        r2 = pygame.Rect(self.inv_col_x,ry,
                                         self.inv_col_w,self.inv_row_h-4)
                        if r2.collidepoint(mouse):
                            self.selected_inv = i
                            ok = self.armour.equip(item, self.inventory)
                            self.message       = (f"Equipped {item.name}!" if ok
                                                  else "Can't equip that.")
                            self.message_timer = 2.0

            # Draw
            self.screen.fill((8,6,4))
            self.screen.blit(self.dim_surf,(0,0))
            self._draw_panel(t)
            if t > 0.8:
                for slot,rect in self.slot_rects.items():
                    self._draw_armour_slot(slot,rect)
                self._draw_player_silhouette()
                self._draw_inv_list(t)
                self._draw_message()

            pygame.display.flip()