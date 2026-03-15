import pygame
import math
import random


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lerp_col(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))


# ---------------------------------------------------------------------------
# Combat sprites
# ---------------------------------------------------------------------------

class CombatPlayer:
    def __init__(self, x, y, size):
        self.base_x   = float(x)
        self.base_y   = float(y)
        self.x        = float(x)
        self.y        = float(y)
        self.size     = size
        self.anim_time = 0.0
        # Attack lunge
        self.lunging       = False
        self.lunge_timer   = 0.0
        self.LUNGE_DUR     = 0.35
        # Damage flash
        self.flash_timer   = 0.0
        self.FLASH_DUR     = 0.4

    def start_lunge(self):
        self.lunging     = True
        self.lunge_timer = 0.0

    def start_flash(self):
        self.flash_timer = self.FLASH_DUR

    def update(self, dt):
        self.anim_time  += dt
        self.flash_timer = max(0.0, self.flash_timer - dt)

        if self.lunging:
            self.lunge_timer += dt
            t = self.lunge_timer / self.LUNGE_DUR
            if t >= 1.0:
                self.lunging = False
                self.x = self.base_x
                self.y = self.base_y
            else:
                # Quick dart right then snap back
                offset = math.sin(t * math.pi) * self.size * 0.9
                self.x = self.base_x + offset
                self.y = self.base_y

    def draw(self, surface):
        s   = self.size
        cx  = int(self.x)
        cy  = int(self.y)
        bob = math.sin(self.anim_time * 2.2) * 3 if not self.lunging else 0

        # Flash white when hit
        flash = self.flash_timer / self.FLASH_DUR if self.flash_timer > 0 else 0.0

        # Shadow
        sh = pygame.Surface((s, s//4), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0,0,0,50), (0,0,s,s//4))
        surface.blit(sh, (cx - s//2, cy + s//2 - s//8))

        cloak_col = _lerp_col((45,35,70), (255,255,255), flash*0.6)
        eye_col   = _lerp_col((160,210,255), (255,255,255), flash)

        # Cloak
        cloak_pts = [
            (cx - s//4, cy - s//4 + int(bob)),
            (cx - s//3, cy + s//2 + int(bob)),
            (cx + s//3, cy + s//2 + int(bob)),
            (cx + s//4, cy - s//4 + int(bob)),
        ]
        pygame.draw.polygon(surface, cloak_col, cloak_pts)
        pygame.draw.polygon(surface, _lerp_col((75,58,110),(255,255,255),flash*0.4),
                            cloak_pts, 2)

        # Hood
        hr = s // 4
        hy = cy - s//4 - hr//2 + int(bob)
        pygame.draw.circle(surface, _lerp_col((30,22,48),(255,255,255),flash*0.5), (cx,hy), hr+2)
        pygame.draw.circle(surface, _lerp_col((60,45,92),(255,255,255),flash*0.4), (cx,hy), hr)

        # Eyes
        eox = hr // 2
        pygame.draw.circle(surface, eye_col, (cx-eox, hy), 3)
        pygame.draw.circle(surface, eye_col, (cx+eox, hy), 3)

        # Sword
        sw_x1 = cx + s//3
        sw_y1 = cy - s//8 + int(bob)
        sw_x2 = cx + s//3 + s//2
        sw_y2 = cy - s//4 + int(bob)
        pygame.draw.line(surface, (140,145,170), (sw_x1,sw_y1), (sw_x2,sw_y2), 3)
        pygame.draw.line(surface, (200,205,225), (sw_x1,sw_y1), (sw_x2,sw_y2), 1)
        pygame.draw.line(surface, (160,130,60),
                         (sw_x1-4,sw_y1-5), (sw_x1+4,sw_y1+3), 3)


class CombatGoblin:
    def __init__(self, x, y, size):
        self.base_x   = float(x)
        self.base_y   = float(y)
        self.x        = float(x)
        self.y        = float(y)
        self.size     = size
        self.anim_time = random.uniform(0, math.tau)
        # Attack lunge (toward player — left)
        self.lunging       = False
        self.lunge_timer   = 0.0
        self.LUNGE_DUR     = 0.35
        # Damage flash
        self.flash_timer   = 0.0
        self.FLASH_DUR     = 0.4

    def start_lunge(self):
        self.lunging     = True
        self.lunge_timer = 0.0

    def start_flash(self):
        self.flash_timer = self.FLASH_DUR

    def update(self, dt):
        self.anim_time  += dt
        self.flash_timer = max(0.0, self.flash_timer - dt)

        if self.lunging:
            self.lunge_timer += dt
            t = self.lunge_timer / self.LUNGE_DUR
            if t >= 1.0:
                self.lunging = False
                self.x = self.base_x
                self.y = self.base_y
            else:
                offset = math.sin(t * math.pi) * self.size * 0.9
                self.x = self.base_x - offset   # lunge LEFT toward player
                self.y = self.base_y

    def draw(self, surface):
        s   = self.size
        cx  = int(self.x)
        cy  = int(self.y)
        bob = math.sin(self.anim_time * 2.6) * 3 if not self.lunging else 0
        flash = self.flash_timer / self.FLASH_DUR if self.flash_timer > 0 else 0.0

        skin  = _lerp_col((70,130,55),  (255,255,255), flash*0.7)
        dark  = _lerp_col((50, 95,40),  (255,255,255), flash*0.5)
        body  = _lerp_col((55,110,45),  (255,255,255), flash*0.6)
        lc    = _lerp_col((40, 80,35),  (255,255,255), flash*0.5)
        ec    = _lerp_col((60,115,48),  (255,255,255), flash*0.4)

        # Shadow
        sh = pygame.Surface((s, s//4), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0,0,0,50), (0,0,s,s//4))
        surface.blit(sh, (cx-s//2, cy+s//2-s//8))

        # Legs
        lw, lh = s//5, s//3
        lby = cy + s//4 + int(bob)
        pygame.draw.rect(surface, lc, (cx-lw-3, lby, lw, lh))
        pygame.draw.rect(surface, lc, (cx+3,    lby, lw, lh))

        # Body
        bw, bh = s//2, s//2
        bx = cx - bw//2
        by = cy - bh//4 + int(bob)
        pygame.draw.rect(surface, body, (bx,by,bw,bh))
        pygame.draw.rect(surface, dark, (bx,by,bw,bh), 2)

        # Arms + club toward player (left)
        arm_y = by + bh//4
        pygame.draw.line(surface, lc, (cx-bw//2, arm_y),
                         (cx-bw//2-s//3, arm_y+s//8), 3)
        club_x = cx - bw//2 - s//3
        club_y = arm_y + s//8
        pygame.draw.line(surface, _lerp_col((100,70,40),(255,255,255),flash*0.3),
                         (club_x,club_y),(club_x-s//4,club_y-s//5), 4)
        pygame.draw.circle(surface, _lerp_col((80,55,30),(255,255,255),flash*0.3),
                           (club_x-s//4, club_y-s//5), 5)
        pygame.draw.line(surface, lc, (cx+bw//2,arm_y),
                         (cx+bw//2+s//6,arm_y+s//8), 3)

        # Head
        hr = s // 4
        hx, hy = cx, by - hr + int(bob)
        pygame.draw.circle(surface, skin, (hx,hy), hr)
        pygame.draw.circle(surface, dark, (hx,hy), hr, 2)

        # Ears
        pygame.draw.polygon(surface, ec, [
            (hx-hr,hy-2),(hx-hr-8,hy-10),(hx-hr+2,hy+3)])
        pygame.draw.polygon(surface, ec, [
            (hx+hr,hy-2),(hx+hr+6,hy-8),(hx+hr-2,hy+3)])

        # Eyes
        eox = hr//2
        pygame.draw.circle(surface, _lerp_col((220,200,40),(255,255,255),flash), (hx-eox,hy), 4)
        pygame.draw.circle(surface, _lerp_col((220,200,40),(255,255,255),flash), (hx+eox,hy), 4)
        pygame.draw.circle(surface, (20,12,2), (hx-eox,hy), 2)
        pygame.draw.circle(surface, (20,12,2), (hx+eox,hy), 2)

        # Mouth
        my = hy + hr//2
        pygame.draw.line(surface, (20,10,5), (hx-5,my),(hx+5,my), 2)
        for tx in [hx-3,hx,hx+3]:
            pygame.draw.line(surface, (220,215,200),(tx,my),(tx,my-3),1)




# ---------------------------------------------------------------------------
# Goblin King combat sprite
# ---------------------------------------------------------------------------

class CombatGoblinKing:
    """Big imposing boss sprite — drawn on the RIGHT side, facing left."""

    def __init__(self, x: int, y: int, size: int):
        self.base_x   = float(x)
        self.base_y   = float(y)
        self.x        = float(x)
        self.y        = float(y)
        self.size     = size
        self.anim_time    = 0.0
        self.flash_timer  = 0.0
        self.FLASH_DUR    = 0.5
        self.lunging      = False
        self.lunge_timer  = 0.0
        self.LUNGE_DUR    = 0.45

    def start_lunge(self):
        self.lunging = True
        self.lunge_timer = 0.0

    def start_flash(self):
        self.flash_timer = self.FLASH_DUR

    def update(self, dt):
        self.anim_time   += dt
        self.flash_timer  = max(0.0, self.flash_timer - dt)
        if self.lunging:
            self.lunge_timer += dt
            t = self.lunge_timer / self.LUNGE_DUR
            if t >= 1.0:
                self.lunging = False
                self.x = self.base_x
                self.y = self.base_y
            else:
                self.x = self.base_x - math.sin(t * math.pi) * self.size * 1.2
                self.y = self.base_y

    def draw(self, surface):
        s   = self.size
        cx  = int(self.x)
        cy  = int(self.y)
        bob = math.sin(self.anim_time * 2.0) * 4 if not self.lunging else 0
        flash = self.flash_timer / self.FLASH_DUR if self.flash_timer > 0 else 0.0

        def fc(col):
            return _lerp_col(col, (255,255,255), flash*0.65)

        # Shadow (bigger than regular goblin)
        sh = pygame.Surface((int(s*1.4), s//3), pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,60),(0,0,int(s*1.4),s//3))
        surface.blit(sh,(cx-int(s*0.7), cy+int(s*0.55)-s//6))

        # Legs — thick, powerful
        lc = fc((50,100,40))
        lw, lh = s//3, int(s*0.45)
        lby = cy + int(s*0.3) + int(bob)
        pygame.draw.rect(surface,lc,(cx-lw-6,lby,lw,lh))
        pygame.draw.rect(surface,lc,(cx+6,   lby,lw,lh))
        # Boots
        pygame.draw.rect(surface,fc((35,55,20)),(cx-lw-8,lby+lh-8,lw+4,12))
        pygame.draw.rect(surface,fc((35,55,20)),(cx+4,   lby+lh-8,lw+4,12))

        # Body — barrel-chested
        bw, bh = int(s*0.85), int(s*0.6)
        bx = cx - bw//2
        by = cy - bh//4 + int(bob)
        pygame.draw.rect(surface,fc((65,128,50)),(bx,by,bw,bh))
        pygame.draw.rect(surface,fc((40,85,30)),(bx,by,bw,bh),2)
        # Armour plates on body
        for i in range(3):
            ax = bx + 4 + i*(bw//3)
            pygame.draw.rect(surface,fc((80,65,40)),(ax,by+4,bw//3-4,bh//3))
            pygame.draw.rect(surface,fc((60,48,28)),(ax,by+4,bw//3-4,bh//3),1)

        # Arms — massive
        arm_y = by + bh//5
        # Left arm — raised with giant club toward player
        pygame.draw.line(surface,fc((55,105,42)),(cx-bw//2,arm_y),
                         (cx-bw//2-s//2,arm_y-s//4),6)
        # Giant spiked club
        club_x = cx-bw//2-s//2
        club_y = arm_y-s//4
        pygame.draw.line(surface,fc((110,78,42)),(club_x,club_y),
                         (club_x-s//3,club_y-s//2),7)
        # Club head (big)
        pygame.draw.circle(surface,fc((90,62,30)),(club_x-s//3,club_y-s//2),s//5)
        pygame.draw.circle(surface,fc((70,48,22)),(club_x-s//3,club_y-s//2),s//5,2)
        # Spikes on club
        for sa in [0,60,120,180,240,300]:
            ra = math.radians(sa)
            spx = club_x-s//3+int(math.cos(ra)*s//5)
            spy = club_y-s//2+int(math.sin(ra)*s//5)
            pygame.draw.line(surface,fc((140,100,50)),
                             (club_x-s//3,club_y-s//2),(spx,spy),3)
        # Right arm
        pygame.draw.line(surface,fc((55,105,42)),(cx+bw//2,arm_y),
                         (cx+bw//2+s//5,arm_y+s//6),5)

        # Head — big and menacing
        hr = int(s*0.35)
        hx, hy = cx, by-hr+int(bob)
        # Head base
        pygame.draw.circle(surface,fc((80,148,60)),(hx,hy),hr)
        pygame.draw.circle(surface,fc((55,105,42)),(hx,hy),hr,3)

        # Crown — jagged iron crown
        crown_col = fc((80,68,40))
        crown_pts = [
            (hx-hr,   hy-hr+6),
            (hx-hr+4, hy-hr-12),
            (hx-hr+10,hy-hr+2),
            (hx-hr+16,hy-hr-16),
            (hx,      hy-hr-4),
            (hx+hr-16,hy-hr-16),
            (hx+hr-10,hy-hr+2),
            (hx+hr-4, hy-hr-12),
            (hx+hr,   hy-hr+6),
        ]
        pygame.draw.polygon(surface,crown_col,crown_pts)
        pygame.draw.polygon(surface,fc((110,92,55)),crown_pts,2)
        # Crown jewels
        for jx,jy,jc in [(hx-hr+16,hy-hr-10,(200,60,60)),
                          (hx,       hy-hr-4, (60,180,60)),
                          (hx+hr-16,hy-hr-10,(60,60,200))]:
            pygame.draw.circle(surface,fc(jc),(jx,jy),4)

        # Ears — huge and pointy
        ec = fc((70,130,55))
        pygame.draw.polygon(surface,ec,[
            (hx-hr,     hy-4),
            (hx-hr-18,  hy-22),
            (hx-hr+5,   hy+6)])
        pygame.draw.polygon(surface,ec,[
            (hx+hr,     hy-4),
            (hx+hr+18,  hy-22),
            (hx+hr-5,   hy+6)])

        # Eyes — glowing red (angry boss)
        eox = hr//2
        eye_col = fc((240,50,30))
        pygame.draw.circle(surface,eye_col,(hx-eox,hy),5)
        pygame.draw.circle(surface,eye_col,(hx+eox,hy),5)
        pygame.draw.circle(surface,(255,180,100),(hx-eox,hy),2)
        pygame.draw.circle(surface,(255,180,100),(hx+eox,hy),2)

        # Snarl — jagged teeth
        my = hy+hr//2
        pygame.draw.line(surface,fc((15,10,5)),(hx-8,my),(hx+8,my),3)
        for tx in [hx-6,hx-2,hx+2,hx+6]:
            pygame.draw.line(surface,fc((230,220,200)),(tx,my),(tx,my-5),2)



# ---------------------------------------------------------------------------
# Action button
# ---------------------------------------------------------------------------

class ActionButton:
    def __init__(self, x, y, w, h, text, icon_color):
        self.rect       = pygame.Rect(x, y, w, h)
        self.text       = text
        self.icon_color = icon_color
        self._hover     = 0.0
        self.enabled    = True

    def update(self, mouse_pos, dt):
        if not self.enabled:
            self._hover = 0.0
            return
        target      = 1.0 if self.rect.collidepoint(mouse_pos) else 0.0
        self._hover += (target - self._hover) * 10 * dt
        self._hover  = max(0.0, min(1.0, self._hover))

    def is_clicked(self, event):
        return (self.enabled
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, surface, font):
        t = self._hover
        alpha = 210 if self.enabled else 80

        fill = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        fill.fill((int(18+35*t), int(14+28*t), int(10+18*t), alpha))
        surface.blit(fill, self.rect.topleft)

        border = _lerp_col((70,55,38),(200,165,90),t) if self.enabled else (40,32,22)
        pygame.draw.rect(surface, border, self.rect, 2)

        ic = self.icon_color if self.enabled else (50,40,30)
        ic = tuple(int(c+(255-c)*t*0.3) for c in ic)
        pygame.draw.circle(surface, ic, (self.rect.x+18, self.rect.centery), 5)

        tc = _lerp_col((150,120,80),(235,205,135),t) if self.enabled else (70,58,42)
        lbl = font.render(self.text, True, tc)
        surface.blit(lbl, (self.rect.x+32,
                           self.rect.centery - lbl.get_height()//2))


# ---------------------------------------------------------------------------
# CombatScene
# ---------------------------------------------------------------------------

# Turn states
STATE_PLAYER_CHOOSE  = "player_choose"   # waiting for button press
STATE_PLAYER_ACTION  = "player_action"   # animation playing
STATE_ENEMY_ACTION   = "enemy_action"    # goblin attacking
STATE_MESSAGE        = "message"         # showing a message, click to continue
STATE_VICTORY        = "victory"
STATE_DEFEAT         = "defeat"
STATE_RELIC_MENU     = "relic_menu"

PLAYER_MAX_HP  = 30
GOBLIN_MAX_HP  = 12
GOBLIN_DAMAGE  = 4     # how much the goblin hits for
SWORD_DAMAGE   = 6
SUN_SWORD_DMG  = 12
POTION_HEAL    = 5

# Goblin King stats
BOSS_MAX_HP    = 45
BOSS_DAMAGE    = 12   # massive damage
BOSS_NAME      = "GOBLIN KING"


class CombatScene:
    def __init__(self, screen, inventory, is_boss=False, armour=None, player_hp=None, player_stats=None):
        self.inventory = inventory
        self.is_boss   = is_boss
        self.armour    = armour
        self._start_hp   = player_hp
        self.player_stats = player_stats
        self.screen = screen
        self.W, self.H = screen.get_size()
        self.clock = pygame.time.Clock()
        self.time  = 0.0

        self.font_large  = pygame.font.SysFont("courier new", 28, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 20, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 16)

        self.PANEL_H     = int(self.H * 0.32)
        self.BATTLE_H    = self.H - self.PANEL_H
        self.SPRITE_SIZE = int(min(self.W, self.BATTLE_H) * 0.28)

        # Sprites
        px = int(self.W * 0.22)
        py = int(self.BATTLE_H * 0.58)
        self.combat_player = CombatPlayer(px, py, self.SPRITE_SIZE)

        ex = int(self.W * 0.72)
        ey = int(self.BATTLE_H * 0.35)
        if is_boss:
            boss_size = int(self.SPRITE_SIZE * 1.55)
            self.combat_goblin = CombatGoblinKing(ex, int(self.BATTLE_H*0.40), boss_size)
            self.goblin_hp     = BOSS_MAX_HP
            self.goblin_max_hp = BOSS_MAX_HP
            self._goblin_name  = BOSS_NAME
            self._goblin_dmg   = BOSS_DAMAGE
        else:
            self.combat_goblin = CombatGoblin(ex, ey, self.SPRITE_SIZE)
            self.goblin_hp     = GOBLIN_MAX_HP
            self.goblin_max_hp = GOBLIN_MAX_HP
            self._goblin_name  = "GOBLIN"
            self._goblin_dmg   = GOBLIN_DAMAGE

        # Stats
        _max = self.player_stats.max_hp if self.player_stats else PLAYER_MAX_HP
        self.player_hp  = self._start_hp if self._start_hp is not None else _max
        self.player_max_hp = _max

        # State machine
        self.state          = STATE_MESSAGE
        self.next_state     = STATE_PLAYER_CHOOSE
        self.message        = (f"The GOBLIN KING blocks your path! "
                               "His eyes burn with fury!" if is_boss
                               else f"A wild {self._goblin_name} appeared!")
        self.pending_action = None   # what the player chose

        # Action timer (how long to wait during animations)
        self.action_timer   = 0.0
        self.ACTION_WAIT    = 0.55   # seconds before dealing damage mid-animation

        # Buttons
        bw  = int(self.W * 0.20)
        bh  = int(self.PANEL_H * 0.30)
        gx  = int(self.W * 0.52)
        rx  = gx + bw + 16
        ty  = self.BATTLE_H + int(self.PANEL_H * 0.12)
        by_ = ty + bh + 12

        self.buttons = [
            ActionButton(gx, ty,  bw, bh, "ATTACK", (200, 60,  60)),
            ActionButton(rx, ty,  bw, bh, "ITEMS",  (60,  160, 200)),
            ActionButton(gx, by_, bw, bh, "RELICS", (160, 80,  200)),
            ActionButton(rx, by_, bw, bh, "RUN",    (80,  180, 80)),
        ]
        self._set_buttons_enabled(False)

        # Disable RUN for boss fights
        if self.is_boss:
            for btn in self.buttons:
                if btn.text == "RUN":
                    btn.enabled = False

        # Relic selection menu
        self._relic_selection    = False
        self._relic_options      = []
        self._relic_selected_idx = 0

        self.bg = self._build_background()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _set_buttons_enabled(self, enabled: bool):
        for btn in self.buttons:
            # Never re-enable RUN during a boss fight
            if btn.text == "RUN" and getattr(self, "is_boss", False):
                btn.enabled = False
            else:
                btn.enabled = enabled

    def _show_message(self, text: str, next_state: str):
        self.state      = STATE_MESSAGE
        self.message    = text
        self.next_state = next_state
        self._set_buttons_enabled(False)

    def _player_attack(self, damage: int, weapon_name: str):
        """Start player attack animation sequence."""
        self.state          = STATE_PLAYER_ACTION
        self.pending_action = ("attack", damage, weapon_name)
        self.action_timer   = 0.0
        self._set_buttons_enabled(False)
        self.combat_player.start_lunge()

    # ------------------------------------------------------------------ #
    # Background
    # ------------------------------------------------------------------ #

    def _build_background(self):
        surf = pygame.Surface((self.W, self.H))

        for y in range(self.BATTLE_H):
            t = y / self.BATTLE_H
            pygame.draw.line(surf, (int(8+18*t), int(6+12*t), int(4+8*t)),
                             (0,y),(self.W,y))

        gtp = int(self.BATTLE_H * 0.62)
        pygame.draw.polygon(surf, (28,22,14), [
            (0,gtp),(self.W,gtp),(self.W,self.BATTLE_H),(0,self.BATTLE_H)])

        tc = (38,30,20)
        for i in range(1,8):
            f = i/8
            yp = int(gtp + (self.BATTLE_H-gtp)*f)
            xo = int((self.W//2)*(1-f)*0.6)
            pygame.draw.line(surf, tc, (xo,yp),(self.W-xo,yp),1)
        for i in range(-6,7):
            xc = self.W//2 + i*(self.W//14)
            pygame.draw.line(surf, tc, (xc,gtp),
                             (self.W//2+i*(self.W//4),self.BATTLE_H),1)

        rng = random.Random(99)
        for _ in range(14):
            sx = rng.randint(40,self.W-40)
            sh2= rng.randint(20,60)
            sw = rng.randint(8,18)
            pts= [(sx-sw//2,0),(sx+sw//2,0),(sx,sh2)]
            pygame.draw.polygon(surf,(35,28,18),pts)
            pygame.draw.polygon(surf,(50,40,26),pts,1)

        pygame.draw.line(surf,(90,70,45),(0,self.BATTLE_H),(self.W,self.BATTLE_H),2)
        pygame.draw.rect(surf,(12,9,6),(0,self.BATTLE_H,self.W,self.PANEL_H))
        pygame.draw.rect(surf,(70,54,34),
                         pygame.Rect(0,self.BATTLE_H,self.W,self.PANEL_H).inflate(-8,-8),1)
        return surf

    # ------------------------------------------------------------------ #
    # Draw helpers
    # ------------------------------------------------------------------ #

    def _draw_health_bar(self, surface, x, y, w, h, current, maximum, label):
        name_s = self.font_medium.render(label, True, (210,185,130))
        surface.blit(name_s, (x,y))
        y += name_s.get_height() + 4

        hp_s = self.font_small.render(f"HP  {current}/{maximum}", True, (160,140,100))
        surface.blit(hp_s, (x,y))
        y += hp_s.get_height() + 4

        pygame.draw.rect(surface, (30,22,14), (x,y,w,h))
        pygame.draw.rect(surface, (60,46,28), (x,y,w,h), 1)

        ratio = max(0.0, current/maximum)
        if ratio > 0.5:    bar_col = (50,180,60)
        elif ratio > 0.25: bar_col = (210,175,40)
        else:              bar_col = (210,55,45)

        fw = int(w*ratio)
        if fw > 0:
            pygame.draw.rect(surface, bar_col, (x,y,fw,h))
            pygame.draw.rect(surface, tuple(min(255,c+60) for c in bar_col),
                             (x,y,fw,h//3))

    def _draw_relic_menu(self, surface):
        """Overlay panel listing owned relics to choose from."""
        items  = self._relic_options
        if not items:
            return

        rows   = len(items)
        pw     = int(self.W * 0.36)
        row_h  = 58
        pad    = 20
        ph     = rows * row_h + pad * 2 + 50
        px     = int(self.W * 0.52) + (int(self.W * 0.48) - pw) // 2
        py     = self.BATTLE_H + (self.PANEL_H - ph) // 2

        # Panel
        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg.fill((14, 10, 7, 245))
        surface.blit(bg, (px, py))
        pygame.draw.rect(surface, (105, 82, 50), (px, py, pw, ph), 2)
        pygame.draw.rect(surface, (62, 48, 28), (px+4, py+4, pw-8, ph-8), 1)

        # Corner ticks
        c2 = (145, 112, 64)
        for bpx, bpy, dx, dy in [(px,py,1,1),(px+pw,py,-1,1),
                                  (px,py+ph,1,-1),(px+pw,py+ph,-1,-1)]:
            pygame.draw.line(surface,c2,(bpx,bpy),(bpx+dx*10,bpy),2)
            pygame.draw.line(surface,c2,(bpx,bpy),(bpx,bpy+dy*10),2)

        # Title
        title = self.font_medium.render("CHOOSE RELIC", True, (215,180,105))
        surface.blit(title, (px + pw//2 - title.get_width()//2, py + 10))
        pygame.draw.line(surface, (80,62,36),
                         (px+16, py+10+title.get_height()+4),
                         (px+pw-16, py+10+title.get_height()+4), 1)

        # Relic rows
        for i, item in enumerate(items):
            ry      = py + pad + 38 + i * row_h
            is_sel  = (i == self._relic_selected_idx)

            row_bg = pygame.Surface((pw - pad*2, row_h - 6), pygame.SRCALPHA)
            row_bg.fill((38,28,16,220) if is_sel else (20,14,8,160))
            surface.blit(row_bg, (px+pad, ry))

            border_col = (160,128,68) if is_sel else (55,42,26)
            pygame.draw.rect(surface, border_col,
                             (px+pad, ry, pw-pad*2, row_h-6), 2)

            if is_sel:
                arr = self.font_small.render("▶", True, (200,165,80))
                surface.blit(arr, (px+pad+4, ry + row_h//2 - arr.get_height()//2 - 3))

            # Icon
            item.draw_icon(surface, px+pad+28, ry+row_h//2-3, 30)

            # Name + desc
            nc = (225,195,130) if is_sel else (170,145,95)
            ns = self.font_medium.render(item.name, True, nc)
            surface.blit(ns, (px+pad+48, ry+6))
            ds = self.font_small.render(item.description, True, (130,108,68))
            surface.blit(ds, (px+pad+48, ry+6+ns.get_height()+2))

        # Hint
        hint = self.font_small.render(
            "↑↓ select   ENTER use   ESC cancel", True, (70,56,34))
        surface.blit(hint, (px + pw//2 - hint.get_width()//2,
                            py + ph - hint.get_height() - 8))

    def _draw_message_box(self, surface):
        mx  = int(self.W * 0.02)
        my  = self.BATTLE_H + int(self.PANEL_H * 0.08)
        mw  = int(self.W * 0.44)
        mh  = int(self.PANEL_H * 0.82)

        bg = pygame.Surface((mw,mh), pygame.SRCALPHA)
        bg.fill((14,10,7,220))
        surface.blit(bg,(mx,my))
        pygame.draw.rect(surface,(90,70,44),(mx,my,mw,mh),2)
        pygame.draw.rect(surface,(55,42,26),(mx+4,my+4,mw-8,mh-8),1)

        c = (120,92,55)
        sz = 10
        for px2,py2,dx,dy in [(mx,my,1,1),(mx+mw,my,-1,1),
                               (mx,my+mh,1,-1),(mx+mw,my+mh,-1,-1)]:
            pygame.draw.line(surface,c,(px2,py2),(px2+dx*sz,py2),1)
            pygame.draw.line(surface,c,(px2,py2),(px2,py2+dy*sz),1)

        # Draw sword icon if message is about attacking
        if "sword" in self.message.lower() or "slash" in self.message.lower() or "sun" in self.message.lower():
            self._draw_sword_icon(surface, mx+mw//2, my+mh//2 - 10)
        elif "potion" in self.message.lower() or "heal" in self.message.lower() or "drink" in self.message.lower():
            self._draw_potion_icon(surface, mx+mw//2, my+mh//2 - 10)

        # Word-wrap text
        words   = self.message.split()
        lines   = []
        current = ""
        for word in words:
            test = current + (" " if current else "") + word
            if self.font_small.size(test)[0] < mw - 24:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        ty2 = my + mh - len(lines)*(self.font_small.get_height()+4) - 16
        for line in lines:
            ls = self.font_small.render(line, True, (200,180,130))
            surface.blit(ls,(mx+12,ty2))
            ty2 += ls.get_height() + 4

        if self.state == STATE_MESSAGE:
            if int(self.time*2)%2==0:
                arr = self.font_small.render("▼", True, (160,130,80))
                surface.blit(arr,(mx+mw-arr.get_width()-10,
                                  my+mh-arr.get_height()-8))

    def _draw_sword_icon(self, surface, cx, cy):
        """Draw a sword icon in the message box."""
        # Blade
        pygame.draw.line(surface, (180,185,210), (cx-40,cy+20),(cx+40,cy-20), 4)
        pygame.draw.line(surface, (220,225,245), (cx-38,cy+18),(cx+38,cy-18), 2)
        # Tip
        pygame.draw.polygon(surface, (220,225,245),
                            [(cx+38,cy-18),(cx+44,cy-28),(cx+30,cy-22)])
        # Guard
        pygame.draw.line(surface, (180,140,60),
                         (cx-8,cy+8),(cx+8,cy-8),  6)
        # Handle
        pygame.draw.line(surface, (120,80,40),(cx-20,cy+16),(cx-8,cy+8), 5)

    def _draw_sun_sword_icon(self, surface, cx, cy):
        """Draw the Sun Sword — glowing gold blade."""
        # Glow
        glow = pygame.Surface((120,80), pygame.SRCALPHA)
        pygame.draw.ellipse(glow,(255,200,40,35),(0,0,120,80))
        surface.blit(glow,(cx-60,cy-40))
        # Blade — bright gold
        pygame.draw.line(surface,(255,215,0),(cx-42,cy+22),(cx+42,cy-22),5)
        pygame.draw.line(surface,(255,240,100),(cx-40,cy+20),(cx+40,cy-20),2)
        # Sun rays
        for angle_deg in range(0,360,45):
            a = math.radians(angle_deg)
            rx,ry = int(math.cos(a)*22), int(math.sin(a)*22)
            rx2,ry2=int(math.cos(a)*30),int(math.sin(a)*30)
            pygame.draw.line(surface,(255,200,40),(cx+rx,cy+ry),(cx+rx2,cy+ry2),2)
        # Guard
        pygame.draw.line(surface,(220,170,50),(cx-10,cy+10),(cx+10,cy-10),6)
        # Handle
        pygame.draw.line(surface,(150,100,30),(cx-22,cy+18),(cx-10,cy+10),5)

    def _draw_potion_icon(self, surface, cx, cy):
        """Draw a red healing potion."""
        # Cork
        pygame.draw.rect(surface,(120,80,50),(cx-5,cy-28,10,8))
        # Bottle neck
        pygame.draw.rect(surface,(80,160,140),(cx-5,cy-20,10,8))
        # Bottle body
        pygame.draw.ellipse(surface,(180,40,40),(cx-18,cy-14,36,38))
        pygame.draw.ellipse(surface,(80,160,140),(cx-18,cy-14,36,38),2)
        # Shine
        pygame.draw.ellipse(surface,(230,100,100),(cx-12,cy-10,10,12))
        # HP cross
        pygame.draw.line(surface,(240,200,200),(cx,cy-4),(cx,cy+10),3)
        pygame.draw.line(surface,(240,200,200),(cx-6,cy+3),(cx+6,cy+3),3)

    # ------------------------------------------------------------------ #
    # State machine
    # ------------------------------------------------------------------ #

    def _handle_player_choose(self, event):
        for btn in self.buttons:
            if btn.is_clicked(event):
                if btn.text == "ATTACK":
                    self._player_attack(SWORD_DAMAGE, "sword")

                elif btn.text == "ITEMS":
                    from src.scenes.chest_scene import PotionItem
                    potion = next((it for it in self.inventory.items
                                   if isinstance(it, PotionItem)), None)
                    if potion:
                        self.inventory.remove_one(PotionItem)
                        heal = min(POTION_HEAL, PLAYER_MAX_HP - self.player_hp)
                        self.player_hp += heal
                        remaining = self.inventory.count(PotionItem)
                        self._show_message(
                            f"You drink a potion and heal {heal} HP! "
                            f"({self.player_hp}/{PLAYER_MAX_HP})  "
                            f"Potions left: {remaining}",
                            STATE_ENEMY_ACTION)
                    else:
                        self._show_message(
                            "You have no potions!", STATE_PLAYER_CHOOSE)

                elif btn.text == "RELICS":
                    from src.scenes.chest_scene import ShieldItem, SunSwordItem
                    relics = [it for it in self.inventory.items
                              if isinstance(it, (ShieldItem, SunSwordItem))]
                    if not relics:
                        self._show_message(
                            "You have no relics!", STATE_PLAYER_CHOOSE)
                    elif len(relics) == 1:
                        self._use_relic(relics[0])
                    else:
                        self._relic_options      = relics
                        self._relic_selected_idx = 0
                        self.state               = STATE_RELIC_MENU
                        self._set_buttons_enabled(False)

                elif btn.text == "RUN":
                    self._show_message(
                        "You flee into the darkness!", "game")

    def _roll_loot(self):
        """Randomly generate 2 goblin drops."""
        from src.scenes.chest_scene import PotionItem, CandleItem, GoldItem

        def _one_drop():
            roll = random.random()
            if roll < 0.40:
                return PotionItem()
            elif roll < 0.70:
                return GoldItem(random.choice([5, 10, 15]))
            else:
                return CandleItem()

        return [_one_drop(), _one_drop()]

    def _use_relic(self, relic):
        """Activate a relic by item instance."""
        from src.scenes.chest_scene import ShieldItem, SunSwordItem
        if isinstance(relic, ShieldItem):
            self._shield_active = True
            self._show_message(
                "You raise the Iron Shield! The next hit will be blocked!",
                STATE_ENEMY_ACTION)
        elif isinstance(relic, SunSwordItem):
            self._player_attack(SUN_SWORD_DMG, "sun sword")

    def _update_player_action(self, dt):
        """Wait for lunge to reach midpoint, then deal damage."""
        self.action_timer += dt
        if self.action_timer >= self.ACTION_WAIT and not self.combat_goblin.flash_timer > 0:
            action, damage, weapon = self.pending_action
            self.goblin_hp = max(0, self.goblin_hp - damage)
            self.combat_goblin.start_flash()

            if weapon == "sun sword":
                msg = f"The Sun Sword blazes! {damage} damage! ({self.goblin_hp}/{self.goblin_max_hp} HP)"
            else:
                msg = f"You slash with your sword for {damage} damage! ({self.goblin_hp}/{self.goblin_max_hp} HP)"

            if self.goblin_hp <= 0:
                self._goblin_loot = self._roll_loot()
                self._show_message(msg + " The goblin is defeated!", STATE_VICTORY)
            else:
                self._show_message(msg, STATE_ENEMY_ACTION)

    def _update_enemy_action(self, dt):
        """Goblin attacks — lunge then deal damage."""
        self.action_timer += dt
        if self.action_timer == 0.0 or not hasattr(self, '_goblin_attacked'):
            self._goblin_attacked = False

        if self.action_timer >= 0.3 and not self._goblin_attacked:
            self._goblin_attacked = True
            self.combat_goblin.start_lunge()

        if self.action_timer >= 0.3 + self.ACTION_WAIT and not self.combat_player.flash_timer > 0:
            if not self._goblin_attacked:
                return
            if getattr(self, '_shield_active', False):
                self._shield_active = False
                self._goblin_attacked = False
                self.action_timer = -9999
                self._show_message(
                    "The goblin strikes — BLOCKED by your shield! "
                    "The shield holds firm.",
                    STATE_PLAYER_CHOOSE)
                return
            defence = self.armour.total_defence() if self.armour else 0
            dmg = max(1, self._goblin_dmg - defence)
            self.player_hp = max(0, self.player_hp - dmg)
            self.combat_player.start_flash()
            self._goblin_attacked = False   # reset for next round

            msg = f"The goblin clubs you for {dmg} damage! ({self.player_hp}/{PLAYER_MAX_HP} HP)"
            if self.player_hp <= 0:
                self._show_message(msg + " You have fallen in battle...", STATE_DEFEAT)
            else:
                self._show_message(msg, STATE_PLAYER_CHOOSE)
            # Reset timer so this block doesn't fire again
            self.action_timer = -9999

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while True:
            dt        = self.clock.tick(60) / 1000.0
            self.time += dt
            mouse_pos  = pygame.mouse.get_pos()

            # ---- Events ----
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if (event.type == pygame.KEYDOWN
                        and event.key == pygame.K_ESCAPE
                        and self.state not in (STATE_RELIC_MENU,)):
                    return "pause"

                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    key = getattr(event, "key", None)
                    btn = getattr(event, "button", None)

                    advance = (key in (pygame.K_SPACE, pygame.K_RETURN)
                               or btn == 1)

                    if self.state == STATE_MESSAGE and advance:
                        ns = self.next_state
                        if ns == STATE_PLAYER_CHOOSE:
                            self.state = STATE_PLAYER_CHOOSE
                            self._set_buttons_enabled(True)
                        elif ns == STATE_ENEMY_ACTION:
                            self.state = STATE_ENEMY_ACTION
                            self.action_timer     = 0.0
                            self._goblin_attacked = False
                        elif ns == "game":
                            return "game"
                        elif ns == STATE_VICTORY:
                            return "loot"
                        elif ns == STATE_DEFEAT:
                            return "death"
                        else:
                            self.state = ns

                    elif self.state == STATE_PLAYER_CHOOSE:
                        self._handle_player_choose(event)

                    elif self.state == STATE_RELIC_MENU:
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_UP:
                                self._relic_selected_idx = max(
                                    0, self._relic_selected_idx - 1)
                            elif event.key == pygame.K_DOWN:
                                self._relic_selected_idx = min(
                                    len(self._relic_options)-1,
                                    self._relic_selected_idx + 1)
                            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                                chosen = self._relic_options[self._relic_selected_idx]
                                self.state = STATE_PLAYER_CHOOSE
                                self._use_relic(chosen)
                            elif event.key == pygame.K_ESCAPE:
                                self.state = STATE_PLAYER_CHOOSE
                                self._set_buttons_enabled(True)

            # ---- Update ----
            self.combat_player.update(dt)
            self.combat_goblin.update(dt)

            if self.state == STATE_PLAYER_CHOOSE:
                for btn in self.buttons:
                    btn.update(mouse_pos, dt)

            elif self.state == STATE_PLAYER_ACTION:
                self._update_player_action(dt)

            elif self.state == STATE_ENEMY_ACTION:
                self._update_enemy_action(dt)

            # ---- Draw ----
            self.screen.blit(self.bg, (0,0))

            bw = int(self.W * 0.18)
            bh = 14
            self._draw_health_bar(self.screen,
                int(self.W*0.60), int(self.BATTLE_H*0.06),
                bw, bh, self.goblin_hp, self.goblin_max_hp, self._goblin_name)
            self._draw_health_bar(self.screen,
                int(self.W*0.05), int(self.BATTLE_H*0.72),
                bw, bh, self.player_hp, self.player_max_hp, "HERO")

            self.combat_goblin.draw(self.screen)
            self.combat_player.draw(self.screen)

            self._draw_message_box(self.screen)

            if self.state == STATE_PLAYER_CHOOSE:
                for btn in self.buttons:
                    btn.draw(self.screen, self.font_medium)
                # Draw item/relic counts next to buttons
                from src.scenes.chest_scene import PotionItem, SunSwordItem, ShieldItem
                pot_count = self.inventory.count(PotionItem)
                pot_s = self.font_small.render(
                    f"x{pot_count}", True,
                    (120,180,210) if pot_count>0 else (60,50,40))
                self.screen.blit(pot_s,
                    (self.buttons[1].rect.right - pot_s.get_width() - 6,
                     self.buttons[1].rect.y + 4))

                from src.scenes.chest_scene import SunSwordItem, ShieldItem
                # ATTACK always shows iron sword
                atk_s = self.font_small.render("iron sword", True, (140,140,160))
                self.screen.blit(atk_s,
                    (self.buttons[0].rect.x + 6,
                     self.buttons[0].rect.bottom - atk_s.get_height() - 4))

                # RELICS shows count of owned relics
                relic_count = sum(1 for it in self.inventory.items
                                  if isinstance(it, (SunSwordItem, ShieldItem)))
                rel_label = f"{relic_count} relic{'s' if relic_count!=1 else ''}"                             if relic_count > 0 else "no relics"
                rel_col = (190,160,90) if relic_count > 0 else (60,50,40)
                rel_s = self.font_small.render(rel_label, True, rel_col)
                self.screen.blit(rel_s,
                    (self.buttons[2].rect.x + 6,
                     self.buttons[2].rect.bottom - rel_s.get_height() - 4))
            else:
                # Dim buttons when not player's turn
                dim = pygame.Surface((int(self.W*0.48), self.PANEL_H), pygame.SRCALPHA)
                dim.fill((0,0,0,120))
                self.screen.blit(dim,(int(self.W*0.50), self.BATTLE_H))

            # Relic selection menu overlay
            if self.state == STATE_RELIC_MENU:
                self._draw_relic_menu(self.screen)

            # Sun sword icon shown during relic use
            if (self.state in (STATE_MESSAGE, STATE_PLAYER_ACTION)
                    and self.pending_action
                    and self.pending_action[2] == "sun sword"):
                self._draw_sun_sword_icon(
                    self.screen,
                    int(self.W*0.24),
                    self.BATTLE_H + self.PANEL_H//2)

            pygame.display.flip()