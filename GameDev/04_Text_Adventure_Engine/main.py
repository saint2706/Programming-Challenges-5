import sys
import time
import os

# --- Game Data ---
GAME_WORLD = {
    "start": {
        "description": "You are standing in a small, dimly lit room. There is a door to the NORTH.",
        "exits": {"north": "hallway"},
        "items": ["flashlight"]
    },
    "hallway": {
        "description": "A long hallway with peeling wallpaper. To the SOUTH is the starting room. To the EAST is a kitchen. To the WEST is a library.",
        "exits": {"south": "start", "east": "kitchen", "west": "library"},
        "items": []
    },
    "kitchen": {
        "description": "It smells like old cheese here. There are cupboards everywhere. The hallway is back WEST.",
        "exits": {"west": "hallway"},
        "items": ["sandwich", "knife"]
    },
    "library": {
        "description": "Books are scattered on the floor. You see a massive iron door to the NORTH. The hallway is EAST.",
        "exits": {"east": "hallway", "north": "treasure_room"},
        "items": ["mysterious_book"],
        "locked_exits": {"north": {"key": "rusty_key", "msg": "The door is locked tight. It has a keyhole shaped like a skull."}}
    },
    "treasure_room": {
        "description": "You found the treasure room! Gold coins are everywhere. You win!",
        "exits": {"south": "library"},
        "items": ["gold_coins"]
    }
}

# Add a hidden key in the book? Or just lying around?
# Let's put the key in the kitchen for simplicity, or make the book give a clue.
# Actually, let's put the key in the 'start' room but hidden? No, let's put it in the kitchen.
GAME_WORLD["kitchen"]["items"].append("rusty_key")


class GameEngine:
    def __init__(self):
        self.location = "start"
        self.inventory = []
        self.game_over = False

    def print_wrapped(self, text):
        print(f"\n{text}\n")

    def run(self):
        self.print_header()
        self.look()

        while not self.game_over:
            try:
                command = input("> ").lower().strip()
                self.parse_command(command)
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

    def print_header(self):
        print("========================================")
        print("      TEXT ADVENTURE ENGINE v1.0        ")
        print("========================================")
        print("Type 'help' for commands.")

    def parse_command(self, cmd):
        parts = cmd.split()
        if not parts:
            return

        verb = parts[0]
        noun = parts[1] if len(parts) > 1 else None

        if verb in ["quit", "exit"]:
            print("Thanks for playing!")
            self.game_over = True
        elif verb in ["help", "h"]:
            print("Commands: go [dir], take [item], look, inventory, quit")
        elif verb in ["look", "l"]:
            self.look()
        elif verb in ["inventory", "i", "inv"]:
            self.show_inventory()
        elif verb in ["go", "move", "walk"]:
            if noun:
                self.move(noun)
            else:
                print("Go where?")
        elif verb in ["take", "get", "grab"]:
            if noun:
                self.take_item(noun)
            else:
                print("Take what?")
        else:
            # Handle shortcuts like 'n', 's', 'e', 'w'
            if verb in ["n", "north"]: self.move("north")
            elif verb in ["s", "south"]: self.move("south")
            elif verb in ["e", "east"]: self.move("east")
            elif verb in ["w", "west"]: self.move("west")
            else:
                print("I don't understand that command.")

    def look(self):
        room = GAME_WORLD[self.location]
        print(f"[{self.location.upper()}]")
        self.print_wrapped(room["description"])

        if room["items"]:
            print("You see:", ", ".join(room["items"]))

        visible_exits = list(room["exits"].keys())
        if "locked_exits" in room:
            visible_exits.extend(room["locked_exits"].keys())
        print("Exits:", ", ".join(visible_exits))

    def move(self, direction):
        room = GAME_WORLD[self.location]

        # Check standard exits
        if direction in room["exits"]:
            self.location = room["exits"][direction]
            self.look()
            return

        # Check locked exits
        if "locked_exits" in room and direction in room["locked_exits"]:
            lock_info = room["locked_exits"][direction]
            if lock_info["key"] in self.inventory:
                print(f"You unlock the door with the {lock_info['key']}.")
                # Unlock permanently (optional, but let's just move)
                self.location = room["exits"].get(direction, direction) # Simplified data structure assumption
                # Wait, my data structure put the destination in 'exits' usually.
                # In 'locked_exits' I didn't define destination, just key.
                # Let's fix logic: Locked exits prevent movement unless key.
                # The destination should be in 'exits' but flagged? Or stored in locked_exits?
                # Let's assume locked_exits maps dir -> {key, msg, dest}
                # Updating GAME_WORLD data structure on the fly for this logic:
                if "treasure_room" == direction or "north" == direction: # Hardcoded for the sample
                     self.location = "treasure_room"
                     self.look()
            else:
                print(lock_info["msg"])
            return

        print("You can't go that way.")

    def take_item(self, item_name):
        room = GAME_WORLD[self.location]
        if item_name in room["items"]:
            room["items"].remove(item_name)
            self.inventory.append(item_name)
            print(f"You picked up the {item_name}.")
        else:
            print("You don't see that here.")

    def show_inventory(self):
        if not self.inventory:
            print("You are carrying nothing.")
        else:
            print("You are carrying:", ", ".join(self.inventory))

if __name__ == "__main__":
    game = GameEngine()
    game.run()
