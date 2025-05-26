
from show import Show

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
import uvicorn

app = FastAPI()

show: Show | None = None

@app.on_event("startup")
@repeat_every(seconds=0.1)
async def update_polling_show_tasks() -> None:
    if show:
        show.update_polling_tasks()

if __name__ == '__main__':
    uvicorn.run("main:app")