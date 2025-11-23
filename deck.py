# deck.py
from tile import Tile
import random

class Deck:
    def __init__(self):
        self.tiles = []
        self.all_tiles = []  # Add this line
        self._build_tiles()
        self.shuffle()

    def _build_tiles(self):
        suits = ["Dots", "Bamboo", "Characters"]
        honors = {
            "Wind": ["East", "South", "West", "North"],
            "Dragon": ["Red", "Green", "White"]
        }

        # 108 suit tiles
        for suit in suits:
            for value in range(1, 10):
                for copy_no in range(1, 5):
                    tile = Tile(suit, value, copy_no)
                    self.tiles.append(tile)
                    self.all_tiles.append(tile)  # Track all tiles

        # 28 honor tiles
        for suit, values in honors.items():
            for value in values:
                for copy_no in range(1, 5):
                    tile = Tile(suit, value, copy_no)
                    self.tiles.append(tile)
                    self.all_tiles.append(tile)  # Track all tiles

        assert len(self.tiles) == 136, "Deck should have 136 tiles!"

    # ...existing code...

    def shuffle(self):
        random.shuffle(self.tiles)

    def draw(self):
        if self.tiles:
            return self.tiles.pop()
        return None
