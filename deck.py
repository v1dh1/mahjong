# deck.py
from tile import Tile
import random

class Deck:
    def __init__(self):
        self.tiles = []
        self.all_tiles = []  # track all Tile objects for global state inspection
        self._build_tiles()
        self.shuffle()

    def _build_tiles(self):
        suits = ["Dots", "Bamboo", "Characters"]
        honors = {
            "Wind": ["East", "South", "West", "North"],
            "Dragon": ["Red", "Green", "White"]
        }

        # 108 suit tiles (1-9, 4 copies each, 3 suits)
        for suit in suits:
            for value in range(1, 10):
                for copy_no in range(1, 5):
                    tile = Tile(suit, value, copy_no)
                    self.tiles.append(tile)
                    self.all_tiles.append(tile)

        # 28 honor tiles (winds + dragons, 4 copies each)
        for suit, values in honors.items():
            for value in values:
                for copy_no in range(1, 5):
                    tile = Tile(suit, value, copy_no)
                    self.tiles.append(tile)
                    self.all_tiles.append(tile)

        assert len(self.tiles) == 136, f"Deck should have 136 tiles, got {len(self.tiles)}"

    def shuffle(self):
        random.shuffle(self.tiles)

    def draw(self):
        """Pop from the end of the deck (the wall)."""
        if self.tiles:
            return self.tiles.pop()
        return None

    def draw_random_state0(self):
        """
        Choose a random tile whose state == 0 (still in wall/unseen),
        remove it from self.tiles and return it. If none available return None.
        This is handy if you mark some tiles with state != 0 but kept them in all_tiles list.
        """
        available = [t for t in self.tiles if getattr(t, "state", 0) == 0]
        if not available:
            return None
        chosen = random.choice(available)
        # Remove the chosen tile from the deck list so it can't be drawn again
        # There might be multiple identical copies - remove that exact object
        self.tiles.remove(chosen)
        return chosen
