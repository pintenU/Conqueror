# ---------------------------------------------------------------------------
# Shared inventory — single instance passed between all scenes
# ---------------------------------------------------------------------------

class Inventory:
    def __init__(self):
        self.items = []   # list of Item instances

        # Pre-load starting items
        from src.scenes.chest_scene import SwordItem, SunSwordItem, PotionItem
        self.items.append(SwordItem())
        self.items.append(SunSwordItem())
        self.items.append(PotionItem())

    def add(self, item):
        self.items.append(item)

    def remove(self, item):
        if item in self.items:
            self.items.remove(item)

    def count(self, item_class):
        return sum(1 for i in self.items if isinstance(i, item_class))