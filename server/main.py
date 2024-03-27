from fastapi import FastAPI
import uvicorn
import asyncio
import threading
from .utils import *
from .mission_scheduler import check_and_fire_missions
from .routers import drones, missions, schedules

app = FastAPI()

app.include_router(drones.router)
app.include_router(schedules.router)
app.include_router(missions.router)

# TODO: figure how how to extract the db data using models


@app.get("/")
async def root():
    return {"message": "Hello World"}


# Function to run the task in a separate thread
def threaded_task():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_and_fire_missions())
    loop.close()


# Asynchronous function to execute periodically
async def periodic_task():
    while True:
        t = threading.Thread(target=threaded_task)
        t.start()
        # sleep for 120 seconds before executing again
        await asyncio.sleep(120)


# define a background task when the server is up
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_task())


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
