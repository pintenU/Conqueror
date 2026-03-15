# ---------------------------------------------------------------------------
# Armour system — tracks what's equipped in each slot
# ---------------------------------------------------------------------------

SLOTS = ["helmet", "chestplate", "leggings", "boots"]


class ArmourSystem:
    def __init__(self):
        self.equipped = {slot: None for slot in SLOTS}

    def equip(self, item, inventory):
        """Equip an armour piece. Unequip existing in that slot back to inventory."""
        from src.scenes.chest_scene import ArmourItem
        if not isinstance(item, ArmourItem):
            return False
        slot = item.slot
        if slot not in SLOTS:
            return False
        # Return currently equipped piece to inventory
        if self.equipped[slot] is not None:
            inventory.add(self.equipped[slot])
        # Remove new piece from inventory and equip
        inventory.remove(item)
        self.equipped[slot] = item
        return True

    def unequip(self, slot, inventory):
        """Unequip a slot back to inventory."""
        if self.equipped[slot] is not None:
            inventory.add(self.equipped[slot])
            self.equipped[slot] = None

    def total_defence(self) -> int:
        """Sum of defence from all equipped pieces."""
        return sum(
            item.defence for item in self.equipped.values()
            if item is not None
        )

    def get(self, slot):
        return self.equipped.get(slot)

    def is_equipped(self, item) -> bool:
        return any(v is item for v in self.equipped.values())

    def to_dict(self) -> dict:
        from src.scenes.chest_scene import ArmourItem
        result = {}
        for slot, item in self.equipped.items():
            if item is not None:
                result[slot] = type(item).__name__
            else:
                result[slot] = None
        return result

    def from_dict(self, d: dict):
        """Restore equipped armour from save data."""
        cls_map = {}
        try:
            from src.scenes.chest_scene import (
                IronHelmet, IronChestplate, IronLeggings, IronBoots)
            cls_map = {
                "IronHelmet":     IronHelmet,
                "IronChestplate": IronChestplate,
                "IronLeggings":   IronLeggings,
                "IronBoots":      IronBoots,
            }
        except Exception:
            pass
        for slot, cls_name in d.items():
            if cls_name and cls_name in cls_map:
                self.equipped[slot] = cls_map[cls_name]()
            else:
                self.equipped[slot] = None