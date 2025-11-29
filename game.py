# game.py
from deck import Deck
from player import Player
from tile import Tile
import random
from agent import MahjongAgent


class Game:
    def __init__(self):
        self.deck = Deck()
        print("DECK CREATED")
        print("length of deck", len(Deck().tiles))
        self.players = [Player(f"Player {i+1}") for i in range(4)]
        self.discard_pile = []
        self.current_player_idx = 0  # track whose turn it is

    def assign_seats(self):
        print("💺 Randomly assign seats (wind directions) to the 4 players.")
        winds = ["East", "South", "West", "North"]
        random.shuffle(winds)

        for player, wind in zip(self.players, winds):
            player.wind = wind

        print("🎲 Seats assigned:")
        for p in self.players:
            print(f"{p.name} → {p.wind}")

    def assign_simulator(self):
        print("Assigning one of the players as the simulator")
        simulator_player = random.choice(self.players)
        simulator_player.simulator = True
        print(f"🖥️ Simulator: {simulator_player.name} -> {simulator_player.wind}")

    def get_player_by_wind(self, wind):
        """Get player by their wind position."""
        return next(p for p in self.players if p.wind == wind)

    def get_turn_order(self):
        """Return players in turn order starting from East."""
        wind_order = ["East", "South", "West", "North"]
        return [self.get_player_by_wind(w) for w in wind_order]

    def get_next_player(self, current_player):
        """Get the next player in turn order."""
        wind_order = ["East", "South", "West", "North"]
        current_idx = wind_order.index(current_player.wind)
        next_idx = (current_idx + 1) % 4
        return self.get_player_by_wind(wind_order[next_idx])

    def print_tile_states(self):
        print("\n--- Deck ---")
        for t in self.deck.tiles:
            print(t)

        print("\n--- Players' hands ---")
        for p in self.players:
            print(f"{p.name} hand: {p.hand}")
            print(f"{p.name} exposed melds: {p.exposed_melds}")

        print("\n--- Discard pile ---")
        for t in self.discard_pile:
            print(t)

    def start(self):
        print("🔄 Shuffling deck...")
        self.deck.shuffle()
        self.assign_seats()
        self.assign_simulator()

        print("🀄 Dealing initial hands...\n")
        for _ in range(13):
            for p in self.players:
                tile = self.deck.draw()
                p.draw_tile(tile, is_simulator=p.simulator)

        # Dealer draws 14th tile
        dealer = self.get_player_by_wind("East")
        dealer.draw_tile(self.deck.draw(), is_simulator=dealer.simulator)

        print(f"Dealer starting hand (14 tiles): {dealer.hand}\n")

        # Dealer discards the 14th tile
        discard = dealer.discard_tile()
        self.discard_pile.append(discard)
        print(f"🗑️ Dealer discards: {discard}\n")

        print("Game initialized — starting automated simulation...\n")
        self.play_game()

    def play_game(self):
        round_number = 1
        simulator_agent = MahjongAgent(self)
        current_player = self.get_player_by_wind("South")

        while True:
            print(f"\n=== Round {round_number} ===")
            result = self.play_round(simulator_agent, current_player)

            if result == "win":
                return
            elif result == "draw":
                print("Game ended in a draw (wall empty).")
                return

            # advance round and starting player
            round_number += 1
            current_player = self.get_next_player(current_player)



    def check_claims(self, discarded_tile, discarder, simulator_agent):
        """
        Check if any player wants to claim the discarded tile.
        Priority: Ron (win) > Kong > Pong > Chow
        Returns: (claiming_player, claim_type, extra_info) or (None, None, None)
        """
        wind_order = ["East", "South", "West", "North"]
        discarder_idx = wind_order.index(discarder.wind)

        # Check players in order (starting from player after discarder)
        # But priority matters: Ron > Kong > Pong > Chow

        ron_claims = []
        kong_claims = []
        pong_claims = []
        chow_claims = []

        for i in range(1, 4):  # Check other 3 players
            player_idx = (discarder_idx + i) % 4
            player = self.get_player_by_wind(wind_order[player_idx])

            # Check Ron (win)
            if player.can_win_with(discarded_tile):
                ron_claims.append(player)

            # Check Kong
            if player.can_kong(discarded_tile):
                kong_claims.append(player)

            # Check Pong
            if player.can_pong(discarded_tile):
                pong_claims.append(player)

            # Check Chow (only from player to the left of discarder)
            if player.can_chow(discarded_tile, discarder.wind, player.wind):
                chow_options = player.get_chow_options(discarded_tile)
                if chow_options:
                    chow_claims.append((player, chow_options))

        # Decision logic using agent's Q-value evaluation:
        # - Always claim Ron (it's a win!)
        # - Use agent to evaluate if Kong/Pong/Chow is worth claiming

        # Ron takes priority
        if ron_claims:
            # If multiple Ron, first in turn order wins
            return (ron_claims[0], "ron", None)

        # Kong - use agent to decide if beneficial
        if kong_claims:
            for player in kong_claims:
                if self.should_claim_kong(player, discarded_tile, simulator_agent):
                    return (player, "kong", None)

        # Pong - use agent to decide if beneficial
        if pong_claims:
            for player in pong_claims:
                if self.should_claim_pong(player, discarded_tile, simulator_agent):
                    return (player, "pong", None)

        # Chow - only the next player can claim, use agent to decide
        if chow_claims:
            next_player = self.get_next_player(discarder)
            for player, options in chow_claims:
                if player == next_player:
                    # Evaluate the best chow option
                    best_option = self.get_best_chow_option(player, discarded_tile, options, simulator_agent)
                    if best_option is not None:
                        return (player, "chow", best_option)

        return (None, None, None)

    def should_claim_pong(self, player, tile, agent):
        """
        Decide if player should claim a Pong using agent's Q-value evaluation.
        Compares value of claiming vs expected value of drawing from deck.
        """
        return agent.should_claim_pong(player, tile)

    def should_claim_kong(self, player, tile, agent):
        """
        Decide if player should claim a Kong using agent's Q-value evaluation.
        """
        return agent.should_claim_kong(player, tile)

    def should_claim_chow(self, player, tile, sequence, agent):
        """
        Decide if player should claim a Chow using agent's Q-value evaluation.
        """
        return agent.should_claim_chow(player, tile, sequence)

    def get_best_chow_option(self, player, tile, options, agent):
        """
        Evaluate all chow options and return the best one if it's worth claiming.
        Returns None if no chow is worth claiming.
        """
        best_option = None
        best_value = agent.compute_expected_draw_value(player)  # baseline: value of drawing
        
        for sequence in options:
            claim_value = agent.evaluate_chow_claim(player, tile, sequence)
            if claim_value > best_value:
                best_value = claim_value
                best_option = sequence
        
        return best_option

    def play_round(self, simulator_agent, starting_player):
        """
        Play one round of turns.
        Returns: "win", "draw", or "continue"
        """
        current_player = starting_player
        turns_taken = 0

        while turns_taken < 4:
            player = current_player

            # Draw tile from wall
            tile_to_draw = self.deck.draw()
            if not tile_to_draw:
                print("No more available tiles to draw! Wall empty.")
                return "draw"

            player.draw_tile(tile_to_draw, is_simulator=player.simulator)
            print(f"{player.name} draws {tile_to_draw}")

            # Check for self-draw win (Tsumo)
            if player.check_win():
                print(f"🏆 {player.name} wins by self-draw (Tsumo)!")
                self.print_winning_hand(player)
                return "win"


            if player.simulator:
                hand = player.hand
                print("\n  Q-values for simulator hand:")
                for t in hand:
                    q1 = simulator_agent.computeQ(hand, t, depth=0)
                    q2 = simulator_agent.computeQ_depth2(hand, t)
                    print(f"    {t}: Q1={q1:.3f}, Q2={q2:.3f}")

            # Decide and execute discard
            discard_tile = simulator_agent.select_discard(player)
            print(f"{player.name} discards: {discard_tile}")

            # Apply discard
            discard_tile.state = 2
            player.hand.remove(discard_tile)

            # Check if anyone wants to claim this discard
            claimer, claim_type, extra = self.check_claims(discard_tile, player, simulator_agent)

            if claimer:
                if claim_type == "ron":
                    print(f"🏆 {claimer.name} wins by claiming discard (Ron)!")
                    claimer.claim_win(discard_tile)
                    self.print_winning_hand(claimer)
                    return "win"

                elif claim_type == "kong":
                    print(f"🀄 {claimer.name} claims Kong!")
                    meld = claimer.claim_kong(discard_tile)
                    print(f"   Meld formed: {meld}")

                    # After Kong, player draws a replacement tile
                    replacement = self.deck.draw()
                    if replacement:
                        claimer.draw_tile(replacement)
                        print(f"   {claimer.name} draws replacement: {replacement}")

                        if claimer.check_win():
                            print(f"🏆 {claimer.name} wins after Kong!")
                            self.print_winning_hand(claimer)
                            return "win"

                        new_discard = simulator_agent.select_discard(claimer)
                        print(f"   {claimer.name} discards: {new_discard}")
                        new_discard.state = 2
                        claimer.hand.remove(new_discard)
                        self.discard_pile.append(new_discard)

                elif claim_type == "pong":
                    print(f"🀄 {claimer.name} claims Pong!")
                    meld = claimer.claim_pong(discard_tile)
                    print(f"   Meld formed: {meld}")

                    new_discard = simulator_agent.select_discard(claimer)
                    print(f"   {claimer.name} discards: {new_discard}")
                    new_discard.state = 2
                    claimer.hand.remove(new_discard)
                    self.discard_pile.append(new_discard)

                elif claim_type == "chow":
                    print(f"🀄 {claimer.name} claims Chow!")
                    meld = claimer.claim_chow(discard_tile, extra)
                    print(f"   Meld formed: {meld}")

                    new_discard = simulator_agent.select_discard(claimer)
                    print(f"   {claimer.name} discards: {new_discard}")
                    new_discard.state = 2
                    claimer.hand.remove(new_discard)
                    self.discard_pile.append(new_discard)

                # After a claim, next player is the one AFTER the claimer
                current_player = self.get_next_player(claimer)
            else:
                # No one claimed, add to discard pile
                self.discard_pile.append(discard_tile)
                current_player = self.get_next_player(player)

            turns_taken += 1

        return "continue"

    def print_winning_hand(self, player):
        """Print the winning hand details."""
        print(f"\n{'='*50}")
        print(f"🎉 {player.name}'s winning hand:")
        print(f"   Hand: {player.hand}")
        if player.exposed_melds:
            print(f"   Exposed melds: {player.exposed_melds}")
        print(f"{'='*50}\n")
