"""Text Adventure Engine.

A text-based adventure game engine that loads world data from JSON files.
Players explore rooms, collect items, and interact with the environment
using simple text commands.

Commands:
    go/move/walk <direction>: Move to adjacent room
    look/l [item]: Examine room or item
    take/get/grab <item>: Pick up item
    inventory/i/inv: Show inventory
    help/h: Show available commands
    quit/q: Exit game
"""
import json
import os
import sys

class Game:
    """
    Docstring for Game.
    """
    def __init__(self, world_file):
        """
        Docstring for __init__.
        """
        self.world = self.load_world(world_file)
        self.current_room_id = self.world["start_room"]
        self.inventory = []
        self.running = True

    def load_world(self, file_path):
        """
        Docstring for load_world.
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: World file '{file_path}' not found.")
            sys.exit(1)

    def get_room(self, room_id):
        """
        Docstring for get_room.
        """
        return self.world["rooms"].get(room_id)

    def get_item_desc(self, item_id):
        """
        Docstring for get_item_desc.
        """
        return self.world["items"].get(item_id, "Unknown item.")

    def print_room(self):
        """
        Docstring for print_room.
        """
        room = self.get_room(self.current_room_id)
        print(f"\n=== {room['name']} ===")
        print(room['description'])
        if room['items']:
            print("You see:", ", ".join(room['items']))
        print("Exits:", ", ".join(room['exits'].keys()))

    def parse_command(self, command):
        """
        Docstring for parse_command.
        """
        parts = command.lower().split()
        if not parts:
            return

        verb = parts[0]
        noun = " ".join(parts[1:]) if len(parts) > 1 else None

        if verb in ["go", "move", "walk"]:
            self.cmd_go(noun)
        elif verb in ["look", "l"]:
            self.cmd_look(noun)
        elif verb in ["take", "get", "grab"]:
            self.cmd_take(noun)
        elif verb in ["inventory", "i", "inv"]:
            self.cmd_inventory()
        elif verb in ["help", "h"]:
            self.cmd_help()
        elif verb in ["quit", "exit", "q"]:
            self.running = False
        else:
            print("I don't understand that command.")

    def cmd_go(self, direction):
        """
        Docstring for cmd_go.
        """
        if not direction:
            print("Go where?")
            return

        room = self.get_room(self.current_room_id)
        if direction in room['exits']:
            self.current_room_id = room['exits'][direction]
            self.print_room()
        else:
            print("You can't go that way.")

    def cmd_look(self, noun):
        """
        Docstring for cmd_look.
        """
        if not noun:
            self.print_room()
        else:
            # Check if item in room or inventory
            room = self.get_room(self.current_room_id)
            if noun in room['items'] or noun in self.inventory:
                print(f"{noun}: {self.get_item_desc(noun)}")
            else:
                print("You don't see that here.")

    def cmd_take(self, item):
        """
        Docstring for cmd_take.
        """
        if not item:
            print("Take what?")
            return

        room = self.get_room(self.current_room_id)
        if item in room['items']:
            room['items'].remove(item)
            self.inventory.append(item)
            print(f"You picked up the {item}.")
        else:
            print("That item is not here.")

    def cmd_inventory(self):
        """
        Docstring for cmd_inventory.
        """
        if not self.inventory:
            print("You are not carrying anything.")
        else:
            print("You are carrying:", ", ".join(self.inventory))

    def cmd_help(self):
        """
        Docstring for cmd_help.
        """
        print("Commands:")
        print("  go [direction]  - Move to another room")
        print("  look [item]     - Inspect an item or the room")
        print("  take [item]     - Pick up an item")
        print("  inventory       - Show your items")
        print("  quit            - Exit the game")

    def run(self):
        """
        Docstring for run.
        """
        print("Welcome to the Adventure!")
        self.print_room()
        while self.running:
            try:
                command = input("\n> ")
                self.parse_command(command)
            except (EOFError, KeyboardInterrupt):
                self.running = False
        print("\nGoodbye!")

if __name__ == "__main__":
    world_file = "world.json"
    if len(sys.argv) > 1:
        world_file = sys.argv[1]
    
    # Ensure we look in the same directory as the script if not found
    if not os.path.exists(world_file):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        world_file = os.path.join(script_dir, "world.json")

    game = Game(world_file)
    game.run()
