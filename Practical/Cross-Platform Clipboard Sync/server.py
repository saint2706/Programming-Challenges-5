"""
Project implementation.
"""

import json
import os
import socket
import threading
import time
from typing import Dict, Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DISCOVERY_PORT = int(os.environ.get("CLIPBOARD_DISCOVERY_PORT", 50505))
SERVICE_PORT = int(os.environ.get("CLIPBOARD_SERVICE_PORT", 8000))
SECRET_KEY = os.environ.get("CLIPBOARD_SECRET")

if not SECRET_KEY:
    raise RuntimeError("CLIPBOARD_SECRET environment variable is required")

fernet = Fernet(SECRET_KEY)

app = FastAPI(title="Clipboard Sync Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    """
    Docstring for RegisterRequest.
    """
    client_id: str
    display_name: Optional[str] = None


class RegisteredClient(BaseModel):
    """
    Docstring for RegisteredClient.
    """
    client_id: str
    display_name: Optional[str] = None
    connected: bool = False


discovery_running = threading.Event()
clients: Dict[str, RegisteredClient] = {}
connections: Dict[str, WebSocket] = {}


@app.post("/register", response_model=RegisteredClient)
async def register_client(payload: RegisterRequest) -> RegisteredClient:
    """
    Docstring for register_client.
    """
    client = RegisteredClient(
        client_id=payload.client_id, display_name=payload.display_name, connected=False
    )
    clients[payload.client_id] = client
    return client


@app.get("/clients")
async def list_clients() -> Dict[str, RegisteredClient]:
    """
    Docstring for list_clients.
    """
    return clients


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Docstring for websocket_endpoint.
    """
    client_id = websocket.query_params.get("client_id") or f"anon-{int(time.time())}"
    await websocket.accept()
    connections[client_id] = websocket
    if client_id not in clients:
        clients[client_id] = RegisteredClient(client_id=client_id, connected=True)
    else:
        clients[client_id].connected = True

    try:
        while True:
            text = await websocket.receive_text()
            try:
                decrypted = fernet.decrypt(text.encode())
            except InvalidToken:
                continue

            try:
                payload = json.loads(decrypted.decode())
            except json.JSONDecodeError:
                continue

            payload["received_by"] = client_id
            payload["received_at"] = time.time()
            message = fernet.encrypt(json.dumps(payload).encode()).decode()

            for other_id, other_ws in list(connections.items()):
                if other_id == client_id:
                    continue
                try:
                    await other_ws.send_text(message)
                except Exception:
                    await _disconnect_client(other_id)
    except WebSocketDisconnect:
        pass
    finally:
        await _disconnect_client(client_id)


async def _disconnect_client(client_id: str) -> None:
    """
    Docstring for _disconnect_client.
    """
    ws = connections.pop(client_id, None)
    if ws:
        try:
            await ws.close()
        except Exception:
            pass
    if client_id in clients:
        clients[client_id].connected = False


def _local_ip() -> str:
    """
    Docstring for _local_ip.
    """
    sock: Optional[socket.socket] = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        if sock:
            sock.close()
    return ip


def _discovery_server(host: str, port: int, service_port: int) -> None:
    """
    Docstring for _discovery_server.
    """
    discovery_running.set()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    response = json.dumps({"host": _local_ip(), "port": service_port}).encode()
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data and data.decode().strip().upper() == "DISCOVER_CLIPBOARD":
                sock.sendto(response, addr)
        except Exception:
            time.sleep(0.1)


def start_discovery_server(host: str = "0.0.0.0") -> None:
    """
    Docstring for start_discovery_server.
    """
    if discovery_running.is_set():
        return
    thread = threading.Thread(
        target=_discovery_server,
        args=(host, DISCOVERY_PORT, SERVICE_PORT),
        daemon=True,
        name="discovery-server",
    )
    thread.start()


start_discovery_server()


if __name__ == "__main__":
    import uvicorn

    start_discovery_server()
    uvicorn.run("server:app", host="0.0.0.0", port=SERVICE_PORT, reload=False)
