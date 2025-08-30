
from pathlib import Path
import copy

from show import Show
from cue import Cue, CueModel, PartialCueModel
from p2p_networking import p2p_network_manager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException
from fastapi_utils.tasks import repeat_every
from socketio import AsyncServer, ASGIApp
import uvicorn

app = FastAPI()
sio = AsyncServer(async_mode="asgi", logger=True, engineio_logger=True)
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

@sio.on("master_node")
def master_node(sid, data):
    p2p_network_manager.master_node = p2p_network_manager.get_peer_by_uuid(data["master_uuid"])
    p2p_network_manager.fallback_master = p2p_network_manager.get_peer_by_uuid(data["fallback_master_uuid"])

app.mount("/", StaticFiles(directory="frontend/static"))

if __name__ == '__main__':
    uvicorn.run("main:deploy_app", host="0.0.0.0", port=8383)
    p2p_network_manager.shutdown()