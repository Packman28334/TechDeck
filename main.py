
from pathlib import Path
import os
import hashlib
import base64
import requests
from math import ceil

from show import Show
from cue import Cue
from p2p_networking import p2p_network_manager
from config import DUMMY_MODE, DEBUG_MODE, SOCKETIO_LOGGING

from fastapi import FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, HTMLResponse
from fastapi_utils.tasks import repeat_every
from socketio import AsyncServer, ASGIApp
import uvicorn

app = FastAPI()
sio = AsyncServer(async_mode="asgi", logger=SOCKETIO_LOGGING, engineio_logger=SOCKETIO_LOGGING)
p2p_network_manager.sio = sio
deploy_app = ASGIApp(sio, app)

# i need to rebuild everything asap this code is awful and i hate it
current_audio_transfers: dict[str, list[int | set[int] | dict[int, bytes]]] = {} # {filename: [total # of chunks, list of chunks that we have, values of each chunk]}
current_backdrop_transfers: dict[str, list[int | set[int] | dict[int, bytes]]] = {} # {filename: [total # of chunks, list of chunks that we have, values of each chunk]}

show: Show | None = None

def hash_of_file(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

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
                    <link href="/assets/css/material_symbols.css" rel="stylesheet" />
                    <link rel="stylesheet" href="/assets/css/global.css" />
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

@app.post("/import-cue-sheet")
def import_cue_sheet(sheet: UploadFile):
    contents: str = sheet.file.read().decode("utf-8")
    if p2p_network_manager.is_master_node:
        if show:
            show.cue_list.import_cue_sheet(contents)
    else:
        requests.post(f"http://{p2p_network_manager.master_node.ip_address}:{p2p_network_manager.master_node.port}/import-cue-sheet",
            files={"sheet": sheet.file},
            headers={"Content-Type": "multipart/form-data"}
        )

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

@sio.on("server_ping") # recieve ping from another node and send it back
def server_ping(sid, data):
    print(filter(lambda x: x.uuid == data["my_uuid"], p2p_network_manager.peers)[0]) # TODO: finish

@sio.on("client_ping") # recieve ping from client and send it back
async def client_ping(sid, data):
    await p2p_network_manager.broadcast_to_client_async("client_ping", data)

@sio.on("shutdown_network") # request a shutdown of the Tech Deck network
def shutdown_network(sid, data=None):
    if p2p_network_manager.is_master_node:
        p2p_network_manager.broadcast_to_servers("shutdown_now")
        print("Shutting down now")
        if not DUMMY_MODE:
            os.system("shutdown now")
    else:
        p2p_network_manager.master_node.send("shutdown_network")

@sio.on("shutdown_now") # shutdown this peer
def shutdown_now(sid, data=None):
    print("Shutting down now")
    if not DUMMY_MODE:
        os.system("shutdown now")

@sio.on("save") # save the show
def save(sid, data=None):
    if not p2p_network_manager.is_master_node:
        p2p_network_manager.master_node.send("save")
    if show:
        show.save(show.title)

@sio.on("select_show") # ask to load or create a different show
async def select_show(sid, title):
    if p2p_network_manager.is_master_node:
        global show
        show = Show.load_or_create(title)
        p2p_network_manager.broadcast_to_servers("selected_show", show.title)
        await p2p_network_manager.broadcast_to_client_async("selected_show", show.title)
    else:
        p2p_network_manager.master_node.send("select_show", title)

@sio.on("selected_show") # load or create show that was just selected by the master node
async def selected_show(sid, title):
    global show
    show = Show.load_or_create(title)
    p2p_network_manager.master_node.send("get_audio_library_entries")
    await p2p_network_manager.broadcast_to_client_async("selected_show", show.title)

@sio.on("is_show_loaded") # inform client of whether a show is loaded
async def is_show_loaded(sid, data=None):
    global show
    if p2p_network_manager.master_node: # if there is a master node
        await p2p_network_manager.broadcast_to_client_async("is_show_loaded", {"loaded": show.title if show else False, "master_node_present": True})
    else:
        await p2p_network_manager.broadcast_to_client_async("is_show_loaded", {"loaded": False, "master_node_present": False})

@sio.on("subsystem_state_changed")
def subsystem_state_changed(sid, states):
    global show
    if show:
        show.update_subsystem_states(states)

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
    else:
        p2p_network_manager.master_node.send("blackout_change_state", data)

@sio.on("blackout_state_changed") # update local backend and client with blackout state
async def blackout_state_changed(sid, data):
    show.blackout = data["new_state"]
    await p2p_network_manager.broadcast_to_client_async("blackout_state_changed", data)

@sio.on("get_blackout_state") # get the state of the blackout for the client
async def get_blackout_state(sid, data=None):
    await p2p_network_manager.broadcast_to_client_async("blackout_state_changed", {"new_state": show.blackout})

@sio.on("save_state_changed") # update local backend and client with save state
async def save_state_changed(sid, new_state):
    show.cue_list.unsaved = new_state
    await p2p_network_manager.broadcast_to_client_async("save_state_changed", new_state)

@sio.on("get_save_state") # get the save state
async def get_save_state(sid, data=None):
    if show:
        p2p_network_manager.broadcast_to_servers("save_state_changed", show.cue_list.unsaved)
        await p2p_network_manager.broadcast_to_client_async("save_state_changed", show.cue_list.unsaved)

@sio.on("cue_list_changed") # update local backend and client with cue list
def cue_list_changed(sid, data):
    global show
    if show:
        show.save(show.title, backup=True)
        show.cue_list.deserialize_to_self(data["cue_list"])

@sio.on("current_cue_changed") # update local backend and client with current cue
async def current_cue_changed(sid, data):
    global show
    if show:
        show.current_cue = data["index"]
        await p2p_network_manager.broadcast_to_client_async("current_cue_changed", data)

@sio.on("cue_edited") # update local backend and client with new data for cue
def cue_edited(sid, data):
    global show
    if show:
        show.cue_list[data["index"]] = Cue.deserialize(data["cue"])

@sio.on("get_cues") # broadcast current cue list
async def get_cues(sid, data=None):
    global show
    if show:
        p2p_network_manager.broadcast_to_servers("cue_list_changed", {"cue_list": show.cue_list.serialize()})
        await p2p_network_manager.broadcast_to_client_async("cue_list_changed", {"cue_list": show.cue_list.serialize()})

@sio.on("get_current_cue") # broadcast the current cue
async def get_current_cue(sid, data=None):
    global show
    if show:
        p2p_network_manager.broadcast_to_servers("current_cue_changed", {"index": show.current_cue})
        await p2p_network_manager.broadcast_to_client_async("current_cue_changed", {"index": show.current_cue})

@sio.on("add_cue") # add a cue to the list
def add_cue(sid, data):
    global show
    if show:
        if p2p_network_manager.is_master_node:
            show.cue_list.append(Cue.deserialize(data))
        else:
            p2p_network_manager.master_node.send("add_cue", data)

@sio.on("edit_cue") # edit a cue at an index
def edit_cue(sid, data):
    global show
    if show:
        if p2p_network_manager.is_master_node:
            show.cue_list[data["index"]] = Cue.deserialize(data["cue"])
        else:
            p2p_network_manager.master_node.send("edit_cue", data)

@sio.on("delete_cue") # delete cue at an index
def delete_cue(sid, index):
    global show
    if show:
        if p2p_network_manager.is_master_node:
            show.cue_list.pop(index)
        else:
            p2p_network_manager.master_node.send("delete_cue", index)

@sio.on("jump_to_cue") # jump to cue
def jump_to_cue(sid, cue_index):
    global show
    if p2p_network_manager.is_master_node:
        if show:
            show.jump_to_cue(cue_index)
    else:
        p2p_network_manager.master_node.send("jump_to_cue", cue_index)

@sio.on("move_cues_up") # move cues up
def move_cues_up(sid, cues):
    global show
    if p2p_network_manager.is_master_node:
        if show:
            show.cue_list.move_multiple_up(cues, 1)
    else:
        p2p_network_manager.master_node.send("move_cues_up", cues)

@sio.on("move_cues_down") # move cues down
def move_cues_down(sid, cues):
    global show
    if p2p_network_manager.is_master_node:
        if show:
            show.cue_list.move_multiple_down(cues, 1)
    else:
        p2p_network_manager.master_node.send("move_cues_down", cues)

@sio.on("backdrop_changed") # change the backdrop
async def backdrop_changed(sid, data):
    await p2p_network_manager.broadcast_to_client_async("backdrop_changed", data)

@sio.on("get_current_backdrop") # broadcast the current backdrop
def get_current_backdrop(sid, data=None):
    if p2p_network_manager.is_master_node:
        if show:
            p2p_network_manager.broadcast_to_servers("backdrop_changed", {"is-video": show.scenery_subsystem.is_video, "filename": show.scenery_subsystem.media_filename})
            p2p_network_manager.broadcast_to_client("backdrop_changed", {"is-video": show.scenery_subsystem.is_video, "filename": show.scenery_subsystem.media_filename})
    else:
        p2p_network_manager.master_node.send("get_current_backdrop")

@sio.on("get_audio_library_entries") # broadcast audio library entries
def get_audio_library_entries(sid, data=None):
    if p2p_network_manager.is_master_node:
        if show:
            p2p_network_manager.broadcast_to_servers("audio_library_entries", {filename: hash_of_file(f"_working_show/audio_library/{filename}") for filename in os.listdir("_working_show/audio_library")})
    else:
        p2p_network_manager.master_node.send("get_audio_library_entries")

@sio.on("audio_library_entries") # compare audio library entries and update necessary files
def audio_library_entries(sid, entries):
    if p2p_network_manager.is_master_node: # this shouldn't be able to happen, but we stop it just in case
        return
    for filename in entries:
        if os.path.exists(f"_working_show/audio_library/{filename}") and hash_of_file(f"_working_show/audio_library/{filename}") == entries[filename]:
            continue # file matches, don't request
        p2p_network_manager.master_node.send("get_audio_file", filename) # no match, request
    for file in os.listdir("_working_show/audio_library"):
        if file not in entries:
            os.remove(f"_working_show/audio_library/{file}")

@sio.on("get_audio_file") # request contents of audio file by filename
def get_audio_file(sid, filename):
    if not p2p_network_manager.is_master_node: # this also shouldn't be able to happen, but we stop it just in case
        pass
    if not os.path.exists(f"_working_show/audio_library/{filename}"): # again, impossible, but we still stop it
        return
    file_data: bytes = Path(f"_working_show/audio_library/{filename}").read_bytes()
    n_chunks: int = ceil(len(file_data) / 512000)
    if DEBUG_MODE:
        print(f"Sharing audio file {filename}: size {len(file_data)} bytes, {n_chunks} chunks")
    for chunk_idx in range(n_chunks):
        chunk_data = file_data[chunk_idx*512000:(chunk_idx+1)*512000]
        p2p_network_manager.broadcast_to_servers("audio_file", {
            "filename": filename,
            "hash": hash_of_file(f"_working_show/audio_library/{filename}"),
            "total_chunks": n_chunks,
            "chunk_idx": chunk_idx,
            "contents": base64.b64encode(chunk_data).decode("utf-8")
        })

@sio.on("audio_file") # update an audio file
def audio_file(sid, data):
    global current_audio_transfers
    if os.path.exists(f"_working_show/audio_library/{data['filename']}"):
        if hash_of_file(f"_working_show/audio_library/{data['filename']}") == data["hash"]:
            return # if the file path and hash match, don't update
        os.remove(f"_working_show/audio_library/{data['filename']}") # if the file exists but is outdated, delete it
    if data['filename'] not in current_audio_transfers:
        current_audio_transfers[data['filename']] = [data['total_chunks'], set(), {}]
    current_audio_transfers[data['filename']][1].add(data['chunk_idx'])
    current_audio_transfers[data['filename']][2][data['chunk_idx']] = base64.b64decode(data["contents"].encode("utf-8"))
    if DEBUG_MODE:
        print(f"Recieved chunk {data['chunk_idx']+1} of {data['total_chunks']} for audio file {data['filename']}")
    if len(current_audio_transfers[data['filename']][2]) == data['total_chunks']:
        if DEBUG_MODE:
            print(f"Recieved all chunks for audio file {data['filename']}, writing file now...")
        full_file: bytes = bytes()
        for i in range(data['total_chunks']):
            full_file = b"".join([full_file, current_audio_transfers[data['filename']][2][i]])
        Path(f"_working_show/audio_library/{data['filename']}").write_bytes(full_file)
        del current_audio_transfers[data['filename']]

@sio.on("get_backdrop_library_entries") # broadcast backdrop library entries
def get_backdrop_library_entries(sid, data=None):
    if p2p_network_manager.is_master_node:
        if show:
            p2p_network_manager.broadcast_to_servers("backdrop_library_entries", {filename: hash_of_file(f"_working_show/backdrop_library/{filename}") for filename in os.listdir("_working_show/backdrop_library")})
    else:
        p2p_network_manager.master_node.send("get_backdrop_library_entries")

@sio.on("backdrop_library_entries") # compare backdrop library entries and update necessary files
def backdrop_library_entries(sid, entries):
    if p2p_network_manager.is_master_node: # this shouldn't be able to happen, but we stop it just in case
        return
    for filename in entries:
        if os.path.exists(f"_working_show/backdrop_library/{filename}") and hash_of_file(f"_working_show/backdrop_library/{filename}") == entries[filename]:
            continue # file matches, don't request
        p2p_network_manager.master_node.send("get_backdrop_file", filename) # no match, request
    for file in os.listdir("_working_show/backdrop_library"):
        if file not in entries:
            os.remove(f"_working_show/backdrop_library/{file}")

@sio.on("get_backdrop_file") # request contents of backdrop file by filename
def get_backdrop_file(sid, filename):
    if not p2p_network_manager.is_master_node: # this also shouldn't be able to happen, but we stop it just in case
        pass
    if not os.path.exists(f"_working_show/backdrop_library/{filename}"): # again, impossible, but we still stop it
        return
    file_data: bytes = Path(f"_working_show/backdrop_library/{filename}").read_bytes()
    n_chunks: int = ceil(len(file_data) / 512000)
    if DEBUG_MODE:
        print(f"Sharing backdrop file {filename}: size {len(file_data)} bytes, {n_chunks} chunks")
    for chunk_idx in range(n_chunks):
        chunk_data = file_data[chunk_idx*512000:(chunk_idx+1)*512000]
        p2p_network_manager.broadcast_to_servers("backdrop_file", {
            "filename": filename,
            "hash": hash_of_file(f"_working_show/backdrop_library/{filename}"),
            "total_chunks": n_chunks,
            "chunk_idx": chunk_idx,
            "contents": base64.b64encode(chunk_data).decode("utf-8")
        })

@sio.on("backdrop_file") # update a backdrop file
def backdrop_file(sid, data):
    global current_backdrop_transfers
    if os.path.exists(f"_working_show/backdrop_library/{data['filename']}"):
        if hash_of_file(f"_working_show/backdrop_library/{data['filename']}") == data["hash"]:
            return # if the file path and hash match, don't update
        os.remove(f"_working_show/backdrop_library/{data['filename']}") # if the file exists but is outdated, delete it
    if data['filename'] not in current_backdrop_transfers:
        current_backdrop_transfers[data['filename']] = [data['total_chunks'], set(), {}]
    current_backdrop_transfers[data['filename']][1].add(data['chunk_idx'])
    current_backdrop_transfers[data['filename']][2][data['chunk_idx']] = base64.b64decode(data["contents"].encode("utf-8"))
    if DEBUG_MODE:
        print(f"Recieved chunk {data['chunk_idx']+1} of {data['total_chunks']} for backdrop file {data['filename']}")
    if len(current_backdrop_transfers[data['filename']][2]) == data['total_chunks']:
        if DEBUG_MODE:
            print(f"Recieved all chunks for backdrop file {data['filename']}, writing file now...")
        full_file: bytes = bytes()
        for i in range(data['total_chunks']):
            full_file = b"".join([full_file, current_backdrop_transfers[data['filename']][2][i]])
        Path(f"_working_show/backdrop_library/{data['filename']}").write_bytes(full_file)
        del current_backdrop_transfers[data['filename']]

app.mount("/backdrops", StaticFiles(directory="_working_show/backdrop_library"))
app.mount("/", StaticFiles(directory="frontend/static"))

if __name__ == '__main__':
    uvicorn.run("main:deploy_app", host="0.0.0.0", port=8383)
    p2p_network_manager.shutdown()
