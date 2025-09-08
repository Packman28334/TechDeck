
from pathlib import Path

from show import Show
from cue import Cue
from p2p_networking import p2p_network_manager
from config import SOCKETIO_LOGGING

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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

@sio.on("select_show") # ask to load or create a different show
def select_show(sid, data):
    if p2p_network_manager.is_master_node:
        global show
        show = Show.load_or_create(data["title"])
        p2p_network_manager.broadcast_to_servers("selected_show", {"title": show.title})
        p2p_network_manager.broadcast_to_client("selected_show", {"title": show.title})
    else:
        p2p_network_manager.master_node.send("select_show", {"title": data["title"]})

@sio.on("selected_show") # load or create show that was just selected by the master node
def selected_show(sid, data):
    global show
    show = Show.load_or_create(data["title"])
    p2p_network_manager.broadcast_to_client("selected_show", show.title)

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
        p2p_network_manager.broadcast_to_client("blackout_state_changed", data)
    else:
        p2p_network_manager.master_node.send("blackout_change_state", data)

@sio.on("blackout_state_changed") # update local backend and client with blackout state
def blackout_state_changed(sid, data):
    show.blackout = data["new_state"]
    p2p_network_manager.broadcast_to_client("blackout_state_changed", data)

@sio.on("cue_list_changed") # update local backend and client with cue list
def cue_list_changed(sid, data):
    global show
    if show:
        show.cue_list.deserialize_to_self(data["cue_list"])

@sio.on("current_cue_changed") # update local backend and client with current cue
def current_cue_changed(sid, data):
    global show
    if show:
        show.current_cue = data["current_cue"]

@sio.on("cue_edited") # update local backend and client with new data for cue
def cue_edited(sid, data):
    global show
    if show:
        show.cue_list[data["index"]] = Cue.deserialize(data["cue"])

app.mount("/", StaticFiles(directory="frontend/static"))

if __name__ == '__main__':
    uvicorn.run("main:deploy_app", host="0.0.0.0", port=8383)
    p2p_network_manager.shutdown()