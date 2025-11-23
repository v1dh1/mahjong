# reward_functions.py

def is_winning_hand(hand):
    """Check if hand is winning (placeholder, adapt with real Mahjong rules)."""
    # Currently just return True if 14 tiles for testing
    return len(hand) >= 14

def compute_shangting(hand):
    """ShangTing heuristic: estimate how close hand is to winning."""
    score = -14
    # Placeholder: you can implement counting sets, runs, pairs etc.
    return score

def compute_bonus(hand, w=1.0):
    """Unscented bonus for wind/dragon sets and suit dominance."""
    bonus = 0
    suit_counts = {}
    for tile in hand:
        suit_counts[tile.suit] = suit_counts.get(tile.suit, 0) + 1
    if suit_counts:
        max_count = max(suit_counts.values())
        total = sum(suit_counts.values())
        bonus += 3 * (max_count / total)
    return w * bonus

def shaping_reward(prev_hand, next_hand, w=1.0, base_win_score=100):
    """Compute shaped reward between two hands."""
    if is_winning_hand(next_hand):
        return base_win_score
    prev_score = compute_shangting(prev_hand) + compute_bonus(prev_hand, w)
    next_score = compute_shangting(next_hand) + compute_bonus(next_hand, w)
    return next_score - prev_score
