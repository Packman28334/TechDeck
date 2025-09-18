
from pathlib import Path

from show import Show
from cue import Cue
from p2p_networking import p2p_network_manager
from config import SOCKETIO_LOGGING

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, HTMLResponse
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

@app.get("/component/{component}.js")
def component(component: str):
    content: str = """
        class CustomComponentElement_$COMPONENT$ extends HTMLElement {
            constructor() {
                super();

                const shadow = this.attachShadow({mode: "open"});

                shadow.innerHTML = `
                    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet" />
                    <link rel="stylesheet" href="/assets/global.css" />
                    <link rel="stylesheet" href="/component/$COMPONENT$.css" />
                    $CONTENT$
                `;
            }
        }
        customElements.define("td-$COMPONENT$", CustomComponentElement_$COMPONENT$);
    """.replace("$COMPONENT$", component).replace("$CONTENT$", Path(f"frontend/components/{component}/{component}.html").read_text())
    return Response(content=content, media_type="text/javascript")

@app.get("/component/{component}.css")
def component_style(component: str):
    return Response(content=Path(f"frontend/components/{component}/{component}.css").read_text(), media_type="text/css")

@app.on_event("startup")
@repeat_every(seconds=0.1)
async def update_polling_show_tasks() -> None:
    if show:
        show.update_polling_tasks()

# api routers are for losers. embrace the excessively long main.py file.

@sio.on("promote") # promote this node to the master node
def promote(sid, data=None):
    p2p_network_manager.set_master_node(p2p_network_manager.uuid, p2p_network_manager.uuid)

@sio.on("master_node") # update records of master and fallback master nodes
def master_node(sid, data):
    p2p_network_manager.set_master_node(data["master_uuid"], data["fallback_master_uuid"])

@sio.on("select_show") # ask to load or create a different show
async def select_show(sid, title):
    if p2p_network_manager.is_master_node:
        global show
        show = Show.load_or_create(title)
        p2p_network_manager.broadcast_to_servers("selected_show", show.title)
        await p2p_network_manager.broadcast_to_client("selected_show", show.title)
    else:
        p2p_network_manager.master_node.send("select_show", title)

@sio.on("selected_show") # load or create show that was just selected by the master node
async def selected_show(sid, title):
    global show
    show = Show.load_or_create(title)
    await p2p_network_manager.broadcast_to_client("selected_show", show.title)

@sio.on("is_show_loaded") # inform client of whether a show is loaded
async def is_show_loaded(sid, data=None):
    global show
    if p2p_network_manager.master_node: # if there is a master node
        await p2p_network_manager.broadcast_to_client("is_show_loaded", {"loaded": show.title if show else False, "master_node_present": True})
    else:
        await p2p_network_manager.broadcast_to_client("is_show_loaded", {"loaded": False, "master_node_present": False})

@sio.on("blackout_change_state") # request state change for blackout
async def blackout_change_state(sid, data):
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
        await p2p_network_manager.broadcast_to_client("blackout_state_changed", {"new_state": show.blackout})
    else:
        p2p_network_manager.master_node.send("blackout_change_state", data)

@sio.on("blackout_state_changed") # update local backend and client with blackout state
async def blackout_state_changed(sid, data):
    show.blackout = data["new_state"]
    await p2p_network_manager.broadcast_to_client("blackout_state_changed", data)

@sio.on("cue_list_changed") # update local backend and client with cue list
def cue_list_changed(sid, data):
    global show
    if show:
        show.save(show.title, backup=True)
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
