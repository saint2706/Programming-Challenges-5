# Command Palette for Your OS

A lightweight, cross-platform command palette that stays in the background, listens for a global hotkey, and pops up a PyQt dialog where you can search and run pluggable actions.

## Features

- Global hotkey (default `Ctrl+Shift+P`) opens a minimal palette even when other apps have focus.
- System tray icon with quick actions to open the palette, reload plugins, or quit.
- Plugin-based architecture: drop Python scripts into `plugins/` and they are auto-discovered.
- Live filtering as you type with a list of matching plugins.
- Per-plugin error isolation so failures do not crash the palette.
- Sample plugins for opening URLs, searching files, and running shell commands.

## Running locally

1. Install dependencies (PyQt6 and keyboard are the only new ones):

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Start the palette:

   ```bash
   python "Practical/Command Palette for Your OS/command_palette.py"
   ```

3. Press **Ctrl+Shift+P** (or use the tray menu) to open the palette window.

If global hooks are unavailable on your platform, you can still launch the palette from the tray icon or run the script in focus and press Enter in the dialog.

## Plugin interface

A plugin is a Python file placed in `Practical/Command Palette for Your OS/plugins/` that exposes:

- `METADATA`: a dictionary with `name`, `description`, and optional `keywords`.
- `execute(query: str) -> Optional[str]`: called when the plugin is run. Return text to display in a dialog (or `None` if no message is needed). Exceptions are caught and surfaced as errors without crashing the app.

Example template:

```python
METADATA = {
    "name": "My Plugin",
    "description": "What this plugin does",
    "keywords": ["tag", "another"],
}


def execute(query: str):
    # Do something useful
    return "Done!"
```

### Included plugins

- **Open URL**: Opens a URL or search term in the default browser.
- **Search Files**: Finds filenames under your home folder matching the query (first 15 hits).
- **Run Shell Command**: Executes a shell command and shows stdout/stderr.

## Cross-platform startup hints

- **Windows**: Create a shortcut to `command_palette.py` in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`, or pin the script with a Python interpreter to the taskbar.
- **macOS**: Add the script as a Login Item (System Settings → General → Login Items) or wrap it with `launchctl` using a `.plist` in `~/Library/LaunchAgents`.
- **Linux**: Create a `.desktop` entry in `~/.config/autostart/` pointing to the script, or use `systemd --user` with a service that calls the Python entry point.

Because the app uses a system tray icon, it can live unobtrusively after autostart. The tray menu lets you reopen the palette if the global hotkey is not available.

## Notes on hotkeys and permissions

- The `keyboard` library may need accessibility permissions on macOS and may require running under `sudo` on some Linux distributions to capture global shortcuts.
- If the hotkey cannot be registered, the app will log an error and continue running in the tray so you can still trigger the palette manually.
