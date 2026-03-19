import pygame
import math


class Player(pygame.sprite.Sprite):
    def __init__(self, col: int, row: int, tile_size: int):
        super().__init__()
        self.tile_size = tile_size

        self.tile_col = col
        self.tile_row = row

        self.px = float(col * tile_size)
        self.py = float(row * tile_size)

        self.move_speed = 8.0
        self.moving     = False
        self.target_px  = self.px
        self.target_py  = self.py

        self.anim_time  = 0.0
        self.facing     = "down"
        self.bob_offset = 0.0

        self.size   = int(tile_size * 0.72)
        self.image  = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self._draw_sprite()

        self.rect = self.image.get_rect()

    def _draw_sprite(self):
        self.image.fill((0, 0, 0, 0))
        s  = self.size
        cx = s // 2

        cloak_pts = [
            (cx - s//4,     s//3),
            (cx - s//3 - 1, s - 4),
            (cx + s//3 + 1, s - 4),
            (cx + s//4,     s//3),
        ]
        pygame.draw.polygon(self.image, (45, 35, 70), cloak_pts)
        pygame.draw.polygon(self.image, (65, 50, 100), cloak_pts, 1)

        head_r = s // 5
        pygame.draw.circle(self.image, (30, 22, 48), (cx, s//4), head_r + 1)
        pygame.draw.circle(self.image, (55, 42, 85), (cx, s//4), head_r)

        eye_y  = s // 4
        eye_ox = head_r // 2
        eye_col = (180, 220, 255)
        pygame.draw.circle(self.image, eye_col, (cx - eye_ox, eye_y), 2)
        pygame.draw.circle(self.image, eye_col, (cx + eye_ox, eye_y), 2)

        sword_x = cx + s // 4 + 2
        pygame.draw.line(self.image, (160, 160, 180),
                         (sword_x, s // 3 + 2), (sword_x + 4, s // 2 + 6), 2)
        pygame.draw.line(self.image, (200, 200, 220),
                         (sword_x - 2, s // 2 + 2), (sword_x + 2, s // 2 + 2), 2)

    def try_move(self, dcol: int, drow: int, room_map: list):
        if self.moving:
            return

        new_col = self.tile_col + dcol
        new_row = self.tile_row + drow

        rows = len(room_map)
        cols = len(room_map[0])
        if not (0 <= new_row < rows and 0 <= new_col < cols):
            return

        if room_map[new_row][new_col] != 0:
            return

        self._prev_col = self.tile_col
        self._prev_row = self.tile_row
        self.tile_col  = new_col
        self.tile_row  = new_row
        self.target_px = float(new_col * self.tile_size)
        self.target_py = float(new_row * self.tile_size)
        self.moving    = True

        if   dcol ==  1: self.facing = "right"
        elif dcol == -1: self.facing = "left"
        elif drow ==  1: self.facing = "down"
        elif drow == -1: self.facing = "up"

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
            else:
                self.px += (dx / dist) * step
                self.py += (dy / dist) * step

        if not self.moving:
            self.bob_offset = math.sin(self.anim_time * 2.5) * 1.5
        else:
            self.bob_offset = 0.0

    def draw(self, surface: pygame.Surface, offset_x: int, offset_y: int):
        ts      = self.tile_size
        margin  = (ts - self.size) // 2
        draw_x  = int(self.px) + offset_x + margin
        draw_y  = int(self.py) + offset_y + margin + int(self.bob_offset)

        # Shadow beneath player
        shadow_surf = pygame.Surface((self.size, self.size // 3), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60),
                            (0, 0, self.size, self.size // 3))
        surface.blit(shadow_surf, (draw_x, draw_y + self.size - self.size // 6))

        # Player sprite — no blue glow
        surface.blit(self.image, (draw_x, draw_y))