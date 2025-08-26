
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

import api

app = FastAPI()
app.include_router(api.router)

app.mount("/", StaticFiles(directory="frontend/static"), "static_files")

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8383)