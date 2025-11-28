# Rule-based Chatbot

## Overview

A simple rule-based chatbot that matches user input against predefined patterns (using regular expressions) and returns corresponding responses. It demonstrates basic Natural Language Processing (NLP) concepts without machine learning.

## Features

- Pattern matching using `re` module.
- Fallback responses for unrecognized input.
- Simple command-line interface.

## Installation

1.  Navigate to the project directory:
    ```bash
    cd ArtificialIntelligence/RuleBasedChatbot
    ```
2.  Install dependencies (if any):
    ```bash
    # No external dependencies required
    ```

## Usage

Run the chatbot script:

```bash
python chatbot.py
```

## Implementation Details

The bot uses a list of `(pattern, response)` tuples. It iterates through the list and checks if the user's input matches a pattern.

## Future Improvements

- Add more complex patterns.
- Implement context tracking (remembering user name, etc.).
