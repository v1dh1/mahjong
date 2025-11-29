# player.py
from collections import Counter

# Choose which win-rule to use:
# 'A' = fast/simple (len(hand) >= 14) - DEBUG ONLY
# 'B' = heuristic (quick check: at least one pong+pair and remaining can form melds)
# 'C' = realistic full check (4 melds + 1 pair)
WIN_MODE = "C"   # realistic full check

# ordering helpers for deterministic tile ordering
_suit_order = {"Dots": 0, "Bamboo": 1, "Characters": 2, "Wind": 3, "Dragon": 4}
_wind_order = {"East": 0, "South": 1, "West": 2, "North": 3}
_dragon_order = {"Red": 0, "Green": 1, "White": 2}

def _tile_order_key(tile_key):
    """
    Return a tuple usable for sorting tile types consistently.
    tile_key: (suit, value)
    """
    suit, value = tile_key
    suit_rank = _suit_order.get(suit, 99)
    if suit in ("Dots", "Bamboo", "Characters") and isinstance(value, int):
        return (suit_rank, value)
    if suit == "Wind":
        return (suit_rank, _wind_order.get(value, 99))
    if suit == "Dragon":
        return (suit_rank, _dragon_order.get(value, 99))
    # fallback
    return (suit_rank, value)


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []              # concealed tiles in hand
        self.exposed_melds = []     # list of exposed melds (each meld is a list of tiles)
        self.simulator = False
        self.wind = None

    def draw_tile(self, tile, is_simulator=False):
        if tile:
            tile.state = 1   # mark tile as in-hand when drawn
            self.hand.append(tile)

    def discard_tile(self, index=-1):
        if not self.hand:
            return None
        tile = self.hand.pop(index)
        tile.state = 2
        return tile

    def __repr__(self):
        return f"Player({self.name})"

    # ---------------------------
    # CLAIM CHECKS
    # ---------------------------
    def can_pong(self, tile):
        """Check if player can claim tile for a Pong (has 2 matching tiles)."""
        tile_type = (tile.suit, tile.value)
        matching = sum(1 for t in self.hand if (t.suit, t.value) == tile_type)
        return matching >= 2

    def can_kong(self, tile):
        """Check if player can claim tile for a Kong (has 3 matching tiles)."""
        tile_type = (tile.suit, tile.value)
        matching = sum(1 for t in self.hand if (t.suit, t.value) == tile_type)
        return matching >= 3

    def can_chow(self, tile, from_player_wind, self_wind):
        """
        Check if player can claim tile for a Chow (sequence).
        Chow can only be claimed from the player to your left.
        Only works for suited tiles (Dots, Bamboo, Characters).
        """
        # Chow only allowed from player to your left
        wind_order = ["East", "South", "West", "North"]
        self_idx = wind_order.index(self_wind)
        left_idx = (self_idx - 1) % 4  # player to the left
        if from_player_wind != wind_order[left_idx]:
            return False

        # Only suited tiles can form sequences
        if tile.suit not in ("Dots", "Bamboo", "Characters"):
            return False

        if not isinstance(tile.value, int):
            return False

        # Check all possible sequences this tile could complete
        tile_val = tile.value
        hand_vals = [t.value for t in self.hand if t.suit == tile.suit and isinstance(t.value, int)]

        # Tile could be: low (X, X+1, X+2), middle (X-1, X, X+1), or high (X-2, X-1, X)
        sequences = []
        if tile_val >= 1 and tile_val <= 7:  # can be low tile
            if (tile_val + 1) in hand_vals and (tile_val + 2) in hand_vals:
                sequences.append((tile_val, tile_val + 1, tile_val + 2))
        if tile_val >= 2 and tile_val <= 8:  # can be middle tile
            if (tile_val - 1) in hand_vals and (tile_val + 1) in hand_vals:
                sequences.append((tile_val - 1, tile_val, tile_val + 1))
        if tile_val >= 3 and tile_val <= 9:  # can be high tile
            if (tile_val - 2) in hand_vals and (tile_val - 1) in hand_vals:
                sequences.append((tile_val - 2, tile_val - 1, tile_val))

        return len(sequences) > 0

    def get_chow_options(self, tile):
        """Return list of possible chow sequences for a tile."""
        if tile.suit not in ("Dots", "Bamboo", "Characters"):
            return []
        if not isinstance(tile.value, int):
            return []

        tile_val = tile.value
        hand_vals = [t.value for t in self.hand if t.suit == tile.suit and isinstance(t.value, int)]

        sequences = []
        if tile_val >= 1 and tile_val <= 7:
            if (tile_val + 1) in hand_vals and (tile_val + 2) in hand_vals:
                sequences.append((tile_val, tile_val + 1, tile_val + 2))
        if tile_val >= 2 and tile_val <= 8:
            if (tile_val - 1) in hand_vals and (tile_val + 1) in hand_vals:
                sequences.append((tile_val - 1, tile_val, tile_val + 1))
        if tile_val >= 3 and tile_val <= 9:
            if (tile_val - 2) in hand_vals and (tile_val - 1) in hand_vals:
                sequences.append((tile_val - 2, tile_val - 1, tile_val))

        return sequences

    def can_win_with(self, tile):
        """Check if claiming this tile would complete a winning hand."""
        # Temporarily add tile to hand
        self.hand.append(tile)
        is_win = self.check_win()
        self.hand.remove(tile)
        return is_win

    def claim_pong(self, tile):
        """Claim a tile to form a Pong. Returns the meld formed."""
        tile_type = (tile.suit, tile.value)
        # Find 2 matching tiles in hand
        matching = [t for t in self.hand if (t.suit, t.value) == tile_type][:2]
        for t in matching:
            self.hand.remove(t)
        # Form the meld (3 tiles including the claimed one)
        meld = matching + [tile]
        tile.state = 1  # mark as in-hand/melded
        self.exposed_melds.append(meld)
        return meld

    def claim_kong(self, tile):
        """Claim a tile to form a Kong. Returns the meld formed."""
        tile_type = (tile.suit, tile.value)
        # Find 3 matching tiles in hand
        matching = [t for t in self.hand if (t.suit, t.value) == tile_type][:3]
        for t in matching:
            self.hand.remove(t)
        # Form the meld (4 tiles including the claimed one)
        meld = matching + [tile]
        tile.state = 1
        self.exposed_melds.append(meld)
        return meld

    def claim_chow(self, tile, sequence):
        """
        Claim a tile to form a Chow with specified sequence.
        sequence: tuple of 3 values like (2, 3, 4)
        Returns the meld formed.
        """
        meld = [tile]
        tile.state = 1
        # Find the other 2 tiles from hand
        for val in sequence:
            if val != tile.value:
                # Find a tile with this value and same suit
                for t in self.hand:
                    if t.suit == tile.suit and t.value == val:
                        self.hand.remove(t)
                        meld.append(t)
                        break
        self.exposed_melds.append(meld)
        return meld

    def claim_win(self, tile):
        """Claim a tile to win (Ron). Add tile to hand."""
        tile.state = 1
        self.hand.append(tile)

    # ---------------------------
    # WIN CHECKS
    # ---------------------------
    def check_win(self):
        """Dispatch to selected win mode."""
        if WIN_MODE == "A":
            return self._win_mode_a()
        elif WIN_MODE == "B":
            return self._win_mode_b()
        else:
            return self._win_mode_c()

    def _win_mode_a(self):
        """DEBUG MODE: wins if total tiles >= 14"""
        total_tiles = len(self.hand) + sum(len(m) for m in self.exposed_melds)
        return total_tiles >= 14

    def _win_mode_b(self):
        """Heuristic mode."""
        total_tiles = len(self.hand) + sum(len(m) for m in self.exposed_melds)
        if total_tiles % 3 != 2:
            return False

        keys = [(t.suit, t.value) for t in self.hand]
        counts = Counter(keys)

        has_triplet = any(v >= 3 for v in counts.values()) or len(self.exposed_melds) > 0
        has_pair = any(v >= 2 for v in counts.values())
        if not (has_triplet and has_pair):
            return False

        for triple_key, triple_count in list(counts.items()):
            if triple_count >= 3:
                counts_copy = counts.copy()
                counts_copy[triple_key] -= 3
                for pair_key, pair_count in list(counts_copy.items()):
                    if counts_copy.get(pair_key, 0) >= 2:
                        counts_copy[pair_key] -= 2
                        if self._can_form_melds(counts_copy.copy()):
                            return True
        return False

    def _win_mode_c(self):
        """
        Realistic full check (4 melds + pair).
        Accounts for exposed melds.
        """
        # Total tiles must be 14 (3n + 2 where n=4 melds)
        total_tiles = len(self.hand) + sum(len(m) for m in self.exposed_melds)

        # Handle Kong (4 tiles = 1 meld, so 14 + num_kongs)
        num_kongs = sum(1 for m in self.exposed_melds if len(m) == 4)
        expected_tiles = 14 + num_kongs

        if total_tiles != expected_tiles:
            return False

        # Exposed melds already count as complete melds
        num_exposed_melds = len(self.exposed_melds)
        melds_needed = 4 - num_exposed_melds

        # Hand must have: melds_needed * 3 + 2 (pair) tiles
        hand_tiles_needed = melds_needed * 3 + 2
        if len(self.hand) != hand_tiles_needed:
            return False

        # Check if hand can form remaining melds + pair
        keys = [(t.suit, t.value) for t in self.hand]
        counts = Counter(keys)

        # Try each possible pair (eye)
        for pair_key in sorted([k for k, v in counts.items() if v >= 2], key=_tile_order_key):
            counts_copy = counts.copy()
            counts_copy[pair_key] -= 2
            if self._can_form_melds(counts_copy):
                return True
        return False

    def _can_form_melds(self, counts):
        """
        Return True if the counts can be fully partitioned into melds (pongs/chis).
        """
        if sum(counts.values()) == 0:
            return True

        available_keys = [k for k, v in counts.items() if v > 0]
        if not available_keys:
            return True

        tile = min(available_keys, key=_tile_order_key)
        suit, num = tile

        # Try Pong (triplet)
        if counts.get(tile, 0) >= 3:
            counts[tile] -= 3
            if self._can_form_melds(counts):
                counts[tile] += 3
                return True
            counts[tile] += 3

        # Try Chi (sequence) for numeric suits
        if suit in ("Dots", "Bamboo", "Characters") and isinstance(num, int):
            if num <= 7:
                needed = [(suit, num), (suit, num + 1), (suit, num + 2)]
                if all(counts.get(k, 0) > 0 for k in needed):
                    for k in needed:
                        counts[k] -= 1
                    if self._can_form_melds(counts):
                        for k in needed:
                            counts[k] += 1
                        return True
                    for k in needed:
                        counts[k] += 1

        return False
