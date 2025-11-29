# reward_functions.py
"""
Reward and hand-evaluation utilities for the Mahjong agent.
Implements:
 - accurate winning-hand checks (standard, seven-pairs, kokushi)
 - ShangTing shaped heuristic (paper: start -14, +3 per triplet, +3 per run, +2 first pair)
 - Unscented bonus (honor triplet/pair + suit-dominance)
 - shaped_score and shaping_reward (paper's R_s)
 - small ukeire helper (types that improve ShangTing)
"""

from collections import Counter, defaultdict
from tile import Tile
import copy

# -----------------------
# Winning hand checks
# -----------------------
def is_winning_hand(hand):
    """
    Return True if hand is a valid winning hand under common Japanese-style rules:
     - Standard 4 melds + 1 pair
     - Seven Pairs (Chiitoitsu)
     - Kokushi Musou (Thirteen Orphans)
    Expects `hand` to be a list of Tile-like objects (suit, value).
    """
    # Normalize counts by tile type (suit, value)
    if len(hand) != 14:
        return False

    counts = _counts_from_hand(hand)
    # Standard 4 melds + 1 pair
    if _is_standard_win(counts):
        return True
    # Seven pairs
    if _is_seven_pairs(counts):
        return True
    # Kokushi: 13 terminals & honors + one duplicate
    if _is_kokushi(counts):
        return True

    return False


def _counts_from_hand(hand):
    """Return Counter mapping (suit, value) -> count."""
    keys = [(t.suit, t.value) for t in hand]
    return Counter(keys)


def _is_seven_pairs(counts):
    """
    Seven Pairs (Chiitoitsu).
    We treat a four-of-a-kind as two pairs (common rule).
    """
    pair_count = 0
    for v in counts.values():
        pair_count += v // 2
    return pair_count == 7


def _is_kokushi(counts):
    """
    Kokushi Musou: need at least one of each of the 13 terminals/honors,
    plus one duplicate among them. Terminal tiles = 1 or 9 of suits,
    honors = winds + dragons.
    """
    terminals_and_honors = []
    suits = ("Dots", "Bamboo", "Characters")
    for s in suits:
        terminals_and_honors.append((s, 1))
        terminals_and_honors.append((s, 9))
    for wind in ("East", "South", "West", "North"):
        terminals_and_honors.append(("Wind", wind))
    for dragon in ("Red", "Green", "White"):
        terminals_and_honors.append(("Dragon", dragon))

    # need all 13 types present at least once
    for key in terminals_and_honors:
        if counts.get(key, 0) < 1:
            return False

    # total tiles must be 14 and there must be one duplicate among the 13
    # (since counts sum to 14 and each of 13 types has >=1, at least one has >=2)
    return sum(counts.values()) == 14 and any(counts[k] >= 2 for k in terminals_and_honors)


def _is_standard_win(counts):
    """
    Check standard 4 melds + 1 pair.
    Approach: try every possible pair, remove it, then check if remaining tiles can be partitioned into melds.
    Melds are:
      - Pong (three identical tiles)
      - Chi (sequence of three consecutive numbers in same suit) for suited tiles only
    """
    total_tiles = sum(counts.values())
    if total_tiles != 14:
        return False

    # Try every possible tile type as the pair candidate
    for tile_type, c in list(counts.items()):
        if c >= 2:
            counts[tile_type] -= 2
            if _can_partition_into_melds(counts):
                counts[tile_type] += 2
                return True
            counts[tile_type] += 2
    return False


def _can_partition_into_melds(counts):
    """
    Recursively check if given counts (sum must be 12) can be decomposed into melds.
    Uses backtracking. Negative or zero counts are handled.
    """
    # If no tiles left, success
    if sum(counts.values()) == 0:
        return True

    # pick the tile type with positive count
    # deterministic pick: smallest (suit, value) for reproducibility
    tile_type = next(k for k, v in counts.items() if v > 0)
    c = counts[tile_type]
    suit, value = tile_type

    # Try pong/triplet if available
    if c >= 3:
        counts[tile_type] -= 3
        if _can_partition_into_melds(counts):
            counts[tile_type] += 3
            return True
        counts[tile_type] += 3

    # Try chi/sequence if suited numeric
    if suit in ("Dots", "Bamboo", "Characters") and isinstance(value, int):
        # need value, value+1, value+2 each present
        if value <= 7:
            needed = [(suit, value), (suit, value + 1), (suit, value + 2)]
            if all(counts.get(k, 0) > 0 for k in needed):
                for k in needed:
                    counts[k] -= 1
                if _can_partition_into_melds(counts):
                    for k in needed:
                        counts[k] += 1
                    return True
                for k in needed:
                    counts[k] += 1

    return False


# -----------------------
# ShangTing heuristic (per paper's description you provided)
# -----------------------
def compute_shangting(hand):
    """
    Implementation of ShangTing scoring as described:
    - initialize score = -14
    - +3 for each completed triplet (pong) found
    - +3 for each sequence (chi) found greedily per suit
    - +2 for the first pair present
    This is a heuristic estimate of closeness to winning (shaped component).
    """
    counts = _counts_from_hand(hand)
    score = -14

    # Count triplets (integer division)
    triplet_count = 0
    for tile_key, c in counts.items():
        triplet_count += c // 3
    score += 3 * triplet_count

    # For sequences (only for numeric suits), do greedy extraction per suit
    sequence_count = 0
    # copy counts into a mutable structure keyed by suit -> array counts 1..9
    suit_num_counts = {
        "Dots": [0] * 10,
        "Bamboo": [0] * 10,
        "Characters": [0] * 10
    }
    for (s, v), c in counts.items():
        if s in suit_num_counts and isinstance(v, int):
            suit_num_counts[s][v] += c

    # Greedy extraction of sequences for each suit
    for s in ("Dots", "Bamboo", "Characters"):
        arr = suit_num_counts[s]
        # attempt to extract sequences while possible
        i = 1
        while i <= 7:
            if arr[i] > 0 and arr[i + 1] > 0 and arr[i + 2] > 0:
                arr[i] -= 1
                arr[i + 1] -= 1
                arr[i + 2] -= 1
                sequence_count += 1
                # restart at 1 to extract overlapping runs if present
                i = 1
                continue
            i += 1
    score += 3 * sequence_count

    # First pair bonus: check if there's at least one pair anywhere
    has_pair = any(c >= 2 for c in counts.values())
    if has_pair:
        score += 2

    return score


# -----------------------
# Ukeire helper (optional, not in original paper but useful)
# -----------------------
def compute_ukeire_count(hand):
    """
    Return the number of distinct tile *types* that would improve the ShangTing score
    if drawn (i.e., how many tile types are ukeire).
    This is useful if you later want to weight draws by usefulness.
    """
    baseline = compute_shangting(hand)
    # enumerate all 34 tile types
    suits = ("Dots", "Bamboo", "Characters")
    tile_types = []
    for s in suits:
        for v in range(1, 10):
            tile_types.append((s, v))
    for wind in ("East", "South", "West", "North"):
        tile_types.append(("Wind", wind))
    for dragon in ("Red", "Green", "White"):
        tile_types.append(("Dragon", dragon))

    count = 0
    for (s, v) in tile_types:
        synthetic = list(hand)
        synthetic.append(Tile(s, v, copy_no=0))
        if compute_shangting(synthetic) > baseline:
            count += 1
    return count


# -----------------------
# Unscented bonus (paper)
# -----------------------
def unscented_bonus(hand, w=1.0):
    """
    Implements the paper's 'unscented bonus':
      - +3 per triplet of honor tiles (Wind/Dragon)
      - +1 for the first remaining honor pair
      - Suit dominance: 3 * (max_tiles_in_one_suit / total_suited_tiles) ** 5
    Multiply sum by weight w.
    """
    keys = [(t.suit, t.value) for t in hand]
    counts = Counter(keys)

    triplet_honor_score = 0
    pair_honor_score = 0
    for (suit, value), c in counts.items():
        if suit in ("Wind", "Dragon"):
            triplets = c // 3
            triplet_honor_score += 3 * triplets
            if c % 3 >= 2:
                pair_honor_score += 1

    # Suit dominance
    suit_counts = {"Dots": 0, "Bamboo": 0, "Characters": 0}
    for t in hand:
        if t.suit in suit_counts:
            suit_counts[t.suit] += 1
    total_suited = sum(suit_counts.values())
    suit_dominance = 0.0
    if total_suited > 0:
        max_in_one = max(suit_counts.values())
        suit_dominance = 3.0 * ((max_in_one / total_suited) ** 5)

    bonus = triplet_honor_score + pair_honor_score + suit_dominance
    return w * bonus


# Deprecated alias for backwards compatibility
def compute_bonus(hand, w=1.0):
    return unscented_bonus(hand, w)


# -----------------------
# Shaped score and shaping reward
# -----------------------
def shaped_score(hand, w=1.0, base_win_score=100):
    """
    Combined shaped score: ShangTing + unscented bonus.
    If hand is winning, return base_win_score (paper uses official score).
    """
    if is_winning_hand(hand):
        return base_win_score
    return compute_shangting(hand) + unscented_bonus(hand, w)


def official_score(hand):
    """
    Placeholder for official Mahjong scoring for a winning hand.
    Implement full yaku/hans/points if you want actual scores.
    For now returns a default value; the agent will treat it as the terminal reward.
    """
    # TODO: Replace with full yaku/han/point calculation if needed.
    # For now return a fixed scale baseline (you may pass this through shaped_reward)
    return 100


def shaping_reward(prev_hand, next_hand, w=1.0, base_win_score=100):
    """
    Paper's shaped reward R_s(s', s):
     - If next_hand is winning: return official_score(next_hand) (or base_win_score wrapper)
     - Else: shaped_score(next_hand) - shaped_score(prev_hand)
    """
    if is_winning_hand(next_hand):
        # Use official_score (if you want to keep base_win_score use that instead)
        return base_win_score if base_win_score is not None else official_score(next_hand)
    return shaped_score(next_hand, w, base_win_score) - shaped_score(prev_hand, w, base_win_score)
