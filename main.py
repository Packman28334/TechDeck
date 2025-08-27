
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

import api

app = FastAPI()
app.include_router(api.router)

@app.get("/")
def index():
    return HTMLResponse(Path("frontend/index.html").read_text())

app.mount("/", StaticFiles(directory="frontend/static"))

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8383)