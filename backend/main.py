
import os, copy

from show import Show
from cue import Cue, CueModel, PartialCueModel

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException
from fastapi_utils.tasks import repeat_every
import uvicorn

app = FastAPI()

show: Show | None = None

if os.path.exists("shows/") and os.path.isdir("shows/"):
    if os.path.exists("shows/autosave.tdshw"):
        show: Show = Show.load("autosave")

@app.on_event("startup")
@repeat_every(seconds=0.1)
async def update_polling_show_tasks() -> None:
    if show:
        show.update_polling_tasks()

@app.on_event("shutdown")
def autosave() -> None:
    if show:
        show.save("autosave")

@app.get("/load_show/{show_name}")
def load_show(show_name: str):
    global show
    show = Show.load(show_name)
    return {"show": show_name}

@app.get("/save_show/{show_name}")
def save_show(show_name: str):
    global show
    if not show:
        raise HTTPException(500, "No show loaded")
    show.save(show_name)
    return {"show": show_name}

@app.get("/is_show_loaded")
def is_show_loaded():
    global show
    if show:
        return {"loaded": True, "show": show.title}
    else:
        return {"loaded": False, "show": ""}

@app.get("/list_shows")
def list_shows():
    return {"shows": Show.list_shows()}

@app.get("/new_show/{show_name}")
def new_show(show_name: str):
    global show
    show = Show.new(show_name)
    return {"show": show_name}

@app.get("/list_audio")
def list_audio():
    global show
    if show:
        return {"audio": show.audio_subsystem.list_audio()}

@app.get("/enter_blackout")
def enter_blackout():
    global show
    if show:
        return {"change": show.enter_blackout()}
    return {"change": False}

@app.get("/exit_blackout")
def exit_blackout():
    global show
    if show:
        return {"change": show.exit_blackout()}
    return {"change": False}

@app.get("/toggle_blackout")
def toggle_blackout():
    global show
    if show:
        show.exit_blackout() if show.blackout else show.enter_blackout()
        return {"change": True}
    return {"change": False}

@app.get("/is_blackout")
def is_blackout():
    global show
    if show:
        return {"blackout": show.blackout}

@app.get("/next_cue")
def next_cue():
    global show
    if show:
        return {"cue": show.next_cue()}
    return {}

@app.get("/previous_cue")
def next_cue():
    global show
    if show:
        return {"cue": show.previous_cue()}
    return {}

@app.get("/jump_to_cue/{cue}")
def jump_to_cue(cue: int):
    global show
    if show:
        return {"cue": show.jump_to_cue(cue)}
    return {}

@app.get("/list_cues")
def list_cues():
    global show
    if show:
        return {"cues": show.serialize_cues()}
    return {}

@app.post("/add_cue")
async def add_cue(cue_model: CueModel, position: int | None = None):
    global show
    if show:
        if position == None:
            show.cues.append(Cue(
                description=cue_model.description,
                commands=cue_model.commands,
                blackout=cue_model.blackout
            ))
        else:
            show.cues.insert(position, Cue(
                description=cue_model.description,
                commands=cue_model.commands,
                blackout=cue_model.blackout
            ))
        for websocket in show.websockets:
            await websocket.send_json({"cues": show.serialize_cues()})
        return {"cues": show.serialize_cues()}

@app.get("/copy_cue/{old_cue}/{new_cue}")
async def copy_cue(old_cue: int, new_cue: int):
    global show
    if show:
        show.cues.insert(new_cue, copy.deepcopy(show.cues[old_cue]))
        for websocket in show.websockets:
            await websocket.send_json({"cues": show.serialize_cues()})
        return {"cues": show.serialize_cues()}

@app.get("/move_cue/{old_location}/{new_location}")
async def move_cue(old_location: int, new_location: int):
    global show
    if show:
        if new_location > old_location:
            show.cues.insert(new_location-1, show.cues.pop(old_location))
        elif new_location < old_location:
            show.cues.insert(new_location, show.cues.pop(old_location))
        for websocket in show.websockets:
            await websocket.send_json({"cues": show.serialize_cues()})
        return {"cues": show.serialize_cues()}

@app.get("/move_cue_up/{location}/{amount}")
async def move_cue(location: int, amount: int):
    global show
    if show:
        show.cues.insert(location-amount, show.cues.pop(location))
        for websocket in show.websockets:
            await websocket.send_json({"cues": show.serialize_cues()})
        return {"cues": show.serialize_cues()}

@app.get("/move_cue_down/{location}/{amount}")
async def move_cue(location: int, amount: int):
    global show
    if show:
        show.cues.insert(location+amount+1, show.cues.pop(location))
        for websocket in show.websockets:
            await websocket.send_json({"cues": show.serialize_cues()})
        return {"cues": show.serialize_cues()}

@app.get("/remove_cue/{cue}")
async def remove_cue(cue: int):
    global show
    if show:
        show.cues.pop(cue)
        for websocket in show.websockets:
            await websocket.send_json({"cues": show.serialize_cues()})
        return {"cues": show.serialize_cues()}

@app.post("/update_cue/{cue}")
def update_cue(cue: int, update: PartialCueModel):
    global show
    if show:
        if update.description != None:
            show.cues[cue].description = update.description
        if update.commands != None:
            show.cues[cue].commands = update.commands
        if update.blackout != None:
            show.cues[cue].blackout = update.blackout

@app.post("/add_comand/{cue}")
async def add_command(request: Request, cue: int, position: int | None = None):
    global show
    if show:
        command: dict = await request.json()
        if position != None:
            show.cues[cue].commands.insert(position, command)
        else:
            show.cues[cue].commands.append(command)

@app.get("/move_command/{cue}/{old_location}/{new_location}")
def move_command(cue: int, old_location: int, new_location: int):
    global show
    if show:
        if new_location > old_location:
            show.cues[cue].commands.insert(new_location-1, show.cues[cue].commands.pop(old_location))
        elif new_location < old_location:
            show.cues[cue].commands.insert(new_location, show.cues[cue].commands.pop(old_location))

@app.post("/update_command/{cue}/{command}")
async def update_command(request: Request, cue: int, command: int):
    global show
    if show:
        for key, value in await request.json():
            show.cues[cue].commands[command][key] = value

@app.websocket("/websocket")
async def websocket_handler(websocket: WebSocket):
    global show
    if not show:
        return
    await websocket.accept()
    show.websockets.append(websocket)
    try:
        while True:
            request: str = await websocket.receive_text()
            print(f"recieved ws request {request}")
            match request:
                case "cues":
                    await websocket.send_json({"cues": show.serialize_cues()})
    except WebSocketDisconnect:
        show.websockets.remove(websocket)

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8383)
