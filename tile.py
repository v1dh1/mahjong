# tile.py
class Tile:
    """
    Tile(suit, value, copy_no)
    suit: "Dots" | "Bamboo" | "Characters" | "Wind" | "Dragon"
    value: int for suits (1-9) or string for honors ("East","Red",etc.)
    copy_no: 1..4 to differentiate identical copies
    state: 0=wall/unseen, 1=in-hand, 2=discarded
    """

    def __init__(self, suit, value, copy_no):
        self.suit = suit
        self.value = value
        self.copy_no = copy_no
        self.state = 0  # default: in wall / available

    def mark_in_hand(self):
        self.state = 1

    def mark_discarded(self):
        self.state = 2

    def __repr__(self):
        return f"{self.suit}-{self.value}-{self.copy_no}(state={self.state})"
