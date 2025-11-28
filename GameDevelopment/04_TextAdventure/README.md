# Text Adventure Engine

A simple text-based adventure game engine with JSON-defined worlds.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [World Format](#world-format)

## ✨ Features

- JSON-based world definition
- Room navigation with compass directions
- Item pickup and inventory system
- Parser for natural language commands
- Extensible world structure

## 💻 Installation

Ensure you have Python 3.8+ installed. No additional dependencies required.

## 🚀 Usage

### Running the Game

```bash
cd GameDevelopment/04_TextAdventure
python main.py
```

## 🎮 Commands

| Command          | Description                                     |
| :--------------- | :---------------------------------------------- |
| `go <direction>` | Move to another room (north, south, east, west) |
| `look`           | Look around the current room                    |
| `take <item>`    | Pick up an item                                 |
| `inventory`      | View your inventory                             |
| `help`           | Show available commands                         |
| `quit`           | Exit the game                                   |

## 📄 World Format

The world is defined in `world.json`:

```json
{
  "start_room": "entrance",
  "rooms": {
    "entrance": {
      "name": "Room Name",
      "description": "Room description",
      "exits": { "north": "other_room" },
      "items": ["item_id"]
    }
  },
  "items": {
    "item_id": "Item description"
  }
}
```
