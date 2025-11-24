# import random
# from copy import deepcopy
# from collections import Counter

# class MonteCarloAI:
#     def __init__(self, simulations=100):
#         self.simulations = simulations

#     def choose_discard(self, player, game):
#         """
#         player: Player object
#         game: Game object (to access deck and discard pile)
#         """
#         best_tile = None
#         best_score = -1

#         for tile in player.hand:
#             total_score = 0

#             for _ in range(self.simulations):
#                 # Simulate hand after discarding this tile
#                 sim_hand = player.hand[:]
#                 for i, sim_tile in enumerate(sim_hand):
#                     if sim_tile.suit == tile.suit and sim_tile.value == tile.value and sim_tile.copy_no == tile.copy_no:
#                         sim_hand.pop(i)
#                         break

#                 # Simulate random draw from remaining wall
#                 sim_wall = [t for t in game.deck.tiles if t.state == 0]
#                 random.shuffle(sim_wall)
#                 if sim_wall:
#                     drawn_tile = sim_wall.pop()
#                     sim_hand.append(drawn_tile)

#                 # Evaluate simulated hand
#                 score = self.evaluate_hand(sim_hand)
#                 total_score += score

#             avg_score = total_score / self.simulations
#             if avg_score > best_score:
#                 best_score = avg_score
#                 best_tile = tile

#         return best_tile

#     def evaluate_hand(self, hand):
#         """
#         Simplified scoring:
#         +1 for each triplet/pong (3 identical tiles)
#         +0.5 for each pair
#         """
#         counts = Counter((t.suit, t.value) for t in hand)
#         score = sum(v // 3 for v in counts.values())  # triplets
#         score += sum((v % 3) // 2 * 0.5 for v in counts.values())  # pairs
#         return score

import random  # used for shuffling the wall (remaining tiles)
from copy import deepcopy  # used if we need deep copies of hands (not strictly needed here)
from collections import Counter  # used to count identical tiles for scoring

class MonteCarloAI:
    def __init__(self, simulations=100):
        # Number of random simulations to run per possible discard
        self.simulations = simulations

    def choose_discard(self, player, game):
        """
        Chooses the best tile to discard using a Monte Carlo approach.
        
        player: Player object whose turn it is
        game: Game object to access the deck (wall) and other game info
        """
        best_tile = None  # will hold the tile that yields the best average score
        best_score = -1   # track the best average score found

        # Consider each tile in the player's hand as a candidate to discard
        for tile in player.hand:
            total_score = 0  # accumulate scores across simulations

            # Perform Monte Carlo simulations
            for _ in range(self.simulations):
                # Create a shallow copy of the player's hand for simulation
                sim_hand = player.hand[:]
                print(player.hand)

                # Remove the candidate tile from the simulated hand
                # We match tiles by attributes (suit, value, copy_no) instead of object identity
                for i, sim_tile in enumerate(sim_hand):
                    print("PLAYER HAND", player.hand)
                    if sim_tile.suit == tile.suit and sim_tile.value == tile.value and sim_tile.copy_no == tile.copy_no:
                        sim_hand.pop(i)  # remove this tile from simulated hand
                        break  # only remove one copy

                # Simulate drawing a random tile from the remaining wall
                sim_wall = [t for t in game.deck.tiles if t.state == 0]  # get available tiles
                random.shuffle(sim_wall)  # randomize order
                if sim_wall:  # if any tiles remain
                    drawn_tile = sim_wall.pop()  # take the top tile from shuffled wall
                    sim_hand.append(drawn_tile)  # add it to the simulated hand

                # Evaluate the simulated hand's strength using a simple heuristic
                score = self.evaluate_hand(sim_hand)
                total_score += score  # accumulate score for this discard candidate

            # Compute the average score for this discard
            avg_score = total_score / self.simulations

            # If this discard has the best average score so far, update best_tile
            if avg_score > best_score:
                best_score = avg_score
                best_tile = tile

        return best_tile  # return the tile that should be discarded

    def evaluate_hand(self, hand):
        """
        Simple heuristic scoring function:
        - +1 for each triplet (3 identical tiles)
        - +0.5 for each pair (2 identical tiles)
        
        hand: list of Tile objects
        """
        counts = Counter((t.suit, t.value) for t in hand)  # count identical tiles ignoring copy_no
        score = sum(v // 3 for v in counts.values())  # add 1 point for each triplet
        score += sum((v % 3) // 2 * 0.5 for v in counts.values())  # add 0.5 point for each pair
        return score
