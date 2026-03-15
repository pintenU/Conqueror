import pygame
import math
import random


# ===========================================================================
# Item base + all item types
# ===========================================================================

class Item:
    def __init__(self, name, description, icon_color):
        self.name        = name
        self.description = description
        self.icon_color  = icon_color

    def draw_icon(self, surface, cx, cy, size):
        pygame.draw.rect(surface, self.icon_color,
                         (cx - size//2, cy - size//2, size, size))


# ---------------------------------------------------------------------------

class CandleItem(Item):
    def __init__(self):
        super().__init__("Candle", "A dusty wax candle. It flickers faintly.",
                         (210, 190, 120))
        self.stackable = True
        self.amount    = 1

    def draw_icon(self, surface, cx, cy, size):
        s = size
        pygame.draw.rect(surface, (180,155,90), (cx-s//5, cy, s//2+1, s//2))
        pygame.draw.rect(surface, (140,115,65), (cx-s//5, cy, s//2+1, s//2), 1)
        pygame.draw.line(surface, (60,45,25),
                         (cx+s//10, cy), (cx+s//10, cy-s//5), 2)
        pygame.draw.polygon(surface, (255,200,50), [
            (cx+s//10-4, cy-s//5),
            (cx+s//10,   cy-s//5-s//3),
            (cx+s//10+4, cy-s//5)])
        pygame.draw.polygon(surface, (255,240,160), [
            (cx+s//10-2, cy-s//5),
            (cx+s//10,   cy-s//5-s//4),
            (cx+s//10+2, cy-s//5)])
        glow = pygame.Surface((s,s), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255,200,50,30), (s//2,s//4), s//2)
        surface.blit(glow, (cx-s//2, cy-s//2))


# ---------------------------------------------------------------------------

class PotionItem(Item):
    def __init__(self):
        super().__init__("Healing Potion",
                         "A red vial. Restores 5 HP when used in combat.",
                         (180, 40, 40))
        self.stackable = True
        self.amount    = 1

    def draw_icon(self, surface, cx, cy, size):
        s = size
        pygame.draw.rect(surface, (120,80,50),  (cx-s//6, cy-s//2, s//3, s//5))
        pygame.draw.rect(surface, (80,160,140), (cx-s//6, cy-s//2+s//5, s//3, s//5))
        pygame.draw.ellipse(surface, (180,40,40),
                            (cx-s//3, cy-s//4, s//1.5, s//1.5))
        pygame.draw.ellipse(surface, (80,160,140),
                            (cx-s//3, cy-s//4, s//1.5, s//1.5), 2)
        pygame.draw.ellipse(surface, (230,100,100),
                            (cx-s//4, cy-s//5, s//4, s//3))
        pygame.draw.line(surface, (240,200,200),
                         (cx, cy+s//8), (cx, cy+s//2-4), 3)
        pygame.draw.line(surface, (240,200,200),
                         (cx-s//6, cy+s//3), (cx+s//6, cy+s//3), 3)


# ---------------------------------------------------------------------------

class SwordItem(Item):
    def __init__(self):
        super().__init__("Sword",
                         "A reliable iron blade. Deals 6 damage.",
                         (160, 165, 185))

    def draw_icon(self, surface, cx, cy, size):
        s = size
        pygame.draw.line(surface, (180,185,210),
                         (cx-s//2+4, cy+s//2-4), (cx+s//2-4, cy-s//2+4), 4)
        pygame.draw.line(surface, (220,225,245),
                         (cx-s//2+6, cy+s//2-6), (cx+s//2-6, cy-s//2+6), 2)
        pygame.draw.polygon(surface, (220,225,245), [
            (cx+s//2-4, cy-s//2+4),
            (cx+s//2+2, cy-s//2-4),
            (cx+s//2-10, cy-s//2+2)])
        pygame.draw.line(surface, (180,140,60),
                         (cx-6, cy+4), (cx+6, cy-4), 5)
        pygame.draw.line(surface, (120,80,40),
                         (cx-s//3, cy+s//3), (cx-6, cy+4), 4)


# ---------------------------------------------------------------------------

class SunSwordItem(Item):
    def __init__(self):
        super().__init__("Sun Sword",
                         "A relic blazing with solar power. Deals 12 damage.",
                         (255, 200, 40))

    def draw_icon(self, surface, cx, cy, size):
        s = size
        glow = pygame.Surface((s, s), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255,200,40,40), (0,0,s,s))
        surface.blit(glow, (cx-s//2, cy-s//2))
        for angle_deg in range(0, 360, 45):
            a  = math.radians(angle_deg)
            r1, r2 = s//4, s//3
            pygame.draw.line(surface, (255,200,40),
                             (int(cx+math.cos(a)*r1), int(cy+math.sin(a)*r1)),
                             (int(cx+math.cos(a)*r2), int(cy+math.sin(a)*r2)), 2)
        pygame.draw.line(surface, (255,215,0),
                         (cx-s//2+6, cy+s//2-6), (cx+s//2-6, cy-s//2+6), 4)
        pygame.draw.line(surface, (255,240,100),
                         (cx-s//2+8, cy+s//2-8), (cx+s//2-8, cy-s//2+8), 2)
        pygame.draw.line(surface, (220,170,50),
                         (cx-8, cy+4), (cx+8, cy-4), 5)
        pygame.draw.line(surface, (150,100,30),
                         (cx-s//3, cy+s//3), (cx-8, cy+4), 4)


# ---------------------------------------------------------------------------

class ShieldItem(Item):
    def __init__(self):
        super().__init__("Iron Shield",
                         "A sturdy artifact. Blocks all damage for one hit.",
                         (100, 130, 160))

    def draw_icon(self, surface, cx, cy, size):
        s  = size
        hw = s // 2 - 2
        # Shield shape
        pts = [
            (cx - hw,     cy - hw + 4),
            (cx,          cy - hw - 4),
            (cx + hw,     cy - hw + 4),
            (cx + hw,     cy + hw//2),
            (cx,          cy + hw + 4),
            (cx - hw,     cy + hw//2),
        ]
        pygame.draw.polygon(surface, (80, 105, 130), pts)
        pygame.draw.polygon(surface, (140, 170, 200), pts, 2)
        # Boss (centre stud)
        pygame.draw.circle(surface, (160, 185, 210), (cx, cy), s//6)
        pygame.draw.circle(surface, (100, 130, 160), (cx, cy), s//6, 1)
        # Cross detail
        pygame.draw.line(surface, (110,140,170),(cx,cy-s//4),(cx,cy+s//4),2)
        pygame.draw.line(surface, (110,140,170),(cx-s//4,cy),(cx+s//4,cy),2)




# ---------------------------------------------------------------------------

class GoldItem(Item):
    def __init__(self, amount=10):
        self.amount    = amount
        self.stackable = True
        super().__init__(f"Gold",
                         f"{amount} gold coins, shiny and heavy.",
                         (220, 185, 40))

    def draw_icon(self, surface, cx, cy, size):
        s = size
        # Stack of coins
        for i in range(3):
            oy = i * 4
            pygame.draw.ellipse(surface, (180,145,25),
                                (cx-s//3, cy+s//6-oy, s//1.5, s//4))
            pygame.draw.ellipse(surface, (220,185,40),
                                (cx-s//3, cy+s//6-oy-3, s//1.5, s//4))
            pygame.draw.ellipse(surface, (240,210,80),
                                (cx-s//3+2, cy+s//6-oy-3, s//2, s//6))


# ---------------------------------------------------------------------------

class KeyItem(Item):
    def __init__(self, key_id: str = "key_1"):
        self.key_id = key_id
        super().__init__("Dungeon Key",
                         "An old iron key. Opens a locked door somewhere.",
                         (160, 140, 80))

    def draw_icon(self, surface, cx, cy, size):
        s  = size
        # Key bow (circle)
        pygame.draw.circle(surface, (140,115,50), (cx-s//4, cy-s//5), s//5+1)
        pygame.draw.circle(surface, (180,150,65), (cx-s//4, cy-s//5), s//5)
        pygame.draw.circle(surface, (60,48,20),   (cx-s//4, cy-s//5), s//8)
        # Key shaft
        pygame.draw.line(surface, (160,130,55),
                         (cx-s//4+s//5, cy-s//5),
                         (cx+s//3,      cy-s//5), 4)
        # Key teeth
        pygame.draw.line(surface, (160,130,55),
                         (cx+s//5,  cy-s//5),
                         (cx+s//5,  cy-s//5+s//6), 3)
        pygame.draw.line(surface, (160,130,55),
                         (cx+s//3,  cy-s//5),
                         (cx+s//3,  cy-s//5+s//8), 3)



# ---------------------------------------------------------------------------

class ExitKeyItem(Item):
    def __init__(self):
        super().__init__("Exit Key",
                         "A heavy iron key engraved with a sun. Opens the dungeon exit.",
                         (200, 170, 60))
        self.stackable = False

    def draw_icon(self, surface, cx, cy, size):
        s  = size
        # Large ornate key
        pygame.draw.circle(surface, (180,150,45), (cx-s//4, cy-s//5), s//4+1)
        pygame.draw.circle(surface, (220,185,65), (cx-s//4, cy-s//5), s//4)
        pygame.draw.circle(surface, (80,60,15),   (cx-s//4, cy-s//5), s//8)
        # Sun detail on bow
        for a in range(0,360,60):
            r2 = math.radians(a)
            rx = int(math.cos(r2)*(s//4+3))
            ry = int(math.sin(r2)*(s//4+3))
            pygame.draw.line(surface,(220,185,65),
                             (cx-s//4+int(math.cos(r2)*s//5),
                              cy-s//5+int(math.sin(r2)*s//5)),
                             (cx-s//4+rx, cy-s//5+ry), 1)
        # Shaft
        pygame.draw.line(surface,(200,165,55),
                         (cx-s//4+s//4, cy-s//5),
                         (cx+s//3,      cy-s//5), 4)
        # Teeth
        pygame.draw.line(surface,(200,165,55),
                         (cx+s//8,  cy-s//5),
                         (cx+s//8,  cy-s//5+s//5), 3)
        pygame.draw.line(surface,(200,165,55),
                         (cx+s//3,  cy-s//5),
                         (cx+s//3,  cy-s//5+s//7), 3)



# ===========================================================================
# Armour items
# ===========================================================================

class ArmourItem(Item):
    """Base class for all armour pieces."""
    slot        = "none"    # helmet / chestplate / leggings / boots
    defence     = 0         # damage reduction per hit
    stackable   = False
    material    = "iron"

    def __init__(self, name, description, icon_color, slot, defence, material="iron"):
        super().__init__(name, description, icon_color)
        self.slot     = slot
        self.defence  = defence
        self.material = material


class IronHelmet(ArmourItem):
    def __init__(self):
        super().__init__("Iron Helmet",
                         "Sturdy iron headgear. Reduces damage by 1.",
                         (160,170,185), "helmet", 1)

    def draw_icon(self, surface, cx, cy, size):
        s  = size
        hw = s//2
        # Dome
        pygame.draw.ellipse(surface,(130,140,155),(cx-hw,cy-hw,hw*2,hw))
        pygame.draw.ellipse(surface,(160,170,185),(cx-hw,cy-hw,hw*2,hw),2)
        # Brim
        pygame.draw.rect(surface,(130,140,155),(cx-hw-4,cy-4,hw*2+8,8))
        pygame.draw.rect(surface,(160,170,185),(cx-hw-4,cy-4,hw*2+8,8),2)
        # Visor slit
        pygame.draw.rect(surface,(50,55,65),(cx-hw+4,cy-6,hw*2-8,4))
        # Cheek guards
        pygame.draw.rect(surface,(130,140,155),(cx-hw,cy-4,8,s//3))
        pygame.draw.rect(surface,(130,140,155),(cx+hw-8,cy-4,8,s//3))


class IronChestplate(ArmourItem):
    def __init__(self):
        super().__init__("Iron Chestplate",
                         "Heavy iron armour. Reduces damage by 3.",
                         (150,160,175), "chestplate", 3)

    def draw_icon(self, surface, cx, cy, size):
        s  = size
        hw = s//2
        # Body plate
        pts = [(cx-hw+4, cy-hw+4),(cx-hw,cy-4),(cx-hw,cy+hw-2),
               (cx+hw,cy+hw-2),(cx+hw,cy-4),(cx+hw-4,cy-hw+4)]
        pygame.draw.polygon(surface,(120,130,145),pts)
        pygame.draw.polygon(surface,(155,165,180),pts,2)
        # Shoulder pads
        for ox2 in [-hw-2, hw-6]:
            pygame.draw.ellipse(surface,(130,140,155),(cx+ox2,cy-hw,10,12))
            pygame.draw.ellipse(surface,(155,165,180),(cx+ox2,cy-hw,10,12),1)
        # Centre line
        pygame.draw.line(surface,(100,110,125),(cx,cy-hw+6),(cx,cy+hw-4),2)
        # Horizontal bands
        for dy in [-s//6, s//6]:
            pygame.draw.line(surface,(100,110,125),(cx-hw+2,cy+dy),(cx+hw-2,cy+dy),1)


class IronLeggings(ArmourItem):
    def __init__(self):
        super().__init__("Iron Leggings",
                         "Iron leg protection. Reduces damage by 2.",
                         (145,155,170), "leggings", 2)

    def draw_icon(self, surface, cx, cy, size):
        s  = size
        hw = s//2
        # Waist band
        pygame.draw.rect(surface,(120,130,145),(cx-hw,cy-hw,hw*2,s//5))
        pygame.draw.rect(surface,(150,160,175),(cx-hw,cy-hw,hw*2,s//5),2)
        # Left leg
        pygame.draw.rect(surface,(115,125,140),(cx-hw,cy-hw+s//5,hw-2,s*2//3))
        pygame.draw.rect(surface,(145,155,170),(cx-hw,cy-hw+s//5,hw-2,s*2//3),2)
        # Right leg
        pygame.draw.rect(surface,(115,125,140),(cx+2,cy-hw+s//5,hw-2,s*2//3))
        pygame.draw.rect(surface,(145,155,170),(cx+2,cy-hw+s//5,hw-2,s*2//3),2)
        # Knee plates
        for lx in [cx-hw+2, cx+2]:
            pygame.draw.rect(surface,(140,150,165),(lx,cy,hw-4,s//6))
            pygame.draw.rect(surface,(155,165,180),(lx,cy,hw-4,s//6),1)


class IronBoots(ArmourItem):
    def __init__(self):
        super().__init__("Iron Boots",
                         "Iron footwear. Reduces damage by 1.",
                         (140,150,165), "boots", 1)

    def draw_icon(self, surface, cx, cy, size):
        s  = size
        hw = s//2
        for ox2, flip in [(-hw//2-2, -1), (2, 1)]:
            bx = cx + ox2
            # Ankle
            pygame.draw.rect(surface,(115,125,140),(bx,cy-s//3,hw//2+2,s//3))
            pygame.draw.rect(surface,(145,155,170),(bx,cy-s//3,hw//2+2,s//3),2)
            # Foot (extends to one side)
            foot_w = hw//2+6
            foot_x = bx if flip==1 else bx-4
            pygame.draw.rect(surface,(120,130,145),(foot_x,cy,foot_w,s//4))
            pygame.draw.rect(surface,(145,155,170),(foot_x,cy,foot_w,s//4),2)
            # Toe cap
            pygame.draw.ellipse(surface,(130,140,155),
                                (foot_x+foot_w-8,cy-2,10,s//4+4))

# ===========================================================================
# Item slot
# ===========================================================================

class ItemSlot:
    def __init__(self, x, y, size):
        self.rect   = pygame.Rect(x, y, size, size)
        self.item   = None
        self._hover = 0.0

    def update(self, mouse_pos, dt):
        target      = 1.0 if self.rect.collidepoint(mouse_pos) else 0.0
        self._hover += (target - self._hover) * 10 * dt
        self._hover  = max(0.0, min(1.0, self._hover))

    def draw(self, surface, font_small, taken=False):
        t = self._hover

        bg = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        bg.fill((int(20+25*t), int(15+20*t), int(10+12*t), 200))
        surface.blit(bg, self.rect.topleft)

        def lc(a, b):
            return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

        border = lc((55,42,28),(180,148,80))
        pygame.draw.rect(surface, border, self.rect, 2)

        sz = 6
        for px,py,dx,dy in [
            (self.rect.x,             self.rect.y,              1, 1),
            (self.rect.x+self.rect.w, self.rect.y,             -1, 1),
            (self.rect.x,             self.rect.y+self.rect.h,  1,-1),
            (self.rect.x+self.rect.w, self.rect.y+self.rect.h, -1,-1),
        ]:
            pygame.draw.line(surface, border, (px,py), (px+dx*sz,py),   1)
            pygame.draw.line(surface, border, (px,py), (px,py+dy*sz),   1)

        if self.item:
            icon_size = int(self.rect.w * 0.52)
            if taken:
                # Draw faded
                ghost = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
                self.item.draw_icon(ghost, self.rect.w//2, self.rect.h//2, icon_size)
                ghost.set_alpha(60)
                surface.blit(ghost, self.rect.topleft)
                done = font_small.render("taken", True, (80,65,42))
                surface.blit(done, (self.rect.centerx - done.get_width()//2,
                                    self.rect.centery - done.get_height()//2))
            else:
                self.item.draw_icon(surface,
                                    self.rect.centerx,
                                    self.rect.centery - 8,
                                    icon_size)
                name_s = font_small.render(
                    self.item.name, True,
                    (200,175,115) if t < 0.5 else (235,210,140))
                surface.blit(name_s, (
                    self.rect.centerx - name_s.get_width()//2,
                    self.rect.bottom  - name_s.get_height() - 5))
        else:
            ec  = (40,32,20)
            mid = self.rect.center
            pygame.draw.line(surface,ec,(mid[0]-8,mid[1]),(mid[0]+8,mid[1]),1)
            pygame.draw.line(surface,ec,(mid[0],mid[1]-8),(mid[0],mid[1]+8),1)


# ===========================================================================
# Take button
# ===========================================================================

class TakeButton:
    def __init__(self, x, y, w, h):
        self.rect   = pygame.Rect(x, y, w, h)
        self._hover = 0.0
        self.taken  = False

    def update(self, mouse_pos, dt):
        if self.taken:
            self._hover = 0.0
            return
        target      = 1.0 if self.rect.collidepoint(mouse_pos) else 0.0
        self._hover += (target - self._hover) * 10 * dt
        self._hover  = max(0.0, min(1.0, self._hover))

    def is_clicked(self, event):
        return (not self.taken
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, surface, font):
        if self.taken:
            return
        t = self._hover
        fill = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        fill.fill((int(18+40*t), int(14+30*t), int(10+18*t), 210))
        surface.blit(fill, self.rect.topleft)
        def lc(a,b):
            return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
        pygame.draw.rect(surface, lc((70,54,34),(180,148,70)), self.rect, 2)
        lbl = font.render("TAKE", True, lc((150,118,72),(235,205,130)))
        surface.blit(lbl, (self.rect.centerx - lbl.get_width()//2,
                           self.rect.centery - lbl.get_height()//2))


# ===========================================================================
# ChestScene
# ===========================================================================

class ChestScene:
    def __init__(self, screen, items: list, inventory, chest=None):
        self.chest = chest
        self.screen    = screen
        self.W, self.H = screen.get_size()
        self.clock     = pygame.time.Clock()
        self.time      = 0.0
        self.items     = list(items)
        self.inventory = inventory

        self.font_title  = pygame.font.SysFont("courier new", 32, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 18, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 14)

        self.panel_w = int(self.W * 0.58)
        self.panel_h = int(self.H * 0.64)
        self.panel_x = (self.W - self.panel_w) // 2
        self.panel_y = (self.H - self.panel_h) // 2

        self.COLS      = 4
        self.slot_size = int(self.panel_w * 0.18)
        self.slots     = self._build_slots()
        self.taken     = [False] * len(self.slots)

        for i, item in enumerate(self.items[:len(self.slots)]):
            self.slots[i].item = item

        # Take buttons — one per slot
        self.take_btns = []
        bw, bh = self.slot_size, 28
        for slot in self.slots:
            btn = TakeButton(slot.rect.x,
                             slot.rect.bottom + 4,
                             bw, bh)
            self.take_btns.append(btn)

        # Close button
        cw, ch = 180, 44
        self.close_rect   = pygame.Rect(
            self.panel_x + self.panel_w//2 - cw//2,
            self.panel_y + self.panel_h - ch - 10,
            cw, ch)
        self._close_hover = 0.0

        self.open_anim = 0.0
        self.OPEN_DUR  = 0.45

        self.dim_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.dim_surf.fill((0, 0, 0, 175))

    # ------------------------------------------------------------------ #

    def _build_slots(self):
        slots  = []
        pad    = 14
        n      = max(len(self.items), 1)
        cols   = min(n, self.COLS)
        grid_w = cols * self.slot_size + (cols-1) * pad
        sx     = self.panel_x + (self.panel_w - grid_w) // 2
        sy     = self.panel_y + 95
        for i in range(cols):
            slots.append(ItemSlot(sx + i*(self.slot_size+pad), sy, self.slot_size))
        return slots

    # ------------------------------------------------------------------ #

    def _draw_panel(self, t):
        ease = 1 - (1-t)**3
        w = int(self.panel_w * ease)
        h = int(self.panel_h * ease)
        x = self.W//2 - w//2
        y = self.H//2 - h//2
        if w < 4 or h < 4:
            return x, y

        sh = pygame.Surface((w+14,h+14), pygame.SRCALPHA)
        sh.fill((0,0,0,90))
        self.screen.blit(sh,(x-7,y-7))

        panel = pygame.Surface((w,h), pygame.SRCALPHA)
        panel.fill((14,10,7,248))
        self.screen.blit(panel,(x,y))

        pygame.draw.rect(self.screen,(105,82,50),(x,y,w,h),2)
        pygame.draw.rect(self.screen,(62,48,28),(x+5,y+5,w-10,h-10),1)

        c  = (145,112,64)
        sz = 14
        for px2,py2,dx,dy in [(x,y,1,1),(x+w,y,-1,1),(x,y+h,1,-1),(x+w,y+h,-1,-1)]:
            pygame.draw.line(self.screen,c,(px2,py2),(px2+dx*sz,py2),2)
            pygame.draw.line(self.screen,c,(px2,py2),(px2,py2+dy*sz),2)
            pygame.draw.circle(self.screen,c,(px2,py2),3)

        if t > 0.85:
            title = self.font_title.render("CHEST", True, (215,180,105))
            self.screen.blit(title,(self.W//2-title.get_width()//2, y+16))
            rule_y = y + 16 + title.get_height() + 4
            pygame.draw.line(self.screen,(80,62,36),(x+20,rule_y),(x+w-20,rule_y),1)

        return x, y

    def _draw_chest_icon(self, cx, cy, t):
        w, h = 44, 30
        x, y = cx-w//2, cy-h//2
        pygame.draw.rect(self.screen,(100,72,38),(x,y+h//2,w,h//2))
        pygame.draw.rect(self.screen,(130,95,50),(x,y+h//2,w,h//2),1)
        lid_col = (120,88,46)
        if t > 0.5:
            pygame.draw.rect(self.screen,lid_col,(x,y-h//3,w,h//2))
        else:
            pygame.draw.rect(self.screen,lid_col,(x,y,w,h//2))
        pygame.draw.rect(self.screen,(180,148,55),(cx-5,y+h//2-4,10,8))
        for sx2,sy2 in [(x+5,y+h//2+4),(x+w-5,y+h//2+4),(x+5,y+h-4),(x+w-5,y+h-4)]:
            pygame.draw.circle(self.screen,(160,128,50),(sx2,sy2),2)

    def _draw_description(self, panel_x, panel_y):
        hovered = None
        for slot in self.slots:
            if slot._hover > 0.3 and slot.item:
                hovered = slot.item
                break
        desc_y = self.panel_y + self.panel_h - 130
        if hovered:
            name_s = self.font_medium.render(hovered.name, True, (215,185,115))
            self.screen.blit(name_s,(self.W//2-name_s.get_width()//2, desc_y))
            desc_s = self.font_small.render(hovered.description, True, (170,145,95))
            self.screen.blit(desc_s,(self.W//2-desc_s.get_width()//2, desc_y+name_s.get_height()+4))
        else:
            hint = self.font_small.render(
                "Hover an item to inspect  |  E or ESC to close",
                True,(75,60,38))
            self.screen.blit(hint,(self.W//2-hint.get_width()//2, desc_y+8))

    def _draw_close_button(self):
        mouse = pygame.mouse.get_pos()
        target = 1.0 if self.close_rect.collidepoint(mouse) else 0.0
        self._close_hover += (target-self._close_hover)*10*(1/60)
        self._close_hover  = max(0.0,min(1.0,self._close_hover))
        t = self._close_hover
        fill = pygame.Surface((self.close_rect.w,self.close_rect.h),pygame.SRCALPHA)
        fill.fill((int(18+40*t),int(14+30*t),int(10+18*t),220))
        self.screen.blit(fill,self.close_rect.topleft)
        def lc(a,b): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
        pygame.draw.rect(self.screen,lc((70,54,34),(200,165,88)),self.close_rect,2)
        lbl = self.font_medium.render("CLOSE  [ E ]",True,lc((150,118,72),(235,205,130)))
        self.screen.blit(lbl,(self.close_rect.centerx-lbl.get_width()//2,
                              self.close_rect.centery-lbl.get_height()//2))

    # ------------------------------------------------------------------ #

    def _close_chest(self):
        """Remove taken items from chest and mark opened if all gone."""
        if self.chest is None:
            return
        # Remove items that were taken
        remaining = [item for i, item in enumerate(self.chest.items)
                     if i < len(self.taken) and not self.taken[i]]
        self.chest.items = remaining
        # Mark as opened (lid stays open) if all items taken
        if not remaining:
            self.chest.opened = True
        else:
            # Partially looted — show as opened but still interactable
            self.chest.opened = False

    def run(self) -> str:
        while True:
            dt         = self.clock.tick(60)/1000.0
            self.time += dt
            self.open_anim += dt
            t          = min(1.0, self.open_anim/self.OPEN_DUR)
            mouse_pos  = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_e, pygame.K_ESCAPE):
                        self._close_chest()
                        return "game"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.close_rect.collidepoint(event.pos):
                        self._close_chest()
                        return "game"
                    for i, btn in enumerate(self.take_btns):
                        if btn.is_clicked(event) and self.slots[i].item:
                            self.inventory.add(self.slots[i].item)
                            self.taken[i] = True
                            btn.taken = True

            if t > 0.9:
                for slot in self.slots:
                    slot.update(mouse_pos, dt)
                for btn in self.take_btns:
                    btn.update(mouse_pos, dt)

            # --- Draw ---
            self.screen.blit(self.dim_surf,(0,0))
            px, py = self._draw_panel(t)

            if t > 0.85:
                self._draw_chest_icon(self.W//2, self.panel_y-28, t)
                for i, slot in enumerate(self.slots):
                    slot.draw(self.screen, self.font_small, self.taken[i])
                    if slot.item:
                        self.take_btns[i].draw(self.screen, self.font_small)
                self._draw_description(px, py)
                self._draw_close_button()

            pygame.display.flip()