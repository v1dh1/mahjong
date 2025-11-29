# agent.py

from reward_functions import (
    shaping_reward,
    shaped_score,
    is_winning_hand,
)
from tile import Tile
import random
from collections import defaultdict


class MahjongAgent:
    def __init__(self, game, w=1.0, search_depth=1, base_win_score=100):
        """
        game: Game instance (provides deck and current state via deck.all_tiles)
        w: weight for unscented bonus (paper varies this to control risk)
        search_depth: reserved for future lookahead
        base_win_score: reward returned for terminal winning states
        """
        self.game = game
        self.w = w
        self.search_depth = search_depth
        self.base_win_score = base_win_score

    # -------------------------
    # Helpers: tile-type key and unseen-type counts
    # -------------------------
    @staticmethod
    def tile_type_key_from_tileobj(tile_obj):
        """Return canonical tile type key (suit, value) for a Tile object."""
        return tile_obj.suit, tile_obj.value

    def build_unseen_type_counts(self):
        """
        Count remaining unseen copies by tile type using deck.all_tiles.
        Any tile with state == 0 is treated as in the wall / unseen.

        Returns: (counts_dict, total_unseen)
          counts_dict: {(suit, value): count_remaining}
          total_unseen: integer total number of unseen copies
        """
        counts = defaultdict(int)
        total = 0
        for t in self.game.deck.all_tiles:
            if getattr(t, "state", 0) == 0:
                counts[(t.suit, t.value)] += 1
                total += 1
        return counts, total

    # -------------------------
    # Core 1-step Q-function
    # -------------------------
    def computeQ(self, state_hand, action_tile, depth=0):
        """
        Exact expected Q(s,a) using tile-type probabilities (1-step lookahead).

        - state_hand: list of Tile objects (current hand)
        - action_tile: Tile object from state_hand to discard

        Returns the expected shaped reward for discarding action_tile and
        drawing one random unseen tile.
        """
        # Defensive check
        if action_tile not in state_hand:
            return -float("inf")

        original_hand = list(state_hand)

        # Build unseen counts by tile type (suit, value)
        unseen_counts, total_unseen = self.build_unseen_type_counts()
        # Remove the action_tile to form post-discard (hand before draw)
        post_discard = list(original_hand)
        post_discard.remove(action_tile)

        if total_unseen == 0:
            # No tiles left to draw; fallback to immediate shaping delta
            return shaping_reward(
                original_hand,
                post_discard,
                w=self.w,
                base_win_score=self.base_win_score,
            )

        expected_Q = 0.0

        for tile_type, count_remaining in unseen_counts.items():
            if count_remaining <= 0:
                continue
            p_t = count_remaining / total_unseen

            # Simulate drawing one copy of this tile type
            suit, value = tile_type
            synthetic_draw = Tile(suit, value, copy_no=0)

            # Construct next_hand (post-discard + drawn tile)
            next_hand = list(post_discard)
            next_hand.append(synthetic_draw)

            # Compute reward for transition
            if is_winning_hand(next_hand):
                r = self.base_win_score
            else:
                r = (
                    shaped_score(
                        next_hand, w=self.w, base_win_score=self.base_win_score
                    )
                    - shaped_score(
                        original_hand, w=self.w, base_win_score=self.base_win_score
                    )
                )

            expected_Q += p_t * r

        return expected_Q

    # -------------------------
    # Helper: 1-step Q from arbitrary hand (used by depth-2)
    # -------------------------
    def _one_step_Q_from_hand(
        self, hand, action_tile, unseen_counts=None, total_unseen=None
    ):
        """
        Helper: 1-step Q(s,a) from a given hand, optionally using precomputed
        unseen_counts/total_unseen to avoid recomputation.
        """
        if action_tile not in hand:
            return -float("inf")

        original_hand = list(hand)

        if unseen_counts is None or total_unseen is None:
            unseen_counts, total_unseen = self.build_unseen_type_counts()

        post_discard = list(original_hand)
        post_discard.remove(action_tile)

        if total_unseen == 0:
            return shaping_reward(
                original_hand,
                post_discard,
                w=self.w,
                base_win_score=self.base_win_score,
            )

        expected_q = 0.0
        for tile_type, count_remaining in unseen_counts.items():
            if count_remaining <= 0:
                continue
            p_t = count_remaining / total_unseen
            suit, value = tile_type
            draw = Tile(suit, value, copy_no=0)
            next_hand = list(post_discard)
            next_hand.append(draw)

            r = shaping_reward(
                original_hand,
                next_hand,
                w=self.w,
                base_win_score=self.base_win_score,
            )
            expected_q += p_t * r

        return expected_q

    # -------------------------
    # Depth-2 Q-function
    # -------------------------
    def computeQ_depth2(self, state_hand, action_tile):
        """
        Two-step lookahead Q(s,a):

        Step 1: discard action_tile, draw from unseen -> reward r1(s -> s1).
        Step 2: from s1, assume we take the discard that maximizes 1-step Q.

        Q2(s,a) = E_{first draw} [ r1 + max_{a'} Q1(s1, a') ].
        """
        if action_tile not in state_hand:
            return -float("inf")

        original_hand = list(state_hand)
        unseen_counts, total_unseen = self.build_unseen_type_counts()

        post_discard = list(original_hand)
        post_discard.remove(action_tile)

        if total_unseen == 0:
            return shaping_reward(
                original_hand,
                post_discard,
                w=self.w,
                base_win_score=self.base_win_score,
            )

        expected_Q = 0.0

        for tile_type, count_remaining in unseen_counts.items():
            if count_remaining <= 0:
                continue
            p_t = count_remaining / total_unseen

            suit, value = tile_type
            first_draw = Tile(suit, value, copy_no=0)

            hand1 = list(post_discard)
            hand1.append(first_draw)

            r1 = shaping_reward(
                original_hand,
                hand1,
                w=self.w,
                base_win_score=self.base_win_score,
            )

            if is_winning_hand(hand1):
                expected_Q += p_t * r1
                continue

            # Best 1-step Q from the next state
            best_future_q = -float("inf")
            for a2 in hand1:
                q1 = self._one_step_Q_from_hand(
                    hand1, a2, unseen_counts, total_unseen
                )
                if q1 > best_future_q:
                    best_future_q = q1

            expected_Q += p_t * (r1 + best_future_q)

        return expected_Q

    # -------------------------
    # Policy: pick discard with max Q (depth-1 by default)
    # -------------------------
    def select_discard(self, player, use_depth2=False):
        """
        Evaluate Q(s,a) for each tile in player's hand and return the tile
        with max Q. If use_depth2=True, uses depth-2 Q; else uses 1-step Q.
        Break ties randomly.
        """
        best_q = -float("inf")
        best_tiles = []

        for tile in list(player.hand):
            if use_depth2:
                q_val = self.computeQ_depth2(player.hand, tile)
            else:
                q_val = self.computeQ(player.hand, tile, depth=0)

            if q_val > best_q:
                best_q = q_val
                best_tiles = [tile]
            elif q_val == best_q:
                best_tiles.append(tile)

        if not best_tiles:
            return random.choice(player.hand) if player.hand else None
        return random.choice(best_tiles)

    # -------------------------
    # Expected draw value (for claim decisions)
    # -------------------------
    def compute_expected_draw_value(self, player):
        """
        Compute the expected shaped_score if the player draws from the deck.
        Used as a baseline for deciding whether to claim Pong/Kong/Chow.
        """
        current_hand = list(player.hand)
        current_score = shaped_score(
            current_hand, w=self.w, base_win_score=self.base_win_score
        )

        unseen_counts, total_unseen = self.build_unseen_type_counts()
        if total_unseen == 0:
            return current_score

        expected_score = 0.0
        for tile_type, count_remaining in unseen_counts.items():
            if count_remaining <= 0:
                continue
            p_t = count_remaining / total_unseen
            suit, value = tile_type
            synthetic_draw = Tile(suit, value, copy_no=0)

            hand_after_draw = list(current_hand)
            hand_after_draw.append(synthetic_draw)

            if is_winning_hand(hand_after_draw):
                score_after = self.base_win_score
            else:
                score_after = shaped_score(
                    hand_after_draw,
                    w=self.w,
                    base_win_score=self.base_win_score,
                )

            expected_score += p_t * score_after

        return expected_score

    # -------------------------
    # Claim evaluation: Pong/Kong/Chow
    # -------------------------
    def evaluate_pong_claim(self, player, tile):
        """
        Evaluate the value of claiming a Pong.
        Returns the shaped_score after claiming (approximate heuristic).
        """
        tile_type = (tile.suit, tile.value)
        simulated_hand = list(player.hand)

        matching = [t for t in simulated_hand if (t.suit, t.value) == tile_type][:2]
        for t in matching:
            simulated_hand.remove(t)

        pong_bonus = 3  # same as ShangTing triplet bonus
        hand_score = shaped_score(
            simulated_hand, w=self.w, base_win_score=self.base_win_score
        )
        return hand_score + pong_bonus

    def evaluate_kong_claim(self, player, tile):
        """
        Evaluate the value of claiming a Kong.
        Returns the shaped_score after claiming (approximate heuristic).
        """
        tile_type = (tile.suit, tile.value)
        simulated_hand = list(player.hand)

        matching = [t for t in simulated_hand if (t.suit, t.value) == tile_type][:3]
        for t in matching:
            simulated_hand.remove(t)

        kong_bonus = 4  # heuristic: 4-of-a-kind is strong
        hand_score = shaped_score(
            simulated_hand, w=self.w, base_win_score=self.base_win_score
        )
        replacement_draw_bonus = 1  # approximate benefit of extra draw
        return hand_score + kong_bonus + replacement_draw_bonus

    def evaluate_chow_claim(self, player, tile, sequence):
        """
        Evaluate the value of claiming a Chow.

        sequence: a tuple of 3 numeric values (e.g., (2,3,4)).
        Returns the shaped_score after claiming (approximate heuristic).
        """
        simulated_hand = list(player.hand)

        # Remove the 2 tiles from hand that complete the sequence with 'tile'
        for val in sequence:
            if val == tile.value:
                continue
            for t in simulated_hand:
                if t.suit == tile.suit and t.value == val:
                    simulated_hand.remove(t)
                    break

        chow_bonus = 3  # same as ShangTing sequence bonus
        hand_score = shaped_score(
            simulated_hand, w=self.w, base_win_score=self.base_win_score
        )
        exposure_penalty = 0.5  # small penalty for exposing hand
        return hand_score + chow_bonus - exposure_penalty

    # -------------------------
    # Claim decision helpers
    # -------------------------
    def should_claim_pong(self, player, tile):
        """
        Decide if player should claim a Pong using value comparison:
        claim_value vs expected draw value.
        """
        claim_value = self.evaluate_pong_claim(player, tile)
        draw_value = self.compute_expected_draw_value(player)
        return claim_value > draw_value

    def should_claim_kong(self, player, tile):
        """
        Decide if player should claim a Kong using value comparison.
        """
        claim_value = self.evaluate_kong_claim(player, tile)
        draw_value = self.compute_expected_draw_value(player)
        return claim_value > draw_value

    def should_claim_chow(self, player, tile, sequence):
        """
        Decide if player should claim a Chow using value comparison.
        """
        claim_value = self.evaluate_chow_claim(player, tile, sequence)
        draw_value = self.compute_expected_draw_value(player)
        return claim_value > draw_value
