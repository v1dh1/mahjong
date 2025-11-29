from deck import Deck
from player import Player
from agent import MahjongAgent
from reward_functions import is_winning_hand, shaped_score

class SinglePlayerGame:
    def __init__(self, w=0, base_win_score=100):
        self.deck = Deck()
        self.discard_pile = []
        self.player = Player("Agent")
        self.agent = MahjongAgent(self, w=w, base_win_score=base_win_score)

    def start(self):
        print("Shuffling deck...")
        self.deck.shuffle()

        print("Dealing initial 13 tiles to agent...")
        for _ in range(13):
            tile = self.deck.draw()
            if tile is None:
                raise RuntimeError("Deck exhausted while dealing initial hand")
            tile.state = 1
            self.player.draw_tile(tile, is_simulator=True)

        print("Starting single-player Q-based simulation...")
        self.play_game()

    def play_game(self, max_steps=500):
        steps = 0
        while True:
            steps += 1
            if steps > max_steps:
                print("Safety stop: too many discards.")
                return

            hand = self.player.hand

            # (Optional) log Q-values for analysis
            print("\nCurrent hand:", hand)
            q_vals = []
            for t in hand:
                q = self.agent.compute_Q(hand, t, depth=0)
                q_vals.append((t, q))
            print("Q-values per tile:")
            for t, q in q_vals:
                print(f"  {t}: Q = {q:.3f}")

            # 1) choose discard using Q(s,a)
            discard_tile = self.agent.select_discard(self.player)
            if discard_tile is None:
                print("No tiles to discard; ending.")
                return

            print(f"Agent discards {discard_tile}")
            discard_tile.state = 2
            self.player.hand.remove(discard_tile)
            self.discard_pile.append(discard_tile)

            # 2) draw from wall
            drawn = self.deck.draw()
            if drawn is None:
                print("Wall empty, game ends (no win).")
                return
            drawn.state = 1
            self.player.hand.append(drawn)
            print(f"Agent draws {drawn} | wall size = {len(self.deck.tiles)}")

            # 3) win check after draw
            if is_winning_hand(self.player.hand):
                print(f"\nAgent wins after {steps} discards!")
                print("Final hand:", self.player.hand)
                print("Final shaped score:",
                      shaped_score(self.player.hand,
                                   w=self.agent.w,
                                   base_win_score=self.agent.base_win_score))
                return
