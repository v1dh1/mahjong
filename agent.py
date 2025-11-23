# agent.py
from reward_functions import shaping_reward
import copy
import random

class MahjongAgent:
    def __init__(self, game, w=1.0, search_depth=1):
        self.game = game
        self.w = w
        self.search_depth = search_depth

    def compute_Q(self, state_hand, action_tile, depth=0):
        """
        Simulate discarding `action_tile` and return expected Q-value.
        state_hand: list of Tile objects (current hand)
        """
        # Clone the hand
        sim_hand = state_hand.copy()
        if action_tile not in sim_hand:
            return -float('inf')
        sim_hand.remove(action_tile)
        
        # Apply shaping reward
        reward = shaping_reward(state_hand, sim_hand, w=self.w)
        
        # Simple depth=1 forward search (could recurse for deeper)
        if depth >= self.search_depth:
            return reward
        
        # Estimate future Q by randomly simulating next draw and discard
        future_rewards = []
        available_tiles = [t for t in self.game.deck.tiles if t.state == 0]
        if not available_tiles:
            return reward
        
        for tile_drawn in random.sample(available_tiles, min(3, len(available_tiles))):
            sim_hand_next = sim_hand.copy()
            sim_hand_next.append(tile_drawn)
            # Random discard (could also call compute_Q recursively)
            discard_candidate = random.choice(sim_hand_next)
            sim_hand_next.remove(discard_candidate)
            r = shaping_reward(sim_hand, sim_hand_next, w=self.w)
            future_rewards.append(r)
        
        if future_rewards:
            reward += sum(future_rewards) / len(future_rewards)
        
        return reward

    def select_discard(self, player):
        """
        Choose the tile to discard from player's hand.
        """
        best_q = -float('inf')
        best_tile = None
        for tile in player.hand:
            q_val = self.compute_Q(player.hand, tile, depth=0)
            if q_val > best_q:
                best_q = q_val
                best_tile = tile
        return best_tile
