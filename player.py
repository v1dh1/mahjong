# player.py


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.simulator = False

    def draw_tile(self, tile, is_simulator=False):
        if tile:
            tile.state = 1 if is_simulator else 0
            self.hand.append(tile)


    def discard_tile(self, index=-1):
        if not self.hand:
            return None
        tile = self.hand.pop(index)
        tile.state = 2   # ✅ mark as discarded
        return tile

    
    def change_tile_state(self, tile):
        tile.state = 2

    def __repr__(self):
        return f"Player({self.name})"

    def check_win(self):
        """
        Placeholder for checking if the player has a winning hand.
        Returns True if winning, False otherwise.
        """
        # Example: win if hand has 14 tiles (just for testing)
        return len(self.hand) >= 14
