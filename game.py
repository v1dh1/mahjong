from deck import Deck
from player import Player
from tile import Tile
import random

import tile


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
                    
            print(index, [i], f"Tile: {i.suit} {i.tileno}, State: {i.state}")
            print("total state 1:", totalOne, "total state 2:", totalTwo, "total state 3:", totalThree, "\n") 
            print("none of the above:", none)
    def start(self):
        print("🔄 Shuffling deck...")
        self.deck.shuffle()
        self.assign_seats()
        self.assign_simulator() 
        print("🀄 Dealing initial hands...\n")

        # Deal 13 tiles to each player
        # Deal 13 tiles to each player
        for _ in range(13):
            for p in self.players:
                # Only simulator player's tiles are 1
                p.draw_tile(self.deck.draw(), is_simulator=p.simulator)

        # Dealer (Player 1) draws the 14th tile
        dealer = self.players[0]
        dealer.draw_tile(self.deck.draw(), is_simulator=dealer.simulator)

        print(f"Dealer starting hand (14 tiles):")
        print(dealer.hand, "\n")

        # Dealer discards the 14th tile
        discard = dealer.discard_tile()
        self.discard_pile.append(discard)

        
        print("length of discard tile:", len(self.discard_pile))
        print("length of deck", len(self.deck.tiles))        
        print("state of discarded tile:", discard.state)

       
        print(f"🗑️ Dealer discards: {discard}\n")



        print("Other players' hands:")
        for p in self.players[1:]:
            print(p, "\n")

        print("Game initialized — ready for next turn.")
        self.play_round()
        self.print_tile_states()
        

    

    def play_round(self):
        print ("⭕️ STARTING A ROUND ⭕️")
        # Define turn order
        turn_order = ["East", "North", "West", "South"]

        for wind in turn_order:
            # Find the player with this wind
            player = next(p for p in self.players if p.wind == wind)

            # Simulator message
            if player.simulator:
                print(f"🖥️ Simulator {player.name} is playing")

            # Draw a random tile with state 0
            available_tiles = [t for t in self.deck.tiles if t.state == 0]
            if not available_tiles:
                print("No more available tiles to draw!")
                break


            #---- RANDOM OPTION -----#
            tile_to_draw = random.choice(available_tiles)
            player.draw_tile(tile_to_draw)
            print("before deck", len(self.deck.tiles))
            # Remove the drawn tile from deck (already marked state=1 in draw_tile)
            self.deck.tiles.remove(tile_to_draw)
            print("after deck", len(self.deck.tiles))
            print(f"{player.name} draws {tile_to_draw}")
            
            discard_tile = random.choice(player.hand)
            discard_tile.state = 2
            print("player hand before discard", len(player.hand))
            player.hand.remove(discard_tile)
            print("player hand after discard", len(player.hand))
            self.discard_pile.append(discard_tile)
            print(f"{player.name} discards {discard_tile}\n")


            #-----NON RANDOM OPTION ----#

    def play_game(self):
        """Keep playing rounds until deck is empty or someone wins."""
        round_number = 1

        while True:
            print(f"\n=== Round {round_number} ===")

            # Play one round
            self.play_round()

            # Check for winner
            for p in self.players:
                if p.check_win():
                    print(f"🏆 {p.name} wins the game!")
                    return  # Stop the game

            # Check if there are any available tiles left
            available_tiles = [t for t in self.deck.tiles if t.state == 0]
            if not available_tiles:
                print("No more tiles left in the deck. Game ends in a draw.")
                return

            round_number += 1
            

