
import os

from show import Show
from cue import Cue

from fastapi import FastAPI
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

@app.get("/save_show/{show_name}")
def save_show(show_name: str):
    global show
    if not show:
        raise HTTPException(500, "No show loaded")
    show.save(show_name)

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

if __name__ == '__main__':
    uvicorn.run("main:app")