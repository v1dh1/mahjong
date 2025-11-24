from deck import Deck
from player import Player
from tile import Tile
import random
from agent import MahjongAgent
import tile
from monte_carlo_ai import MonteCarloAI



#to do
# Vidhi working on Deck States DONEEEEEE
# Elle working on running the game  - figure out how to simulat other player's choices
# Optimization code, call that in this simulator
    #reward function
# Separate file where we run this n times, and calculate the win rate

# figure out what and where nevedhaa to add to 

class Game:
    def __init__(self):
        self.deck = Deck()
        print ("DECK CREATED")
        print("length of deck", len(Deck().tiles))
        self.players = [Player(f"Player {i+1}") for i in range(4)]
        self.discard_pile = []
        self.mc_ai = MonteCarloAI(simulations=100)

    def assign_seats(self):
        print ("💺 Randomly assign seats (wind directions) to the 4 players.")
        winds = ["East", "South", "West", "North"]
        #shuffling the directions
        random.shuffle(winds)

        for player, wind in zip(self.players, winds):
            # assign each player to a wind (their order to play in) 
            # zip pairs elements from 2 or more lists together, player 1 gets the first item, player 2 the second, and so forth
            player.wind = wind

        # print it out 
        print("🎲 Seats assigned:")
        for p in self.players:
            print(f"{p.name} → {p.wind}")

    def assign_simulator(self):
        print("Assigning one of the players as the simulator")
        simulator_player = random.choice(self.players)
        simulator_player.simulator = True
        print(f"🖥️ Simulator: {simulator_player.name} -> {simulator_player.wind}")


#####FINDING STATES!!!!!!
    def print_tile_states(self):
            print("\n--- Deck ---")
            for t in self.deck.tiles:
                print(t)

            print("\n--- Players' hands ---")
            for p in self.players:
                for t in p.hand:
                    print(f"{p.name}: {t}")

            print("\n--- Discard pile ---")
            for t in self.discard_pile:
                print(t)
            
            totalOne = 0
            totalTwo = 0
            totalThree = 0
            none = []
            for index, i in enumerate(self.deck.all_tiles): #all_tiles has all the states 
                if i.state == 0:
                    totalOne += 1
                elif i.state == 1:
                    totalTwo += 1
                elif i.state == 2:
                    totalThree += 1
                elif i.state != 0 and i.state !=1 and i.state !=2:
                    none.append(i)
                    
            print(index, [i], f"Tile: {i.suit} {i.value}, State: {i.state}")
            print("total state 1:", totalOne, "total state 2:", totalTwo, "total state 3:", totalThree, "\n") 
            print("none of the above:", none)

            
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
        dealer = self.players[0]
        dealer.draw_tile(self.deck.draw(), is_simulator=dealer.simulator)

        print(f"Dealer starting hand (14 tiles): {dealer.hand}\n")

        # Dealer discards the 14th tile
        discard = dealer.discard_tile()
        self.discard_pile.append(discard)
        print(f"🗑️ Dealer discards: {discard}\n")

        print("Game initialized — starting automated simulation...\n")
        self.play_game()

    def play_game(self):
        """Automated game loop until deck empty or someone wins."""
        round_number = 1
        simulator_agent = MahjongAgent(self)

        while True:
            print(f"\n=== Round {round_number} ===")
            self.play_round(simulator_agent)

            # Check for winner
            for p in self.players:
                if p.check_win():
                    print(f"🏆 {p.name} wins the game!")
                    return

            # Check if there are any available tiles left
            available_tiles = [t for t in self.deck.tiles if t.state == 0]
            if not available_tiles:
                print("No more tiles left in the deck. Game ends in a draw.")
                return

            round_number += 1


    ## AI ATTEMPT
    def get_ai_move(self, player):
        url = "http://localhost:80/api/ai_move"
         # Build the game state for AI
        game_state = {
        "hand": [str(t) for t in player.hand],  # convert Tile objects to strings
        "discard_pile": [str(t) for t in self.discard_pile],
        "round": 1  # you can track round numbers if you want
        }
        try:
            response = requests.post(url, json={"game_state": game_state})
            response.raise_for_status()  # raise an exception if HTTP error
            move = response.json()["move"]  # e.g., "discard 5m"
            print("!!!!!!ai worked!!!!!!")
            print("AI move:", response.json())
            return move  # <-- indented inside try
        except Exception as e:
            print(f"⚠️ AI request failed: {e}")
            # fallback to random discard
            random_tile = random.choice(player.hand)
            return f"discard {str(random_tile)}"

    def play_round(self, simulator_agent):
        """Each player takes a turn. Simulator uses Q-function."""
        turn_order = ["East", "North", "West", "South"]

        for wind in turn_order:
            player = next(p for p in self.players if p.wind == wind)

            # Draw tile
            tile_to_draw = self.deck.draw_random_state0()
            if not tile_to_draw:
                print("No more available tiles to draw! Wall empty.")
                return

            player.draw_tile(tile_to_draw, is_simulator=player.simulator)
            print(f"{player.name} draws {tile_to_draw}")


            # Decide discard
            if player.simulator:
                discard_tile = simulator_agent.select_discard(player)
                print(f"🖥️ Simulator {player.name} chooses discard: {discard_tile}")

            else:
                discard_tile = self.mc_ai.choose_discard(player, self)
                print(f"{player.name} discards using Monte Carlo AI: {discard_tile}")
                #ai_move = self.get_ai_move(player)  # <-- call AI
                #discard_tile_code = ai_move.split()[1]  # get "5m" from "discard 5m"
                #discard_tile = next(t for t in player.hand if str(t) == discard_tile_code)
                #print(f"{player.name} discards using AI: {discard_tile}")
            #if player.simulator:
                #discard_tile = simulator_agent.select_discard(player)
                #print(f"🖥️ Simulator {player.name} chooses discard: {discard_tile}")
            #else:
                #discard_tile = random.choice(player.hand)
                #print(f"{player.name} discards randomly: {discard_tile}")

            discard_tile.state = 2
            player.hand.remove(discard_tile)
            self.discard_pile.append(discard_tile)
            

