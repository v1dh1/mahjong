# tile.py
class Tile:
    def __init__(self, tileno, suit, copyno):
        self.tileno = tileno
        self.suit = suit
        self.copyno = copyno
        self.state = 0  # 0=wall, 1=hand, 2=discarded

    def mark_in_hand(self):
        self.state = 1

    def mark_discarded(self):
        self.state = 2

    def __repr__(self):
        return f"{self.suit}-{self.tileno}-{self.copyno}(state={self.state})"

