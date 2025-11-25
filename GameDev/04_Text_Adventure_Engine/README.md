# Text Adventure Engine

A data-driven text adventure engine implemented in pure Python (CLI).

## Features
- **Data-Driven:** Game world (rooms, items) is defined in a dictionary structure (could easily be JSON).
- **Parser:** Supports standard commands: `go [direction]`, `take [item]`, `look`, `inventory`, `help`, `quit`.
- **State:** Tracks player location and inventory.

## How to Run

1.  Ensure you have Python installed.
2.  Run the game:
    ```bash
    python main.py
    ```

## Controls
- Type commands and press Enter.
- Examples:
    - `go north`
    - `take rusty_key`
    - `look`
    - `i` (for inventory)
    - `quit`
