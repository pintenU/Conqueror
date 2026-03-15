# ---------------------------------------------------------------------------
# Player stats — level, EXP, and stat points
# ---------------------------------------------------------------------------

BASE_HP       = 30
DEX_HP_BONUS  = 5     # HP per dexterity point
STR_DMG_BONUS = 1     # extra sword damage per strength point
EXP_BASE      = 100   # EXP needed for level 2
EXP_SCALE     = 1.5   # multiplier per level
EXP_GOBLIN    = 15
EXP_BOSS      = 120


def exp_for_level(level: int) -> int:
    """Total EXP needed to reach `level` from level 1."""
    total = 0
    req   = EXP_BASE
    for _ in range(level - 1):
        total += int(req)
        req   *= EXP_SCALE
    return total


def exp_to_next(level: int) -> int:
    """EXP needed for the next level up from `level`."""
    return int(EXP_BASE * (EXP_SCALE ** (level - 1)))


class PlayerStats:
    def __init__(self):
        self.level       = 1
        self.exp         = 0
        self.stat_points = 0   # unspent points

        # Spent stats
        self.dexterity      = 0   # +5 HP each
        self.strength       = 0   # +1 ATK each
        self.magic_mastery  = 0   # relic effectiveness (future)

    # ------------------------------------------------------------------ #

    @property
    def max_hp(self) -> int:
        return BASE_HP + self.dexterity * DEX_HP_BONUS

    @property
    def atk_bonus(self) -> int:
        return self.strength * STR_DMG_BONUS

    @property
    def magic_bonus(self) -> int:
        return self.magic_mastery

    def exp_needed(self) -> int:
        return exp_to_next(self.level)

    def exp_progress(self) -> float:
        """0.0 – 1.0 progress toward next level."""
        return min(1.0, self.exp / self.exp_needed())

    def add_exp(self, amount: int) -> list[int]:
        """
        Add EXP and handle level ups.
        Returns list of levels gained (empty if none).
        """
        self.exp += amount
        leveled   = []
        while self.exp >= self.exp_needed():
            self.exp    -= self.exp_needed()
            self.level  += 1
            self.stat_points += 1
            leveled.append(self.level)
        return leveled

    def spend_point(self, stat: str) -> bool:
        """Spend one stat point on a stat. Returns True if successful."""
        if self.stat_points <= 0:
            return False
        if stat == "dexterity":
            self.dexterity     += 1
        elif stat == "strength":
            self.strength      += 1
        elif stat == "magic_mastery":
            self.magic_mastery += 1
        else:
            return False
        self.stat_points -= 1
        return True

    # ------------------------------------------------------------------ #
    # Serialise

    def to_dict(self) -> dict:
        return {
            "level":          self.level,
            "exp":            self.exp,
            "stat_points":    self.stat_points,
            "dexterity":      self.dexterity,
            "strength":       self.strength,
            "magic_mastery":  self.magic_mastery,
        }

    def from_dict(self, d: dict):
        self.level          = d.get("level",         1)
        self.exp            = d.get("exp",            0)
        self.stat_points    = d.get("stat_points",    0)
        self.dexterity      = d.get("dexterity",      0)
        self.strength       = d.get("strength",       0)
        self.magic_mastery  = d.get("magic_mastery",  0)