import pygame
import math
import random


class MainMenuScene:
    """
    Serves as both the startup main menu AND the in-game pause menu.
    mode="start"  — shown on launch (no Continue button)
    mode="pause"  — shown mid-game   (Continue button resumes)
    """

    def __init__(self, screen, mode: str = "start"):
        self.screen = screen
        self.W, self.H = screen.get_size()
        self.clock  = pygame.time.Clock()
        self.time   = 0.0
        self.mode   = mode   # "start" or "pause"

        self.font_title  = pygame.font.SysFont("courier new", 72, bold=True)
        self.font_sub    = pygame.font.SysFont("courier new", 18)
        self.font_button = pygame.font.SysFont("courier new", 24, bold=True)

        # Build button list depending on mode
        bw, bh = 300, 58
        cx = self.W//2 - bw//2

        if mode == "pause":
            labels = ["CONTINUE", "SAVES", "MAIN MENU", "EXIT"]
        else:
            labels = ["NEW GAME", "SAVES", "EXIT"]

        spacing = bh + 14
        total_h = len(labels) * spacing
        start_y = self.H//2 + 30

        self.buttons = []
        for i, label in enumerate(labels):
            self.buttons.append({
                "label":  label,
                "rect":   pygame.Rect(cx, start_y + i*spacing, bw, bh),
                "hover":  0.0,
            })

        # Particles
        rng = random.Random(42)
        self.particles = [
            {
                "x":     rng.uniform(0, self.W),
                "y":     rng.uniform(0, self.H),
                "speed": rng.uniform(0.04, 0.18),
                "size":  rng.choice([1,1,1,2]),
                "phase": rng.uniform(0, math.tau),
            }
            for _ in range(90)
        ]

        # Pre-build vignette
        self.vignette = self._build_vignette()

        # Open animation
        self.open_anim = 0.0
        self.OPEN_DUR  = 0.35

        # Dim overlay for pause mode (show game behind)
        self.dim_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.dim_surf.fill((0, 0, 0, 175))

        # "Paused" flash
        self._paused_alpha = 0.0

    def _build_vignette(self):
        surf   = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        cx, cy = self.W//2, self.H//2
        max_r  = int(math.hypot(cx, cy))
        for i in range(60, 0, -1):
            r     = int(max_r * i/60)
            alpha = int(150 * (i/60)**2)
            pygame.draw.circle(surf,(0,0,0,alpha),(cx,cy),r)
        return surf

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #

    def _draw_background(self):
        if self.mode == "pause":
            # In pause mode the game is still drawn behind (handled by caller)
            # Just add a dark overlay
            self.screen.blit(self.dim_surf,(0,0))
        else:
            self.screen.fill((8,6,4))

            dim = pygame.Surface((self.W,self.H),pygame.SRCALPHA)
            for y in range(0,self.H,3):
                pygame.draw.line(dim,(0,0,0,18),(0,y),(self.W,y))
            self.screen.blit(dim,(0,0))

            for p in self.particles:
                flicker = 0.5+0.5*math.sin(self.time*p["speed"]*6+p["phase"])
                alpha = int(30+70*flicker)
                col = (int(160*flicker),int(120*flicker),int(60*flicker),alpha)
                s = pygame.Surface((p["size"]*2,p["size"]*2),pygame.SRCALPHA)
                pygame.draw.circle(s,col,(p["size"],p["size"]),p["size"])
                self.screen.blit(s,(int(p["x"]),int(p["y"])))

            glow  = pygame.Surface((self.W,self.H),pygame.SRCALPHA)
            pulse = 0.85+0.15*math.sin(self.time*0.7)
            for r,a in [(340,40),(220,55),(120,35)]:
                pygame.draw.circle(glow,(80,50,20,int(a*pulse)),
                                   (self.W//2,self.H//2-80),r)
            self.screen.blit(glow,(0,0))

        self.screen.blit(self.vignette,(0,0))

    def _draw_title(self, alpha):
        title_text = "DUNGEON"
        flicker    = 0.92+0.08*math.sin(self.time*3.1+0.5)
        col        = (int(220*flicker),int(175*flicker),int(90*flicker))

        shadow = self.font_title.render(title_text,True,(20,14,6))
        sx = self.W//2 - shadow.get_width()//2
        sy = self.H//2 - 230

        ss = pygame.Surface(shadow.get_size(),pygame.SRCALPHA)
        ss.blit(shadow,(0,0)); ss.set_alpha(alpha)
        self.screen.blit(ss,(sx+3,sy+4))

        label = self.font_title.render(title_text,True,col)
        ls    = pygame.Surface(label.get_size(),pygame.SRCALPHA)
        ls.blit(label,(0,0)); ls.set_alpha(alpha)
        self.screen.blit(ls,(sx,sy))

        if self.mode == "pause":
            pause_s = self.font_sub.render("— PAUSED —",True,(160,130,70))
            ps2     = pygame.Surface(pause_s.get_size(),pygame.SRCALPHA)
            ps2.blit(pause_s,(0,0)); ps2.set_alpha(alpha)
            self.screen.blit(ps2,(self.W//2-pause_s.get_width()//2,
                                   sy+label.get_height()+6))
        else:
            sub   = self.font_sub.render("a roguelike",True,(100,80,45))
            sub_s = pygame.Surface(sub.get_size(),pygame.SRCALPHA)
            sub_s.blit(sub,(0,0)); sub_s.set_alpha(alpha)
            sub_x = self.W//2 - sub.get_width()//2
            sub_y = sy + label.get_height() + 4
            lc    = (70,52,28)
            mid_y = sub_y + sub.get_height()//2
            pygame.draw.line(self.screen,lc,(sub_x-84,mid_y),(sub_x-24,mid_y),1)
            pygame.draw.line(self.screen,lc,
                             (sub_x+sub.get_width()+24,mid_y),
                             (sub_x+sub.get_width()+84,mid_y),1)
            self.screen.blit(sub_s,(sub_x,sub_y))

    def _draw_button(self, btn, alpha):
        t     = btn["hover"]
        rect  = btn["rect"]
        label = btn["label"]

        def lc(a,b):
            return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

        # Special colour for CONTINUE
        if label == "CONTINUE":
            border_idle  = (60,110,60)
            border_hover = (100,210,100)
            text_idle    = (100,160,90)
            text_hover   = (180,240,160)
        elif label in ("EXIT","MAIN MENU"):
            border_idle  = (110,55,40)
            border_hover = (210,100,70)
            text_idle    = (160,80,60)
            text_hover   = (240,150,120)
        else:
            border_idle  = (90,70,50)
            border_hover = (220,180,100)
            text_idle    = (160,130,90)
            text_hover   = (240,210,140)

        border_col = lc(border_idle,border_hover)
        text_col   = lc(text_idle,  text_hover)

        fill = pygame.Surface((rect.w,rect.h),pygame.SRCALPHA)
        r2 = int(20+40*t); g2 = int(15+30*t); b2 = int(10+15*t)
        a2 = int(180+40*t)
        fill.fill((r2,g2,b2,a2))
        fs = pygame.Surface((rect.w,rect.h),pygame.SRCALPHA)
        fs.blit(fill,(0,0)); fs.set_alpha(alpha)
        self.screen.blit(fs,rect.topleft)

        pygame.draw.rect(self.screen,border_col,rect,2)
        pygame.draw.rect(self.screen,lc((30,22,14),(120,90,40)),
                         rect.inflate(-6,-6),1)

        # Corner accents
        sz = 8
        cx2,cy2,cw,ch = rect.x,rect.y,rect.width,rect.height
        for px,py,dx,dy in [(cx2,cy2,1,1),(cx2+cw,cy2,-1,1),
                             (cx2,cy2+ch,1,-1),(cx2+cw,cy2+ch,-1,-1)]:
            pygame.draw.line(self.screen,border_col,(px,py),(px+dx*sz,py),1)
            pygame.draw.line(self.screen,border_col,(px,py),(px,py+dy*sz),1)

        lbl = self.font_button.render(label,True,text_col)
        self.screen.blit(lbl,(rect.centerx-lbl.get_width()//2,
                               rect.centery-lbl.get_height()//2))

    def _draw_footer(self, alpha):
        if self.mode == "pause":
            hint = self.font_sub.render("ESC  resume game",True,(55,44,28))
        else:
            hint = self.font_sub.render("use mouse to navigate",True,(55,44,28))
        hs = pygame.Surface(hint.get_size(),pygame.SRCALPHA)
        hs.blit(hint,(0,0)); hs.set_alpha(alpha)
        self.screen.blit(hs,(self.W//2-hint.get_width()//2,self.H-36))

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        """
        Returns:
          "new_game"  — start fresh
          "continue"  — resume (pause mode only)
          "saves"     — go to saves screen
          "main_menu" — go to main menu (pause mode only)
          "exit"      — quit
        """
        while True:
            dt         = self.clock.tick(60)/1000.0
            self.time += dt
            self.open_anim = min(self.open_anim+dt, self.OPEN_DUR)
            ease       = 1-(1-min(1.0,self.open_anim/self.OPEN_DUR))**3
            alpha      = int(255*ease)
            mouse_pos  = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    # ESC always resumes in pause mode
                    if event.key == pygame.K_ESCAPE and self.mode == "pause":
                        return "continue"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.buttons:
                        if btn["rect"].collidepoint(event.pos):
                            label = btn["label"]
                            if label == "CONTINUE":  return "continue"
                            if label == "NEW GAME":  return "new_game"
                            if label == "SAVES":     return "saves"
                            if label == "MAIN MENU": return "main_menu"
                            if label == "EXIT":      return "exit"

            # Update hovers
            for btn in self.buttons:
                tgt = 1.0 if btn["rect"].collidepoint(mouse_pos) else 0.0
                btn["hover"] += (tgt-btn["hover"])*8*dt
                btn["hover"]  = max(0.0,min(1.0,btn["hover"]))

            # Draw
            self._draw_background()
            self._draw_title(alpha)
            for btn in self.buttons:
                self._draw_button(btn, alpha)
            self._draw_footer(alpha)

            pygame.display.flip()