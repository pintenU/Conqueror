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


# ============================================================
# PATCH: Replace the entire CombatGoblin class in combat_scene.py
# ============================================================

class CombatGoblin:
    # Animation phases for the attack sequence
    PHASE_IDLE      = "idle"
    PHASE_WALK_IN   = "walk_in"
    PHASE_WINDUP    = "windup"
    PHASE_STAB      = "stab"
    PHASE_HOLD      = "hold"
    PHASE_SNAPBACK  = "snapback"

    # Durations (seconds) for each phase
    WALK_DUR    = 0.45
    WINDUP_DUR  = 0.18
    STAB_DUR    = 0.12
    HOLD_DUR    = 0.10
    SNAP_DUR    = 0.22

    def __init__(self, x, y, size):
        self.base_x   = float(x)
        self.base_y   = float(y)
        self.x        = float(x)
        self.y        = float(y)
        self.size     = size
        self.anim_time    = random.uniform(0, math.tau)
        self.flash_timer  = 0.0
        self.FLASH_DUR    = 0.4

        # New multi-phase lunge system
        self.lunging      = False   # kept for compatibility — True during any attack anim
        self.lunge_timer  = 0.0
        self.LUNGE_DUR    = self.WALK_DUR + self.WINDUP_DUR + self.STAB_DUR + self.HOLD_DUR + self.SNAP_DUR
        self._phase       = self.PHASE_IDLE
        self._phase_t     = 0.0    # time within current phase

        # Per-phase state
        self._walk_offset   = 0.0  # how far we've walked left
        self._arm_windup    = 0.0  # 0=neutral, 1=fully wound back
        self._arm_stab      = 0.0  # 0=neutral, 1=fully extended
        self._leg_phase     = 0.0  # drives leg walk cycle

    def start_lunge(self):
        self.lunging    = True
        self.lunge_timer = 0.0
        self._phase     = self.PHASE_WALK_IN
        self._phase_t   = 0.0
        self._walk_offset = 0.0
        self._arm_windup  = 0.0
        self._arm_stab    = 0.0

    def start_flash(self):
        self.flash_timer = self.FLASH_DUR

    def update(self, dt):
        self.anim_time   += dt
        self.flash_timer  = max(0.0, self.flash_timer - dt)

        if not self.lunging:
            self._phase      = self.PHASE_IDLE
            self._arm_windup = 0.0
            self._arm_stab   = 0.0
            return

        self.lunge_timer += dt
        self._phase_t    += dt

        # ── Phase transitions ──────────────────────────────────────────
        if self._phase == self.PHASE_WALK_IN:
            prog = min(1.0, self._phase_t / self.WALK_DUR)
            # Ease in: slow start, fast finish
            ease = 1 - (1 - prog) ** 2
            self._walk_offset = ease * self.size * 0.55
            self._leg_phase   = self.anim_time   # legs animate from anim_time
            if self._phase_t >= self.WALK_DUR:
                self._phase   = self.PHASE_WINDUP
                self._phase_t = 0.0

        elif self._phase == self.PHASE_WINDUP:
            prog = min(1.0, self._phase_t / self.WINDUP_DUR)
            self._arm_windup = prog          # arm pulls back
            self._arm_stab   = 0.0
            if self._phase_t >= self.WINDUP_DUR:
                self._phase   = self.PHASE_STAB
                self._phase_t = 0.0

        elif self._phase == self.PHASE_STAB:
            prog = min(1.0, self._phase_t / self.STAB_DUR)
            # Very fast — ease out so it slams
            ease = 1 - (1 - prog) ** 3
            self._arm_windup = 1.0 - ease    # arm snaps forward
            self._arm_stab   = ease
            if self._phase_t >= self.STAB_DUR:
                self._phase   = self.PHASE_HOLD
                self._phase_t = 0.0
                self._arm_windup = 0.0
                self._arm_stab   = 1.0

        elif self._phase == self.PHASE_HOLD:
            # Fully extended — brief pause
            self._arm_stab = 1.0
            if self._phase_t >= self.HOLD_DUR:
                self._phase   = self.PHASE_SNAPBACK
                self._phase_t = 0.0

        elif self._phase == self.PHASE_SNAPBACK:
            prog = min(1.0, self._phase_t / self.SNAP_DUR)
            ease = 1 - (1 - prog) ** 2
            self._arm_stab    = 1.0 - ease
            self._walk_offset = (1.0 - ease) * self.size * 0.55
            if self._phase_t >= self.SNAP_DUR:
                self.lunging      = False
                self._phase       = self.PHASE_IDLE
                self._phase_t     = 0.0
                self._arm_stab    = 0.0
                self._walk_offset = 0.0
                self.x = self.base_x
                self.y = self.base_y
                return

        # Apply walk offset to x position
        self.x = self.base_x - self._walk_offset

    def draw(self, surface):
        s   = self.size
        cx  = int(self.x)
        cy  = int(self.y)

        # Idle bob — stops during attack so it doesn't fight the animation
        if self._phase == self.PHASE_IDLE:
            bob = math.sin(self.anim_time * 2.0) * 3
        else:
            bob = 0

        flash = self.flash_timer / self.FLASH_DUR if self.flash_timer > 0 else 0.0

        def fc(col):
            return tuple(min(255, int(col[i] + (255 - col[i]) * flash * 0.65))
                         for i in range(3))

        skin    = fc((74,  154,  74))
        dark    = fc((45,  122,  45))
        darker  = fc((29,   90,  29))
        tunic   = fc((155, 107,  67))
        tunic_d = fc((107,  66,  37))
        pants   = fc((139,  94,  60))
        pants_d = fc((107,  66,  37))
        bone    = fc((232, 224, 192))
        tusk    = fc((236, 228, 194))
        wart    = fc((58,  138,  58))
        gold    = fc((200, 160,  80))
        wood    = fc((122,  78,  44))
        wood_d  = fc((90,   56,  26))
        tip_col = fc((176, 149, 106))
        blood   = fc((90,   26,  26))
        mohawk  = fc((45,  106,  45))
        scar    = fc((42,   90,  42))
        bracer  = fc((122,  82,  48))
        bracer_l= fc((154, 112,  64))
        tongue  = fc((180,  60,  60))

        u = s / 200   # scale unit

        # ── Leg walk animation ────────────────────────────────────────────
        # During walk-in and snapback legs cycle; idle they stand still
        if self._phase in (self.PHASE_WALK_IN, self.PHASE_SNAPBACK):
            leg_swing = math.sin(self.anim_time * 12.0)
        elif self._phase == self.PHASE_IDLE:
            leg_swing = math.sin(self.anim_time * 2.5) * 0.15  # tiny idle sway
        else:
            leg_swing = 0.0   # locked during windup/stab/hold

        stride = int(20 * u)
        l_foot_off = int(leg_swing * stride)
        r_foot_off = -l_foot_off

        # ── Shadow ────────────────────────────────────────────────────────
        sh = pygame.Surface((int(s * 1.2), int(s * 0.14)), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 45),
                            (0, 0, int(s * 1.2), int(s * 0.14)))
        surface.blit(sh, (cx - int(s * 0.6), cy + int(s * 0.42) + int(bob)))

        # ── Clawed feet ───────────────────────────────────────────────────
        fw = max(12, int(18 * u)); fh = max(5, int(8 * u))
        foot_y = cy + int(88 * u) + int(bob)
        lf_cx  = cx - int(30 * u) + l_foot_off
        rf_cx  = cx + int(30 * u) + r_foot_off

        for (fx, flip) in [(lf_cx, -1), (rf_cx, 1)]:
            pygame.draw.ellipse(surface, fc((58, 42, 24)),
                                (fx - fw, foot_y - fh // 2, fw * 2, fh))
            for fdx, fdy in [(flip * int(14*u), int(12*u)),
                             (flip * int(10*u), int(14*u)),
                             (flip * int(5*u),  int(14*u))]:
                pygame.draw.line(surface, fc((42, 28, 14)),
                                 (fx, foot_y), (fx + fdx, foot_y + fdy),
                                 max(2, int(3 * u)))

        # ── Legs — two-segment with animated knee ─────────────────────────
        lw = max(8, int(20 * u))
        leg_top_y = cy + int(38 * u) + int(bob)
        hip_l = (cx - int(18 * u), leg_top_y)
        hip_r = (cx + int(18 * u), leg_top_y)

        # Knee positions swing forward/back with feet
        lknee = (cx - int(26 * u) + l_foot_off // 2,
                 cy + int(66 * u) + int(bob))
        rknee = (cx + int(26 * u) + r_foot_off // 2,
                 cy + int(64 * u) + int(bob))

        # Left leg: hip -> knee -> foot
        pygame.draw.line(surface, pants, hip_l, lknee, lw)
        pygame.draw.line(surface, pants, lknee, (lf_cx, foot_y), lw)
        # Right leg
        pygame.draw.line(surface, pants_d, hip_r, rknee, lw)
        pygame.draw.line(surface, pants_d, rknee, (rf_cx, foot_y), lw)

        # Knee pads
        kp = max(6, int(10 * u))
        for kneepos, col in [(lknee, pants_d), (rknee, pants_d)]:
            pygame.draw.circle(surface, col, kneepos, kp)
            pygame.draw.circle(surface, bracer_l, kneepos, kp,
                               max(1, int(2 * u)))
            pygame.draw.circle(surface, gold, kneepos, max(2, int(3 * u)))

        # ── Belt ──────────────────────────────────────────────────────────
        belt_y = cy + int(36 * u) + int(bob)
        belt_w = int(76 * u); belt_h = max(5, int(10 * u))
        pygame.draw.rect(surface, fc((90, 56, 32)),
                         (cx - belt_w // 2, belt_y, belt_w, belt_h),
                         border_radius=3)
        bk_w = max(10, int(18 * u)); bk_h = max(8, int(16 * u))
        pygame.draw.rect(surface, gold,
                         (cx - bk_w // 2, belt_y - bk_h // 4, bk_w, bk_h),
                         border_radius=2)
        pygame.draw.rect(surface, fc((138, 96, 32)),
                         (cx - bk_w // 2 + max(2, int(3*u)),
                          belt_y - bk_h // 4 + max(2, int(3*u)),
                          bk_w - max(4, int(6*u)),
                          bk_h - max(4, int(6*u))))

        # ── Body ──────────────────────────────────────────────────────────
        bw = max(20, int(86 * u)); bh = max(16, int(130 * u))
        body_top = cy - int(54 * u) + int(bob)
        pygame.draw.ellipse(surface, tunic,
                            (cx - bw // 2, body_top, bw, bh))
        pygame.draw.ellipse(surface, tunic_d,
                            (cx - bw // 2, body_top, bw, bh),
                            max(1, int(2 * u)))
        pw = max(16, int(68 * u)); ph = max(12, int(100 * u))
        pygame.draw.ellipse(surface, tunic_d,
                            (cx - pw // 2, body_top + max(2, int(4*u)), pw, ph))
        pygame.draw.ellipse(surface, fc((90, 56, 26)),
                            (cx - pw // 2, body_top + max(2, int(4*u)), pw, ph),
                            max(1, int(2 * u)))
        rivet_r = max(2, int(4 * u))
        for rx_off in [-int(22*u), 0, int(22*u)]:
            pygame.draw.circle(surface, gold,
                               (cx + int(rx_off), body_top + int(22 * u)),
                               rivet_r)
        for rx_off in [-int(18*u), 0, int(18*u)]:
            pygame.draw.circle(surface, fc((168, 120, 48)),
                               (cx + int(rx_off), body_top + int(50 * u)),
                               max(2, int(3 * u)))
        pygame.draw.line(surface, fc((90, 56, 26)),
                         (cx, body_top + int(6*u)),
                         (cx, body_top + ph - int(6*u)),
                         max(1, int(2 * u)))
        for band_off in [int(36*u), int(68*u)]:
            pygame.draw.arc(surface, fc((90, 56, 26)),
                            (cx - pw // 2 + int(4*u),
                             body_top + band_off - int(3*u),
                             pw - int(8*u), int(6*u)),
                            0, math.pi, max(1, int(2*u)))

        # ── ARM ANIMATION offsets ─────────────────────────────────────────
        # windup: weapon arm pulls BACK (right, away from player)
        # stab:   weapon arm thrusts FORWARD (left, toward player)
        windup_back  = int(self._arm_windup * 38 * u)   # pulls right
        stab_forward = int(self._arm_stab   * 52 * u)   # thrusts left

        # ── Right arm — trailing, animates counter to weapon arm ──────────
        arm_w = max(5, int(14 * u))
        # During stab right arm swings back slightly for counterbalance
        r_counter = int(self._arm_stab * 14 * u)
        shoulder_r = (cx + int(40 * u), cy - int(34 * u) + int(bob))
        elbow_r    = (cx + int(66 * u) + r_counter,
                      cy + int(6  * u) + int(bob))
        rhand      = (cx + int(80 * u) + r_counter,
                      cy + int(34 * u) + int(bob))
        pygame.draw.line(surface, skin, shoulder_r, elbow_r, arm_w)
        pygame.draw.line(surface, skin, elbow_r, rhand,
                         max(4, int(12 * u)))
        pygame.draw.circle(surface, skin, rhand, max(5, int(9 * u)))
        for cdx, cdy in [(int(12*u), -int(10*u)), (int(14*u), -int(5*u)),
                         (int(14*u),  int(2*u)),  (int(10*u),  int(8*u))]:
            pygame.draw.line(surface, darker, rhand,
                             (rhand[0] + cdx, rhand[1] + cdy),
                             max(1, int(2 * u)))

        # ── Left arm — weapon arm, animated ──────────────────────────────
        shoulder_l = (cx - int(40 * u), cy - int(34 * u) + int(bob))
        # Windup pulls elbow/hand back (right), stab thrusts left
        elbow_l = (cx - int(70 * u) + windup_back - stab_forward,
                   cy - int(18 * u) + int(bob))
        lhand   = (cx - int(94 * u) + windup_back - stab_forward,
                   cy - int(40 * u) + int(bob))
        pygame.draw.line(surface, skin, shoulder_l, elbow_l, arm_w)
        pygame.draw.line(surface, skin, elbow_l, lhand,
                         max(4, int(12 * u)))
        # Bracer
        mid_arm = ((elbow_l[0] + lhand[0]) // 2,
                   (elbow_l[1] + lhand[1]) // 2)
        angle = math.atan2(lhand[1] - elbow_l[1],
                           lhand[0] - elbow_l[0])
        cos_a = math.cos(angle); sin_a = math.sin(angle)
        hw = int(11 * u); hh = int(7 * u)
        bpts = [
            (mid_arm[0] + int( cos_a*hw - sin_a*hh),
             mid_arm[1] + int( sin_a*hw + cos_a*hh)),
            (mid_arm[0] + int( cos_a*hw + sin_a*hh),
             mid_arm[1] + int( sin_a*hw - cos_a*hh)),
            (mid_arm[0] + int(-cos_a*hw + sin_a*hh),
             mid_arm[1] + int(-sin_a*hw - cos_a*hh)),
            (mid_arm[0] + int(-cos_a*hw - sin_a*hh),
             mid_arm[1] + int(-sin_a*hw + cos_a*hh)),
        ]
        pygame.draw.polygon(surface, bracer, bpts)
        pygame.draw.polygon(surface, bracer_l, bpts, max(1, int(2*u)))
        pygame.draw.circle(surface, skin, lhand, max(5, int(9 * u)))
        for cdx, cdy in [(-int(10*u), -int(10*u)), (-int(6*u), -int(12*u)),
                         ( int(2*u),  -int(12*u))]:
            pygame.draw.line(surface, darker, lhand,
                             (lhand[0] + cdx, lhand[1] + cdy),
                             max(1, int(2 * u)))

        # ── WEAPON — follows the hand ─────────────────────────────────────
        stick_end = (lhand[0] - int(80 * u), lhand[1] - int(90 * u))
        pygame.draw.line(surface, wood, lhand, stick_end, max(5, int(8 * u)))
        # Wood grain
        for t_frac in [0.3, 0.55, 0.78]:
            kx = int(lhand[0] + (stick_end[0] - lhand[0]) * t_frac)
            ky = int(lhand[1] + (stick_end[1] - lhand[1]) * t_frac)
            pygame.draw.line(surface, wood_d,
                             (kx, ky),
                             (kx - int(8*u), ky + int(4*u)),
                             max(1, int(2 * u)))
        # Grip wrap
        for i in range(3):
            t_frac = 0.08 + i * 0.06
            gx = int(lhand[0] + (stick_end[0] - lhand[0]) * t_frac)
            gy = int(lhand[1] + (stick_end[1] - lhand[1]) * t_frac)
            pygame.draw.line(surface, fc((58, 34, 16)),
                             (gx - int(6*u), gy - int(3*u)),
                             (gx + int(6*u), gy + int(3*u)),
                             max(2, int(4 * u)))
        # Bone weight lashed on
        bp = 0.55
        bx = int(lhand[0] + (stick_end[0] - lhand[0]) * bp)
        by = int(lhand[1] + (stick_end[1] - lhand[1]) * bp)
        pygame.draw.line(surface, fc((208, 192, 144)),
                         (bx - int(10*u), by - int(5*u)),
                         (bx + int(6*u),  by + int(3*u)),
                         max(3, int(5 * u)))
        for i in range(2):
            lx = bx - int((4-i*4)*u); ly = by - int((2-i*2)*u)
            pygame.draw.line(surface, wood_d,
                             (lx - int(4*u), ly + int(8*u)),
                             (lx + int(8*u), ly - int(4*u)),
                             max(1, int(2 * u)))
        # Tip
        tip_dx = stick_end[0] - lhand[0]
        tip_dy = stick_end[1] - lhand[1]
        tip_len = math.hypot(tip_dx, tip_dy)
        if tip_len > 0:
            tnx = tip_dx / tip_len; tny = tip_dy / tip_len
            px2 = -tny;             py2 = tnx
            tip_pts = [
                stick_end,
                (int(stick_end[0] + tnx*int(18*u) - px2*int(10*u)),
                 int(stick_end[1] + tny*int(18*u) - py2*int(10*u))),
                (int(stick_end[0] - tnx*int(6*u)  + px2*int(12*u)),
                 int(stick_end[1] - tny*int(6*u)  + py2*int(12*u))),
            ]
            pygame.draw.polygon(surface, tip_col, tip_pts)
            pygame.draw.polygon(surface, wood_d, tip_pts, max(1, int(2*u)))
            pygame.draw.line(surface, fc((212, 180, 128)),
                             stick_end,
                             (int(stick_end[0] + tnx*int(14*u)),
                              int(stick_end[1] + tny*int(14*u))),
                             max(1, int(2*u)))
        bx2 = int(stick_end[0] - tnx*int(8*u))
        by2 = int(stick_end[1] - tny*int(8*u))
        pygame.draw.ellipse(surface, blood,
                            (bx2 - int(6*u), by2 - int(3*u),
                             int(10*u), int(5*u)))

        # ── Neck ──────────────────────────────────────────────────────────
        neck_w = max(6, int(18 * u))
        pygame.draw.line(surface, skin,
                         (cx, body_top + int(bob)),
                         (cx, body_top - int(14*u) + int(bob)),
                         neck_w)

        # ── Head — ears before fill ───────────────────────────────────────
        hr = max(12, int(52 * u))
        head_cy = cy - int(92 * u) + int(bob)
        ep = max(6, int(20 * u))
        for sign, flip in [(-1, -1), (1, 1)]:
            ear = [
                (cx + sign*(hr - max(1, int(4*u))),  head_cy - hr // 3),
                (cx + sign*(hr + ep),                 head_cy - hr - ep),
                (cx + sign*(hr // 2),                 head_cy - hr // 2),
            ]
            pygame.draw.polygon(surface, skin, ear)
            pygame.draw.polygon(surface, dark, ear, max(1, int(2*u)))
            inner = [
                (cx + sign*(hr - max(2, int(6*u))),        head_cy - hr//3  + max(1,int(2*u))),
                (cx + sign*(hr + ep - max(4,int(8*u))),    head_cy - hr - ep + max(4,int(8*u))),
                (cx + sign*(hr//2 - sign*max(2,int(4*u))), head_cy - hr//2  + max(1,int(2*u))),
            ]
            pygame.draw.polygon(surface, darker, inner)
        # Earring on right ear
        pygame.draw.circle(surface, gold,
                           (cx + hr + int(ep * 0.5), head_cy - int(ep * 0.6)),
                           max(3, int(5 * u)), max(1, int(2*u)))
        # Head fill
        pygame.draw.circle(surface, skin, (cx, head_cy), hr)
        pygame.draw.circle(surface, dark, (cx, head_cy), hr, max(1, int(2*u)))

        # ── Mohawk ────────────────────────────────────────────────────────
        for mx_off, spike_h in [(-int(20*u), int(24*u)), (-int(8*u), int(30*u)),
                                 ( int(4*u),  int(28*u)), (int(16*u), int(22*u))]:
            pygame.draw.polygon(surface, mohawk, [
                (cx + mx_off - max(3,int(6*u)), head_cy - hr + max(2,int(4*u))),
                (cx + mx_off + max(1,int(2*u)), head_cy - hr - spike_h),
                (cx + mx_off + max(3,int(6*u)), head_cy - hr + max(2,int(4*u))),
            ])

        # ── Battle scar ───────────────────────────────────────────────────
        pygame.draw.line(surface, scar,
                         (cx - int(30*u), head_cy - int(24*u)),
                         (cx - int(18*u), head_cy + int(10*u)),
                         max(2, int(3*u)))

        # ── Warts ─────────────────────────────────────────────────────────
        for wx, wy, wr in [
            (cx - int(24*u), head_cy - int(12*u), max(3, int(4*u))),
            (cx + int(18*u), head_cy + int(8*u),  max(2, int(3*u))),
            (cx - int(10*u), head_cy + int(14*u), max(2, int(3*u))),
            (cx + int(8*u),  head_cy - int(18*u), max(2, int(3*u))),
        ]:
            pygame.draw.circle(surface, wart, (wx, wy), wr)

        # ── Eyes ──────────────────────────────────────────────────────────
        eox = max(5, int(18 * u))
        er  = max(4, int(9 * u))
        for ex in [cx - eox, cx + eox]:
            ey = head_cy - max(3, int(6*u))
            pygame.draw.circle(surface, (26, 26, 10), (ex, ey), er + 1)
            pygame.draw.circle(surface, (26, 26, 10), (ex, ey), er)
            pygame.draw.circle(surface, (255, 255, 255),
                               (ex + max(1,int(3*u)), ey - max(1,int(2*u))),
                               max(2, int(3*u)))

        # ── Brow ──────────────────────────────────────────────────────────
        brow_y = head_cy - max(4, int(16*u))
        for ex in [cx - eox, cx + eox]:
            pygame.draw.ellipse(surface, dark,
                                (ex - max(4,int(7*u)), brow_y - max(2,int(3*u)),
                                 max(8,int(14*u)), max(4,int(6*u))))
        pygame.draw.line(surface, darker,
                         (cx - eox - max(3,int(6*u)), brow_y - max(1,int(3*u))),
                         (cx - eox + max(3,int(6*u)), brow_y + max(2,int(5*u))),
                         max(2, int(4*u)))
        pygame.draw.line(surface, darker,
                         (cx + eox + max(3,int(6*u)), brow_y - max(1,int(3*u))),
                         (cx + eox - max(3,int(6*u)), brow_y + max(2,int(5*u))),
                         max(2, int(4*u)))

        # ── Nose ──────────────────────────────────────────────────────────
        nw = max(8, int(14*u)); nh = max(6, int(11*u))
        pygame.draw.ellipse(surface, dark,
                            (cx - nw//2, head_cy + max(2,int(8*u)), nw, nh))
        for nox in [-max(3,int(5*u)), max(3,int(5*u))]:
            pygame.draw.circle(surface, darker,
                               (cx + nox, head_cy + max(4,int(13*u))),
                               max(2, int(4*u)))

        # ── Mouth ─────────────────────────────────────────────────────────
        mouth_y = head_cy + max(8, int(26*u))
        mouth_w = max(12, int(46*u))
        pygame.draw.arc(surface, (26, 10, 10),
                        (cx - mouth_w//2, mouth_y - max(3,int(4*u)),
                         mouth_w, max(6,int(14*u))),
                        0, math.pi, max(2, int(3*u)))
        pygame.draw.ellipse(surface, tongue,
                            (cx - max(6,int(10*u)), mouth_y,
                             max(12,int(20*u)), max(4,int(8*u))))
        tooth_w = max(3, int(6*u))
        for tx in range(cx - mouth_w//2 + max(2,int(4*u)),
                        cx + mouth_w//2 - max(2,int(4*u)),
                        max(5, int(8*u))):
            pygame.draw.rect(surface, bone,
                             (tx, mouth_y, tooth_w, max(5,int(8*u))),
                             border_radius=1)
        tusk_w = max(3, int(4*u))
        pygame.draw.line(surface, tusk,
                         (cx - mouth_w//2 + max(1,int(2*u)), mouth_y),
                         (cx - mouth_w//2 - max(1,int(2*u)),
                          mouth_y + max(6,int(16*u))), tusk_w)
        pygame.draw.line(surface, tusk,
                         (cx + mouth_w//2 - max(1,int(2*u)), mouth_y),
                         (cx + mouth_w//2 + max(1,int(2*u)),
                          mouth_y + max(6,int(16*u))), tusk_w)


# ---------------------------------------------------------------------------
# Generic combat sprite proxy — uses enemy.py draw functions
# ---------------------------------------------------------------------------

class CombatEnemyProxy:
    """Wraps enemy draw functions for use in the combat scene."""

    def __init__(self, x, y, size, enemy_type, color):
        self.base_x    = float(x)
        self.base_y    = float(y)
        self.x         = float(x)
        self.y         = float(y)
        self.size      = size
        self.enemy_type = enemy_type
        self.color     = color
        self.anim_time = 0.0
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
            else:
                self.x = self.base_x - math.sin(t*math.pi) * self.size * 1.0

    def draw(self, surface):
        from src.entities.enemy import (
            _draw_skeleton, _draw_troll, _draw_dark_mage, _draw_generic,
            _draw_imp, _draw_dire_rat, _draw_orc_warrior,
            _draw_stone_golem, _draw_werewolf, _draw_lich,
            _draw_bone_lord, _draw_mountain_king, _draw_archmage,
            _draw_inferno_duke, _draw_rat_king, _draw_warchief_grommak,
            _draw_ancient_colossus, _draw_the_alpha, _draw_lich_king)
        s  = self.size
        cx = int(self.x); cy = int(self.y)
        flash  = self.flash_timer / self.FLASH_DUR if self.flash_timer > 0 else 0.0
        draw_x = cx - s//2; draw_y = cy - s//2
        t  = self.anim_time; ts = s
        etype = self.enemy_type
        if   etype=="skeleton":          _draw_skeleton(surface,draw_x,draw_y,t,ts)
        elif etype=="troll":             _draw_troll(surface,draw_x,draw_y,t,ts)
        elif etype=="dark_mage":         _draw_dark_mage(surface,draw_x,draw_y,t,ts)
        elif etype=="imp":               _draw_imp(surface,draw_x,draw_y,t,ts)
        elif etype=="dire_rat":          _draw_dire_rat(surface,draw_x,draw_y,t,ts)
        elif etype=="orc_warrior":       _draw_orc_warrior(surface,draw_x,draw_y,t,ts)
        elif etype=="stone_golem":       _draw_stone_golem(surface,draw_x,draw_y,t,ts)
        elif etype=="werewolf":          _draw_werewolf(surface,draw_x,draw_y,t,ts)
        elif etype=="lich":              _draw_lich(surface,draw_x,draw_y,t,ts)
        elif etype=="bone_lord":         _draw_bone_lord(surface,draw_x,draw_y,t,ts)
        elif etype=="mountain_king":     _draw_mountain_king(surface,draw_x,draw_y,t,ts)
        elif etype=="archmage":          _draw_archmage(surface,draw_x,draw_y,t,ts)
        elif etype=="inferno_duke":      _draw_inferno_duke(surface,draw_x,draw_y,t,ts)
        elif etype=="rat_king":          _draw_rat_king(surface,draw_x,draw_y,t,ts)
        elif etype=="warchief_grommak":  _draw_warchief_grommak(surface,draw_x,draw_y,t,ts)
        elif etype=="ancient_colossus":  _draw_ancient_colossus(surface,draw_x,draw_y,t,ts)
        elif etype=="the_alpha":         _draw_the_alpha(surface,draw_x,draw_y,t,ts)
        elif etype=="lich_king":         _draw_lich_king(surface,draw_x,draw_y,t,ts)
        else:                            _draw_generic(surface,draw_x,draw_y,t,ts,self.color)
        if flash > 0:
            from src.entities.enemy import (
                _draw_skeleton, _draw_troll, _draw_dark_mage, _draw_generic,
                _draw_imp, _draw_dire_rat, _draw_orc_warrior,
                _draw_stone_golem, _draw_werewolf, _draw_lich,
                _draw_bone_lord, _draw_mountain_king, _draw_archmage,
                _draw_inferno_duke, _draw_rat_king, _draw_warchief_grommak,
                _draw_ancient_colossus, _draw_the_alpha, _draw_lich_king)
            flash_surf = pygame.Surface((s*2, s*2), pygame.SRCALPHA)
            etype2 = self.enemy_type
            if   etype2=="skeleton":         _draw_skeleton(flash_surf,s//2,s//2,t,s)
            elif etype2=="troll":            _draw_troll(flash_surf,s//2,s//2,t,s)
            elif etype2=="dark_mage":        _draw_dark_mage(flash_surf,s//2,s//2,t,s)
            elif etype2=="imp":              _draw_imp(flash_surf,s//2,s//2,t,s)
            elif etype2=="dire_rat":         _draw_dire_rat(flash_surf,s//2,s//2,t,s)
            elif etype2=="orc_warrior":      _draw_orc_warrior(flash_surf,s//2,s//2,t,s)
            elif etype2=="stone_golem":      _draw_stone_golem(flash_surf,s//2,s//2,t,s)
            elif etype2=="werewolf":         _draw_werewolf(flash_surf,s//2,s//2,t,s)
            elif etype2=="lich":             _draw_lich(flash_surf,s//2,s//2,t,s)
            elif etype2=="bone_lord":        _draw_bone_lord(flash_surf,s//2,s//2,t,s)
            elif etype2=="mountain_king":    _draw_mountain_king(flash_surf,s//2,s//2,t,s)
            elif etype2=="archmage":         _draw_archmage(flash_surf,s//2,s//2,t,s)
            elif etype2=="inferno_duke":     _draw_inferno_duke(flash_surf,s//2,s//2,t,s)
            elif etype2=="rat_king":         _draw_rat_king(flash_surf,s//2,s//2,t,s)
            elif etype2=="warchief_grommak": _draw_warchief_grommak(flash_surf,s//2,s//2,t,s)
            elif etype2=="ancient_colossus": _draw_ancient_colossus(flash_surf,s//2,s//2,t,s)
            elif etype2=="the_alpha":        _draw_the_alpha(flash_surf,s//2,s//2,t,s)
            elif etype2=="lich_king":        _draw_lich_king(flash_surf,s//2,s//2,t,s)
            else:                            _draw_generic(flash_surf,s//2,s//2,t,s,self.color)
            white = pygame.Surface((s*2, s*2), pygame.SRCALPHA)
            white.fill((255,255,255,int(flash*180)))
            flash_surf.blit(white,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(flash_surf,(draw_x-s//2, draw_y-s//2))

# ---------------------------------------------------------------------------
# Goblin Chieftain combat sprite
# ---------------------------------------------------------------------------

class CombatGoblinChieftain:
    """
    Goblin Chieftain combat sprite — faces LEFT toward the player.
    Larger and more detailed than the wandering version.
    Battle-scarred, dead eye, axe raised and ready.
    """

    PHASE_IDLE     = "idle"
    PHASE_WALK_IN  = "walk_in"
    PHASE_WINDUP   = "windup"
    PHASE_SWING    = "swing"
    PHASE_HOLD     = "hold"
    PHASE_SNAPBACK = "snapback"

    WALK_DUR   = 0.40
    WINDUP_DUR = 0.22
    SWING_DUR  = 0.14
    HOLD_DUR   = 0.12
    SNAP_DUR   = 0.24

    def __init__(self, x, y, size):
        self.base_x  = float(x)
        self.base_y  = float(y)
        self.x       = float(x)
        self.y       = float(y)
        self.size    = size
        self.anim_time   = 0.0
        self.flash_timer = 0.0
        self.FLASH_DUR   = 0.45
        self.lunging     = False
        self.lunge_timer = 0.0
        self.LUNGE_DUR   = (self.WALK_DUR + self.WINDUP_DUR +
                            self.SWING_DUR + self.HOLD_DUR + self.SNAP_DUR)
        self._phase      = self.PHASE_IDLE
        self._phase_t    = 0.0
        self._walk_offset  = 0.0
        self._axe_windup   = 0.0   # 0=ready, 1=fully wound back
        self._axe_swing    = 0.0   # 0=ready, 1=fully swung forward

    def start_lunge(self):
        self.lunging     = True
        self.lunge_timer = 0.0
        self._phase      = self.PHASE_WALK_IN
        self._phase_t    = 0.0
        self._walk_offset  = 0.0
        self._axe_windup   = 0.0
        self._axe_swing    = 0.0

    def start_flash(self):
        self.flash_timer = self.FLASH_DUR

    def update(self, dt):
        self.anim_time   += dt
        self.flash_timer  = max(0.0, self.flash_timer - dt)

        if not self.lunging:
            self._phase     = self.PHASE_IDLE
            self._axe_windup = 0.0
            self._axe_swing  = 0.0
            return

        self.lunge_timer += dt
        self._phase_t    += dt

        if self._phase == self.PHASE_WALK_IN:
            prog = min(1.0, self._phase_t / self.WALK_DUR)
            ease = 1 - (1 - prog) ** 2
            self._walk_offset = ease * self.size * 0.45
            if self._phase_t >= self.WALK_DUR:
                self._phase   = self.PHASE_WINDUP
                self._phase_t = 0.0

        elif self._phase == self.PHASE_WINDUP:
            prog = min(1.0, self._phase_t / self.WINDUP_DUR)
            self._axe_windup = prog
            self._axe_swing  = 0.0
            if self._phase_t >= self.WINDUP_DUR:
                self._phase   = self.PHASE_SWING
                self._phase_t = 0.0

        elif self._phase == self.PHASE_SWING:
            prog = min(1.0, self._phase_t / self.SWING_DUR)
            ease = 1 - (1 - prog) ** 3
            self._axe_windup = 1.0 - ease
            self._axe_swing  = ease
            if self._phase_t >= self.SWING_DUR:
                self._phase      = self.PHASE_HOLD
                self._phase_t    = 0.0
                self._axe_windup = 0.0
                self._axe_swing  = 1.0

        elif self._phase == self.PHASE_HOLD:
            self._axe_swing = 1.0
            if self._phase_t >= self.HOLD_DUR:
                self._phase   = self.PHASE_SNAPBACK
                self._phase_t = 0.0

        elif self._phase == self.PHASE_SNAPBACK:
            prog = min(1.0, self._phase_t / self.SNAP_DUR)
            ease = 1 - (1 - prog) ** 2
            self._axe_swing   = 1.0 - ease
            self._walk_offset = (1.0 - ease) * self.size * 0.45
            if self._phase_t >= self.SNAP_DUR:
                self.lunging     = False
                self._phase      = self.PHASE_IDLE
                self._phase_t    = 0.0
                self._axe_swing  = 0.0
                self._walk_offset = 0.0
                self.x = self.base_x
                self.y = self.base_y
                return

        self.x = self.base_x - self._walk_offset

    def draw(self, surface):
        s   = self.size
        cx  = int(self.x)
        cy  = int(self.y)

        # Idle: slow heavy bob. During attack: locked
        if self._phase == self.PHASE_IDLE:
            bob = math.sin(self.anim_time * 1.8) * 4
        else:
            bob = 0

        flash = self.flash_timer / self.FLASH_DUR if self.flash_timer > 0 else 0.0

        def fc(col):
            return tuple(min(255, int(col[i] + (255 - col[i]) * flash * 0.65))
                         for i in range(3))

        u = s / 220   # scale unit — slightly different base than goblin

        skin    = fc((60,  120,  40))
        dark    = fc((35,   85,  22))
        darker  = fc((22,   60,  14))
        hide    = fc((139,  88,  52))
        hide_d  = fc((105,  62,  30))
        hide_l  = fc((165, 112,  68))
        blood   = fc((160,  18,  18))
        bone    = fc((220, 210, 180))
        bone_d  = fc((170, 158, 130))
        claw_c  = fc(( 38,  26,  12))
        wood    = fc((118,  76,  40))
        wood_d  = fc(( 88,  54,  24))
        iron    = fc((148, 142, 134))
        iron_d  = fc(( 90,  86,  80))
        iron_l  = fc((198, 194, 188))
        belt_c  = fc(( 80,  48,  20))
        gold    = fc((185, 148,  45))

        # ── Shadow ───────────────────────────────────────────────────────
        sh = pygame.Surface((int(s * 1.3), int(s * 0.15)), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 50),
                            (0, 0, int(s * 1.3), int(s * 0.15)))
        surface.blit(sh, (cx - int(s * 0.65), cy + int(s * 0.44) + int(bob)))

        # ── Clawed feet ──────────────────────────────────────────────────
        fw = max(14, int(22 * u)); fh = max(6, int(10 * u))
        foot_y = cy + int(96 * u) + int(bob)
        # Slight forward lean — weight on left foot (toward player)
        lf_cx = cx - int(28 * u)
        rf_cx = cx + int(32 * u)

        for (fx, flip) in [(lf_cx, -1), (rf_cx, 1)]:
            pygame.draw.ellipse(surface, fc((55, 40, 20)),
                                (fx - fw, foot_y - fh // 2, fw * 2, fh))
            for fdx, fdy in [
                (flip * int(16*u), int(14*u)),
                (flip * int(12*u), int(16*u)),
                (flip * int(5*u),  int(16*u)),
            ]:
                pygame.draw.line(surface, claw_c,
                                 (fx, foot_y),
                                 (fx + fdx, foot_y + fdy),
                                 max(2, int(3 * u)))

        # ── Legs — thick hide-covered ─────────────────────────────────────
        lw = max(10, int(24 * u))
        leg_top_y = cy + int(42 * u) + int(bob)
        hip_l = (cx - int(20 * u), leg_top_y)
        hip_r = (cx + int(20 * u), leg_top_y)
        lknee = (cx - int(28 * u), cy + int(72 * u) + int(bob))
        rknee = (cx + int(28 * u), cy + int(70 * u) + int(bob))

        pygame.draw.line(surface, hide,   hip_l, lknee, lw)
        pygame.draw.line(surface, hide,   lknee, (lf_cx, foot_y), lw)
        pygame.draw.line(surface, hide_d, hip_r, rknee, lw)
        pygame.draw.line(surface, hide_d, rknee, (rf_cx, foot_y), lw)

        # Knee pads — crude bone discs
        kp = max(8, int(13 * u))
        for kneepos in [lknee, rknee]:
            pygame.draw.circle(surface, bone_d, kneepos, kp)
            pygame.draw.circle(surface, bone,   kneepos, kp, max(1, int(2*u)))
            pygame.draw.circle(surface, hide_d, kneepos, max(3, int(5*u)))

        # ── Belt ─────────────────────────────────────────────────────────
        belt_y = cy + int(38 * u) + int(bob)
        belt_w = int(88 * u); belt_h = max(6, int(12 * u))
        pygame.draw.rect(surface, belt_c,
                         (cx - belt_w // 2, belt_y, belt_w, belt_h),
                         border_radius=3)
        # Belt buckle
        bk_w = max(12, int(20 * u)); bk_h = max(10, int(18 * u))
        pygame.draw.rect(surface, gold,
                         (cx - bk_w // 2, belt_y - bk_h // 4, bk_w, bk_h),
                         border_radius=2)
        pygame.draw.rect(surface, fc((110, 82, 24)),
                         (cx - bk_w // 2 + max(2, int(3*u)),
                          belt_y - bk_h // 4 + max(2, int(3*u)),
                          bk_w - max(4, int(6*u)),
                          bk_h - max(4, int(6*u))))
        # Trophy skull hanging from belt — left side
        sk_x = cx - belt_w // 2 + int(18 * u)
        sk_y = belt_y + belt_h + max(3, int(5*u))
        pygame.draw.line(surface, belt_c,
                         (sk_x, belt_y + belt_h), (sk_x, sk_y),
                         max(1, int(2*u)))
        sk_r = max(5, int(8*u))
        pygame.draw.circle(surface, bone_d, (sk_x, sk_y + sk_r), sk_r)
        pygame.draw.circle(surface, bone,   (sk_x, sk_y + sk_r), sk_r,
                           max(1, int(2*u)))
        for ex_off in [-max(2, int(3*u)), max(2, int(3*u))]:
            pygame.draw.circle(surface, darker,
                               (sk_x + ex_off, sk_y + sk_r - max(1, int(2*u))),
                               max(1, int(2*u)))

        # ── Body — wide barrel chest, detailed hide tunic ─────────────────
        bw = max(24, int(100 * u)); bh = max(20, int(148 * u))
        body_top = cy - int(60 * u) + int(bob)

        pygame.draw.ellipse(surface, hide,
                            (cx - bw // 2, body_top, bw, bh))
        pygame.draw.ellipse(surface, hide_d,
                            (cx - bw // 2, body_top, bw, bh),
                            max(1, int(2*u)))
        # Inner panel — worn lighter patch in centre
        pw = max(16, int(72 * u)); ph = max(14, int(110 * u))
        pygame.draw.ellipse(surface, hide_d,
                            (cx - pw // 2, body_top + max(2, int(5*u)), pw, ph))
        # Stitching lines down centre
        for stitch_y in range(body_top + int(12*u),
                              body_top + ph, max(5, int(10*u))):
            pygame.draw.line(surface, hide_l,
                             (cx - max(1, int(2*u)), int(stitch_y)),
                             (cx + max(1, int(2*u)), int(stitch_y) + max(3, int(6*u))),
                             max(1, int(2*u)))
        # Horizontal wear bands
        for band_off in [int(38*u), int(78*u)]:
            pygame.draw.arc(surface, fc((90, 56, 26)),
                            (cx - pw // 2 + int(4*u),
                             body_top + band_off - int(3*u),
                             pw - int(8*u), int(6*u)),
                            0, math.pi, max(1, int(2*u)))
        # Crude bone toggle at collar
        tog_x = cx; tog_y = body_top + max(4, int(8*u))
        pygame.draw.line(surface, bone,
                         (tog_x - max(5, int(9*u)), tog_y),
                         (tog_x + max(5, int(9*u)), tog_y),
                         max(2, int(4*u)))
        pygame.draw.circle(surface, hide_d, (tog_x, tog_y), max(2, int(4*u)))

        # ── AXE ANIMATION — windup pulls back (right), swing thrusts left ─
        # During idle: axe held up and ready at left side
        # windup: axe lifts further back over shoulder
        # swing: axe sweeps down and forward toward player (left)
        axe_windup_lift   = int(self._axe_windup * 45 * u)   # lifts up+right
        axe_swing_forward = int(self._axe_swing  * 65 * u)   # sweeps left+down

        # ── RIGHT arm — counterbalance, swings back during attack ─────────
        arm_w = max(6, int(16 * u))
        r_counter = int(self._axe_swing * 18 * u)
        shoulder_r = (cx + int(44 * u), cy - int(38 * u) + int(bob))
        elbow_r    = (cx + int(72 * u) + r_counter,
                      cy + int(8  * u) + int(bob))
        rhand      = (cx + int(88 * u) + r_counter,
                      cy + int(38 * u) + int(bob))
        pygame.draw.line(surface, skin, shoulder_r, elbow_r, arm_w)
        pygame.draw.line(surface, skin, elbow_r, rhand, max(5, int(14*u)))
        pygame.draw.circle(surface, skin, rhand, max(6, int(10*u)))
        for cdx, cdy in [(int(13*u), -int(10*u)), (int(15*u), -int(4*u)),
                         (int(15*u),  int(3*u)),  (int(10*u),  int(9*u))]:
            pygame.draw.line(surface, darker, rhand,
                             (rhand[0] + cdx, rhand[1] + cdy),
                             max(1, int(2*u)))

        # ── LEFT arm — axe arm, animated ─────────────────────────────────
        shoulder_l = (cx - int(44 * u), cy - int(38 * u) + int(bob))
        # Idle: arm raised, axe ready at upper left
        # Windup: arm lifts higher + back (right)
        # Swing: arm sweeps down hard to the left
        elbow_l = (cx - int(68 * u) + axe_windup_lift - axe_swing_forward,
                   cy - int(55 * u) + axe_windup_lift // 2 + int(bob))
        lhand   = (cx - int(88 * u) + axe_windup_lift - axe_swing_forward,
                   cy - int(80 * u) + axe_windup_lift + int(bob))

        pygame.draw.line(surface, skin, shoulder_l, elbow_l, arm_w)
        pygame.draw.line(surface, skin, elbow_l, lhand, max(5, int(14*u)))

        # Bracer on left arm — wide leather strap
        mid_arm = ((elbow_l[0] + lhand[0]) // 2,
                   (elbow_l[1] + lhand[1]) // 2)
        angle   = math.atan2(lhand[1] - elbow_l[1], lhand[0] - elbow_l[0])
        cos_a = math.cos(angle); sin_a = math.sin(angle)
        hw = int(13 * u); hh = int(8 * u)
        bpts = [
            (mid_arm[0] + int( cos_a*hw - sin_a*hh),
             mid_arm[1] + int( sin_a*hw + cos_a*hh)),
            (mid_arm[0] + int( cos_a*hw + sin_a*hh),
             mid_arm[1] + int( sin_a*hw - cos_a*hh)),
            (mid_arm[0] + int(-cos_a*hw + sin_a*hh),
             mid_arm[1] + int(-sin_a*hw - cos_a*hh)),
            (mid_arm[0] + int(-cos_a*hw - sin_a*hh),
             mid_arm[1] + int(-sin_a*hw + cos_a*hh)),
        ]
        pygame.draw.polygon(surface, hide_d, bpts)
        pygame.draw.polygon(surface, hide_l,  bpts, max(1, int(2*u)))
        # Bracer rivet
        pygame.draw.circle(surface, gold, mid_arm, max(2, int(4*u)))

        pygame.draw.circle(surface, skin, lhand, max(6, int(10*u)))
        for cdx, cdy in [(-int(11*u), -int(11*u)), (-int(7*u), -int(13*u)),
                         ( int(3*u),  -int(13*u))]:
            pygame.draw.line(surface, darker, lhand,
                             (lhand[0] + cdx, lhand[1] + cdy),
                             max(1, int(2*u)))

        # ── AXE — detailed, battle-worn ───────────────────────────────────
        # Handle runs from hand upward
        hx1, hy1 = lhand
        handle_len = int(100 * u)
        # Handle angle: idle=up-left, windup=more upright, swing=swept forward-down
        base_angle = math.radians(145)   # up and slightly left
        windup_rotate = self._axe_windup * math.radians(30)  # rotate clockwise (back)
        swing_rotate  = self._axe_swing  * math.radians(90)  # sweep forward hard
        axe_angle = base_angle + windup_rotate - swing_rotate
        hx2 = int(hx1 + math.cos(axe_angle) * handle_len)
        hy2 = int(hy1 + math.sin(axe_angle) * handle_len)

        # Handle — wood with grain
        pygame.draw.line(surface, wood,   (hx1, hy1), (hx2, hy2),
                         max(5, int(9 * u)))
        pygame.draw.line(surface, wood_d, (hx1, hy1), (hx2, hy2),
                         max(2, int(4 * u)))
        # Wood grain marks
        for frac in [0.25, 0.45, 0.65, 0.82]:
            gx = int(hx1 + (hx2-hx1)*frac)
            gy = int(hy1 + (hy2-hy1)*frac)
            perp_x = -math.sin(axe_angle) * int(6*u)
            perp_y =  math.cos(axe_angle) * int(6*u)
            pygame.draw.line(surface, wood_d,
                             (int(gx - perp_x), int(gy - perp_y)),
                             (int(gx + perp_x), int(gy + perp_y)),
                             max(1, int(2*u)))
        # Grip wrapping — leather strips near hand
        for i in range(3):
            frac = 0.08 + i * 0.07
            gx = int(hx1 + (hx2-hx1)*frac)
            gy = int(hy1 + (hy2-hy1)*frac)
            pygame.draw.line(surface, fc((60, 36, 16)),
                             (int(gx - math.sin(axe_angle)*int(7*u)),
                              int(gy + math.cos(axe_angle)*int(7*u))),
                             (int(gx + math.sin(axe_angle)*int(7*u)),
                              int(gy - math.cos(axe_angle)*int(7*u))),
                             max(2, int(5*u)))

        # Iron socket band at top of handle
        sx = int(hx1 + (hx2-hx1)*0.88)
        sy = int(hy1 + (hy2-hy1)*0.88)
        pygame.draw.line(surface, iron_d,
                         (int(sx - math.sin(axe_angle)*int(9*u)),
                          int(sy + math.cos(axe_angle)*int(9*u))),
                         (int(sx + math.sin(axe_angle)*int(9*u)),
                          int(sy - math.cos(axe_angle)*int(9*u))),
                         max(3, int(7*u)))
        pygame.draw.line(surface, iron,
                         (int(sx - math.sin(axe_angle)*int(7*u)),
                          int(sy + math.cos(axe_angle)*int(7*u))),
                         (int(sx + math.sin(axe_angle)*int(7*u)),
                          int(sy - math.cos(axe_angle)*int(7*u))),
                         max(1, int(3*u)))

        # Axe head — broad single-bit stone/iron, faces left toward player
        ax_cx, ax_cy = hx2, hy2
        # Head vectors: along handle and perpendicular
        along_x =  math.cos(axe_angle); along_y =  math.sin(axe_angle)
        perp_x  = -math.sin(axe_angle); perp_y  =  math.cos(axe_angle)
        hw_head = int(28 * u)   # half-height of head
        depth   = int(22 * u)   # how far it sticks out from handle

        axe_pts = [
            (int(ax_cx - along_x * int(6*u) + perp_x * hw_head),
             int(ax_cy - along_y * int(6*u) + perp_y * hw_head)),   # top socket
            (int(ax_cx - along_x * depth + perp_x * (hw_head + int(10*u))),
             int(ax_cy - along_y * depth + perp_y * (hw_head + int(10*u)))),  # top tip
            (int(ax_cx - along_x * (depth + int(8*u))),
             int(ax_cy - along_y * (depth + int(8*u)))),             # belly point
            (int(ax_cx - along_x * depth - perp_x * (hw_head + int(6*u))),
             int(ax_cy - along_y * depth - perp_y * (hw_head + int(6*u)))),  # bottom tip
            (int(ax_cx - along_x * int(6*u) - perp_x * hw_head),
             int(ax_cy - along_y * int(6*u) - perp_y * hw_head)),   # bottom socket
        ]
        pygame.draw.polygon(surface, iron,   axe_pts)
        pygame.draw.polygon(surface, iron_d, axe_pts, max(2, int(3*u)))

        # Edge highlight — sharpened blade edge (the left/outward face)
        pygame.draw.line(surface, iron_l,
                         axe_pts[1], axe_pts[2], max(1, int(2*u)))
        pygame.draw.line(surface, iron_l,
                         axe_pts[2], axe_pts[3], max(1, int(2*u)))

        # Battle damage — chip notch in blade
        chip_x = int((axe_pts[1][0] + axe_pts[2][0]) // 2)
        chip_y = int((axe_pts[1][1] + axe_pts[2][1]) // 2)
        pygame.draw.polygon(surface, iron_d, [
            (chip_x,                         chip_y),
            (chip_x + int(along_x*int(5*u)), chip_y + int(along_y*int(5*u))),
            (chip_x + int(perp_x *int(4*u)), chip_y + int(perp_y *int(4*u))),
        ])

        # Dark stain on blade — old blood
        stain_surf = pygame.Surface((int(depth*3), int(depth*3)), pygame.SRCALPHA)
        pygame.draw.ellipse(stain_surf, (60, 12, 12, 60),
                            (0, 0, int(depth*3), int(depth*2)))
        surface.blit(stain_surf,
                     (int(ax_cx - along_x*depth - depth*1.5),
                      int(ax_cy - along_y*depth - depth)),
                     special_flags=pygame.BLEND_RGBA_ADD)

        # ── Neck — thick ─────────────────────────────────────────────────
        neck_w = max(8, int(22 * u))
        pygame.draw.line(surface, skin,
                         (cx, body_top + int(bob)),
                         (cx, body_top - int(16*u) + int(bob)), neck_w)

        # ── Head — ears drawn BEFORE fill ────────────────────────────────
        hr      = max(14, int(60 * u))
        head_cx = cx
        head_cy = cy - int(105 * u) + int(bob)

        # Ear shape: wide, blade-like, horizontal
        ear_len = int(58 * u)
        ear_h   = int(14 * u)

        # Left ear
        left_ear = [
            (head_cx - hr + max(1, int(4*u)), head_cy - hr // 6),
            (head_cx - hr - ear_len,          head_cy - ear_h),
            (head_cx - hr // 2,               head_cy - hr // 2),
        ]
        pygame.draw.polygon(surface, skin,  left_ear)
        pygame.draw.polygon(surface, dark,  left_ear, max(1, int(2*u)))
        # Inner ear
        pygame.draw.polygon(surface, darker, [
            (head_cx - hr + max(3, int(6*u)), head_cy - hr // 6 + max(2, int(3*u))),
            (head_cx - hr - ear_len + max(8, int(14*u)), head_cy - ear_h + max(4, int(6*u))),
            (head_cx - hr // 2 + max(3, int(5*u)), head_cy - hr // 2 + max(2, int(3*u))),
        ])
        # Nick/notch in left ear from old battle
        nick_x = head_cx - hr - ear_len // 2
        nick_y = head_cy - ear_h - max(2, int(3*u))
        pygame.draw.polygon(surface, dark, [
            (nick_x - max(2, int(4*u)), nick_y),
            (nick_x + max(2, int(4*u)), nick_y),
            (nick_x,                   nick_y + max(3, int(6*u))),
        ])

        # Right ear
        right_ear = [
            (head_cx + hr - max(1, int(4*u)), head_cy - hr // 6),
            (head_cx + hr + ear_len,          head_cy - ear_h),
            (head_cx + hr // 2,               head_cy - hr // 2),
        ]
        pygame.draw.polygon(surface, skin,  right_ear)
        pygame.draw.polygon(surface, dark,  right_ear, max(1, int(2*u)))
        pygame.draw.polygon(surface, darker, [
            (head_cx + hr - max(3, int(6*u)), head_cy - hr // 6 + max(2, int(3*u))),
            (head_cx + hr + ear_len - max(8, int(14*u)), head_cy - ear_h + max(4, int(6*u))),
            (head_cx + hr // 2 - max(3, int(5*u)), head_cy - hr // 2 + max(2, int(3*u))),
        ])

        # Head fill
        pygame.draw.circle(surface, skin, (head_cx, head_cy), hr)
        pygame.draw.circle(surface, dark, (head_cx, head_cy), hr,
                           max(1, int(2*u)))

        # ── Dead right eye (milky, blood vessels) ─────────────────────────
        er  = max(5, int(11 * u))
        eox = max(6, int(hr // 3))
        dead_eye_pos = (head_cx + eox, head_cy - max(2, int(5*u)))

        # Milky eye base
        pygame.draw.circle(surface, (205, 198, 182), dead_eye_pos, er)
        pygame.draw.circle(surface, (165, 158, 145), dead_eye_pos, er,
                           max(1, int(2*u)))
        # Cloudy pupil — barely visible
        pygame.draw.circle(surface, (135, 128, 118), dead_eye_pos,
                           max(2, int(er * 0.5)))
        # Blood vessels — small red lines radiating from pupil
        for angle_deg in [20, 80, 150, 220, 300]:
            va = math.radians(angle_deg)
            vx1 = dead_eye_pos[0] + int(math.cos(va) * max(2, int(er * 0.4)))
            vy1 = dead_eye_pos[1] + int(math.sin(va) * max(2, int(er * 0.4)))
            vx2 = dead_eye_pos[0] + int(math.cos(va) * er)
            vy2 = dead_eye_pos[1] + int(math.sin(va) * er)
            pygame.draw.line(surface, (180, 40, 40),
                             (vx1, vy1), (vx2, vy2),
                             max(1, int(1.5 * u)))

        # ── Normal left eye — dark, furious ───────────────────────────────
        live_eye_pos = (head_cx - eox, head_cy - max(2, int(5*u)))
        pygame.draw.circle(surface, (18, 16, 6), live_eye_pos, er + 1)
        pygame.draw.circle(surface, (18, 16, 6), live_eye_pos, er)
        pygame.draw.circle(surface, (255, 255, 255),
                           (live_eye_pos[0] + max(1, int(3*u)),
                            live_eye_pos[1] - max(1, int(2*u))),
                           max(2, int(3*u)))

        # ── Heavy brow — deep angry V ─────────────────────────────────────
        brow_y = head_cy - er - max(4, int(18*u))
        brow_thick = max(3, int(5*u))
        pygame.draw.line(surface, darker,
                         (head_cx - eox - max(4, int(8*u)), brow_y - max(1, int(3*u))),
                         (head_cx - eox + max(3, int(6*u)), brow_y + max(3, int(7*u))),
                         brow_thick)
        pygame.draw.line(surface, darker,
                         (head_cx + eox + max(4, int(8*u)), brow_y - max(1, int(3*u))),
                         (head_cx + eox - max(3, int(6*u)), brow_y + max(3, int(7*u))),
                         brow_thick)
        # Brow furrow crease between eyes
        pygame.draw.line(surface, darker,
                         (head_cx - max(2, int(4*u)), brow_y + max(1, int(2*u))),
                         (head_cx + max(2, int(4*u)), brow_y + max(3, int(6*u))),
                         max(1, int(2*u)))

        # ── Battle scar — X over left eye, blood drip ────────────────────
        scar_cx, scar_cy = live_eye_pos
        scar_r = max(6, int(13 * u))
        # Outer scar lines — slightly darker red, thicker
        for dx1, dy1, dx2, dy2 in [
            (-scar_r, -scar_r,  scar_r,  scar_r),
            ( scar_r, -scar_r, -scar_r,  scar_r),
        ]:
            pygame.draw.line(surface, fc((120, 12, 12)),
                             (scar_cx + dx1, scar_cy + dy1),
                             (scar_cx + dx2, scar_cy + dy2),
                             max(2, int(4*u)))
        # Inner scar highlight — brighter red on top
        for dx1, dy1, dx2, dy2 in [
            (-scar_r + max(1,int(2*u)), -scar_r + max(1,int(2*u)),
              scar_r - max(1,int(2*u)),  scar_r - max(1,int(2*u))),
            ( scar_r - max(1,int(2*u)), -scar_r + max(1,int(2*u)),
             -scar_r + max(1,int(2*u)),  scar_r - max(1,int(2*u))),
        ]:
            pygame.draw.line(surface, blood,
                             (scar_cx + dx1, scar_cy + dy1),
                             (scar_cx + dx2, scar_cy + dy2),
                             max(1, int(2*u)))
        # Blood drip — longer, with two drops
        drip_x     = scar_cx + max(1, int(2*u))
        drip_start = scar_cy + scar_r
        drip_end   = drip_start + max(10, int(18*u))
        pygame.draw.line(surface, blood,
                         (drip_x, drip_start), (drip_x, drip_end),
                         max(1, int(2*u)))
        # Main drip bulge
        pygame.draw.circle(surface, blood,
                           (drip_x, drip_end), max(3, int(5*u)))
        # Smaller secondary drip midway
        mid_drip = drip_start + (drip_end - drip_start) // 2
        pygame.draw.circle(surface, blood,
                           (drip_x + max(1, int(2*u)), mid_drip),
                           max(2, int(3*u)))

        # ── Chin scar ─────────────────────────────────────────────────────
        chin_y = head_cy + int(hr * 0.55)
        pygame.draw.line(surface, darker,
                         (head_cx - max(4, int(7*u)), chin_y),
                         (head_cx + max(4, int(7*u)), chin_y + max(1, int(2*u))),
                         max(1, int(2*u)))

        # ── Nose — wide, flat ─────────────────────────────────────────────
        nw = max(8, int(16*u)); nh = max(5, int(12*u))
        pygame.draw.ellipse(surface, dark,
                            (head_cx - nw // 2, head_cy + int(hr*0.18), nw, nh))
        for nox in [-max(3, int(5*u)), max(3, int(5*u))]:
            pygame.draw.circle(surface, darker,
                               (head_cx + nox, head_cy + int(hr*0.28)),
                               max(2, int(4*u)))

        # ── Mouth — stern heavy frown, one broken tusk ────────────────────
        mouth_y = head_cy + int(hr * 0.52)
        mouth_w = max(14, int(hr * 0.9))
        # Stern flat line
        pygame.draw.line(surface, darker,
                         (head_cx - mouth_w // 2, mouth_y),
                         (head_cx + mouth_w // 2, mouth_y),
                         max(2, int(4*u)))
        # Downturn at corners
        for side in [-1, 1]:
            pygame.draw.line(surface, darker,
                             (head_cx + side * mouth_w // 2, mouth_y),
                             (head_cx + side * (mouth_w // 2 + max(3, int(5*u))),
                              mouth_y + max(3, int(6*u))),
                             max(1, int(2*u)))
        # One broken tusk — shorter, chipped at tip
        tusk_x = head_cx - max(4, int(7*u))
        pygame.draw.line(surface, bone,
                         (tusk_x, mouth_y),
                         (tusk_x, mouth_y + max(6, int(12*u))),
                         max(3, int(5*u)))
        # Chipped tip — polygon cut
        pygame.draw.polygon(surface, dark, [
            (tusk_x - max(2, int(4*u)), mouth_y + max(5, int(10*u))),
            (tusk_x + max(2, int(4*u)), mouth_y + max(5, int(10*u))),
            (tusk_x + max(3, int(5*u)), mouth_y + max(7, int(13*u))),
        ])
        # Second smaller tooth
        pygame.draw.line(surface, bone_d,
                         (head_cx + max(3, int(5*u)), mouth_y),
                         (head_cx + max(3, int(5*u)), mouth_y + max(4, int(7*u))),
                         max(2, int(3*u)))

        # ── Warts — a few, prominent ──────────────────────────────────────
        for wx, wy, wr in [
            (head_cx + int(hr*0.4),  head_cy + int(hr*0.15), max(3, int(5*u))),
            (head_cx - int(hr*0.28), head_cy - int(hr*0.28), max(2, int(4*u))),
            (head_cx + int(hr*0.15), head_cy - int(hr*0.42), max(2, int(3*u))),
        ]:
            pygame.draw.circle(surface, fc((50, 105, 32)), (int(wx), int(wy)), wr)
            pygame.draw.circle(surface, darker, (int(wx), int(wy)), wr,
                               max(1, int(1.5*u)))
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
# Stats loaded from enemies.json via EntityFactory
from src.entities.entity_factory import get_stat, roll_loot as factory_loot
GOBLIN_MAX_HP  = get_stat('goblin','hp')
GOBLIN_DAMAGE  = get_stat('goblin','damage')
SWORD_DAMAGE   = 6
SUN_SWORD_DMG  = 12
POTION_HEAL    = 5

BOSS_MAX_HP    = get_stat('goblin_king','hp')
BOSS_DAMAGE    = get_stat('goblin_king','damage')
BOSS_NAME      = get_stat('goblin_king','display_name')


class CombatScene:
    def __init__(self, screen, inventory, is_boss=False, armour=None, player_hp=None, player_stats=None, enemy_type=None):
        self.inventory = inventory
        self.is_boss   = is_boss
        self.armour    = armour
        self._start_hp    = player_hp
        self.player_stats = player_stats
        self.enemy_type   = enemy_type  # overrides default goblin stats
        self.screen = screen
        self.W, self.H = screen.get_size()
        self.clock = pygame.time.Clock()
        self.time  = 0.0

        self.font_large  = pygame.font.SysFont("courier new", 28, bold=True)
        self.font_medium = pygame.font.SysFont("courier new", 20, bold=True)
        self.font_small  = pygame.font.SysFont("courier new", 16)

        self.PANEL_H     = int(self.H * 0.32)
        self.BATTLE_H    = self.H - self.PANEL_H
        self.SPRITE_SIZE = int(min(self.W, self.BATTLE_H) * 0.38)

        # Sprites
        px = int(self.W * 0.22)
        py = int(self.BATTLE_H * 0.58)
        self.combat_player = CombatPlayer(px, py, self.SPRITE_SIZE)

        ex = int(self.W * 0.72)
        ey = int(self.BATTLE_H * 0.50)   # centred vertically
        if is_boss:
            boss_size = int(self.SPRITE_SIZE * 1.55)
            self.combat_goblin = CombatGoblinKing(ex, int(self.BATTLE_H*0.40), boss_size)
            self.goblin_hp     = BOSS_MAX_HP
            self.goblin_max_hp = BOSS_MAX_HP
            self._goblin_name  = BOSS_NAME
            self._goblin_dmg   = BOSS_DAMAGE
        elif enemy_type == "goblin_chieftain":
            chieftain_size = int(self.SPRITE_SIZE * 1.25)
            self.combat_goblin = CombatGoblinChieftain(ex, ey, chieftain_size)
            from src.entities.entity_factory import get_definition
            defn = get_definition("goblin_chieftain")
            self.goblin_hp     = defn["hp"]
            self.goblin_max_hp = defn["hp"]
            self._goblin_name  = defn["display_name"]
            self._goblin_dmg   = defn["damage"]
        elif enemy_type and enemy_type not in ("goblin", None):
            # Load stats from enemies.json via factory
            from src.entities.entity_factory import get_stat, get_definition
            defn = get_definition(enemy_type)
            self.goblin_hp     = defn["hp"]
            self.goblin_max_hp = defn["hp"]
            self._goblin_name  = defn["display_name"]
            self._goblin_dmg   = defn["damage"]
            # Pick sprite based on type
            from src.entities.enemy import (
                _draw_skeleton, _draw_troll, _draw_dark_mage, _draw_generic)
            # Size multipliers — troll is bigger, mage is slimmer
            _size_mult = {"troll": 1.2, "skeleton": 0.95,
                          "dark_mage": 0.9}.get(enemy_type, 1.0)
            _esize = int(self.SPRITE_SIZE * _size_mult)
            self.combat_goblin = CombatEnemyProxy(
                ex, ey, _esize, enemy_type, tuple(defn["color"]))
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

        # Disable RUN for boss fights (is_boss flag OR enemy definition marks it as boss)
        _is_boss_fight = self.is_boss
        if not _is_boss_fight and enemy_type:
            from src.entities.entity_factory import get_definition
            try:
                defn = get_definition(enemy_type)
                _is_boss_fight = defn.get("is_boss", False)
            except Exception:
                pass
        self._is_boss_fight = _is_boss_fight
        if _is_boss_fight:
            for btn in self.buttons:
                if btn.text == "RUN":
                    btn.enabled = False

        # Relic selection menu
        self._relic_selection    = False
        self._relic_options      = []
        self._relic_selected_idx = 0

        self.bg = self._build_background()

        # Ability system
        self._turn_count       = 0
        self._ability_interval = 3
        self._burn_turns       = 0
        self._burn_dmg         = 2
        self._cursed           = False
        self._rage_active      = False
        self._hardened         = 0      # int: hits remaining that are halved
        self._parry_active     = False
        self._frozen           = False  # archmage ice: player skips a turn
        self._goblin_dmg_base  = self._goblin_dmg
        self._dmg_reduction    = 0      # goblin king: reduces player damage
        # Boss-specific
        self._resurrected      = False
        self._bone_shield      = 0      # bone lord: hits blocked
        self._phylactery_hp    = 3      # lich king: destroy before boss can die
        self._phylactery_gone  = False

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _set_buttons_enabled(self, enabled: bool):
        for btn in self.buttons:
            # Never re-enable RUN during any boss fight
            if btn.text == "RUN" and getattr(self, "_is_boss_fight", False):
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

    def _get_weapon(self):
        """Get the player's current weapon from inventory."""
        from src.scenes.chest_scene import StickItem, SunSwordItem, SwordItem
        for it in self.inventory.items:
            if isinstance(it, SunSwordItem): return it, SUN_SWORD_DMG, "sun sword"
        for it in self.inventory.items:
            if isinstance(it, StickItem):
                dmg = it.DAMAGE_VALUES[min(it.upgrade_level, 5)]
                str_bonus = self.player_stats.atk_bonus if self.player_stats else 0
                name = it.WEAPON_NAMES[min(it.upgrade_level, 5)].lower()
                return it, dmg + str_bonus, name
        for it in self.inventory.items:
            if isinstance(it, SwordItem):
                str_bonus = self.player_stats.atk_bonus if self.player_stats else 0
                return it, SWORD_DAMAGE + str_bonus, "sword"
        return None, SWORD_DAMAGE, "fists"

    def _handle_player_choose(self, event):
        for btn in self.buttons:
            if btn.is_clicked(event):
                if btn.text == "ATTACK":
                    _, dmg, wname = self._get_weapon()
                    self._player_attack(dmg, wname)

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
        """Roll loot using the entity factory loot table."""
        enemy_type = "goblin_king" if self.is_boss else                      (self.enemy_type if self.enemy_type else "goblin")
        return factory_loot(enemy_type)

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

    def _apply_parry_and_harden(self, damage: int) -> tuple:
        """Returns (final_damage, extra_msg) after all defensive checks."""
        extra = ""
        # Bone shield — blocks completely
        if self._bone_shield > 0:
            self._bone_shield -= 1
            return 0, f" The BONE SHIELD absorbs your attack! ({self._bone_shield} blocks left)" if self._bone_shield > 0 else " The BONE SHIELD shatters!"
        # Parry
        if self._parry_active:
            self._parry_active = False
            return 0, " The skeleton PARRIES your attack! No damage dealt!"
        # Goblin King damage reduction
        if self._dmg_reduction > 0:
            old_dmg = damage
            damage  = max(1, damage - self._dmg_reduction)
            extra  += f" The King's aura weakens your blow! ({old_dmg} → {damage})"
        # Harden (int = hits remaining)
        if self._hardened > 0:
            self._hardened -= 1
            damage = max(1, damage // 2)
            extra += f" The golem HARDENS your blow! Halved to {damage}! ({self._hardened} left)"
        # Curse
        if self._cursed:
            self._cursed = False
            damage = damage * 2
            extra += f" The CURSE activates! Damage doubled to {damage}!"
        # Phylactery check — lich king can't die until it's gone
        if not self._phylactery_gone and self.enemy_type == "lich_king":
            if self.goblin_hp - damage <= 0:
                self._phylactery_hp -= 1
                if self._phylactery_hp <= 0:
                    self._phylactery_gone = True
                    extra += " The PHYLACTERY SHATTERS! The Lich King is now mortal!"
                else:
                    damage = self.goblin_hp - 1  # can't kill yet
                    extra += f" The phylactery protects the Lich King! ({self._phylactery_hp} charges left)"
        return damage, extra

    def _update_player_action(self, dt):
        """Wait for lunge to reach midpoint, then deal damage."""
        self.action_timer += dt
        if self.action_timer >= self.ACTION_WAIT and not self.combat_goblin.flash_timer > 0:
            action, damage, weapon = self.pending_action
            # Apply parry / harden / curse
            damage, extra_msg = self._apply_parry_and_harden(damage)
            if damage > 0:
                self.goblin_hp = max(0, self.goblin_hp - damage)
                self.combat_goblin.start_flash()
            if weapon == "sun sword":
                msg = f"The Sun Sword blazes! {damage} damage! ({self.goblin_hp}/{self.goblin_max_hp} HP)"
            else:
                msg = f"You slash for {damage} damage! ({self.goblin_hp}/{self.goblin_max_hp} HP)"
            msg += extra_msg
            if self.goblin_hp <= 0:
                self._goblin_loot = self._roll_loot()
                self._show_message(msg + f" The {self._goblin_name} is defeated!", STATE_VICTORY)
            else:
                self._show_message(msg, STATE_ENEMY_ACTION)

    def _trigger_ability(self):
        """Trigger this enemy type's special ability. Returns message string."""
        if self.is_boss:
            etype = "goblin_king"
        else:
            etype = (self.enemy_type.lower().replace(" ","_")
                     if self.enemy_type else "goblin")
        mhp = self.goblin_max_hp

        # ---- Regular enemies ----
        if etype == "goblin":
            from src.scenes.chest_scene import PotionItem
            if self.inventory.has(PotionItem):
                self.inventory.remove_one(PotionItem)
                return "The goblin snatches a potion from your pack!"
            return "The goblin rummages through your pack but finds nothing!"

        elif etype == "skeleton":
            self._parry_active = True
            return "The skeleton raises its bones in a PARRY stance! Your next attack will be blocked!"

        elif etype == "troll":
            self.goblin_hp = min(mhp, self.goblin_hp + 3)
            return f"The troll regenerates! +3 HP ({self.goblin_hp}/{mhp})"

        elif etype == "dark_mage":
            self._cursed = True
            return "The dark mage casts a CURSE! Your next hit will deal double damage!"

        elif etype == "imp":
            self._burn_turns = 2; self._burn_dmg = 2
            return "The imp sets you ABLAZE! Burning for 2 damage x 2 turns!"

        elif etype == "dire_rat":
            return "__DOUBLE_BITE__"

        elif etype == "orc_warrior":
            self._goblin_dmg = int(self._goblin_dmg_base * 1.6)
            return f"The orc enters a RAGE! Damage increased to {self._goblin_dmg}!"

        elif etype == "stone_golem":
            self._hardened = 1
            return "The stone golem HARDENS! Your next attack deals half damage!"

        elif etype == "werewolf":
            heal = min(8, mhp - self.goblin_hp)
            if heal > 0:
                self.goblin_hp += heal
                return f"The werewolf HOWLS and heals! +{heal} HP ({self.goblin_hp}/{mhp})"
            return "The werewolf howls but is already at full health!"

        elif etype == "lich":
            drain = min(6, self.player_hp - 1)
            if drain > 0:
                self.player_hp = max(1, self.player_hp - drain)
                self.goblin_hp = min(mhp, self.goblin_hp + drain)
                self.combat_player.start_flash()
                return (f"The lich DRAINS you! -{drain} HP "
                        f"({self.player_hp}/{self.player_max_hp}). "
                        f"Lich heals to {self.goblin_hp}/{mhp}!")
            return "The lich attempts to drain you but you resist!"

        # ---- Bosses ----
        elif etype == "goblin_king":
            self._dmg_reduction = max(self._dmg_reduction, 2)
            return (f"The Goblin King bellows a DARK CURSE! "
                    f"Your attacks are now weakened by {self._dmg_reduction}!")

        elif etype == "bone_lord":
            if self.goblin_hp <= self.goblin_max_hp // 3 and not self._resurrected:
                self._resurrected = True
                self.goblin_hp    = mhp
                self._bone_shield = 2
                return (f"The Bone Lord RISES FROM THE DEAD at full strength! "
                        f"A BONE SHIELD forms — your next 2 attacks are blocked!")
            self._bone_shield = 2
            return "The Bone Lord raises a BONE SHIELD! Your next 2 attacks will be blocked!"

        elif etype == "mountain_king":
            heal = min(8, mhp - self.goblin_hp)
            self.goblin_hp = min(mhp, self.goblin_hp + heal)
            boulder_dmg = 6
            self.player_hp = max(0, self.player_hp - boulder_dmg)
            self.combat_player.start_flash()
            return (f"The Mountain King HURLS A BOULDER! -{boulder_dmg} HP "
                    f"({self.player_hp}/{self.player_max_hp}) "
                    f"and regenerates +{heal} HP ({self.goblin_hp}/{mhp})!")

        elif etype == "archmage":
            phase = (self._turn_count // self._ability_interval) % 3
            if phase == 0:
                dmg = 8; self._burn_turns = 3; self._burn_dmg = 2
                self.player_hp = max(0, self.player_hp - dmg)
                self.combat_player.start_flash()
                return (f"FIREBALL! -{dmg} HP ({self.player_hp}/{self.player_max_hp}). "
                        f"You are BURNING for 2 damage x 3 turns!")
            elif phase == 1:
                dmg = 6; self._frozen = True
                self.player_hp = max(0, self.player_hp - dmg)
                self.combat_player.start_flash()
                return (f"ICE LANCE! -{dmg} HP ({self.player_hp}/{self.player_max_hp}). "
                        f"You are FROZEN — your next turn is skipped!")
            else:
                dmg = 10
                self.player_hp = max(0, self.player_hp - dmg)
                self.combat_player.start_flash()
                return (f"LIGHTNING STRIKE! -{dmg} HP "
                        f"({self.player_hp}/{self.player_max_hp})!")

        elif etype == "inferno_duke":
            self._burn_turns = 4; self._burn_dmg = 4
            direct = 5
            self.player_hp = max(0, self.player_hp - direct)
            self.combat_player.start_flash()
            return (f"HELLFIRE! -{direct} HP ({self.player_hp}/{self.player_max_hp}). "
                    f"Burning for 4 damage x 4 turns!")

        elif etype == "rat_king":
            from src.scenes.chest_scene import PotionItem
            stolen = ""
            if self.inventory.has(PotionItem):
                self.inventory.remove_one(PotionItem)
                stolen = " His swarm STEALS your potion!"
            return f"__RAT_KING_BITE__{stolen}"

        elif etype == "warchief_grommak":
            self._goblin_dmg = int(self._goblin_dmg * 1.4)
            direct = 4
            self.player_hp = max(0, self.player_hp - direct)
            self.combat_player.start_flash()
            return (f"WARCRY! -{direct} HP ({self.player_hp}/{self.player_max_hp}). "
                    f"Grommak's damage surges to {self._goblin_dmg}! (stacks!)")

        elif etype == "ancient_colossus":
            self._hardened = 2
            heal = min(10, mhp - self.goblin_hp)
            self.goblin_hp = min(mhp, self.goblin_hp + heal)
            return (f"EARTH ABSORPTION! +{heal} HP ({self.goblin_hp}/{mhp}). "
                    f"Your next 2 attacks deal HALF damage!")

        elif etype == "the_alpha":
            heal = min(12, mhp - self.goblin_hp)
            self.goblin_hp   = min(mhp, self.goblin_hp + heal)
            self._goblin_dmg = int(self._goblin_dmg_base * 1.4)
            defence = self.armour.total_defence() if self.armour else 0
            bite    = max(1, self._goblin_dmg - defence)
            self.player_hp = max(0, self.player_hp - bite)
            self.combat_player.start_flash()
            return (f"TRANSFORMATION! +{heal} HP ({self.goblin_hp}/{mhp}), "
                    f"damage → {self._goblin_dmg}, "
                    f"FREE BITE for {bite}! ({self.player_hp}/{self.player_max_hp} HP)")

        elif etype == "lich_king":
            drain = min(10, self.player_hp - 1)
            if drain > 0:
                self.player_hp = max(1, self.player_hp - drain)
                self.goblin_hp = min(mhp, self.goblin_hp + drain)
                self.combat_player.start_flash()
            self._cursed = True
            phyl = f" [PHYLACTERY: {self._phylactery_hp} charges — cannot die yet!]" if not self._phylactery_gone else ""
            return (f"SOUL DRAIN! -{drain} HP ({self.player_hp}/{self.player_max_hp}). "
                    f"Next strike CURSED!{phyl}")

        return ""

    def _update_enemy_action(self, dt):
        """Enemy acts — normal attack, ability, or burn tick."""
        self.action_timer += dt
        if not hasattr(self, '_goblin_attacked'):
            self._goblin_attacked = False

        if self.action_timer >= 0.3 and not self._goblin_attacked:
            self._goblin_attacked = True
            self.combat_goblin.start_lunge()

        if self.action_timer >= 0.3 + self.ACTION_WAIT and not self.combat_player.flash_timer > 0:
            if not self._goblin_attacked:
                return
            self._goblin_attacked = False
            self.action_timer     = -9999
            self._turn_count     += 1

            # --- Burn tick (imp) ---
            burn_msg = ""
            if self._burn_turns > 0:
                self.player_hp    = max(0, self.player_hp - self._burn_dmg)
                self._burn_turns -= 1
                self.combat_player.start_flash()
                burn_msg = f" You burn for {self._burn_dmg} damage!"
                if self.player_hp <= 0:
                    self._show_message(
                        f"The flames consume you!{burn_msg} You have fallen...",
                        STATE_DEFEAT)
                    return

            # --- Ability turn (every 3rd turn) ---
            if self._turn_count % self._ability_interval == 0:
                ability_msg = self._trigger_ability()
                if ability_msg.startswith("__DOUBLE_BITE__") or ability_msg.startswith("__RAT_KING_BITE__"):
                    suffix = ability_msg.split("__")[-1] if "__RAT_KING_BITE__" in ability_msg else ""
                    defence = self.armour.total_defence() if self.armour else 0
                    dmg1 = max(1, self._goblin_dmg - defence)
                    dmg2 = max(1, self._goblin_dmg - defence)
                    self.player_hp = max(0, self.player_hp - dmg1 - dmg2)
                    self.combat_player.start_flash()
                    who = "The Rat King's swarm" if "__RAT_KING_BITE__" in ability_msg else "The dire rat"
                    msg = (f"{who} BITES TWICE for {dmg1}+{dmg2} damage! "
                           f"({self.player_hp}/{self.player_max_hp} HP){burn_msg}{suffix}")
                    if self.player_hp <= 0:
                        self._show_message(msg + " You have fallen in battle...", STATE_DEFEAT)
                    else:
                        self._show_message(msg, STATE_PLAYER_CHOOSE)
                    return
                # Lich drain already applied inside _trigger_ability
                if self.player_hp <= 0:
                    self._show_message(ability_msg + " You have fallen...", STATE_DEFEAT)
                    return
                self._show_message(ability_msg + burn_msg, STATE_PLAYER_CHOOSE)
                return

            # --- Normal attack ---
            if getattr(self, '_shield_active', False):
                self._shield_active = False
                self._show_message(
                    f"The {self._goblin_name} strikes — BLOCKED by your shield! "
                    f"The shield holds firm.{burn_msg}",
                    STATE_PLAYER_CHOOSE)
                return

            defence = self.armour.total_defence() if self.armour else 0
            dmg     = max(1, self._goblin_dmg - defence)
            self.player_hp = max(0, self.player_hp - dmg)
            self.combat_player.start_flash()
            msg = (f"The {self._goblin_name} hits you for {dmg} damage! "
                   f"({self.player_hp}/{self.player_max_hp} HP){burn_msg}")
            if self.player_hp <= 0:
                self._show_message(msg + " You have fallen in battle...", STATE_DEFEAT)
            else:
                self._show_message(msg, STATE_PLAYER_CHOOSE)

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
                # ATTACK shows current weapon
                _, _, _wname = self._get_weapon()
                atk_s = self.font_small.render(_wname, True, (140,140,160))
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