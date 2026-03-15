import pygame
import math
import random


class Goblin(pygame.sprite.Sprite):
    def __init__(self, col: int, row: int, tile_size: int,
                 patrol_tiles: list):
        """
        col, row       — starting tile position
        tile_size      — pixels per tile
        patrol_tiles   — list of (col, row) tiles to walk between in order
        """
        super().__init__()
        self.tile_size = tile_size

        self.tile_col  = col
        self.tile_row  = row
        self.px        = float(col * tile_size)
        self.py        = float(row * tile_size)

        # Patrol
        self.patrol_tiles   = patrol_tiles   # e.g. [(4,5), (10,5)]
        self.patrol_index   = 0              # which waypoint we're heading to
        self.patrol_dir     = 1             # +1 forward, -1 backward
        self.move_speed     = 3.0           # tiles per second (slower than player)
        self.moving         = False
        self.target_px      = self.px
        self.target_py      = self.py
        self.move_cooldown  = 0.0           # small pause at each waypoint
        self.PAUSE_TIME     = 0.6           # seconds to wait at each end

        # Animation
        self.anim_time  = random.uniform(0, math.tau)  # offset so goblins desync
        self.facing     = "right"

        # Build sprite surface
        self.size  = int(tile_size * 0.72)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self._draw_sprite()
        self.rect  = self.image.get_rect()

    # ------------------------------------------------------------------ #
    #  Sprite drawing
    # ------------------------------------------------------------------ #
    def _draw_sprite(self, squash: float = 1.0):
        """Draw a goblin. squash slightly compresses height when walking."""
        self.image.fill((0, 0, 0, 0))
        s  = self.size
        cx = s // 2

        body_h = int((s * 0.45) * squash)
        body_y = s - body_h - 2

        # Legs (two small rectangles)
        leg_col = (40, 80, 35)
        leg_w, leg_h = s // 6, int(s * 0.22 * squash)
        pygame.draw.rect(self.image, leg_col,
                         (cx - leg_w - 2, body_y + body_h - 2, leg_w, leg_h))
        pygame.draw.rect(self.image, leg_col,
                         (cx + 2,         body_y + body_h - 2, leg_w, leg_h))

        # Body
        body_rect = pygame.Rect(cx - s//4, body_y, s//2, body_h)
        pygame.draw.rect(self.image, (55, 110, 45), body_rect)
        pygame.draw.rect(self.image, (35, 75, 30),  body_rect, 1)

        # Arms
        arm_col = (50, 100, 40)
        arm_y   = body_y + 4
        # left arm
        pygame.draw.line(self.image, arm_col,
                         (cx - s//4, arm_y),
                         (cx - s//4 - s//5, arm_y + s//6), 2)
        # right arm (holding a crude weapon)
        pygame.draw.line(self.image, arm_col,
                         (cx + s//4, arm_y),
                         (cx + s//4 + s//5, arm_y + s//6), 2)
        # crude club / stick
        club_x = cx + s//4 + s//5
        club_y = arm_y + s//6
        pygame.draw.line(self.image, (100, 70, 40),
                         (club_x, club_y), (club_x + 4, club_y - 8), 3)
        pygame.draw.circle(self.image, (80, 55, 30),
                           (club_x + 4, club_y - 9), 3)

        # Head
        head_r = s // 5
        head_y = body_y - head_r - 1
        pygame.draw.circle(self.image, (70, 130, 55), (cx, head_y), head_r)
        pygame.draw.circle(self.image, (50, 95,  40), (cx, head_y), head_r, 1)

        # Ears (pointy triangles)
        ear_col = (60, 115, 48)
        if self.facing == "right":
            ear_pts_l = [(cx - head_r,     head_y - 2),
                         (cx - head_r - 6, head_y - 8),
                         (cx - head_r + 2, head_y + 2)]
            ear_pts_r = [(cx + head_r,     head_y - 2),
                         (cx + head_r + 7, head_y - 9),
                         (cx + head_r - 2, head_y + 2)]
        else:
            ear_pts_l = [(cx - head_r,     head_y - 2),
                         (cx - head_r - 7, head_y - 9),
                         (cx - head_r + 2, head_y + 2)]
            ear_pts_r = [(cx + head_r,     head_y - 2),
                         (cx + head_r + 6, head_y - 8),
                         (cx + head_r - 2, head_y + 2)]
        pygame.draw.polygon(self.image, ear_col, ear_pts_l)
        pygame.draw.polygon(self.image, ear_col, ear_pts_r)

        # Eyes — yellow with slit pupils
        eye_y  = head_y - 1
        eye_ox = head_r // 2
        pygame.draw.circle(self.image, (220, 200, 40), (cx - eye_ox, eye_y), 3)
        pygame.draw.circle(self.image, (220, 200, 40), (cx + eye_ox, eye_y), 3)
        pygame.draw.circle(self.image, (20, 15, 5),    (cx - eye_ox, eye_y), 1)
        pygame.draw.circle(self.image, (20, 15, 5),    (cx + eye_ox, eye_y), 1)

        # Mouth (jagged grin)
        mouth_y = head_y + head_r // 2
        pygame.draw.line(self.image, (20, 10, 5),
                         (cx - 4, mouth_y), (cx + 4, mouth_y), 1)
        pygame.draw.line(self.image, (220, 215, 200),
                         (cx - 2, mouth_y), (cx - 2, mouth_y - 2), 1)
        pygame.draw.line(self.image, (220, 215, 200),
                         (cx + 2, mouth_y), (cx + 2, mouth_y - 2), 1)

    # ------------------------------------------------------------------ #
    #  Patrol logic
    # ------------------------------------------------------------------ #
    def _next_waypoint(self):
        """Advance patrol index, reversing at ends."""
        next_idx = self.patrol_index + self.patrol_dir
        if next_idx >= len(self.patrol_tiles):
            self.patrol_dir = -1
            next_idx = self.patrol_index + self.patrol_dir
        elif next_idx < 0:
            self.patrol_dir = 1
            next_idx = self.patrol_index + self.patrol_dir
        self.patrol_index = next_idx

    def _start_next_move(self):
        """Kick off movement toward the next waypoint."""
        self._next_waypoint()
        tc, tr = self.patrol_tiles[self.patrol_index]
        old_col = self.tile_col

        self.tile_col  = tc
        self.tile_row  = tr
        self.target_px = float(tc * self.tile_size)
        self.target_py = float(tr * self.tile_size)
        self.moving    = True

        # Update facing based on horizontal movement
        if tc > old_col:
            self.facing = "right"
        elif tc < old_col:
            self.facing = "left"
        self._draw_sprite()

    # ------------------------------------------------------------------ #
    #  Update
    # ------------------------------------------------------------------ #
    def update(self, dt: float):
        self.anim_time += dt

        if self.moving:
            step = self.move_speed * self.tile_size * dt
            dx   = self.target_px - self.px
            dy   = self.target_py - self.py
            dist = math.hypot(dx, dy)

            if dist <= step:
                self.px     = self.target_px
                self.py     = self.target_py
                self.moving = False
                self.move_cooldown = self.PAUSE_TIME
            else:
                self.px += (dx / dist) * step
                self.py += (dy / dist) * step

        else:
            self.move_cooldown -= dt
            if self.move_cooldown <= 0:
                self._start_next_move()

    # ------------------------------------------------------------------ #
    #  Draw
    # ------------------------------------------------------------------ #
    def draw(self, surface: pygame.Surface, offset_x: int, offset_y: int):
        ts     = self.tile_size
        margin = (ts - self.size) // 2

        # Walking bob
        if self.moving:
            bob = math.sin(self.anim_time * 10) * 2.0
        else:
            bob = math.sin(self.anim_time * 2.5) * 1.2

        draw_x = int(self.px) + offset_x + margin
        draw_y = int(self.py) + offset_y + margin + int(bob)

        # Shadow
        shadow = pygame.Surface((self.size, self.size // 3), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 50),
                            (0, 0, self.size, self.size // 3))
        surface.blit(shadow, (draw_x, draw_y + self.size - self.size // 6))

        # Sprite
        surface.blit(self.image, (draw_x, draw_y))

        # Faint green glow
        glow_r = int(ts * 1.1)
        glow   = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (40, 80, 20, 14), (glow_r, glow_r), glow_r)
        cx = draw_x + self.size // 2
        cy = draw_y + self.size // 2
        surface.blit(glow, (cx - glow_r, cy - glow_r),
                     special_flags=pygame.BLEND_RGBA_ADD)