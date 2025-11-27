# Cross-Platform Clipboard Sync

This example shows how to synchronize clipboards across devices on the same network using a FastAPI server and a Python client.

## Features

- FastAPI websocket server that registers clients and broadcasts clipboard updates.
- Optional HTTP registration endpoint for bookkeeping.
- UDP broadcast discovery so clients can find the server on a LAN without manual configuration.
- Symmetric encryption of clipboard payloads using `cryptography.Fernet`.
- Debounced, bidirectional clipboard sync powered by threads for local monitoring and async websockets for network I/O.

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt` (`fastapi`, `uvicorn`, `websockets`, `cryptography`, `pyperclip`).
- Clipboard backends:
  - **macOS**: the built-in pasteboard works out of the box.
  - **Linux**: install `xclip` or `xsel` so `pyperclip` can access the system clipboard.
  - **Windows**: works without extra setup when run from a console with clipboard access.

## Generating a shared key

All nodes must share the same Fernet key. Generate one once and reuse it:

```bash
python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
```

Set the result as `CLIPBOARD_SECRET` for both server and client.

## Running the server

```bash
export CLIPBOARD_SECRET="<your-fernet-key>"
# Optional overrides
export CLIPBOARD_SERVICE_PORT=8000
export CLIPBOARD_DISCOVERY_PORT=50505

python Practical/Cross-Platform\ Clipboard\ Sync/server.py
```

The server listens for websockets on `CLIPBOARD_SERVICE_PORT` and answers UDP broadcasts on `CLIPBOARD_DISCOVERY_PORT` with its host/port so clients can discover it automatically.

## Running a client

```bash
export CLIPBOARD_SECRET="<your-fernet-key>"
python Practical/Cross-Platform\ Clipboard\ Sync/client.py --client-id "laptop" --name "My Laptop"
```

- If `--host` is omitted, the client first sends a UDP broadcast to find the server. If no response arrives, it falls back to `127.0.0.1` and the configured `--port` (default `8000`).
- Clipboard changes are debounced to reduce chatter; remote updates are applied without echoing back to the origin.

Run the client on every machine you want to participate. Each instance keeps its own thread for clipboard monitoring while the asyncio loop handles websocket send/receive without blocking.

## Notes

- The FastAPI app exposes `/register` (POST) and `/clients` (GET) for quick diagnostics.
- To run behind HTTPS or across the internet, place the server behind a reverse proxy/SSH tunnel and point clients to the public host with `--host`.
- The discovery responder uses UDP broadcasts; ensure your firewall allows packets on `CLIPBOARD_DISCOVERY_PORT`.
