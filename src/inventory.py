class Inventory:
    def __init__(self):
        # Stacked storage: {stack_key: {"item": Item, "count": int}}
        # Non-stackable items (swords, shields, keys) each get a unique key
        self._stacks   = {}
        self._order    = []   # stack keys in insertion order
        self._uid      = 0    # for unique keys on non-stackables

        # Start with one potion only — stick is picked up from dungeon floor
        from src.scenes.chest_scene import PotionItem
        self.add(PotionItem())

    # ------------------------------------------------------------------ #

    def _stack_key(self, item):
        """Items with the same class and stackable=True share a key."""
        if getattr(item, 'stackable', False):
            return item.__class__.__name__
        # Non-stackable — give a unique key
        self._uid += 1
        return f"{item.__class__.__name__}_{self._uid}"

    def add(self, item):
        if getattr(item, 'stackable', False):
            key = item.__class__.__name__
            if key in self._stacks:
                amount = getattr(item, 'amount', 1)
                self._stacks[key]["count"] += amount
                # Update the representative item's amount too
                if hasattr(self._stacks[key]["item"], 'amount'):
                    self._stacks[key]["item"].amount = self._stacks[key]["count"]
                return
            else:
                self._stacks[key] = {"item": item, "count": getattr(item, 'amount', 1)}
                self._order.append(key)
        else:
            key = self._stack_key(item)
            self._stacks[key] = {"item": item, "count": 1}
            self._order.append(key)

    def remove(self, item):
        """Remove one instance of item (or reduce stack by item.amount)."""
        if getattr(item, 'stackable', False):
            key = item.__class__.__name__
            if key in self._stacks:
                self._stacks[key]["count"] -= getattr(item, 'amount', 1)
                if self._stacks[key]["count"] <= 0:
                    del self._stacks[key]
                    self._order.remove(key)
                else:
                    if hasattr(self._stacks[key]["item"], 'amount'):
                        self._stacks[key]["item"].amount = self._stacks[key]["count"]
        else:
            # Find by identity
            for key, stack in list(self._stacks.items()):
                if stack["item"] is item:
                    del self._stacks[key]
                    self._order.remove(key)
                    return

    def remove_one(self, item_class):
        """Remove exactly 1 unit from a stackable stack, or remove a non-stackable."""
        for key in list(self._order):
            if isinstance(self._stacks[key]["item"], item_class):
                self._stacks[key]["count"] -= 1
                if hasattr(self._stacks[key]["item"], 'amount'):
                    self._stacks[key]["item"].amount = self._stacks[key]["count"]
                if self._stacks[key]["count"] <= 0:
                    del self._stacks[key]
                    self._order.remove(key)
                return

    @property
    def items(self):
        """Returns list of representative items in order."""
        return [self._stacks[k]["item"] for k in self._order if k in self._stacks]

    def count(self, item_class):
        for key in self._order:
            if key in self._stacks and isinstance(self._stacks[key]["item"], item_class):
                return self._stacks[key]["count"]
        return 0

    def has(self, item_class):
        return self.count(item_class) > 0

    def get(self, item_class):
        for key in self._order:
            if key in self._stacks and isinstance(self._stacks[key]["item"], item_class):
                return self._stacks[key]["item"]
        return None

    def stack_count(self, item):
        """Get the count for a specific item instance."""
        if getattr(item, 'stackable', False):
            key = item.__class__.__name__
            return self._stacks.get(key, {}).get("count", 1)
        for key, stack in self._stacks.items():
            if stack["item"] is item:
                return stack["count"]
        return 1