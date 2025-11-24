# player.py
from collections import Counter

# Choose which win-rule to use:
# 'A' = fast/simple (len(hand) >= 14)
# 'B' = heuristic (quick check: at least one pong+pair and remaining can form melds)
# 'C' = realistic full check (4 melds + 1 pair)
WIN_MODE = "B"   # <--- set default to A as you requested

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.simulator = False

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

    # ---------------------------
    # MODE A: simplest — wins if hand has 14+ tiles
    # Good for fast testing / early wins.
    # ---------------------------
    def _win_mode_a(self):
        return len(self.hand) >= 14

    # ---------------------------
    # MODE B: heuristic
    # - Return True if the hand contains at least one PONG (triplet),
    #   plus at least one pair, and the remainder can be grouped into melds.
    # This is a relaxed rule that is more likely to trigger wins than full mode C
    # but is stricter than mode A.
    # ---------------------------
    def _win_mode_b(self):
        if len(self.hand) % 3 != 2:
            return False

        keys = [(t.suit, t.value) for t in self.hand]
        counts = Counter(keys)

        # require at least one triplet and one pair
        has_triplet = any(v >= 3 for v in counts.values())
        has_pair = any(v >= 2 for v in counts.values())
        if not (has_triplet and has_pair):
            return False

        # try to see if removing one triplet and one pair allows completion
        for triple_key, triple_count in list(counts.items()):
            if triple_count >= 3:
                counts[triple_key] -= 3
                for pair_key, pair_count in list(counts.items()):
                    if counts[pair_key] >= 2:
                        counts[pair_key] -= 2
                        if self._can_form_melds(counts.copy()):
                            return True
                        counts[pair_key] += 2
                counts[triple_key] += 3

        return False

    # ---------------------------
    # MODE C: realistic full check (4 melds + pair)
    # This is the algorithm you already had. Keep it slower but accurate.
    # ---------------------------
    def _win_mode_c(self):
        if len(self.hand) % 3 != 2:
            return False

        tiles = sorted(self.hand, key=lambda t: (t.suit, t.value))
        return self._can_form_hand(tiles)

    # ---------------------------
    # Shared helper functions (used by B and C)
    # ---------------------------
    def _can_form_hand(self, tiles):
        keys = [(t.suit, t.value) for t in tiles]
        counts = Counter(keys)

        for pair in list(counts.keys()):
            if counts[pair] >= 2:
                counts[pair] -= 2
                if self._can_form_melds(counts.copy()):
                    return True
                counts[pair] += 2
        return False

    def _can_form_melds(self, counts):
        if sum(counts.values()) == 0:
            return True

        # pick a tile with positive count
        tile = next(k for k, v in counts.items() if v > 0)
        suit, num = tile

        # Pong
        if counts[tile] >= 3:
            counts[tile] -= 3
            if self._can_form_melds(counts):
                return True
            counts[tile] += 3

        # Chi (only for numeric suits)
        if suit in ("Dots", "Bamboo", "Characters") and isinstance(num, int):
            needed = [(suit, num), (suit, num+1), (suit, num+2)]
            # ensure numbers are within 1..9
            if num <= 7 and all(counts.get(k, 0) > 0 for k in needed):
                for k in needed:
                    counts[k] -= 1
                if self._can_form_melds(counts):
                    return True
                for k in needed:
                    counts[k] += 1

        return False
