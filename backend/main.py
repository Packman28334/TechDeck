
from show import Show
from cue import Cue

from fastapi import FastAPI, UploadFile
from fastapi.exceptions import HTTPException
from fastapi_utils.tasks import repeat_every
import uvicorn

app = FastAPI()

show: Show | None = None

@app.on_event("startup")
@repeat_every(seconds=0.1)
async def update_polling_show_tasks() -> None:
    if show:
        show.update_polling_tasks()

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

if __name__ == '__main__':
    uvicorn.run("main:app")