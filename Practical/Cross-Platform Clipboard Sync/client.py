import argparse
import asyncio
import json
import os
import socket
import threading
import time
from typing import Optional

import pyperclip
import requests
import websockets
from cryptography.fernet import Fernet

DISCOVERY_PORT = int(os.environ.get("CLIPBOARD_DISCOVERY_PORT", 50505))
SERVICE_PORT = int(os.environ.get("CLIPBOARD_SERVICE_PORT", 8000))
SECRET_KEY = os.environ.get("CLIPBOARD_SECRET", "")


def discover_server(timeout: float = 2.0) -> Optional[tuple[str, int]]:
    message = b"DISCOVER_CLIPBOARD"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        sock.sendto(message, ("255.255.255.255", DISCOVERY_PORT))
        try:
            data, addr = sock.recvfrom(1024)
            payload = json.loads(data.decode())
            return payload.get("host") or addr[0], int(payload.get("port", SERVICE_PORT))
        except (socket.timeout, json.JSONDecodeError, OSError):
            return None


def register_client(base_url: str, client_id: str, display_name: Optional[str]) -> None:
    try:
        requests.post(
            f"{base_url}/register",
            json={"client_id": client_id, "display_name": display_name},
            timeout=3,
        )
    except requests.RequestException:
        pass


def clipboard_watcher(loop: asyncio.AbstractEventLoop, queue: asyncio.Queue, debounce: float) -> None:
    last_text = pyperclip.paste()
    last_sent_at = 0.0
    while True:
        try:
            current = pyperclip.paste()
            if current != last_text and (time.time() - last_sent_at) >= debounce:
                last_text = current
                last_sent_at = time.time()
                asyncio.run_coroutine_threadsafe(queue.put(current), loop)
        except pyperclip.PyperclipException:
            pass
        time.sleep(0.4)


def set_clipboard(text: str) -> None:
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException:
        pass


async def send_clipboard_updates(
    ws: websockets.WebSocketClientProtocol,
    queue: asyncio.Queue,
    fernet: Fernet,
    client_id: str,
) -> None:
    while True:
        text = await queue.get()
        payload = json.dumps({"client_id": client_id, "content": text, "sent_at": time.time()})
        await ws.send(fernet.encrypt(payload.encode()).decode())


async def receive_updates(ws: websockets.WebSocketClientProtocol, fernet: Fernet, ignore_value: str) -> None:
    last_text = ignore_value
    async for message in ws:
        try:
            decrypted = fernet.decrypt(message.encode())
            payload = json.loads(decrypted.decode())
            content = payload.get("content")
            if content and content != last_text:
                last_text = content
                set_clipboard(content)
        except Exception:
            continue


async def connect_and_sync(host: str, port: int, client_id: str, display_name: Optional[str]) -> None:
    if not SECRET_KEY:
        raise RuntimeError("Set CLIPBOARD_SECRET to the shared Fernet key before running the client")

    fernet = Fernet(SECRET_KEY)
    queue: asyncio.Queue[str] = asyncio.Queue()

    base_url = f"http://{host}:{port}"
    register_client(base_url, client_id, display_name)

    websocket_url = f"ws://{host}:{port}/ws?client_id={client_id}"
    async with websockets.connect(websocket_url, ping_interval=20, ping_timeout=20) as websocket:
        send_task = asyncio.create_task(send_clipboard_updates(websocket, queue, fernet, client_id))
        receive_task = asyncio.create_task(receive_updates(websocket, fernet, pyperclip.paste()))

        watcher_thread = threading.Thread(
            target=clipboard_watcher,
            args=(asyncio.get_running_loop(), queue, 0.5),
            daemon=True,
        )
        watcher_thread.start()

        await asyncio.gather(send_task, receive_task)


def main():
    parser = argparse.ArgumentParser(description="Bidirectional clipboard sync client")
    parser.add_argument("--host", help="Clipboard server host (discovery used if omitted)")
    parser.add_argument("--port", type=int, default=SERVICE_PORT, help="Clipboard server port")
    parser.add_argument("--client-id", default=socket.gethostname(), help="Unique client identifier")
    parser.add_argument("--name", default=None, help="Human-friendly display name")
    args = parser.parse_args()

    target_host = args.host
    target_port = args.port
    if not target_host:
        discovered = discover_server()
        if discovered:
            target_host, target_port = discovered
        else:
            target_host = f"127.0.0.1"

    print(f"Connecting to clipboard server at {target_host}:{target_port}")

    asyncio.run(connect_and_sync(target_host, target_port, args.client_id, args.name))


if __name__ == "__main__":
    main()
