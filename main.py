
from pathlib import Path
import copy

from show import Show
from cue import Cue, CueModel, PartialCueModel
from p2p_networking import p2p_network_manager, Peer
from config import DEBUG_MODE, SOCKETIO_LOGGING

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException
from fastapi_utils.tasks import repeat_every
from socketio import AsyncServer, ASGIApp
import uvicorn

app = FastAPI()
sio = AsyncServer(async_mode="asgi", logger=SOCKETIO_LOGGING, engineio_logger=SOCKETIO_LOGGING)
p2p_network_manager.sio = sio
deploy_app = ASGIApp(sio, app)

show: Show | None = None

@app.get("/")
def index():
    return HTMLResponse(Path("frontend/index.html").read_text())

@app.on_event("startup")
@repeat_every(seconds=0.1)
async def update_polling_show_tasks() -> None:
    if show:
        show.update_polling_tasks()

# api routers are for losers. embrace the excessively long main.py file.

@app.get("/promote")
def promote():
    p2p_network_manager.set_master_node(p2p_network_manager.uuid, p2p_network_manager.uuid)

@sio.on("master_node")
def master_node(sid, data):
    p2p_network_manager.set_master_node(data["master_uuid"], data["fallback_master_uuid"])

@sio.on("blackout_change_state") # request state change for blackout
def blackout_change_state(sid, data):
    if p2p_network_manager.is_master_node:
        if not show:
            return
        match data["action"]:
            case "enter":
                show.enter_blackout()
            case "exit":
                show.exit_blackout()
            case "toggle":
                if show.blackout:
                    show.exit_blackout()
                else:
                    show.enter_blackout()
    else:
        p2p_network_manager.master_node.send("blackout_change_state", data)

@sio.on("blackout_state_changed") # update local backend and client with blackout state
def blackout_state_changed(sid, data):
    show.blackout = data["new_state"]
    p2p_network_manager.broadcast_to_client("blackout_state_changed", data)

app.mount("/", StaticFiles(directory="frontend/static"))

if __name__ == '__main__':
    uvicorn.run("main:deploy_app", host="0.0.0.0", port=8383)
    p2p_network_manager.shutdown()