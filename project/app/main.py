from contextlib import asynccontextmanager

from fastapi import FastAPI

# &begin[Database]
from app.applications import models  # noqa: F401  (registers models on Base.metadata)
from app.core.db import init_db
# &end[Database]
from app.applications import router as applications  # &line[Applications]

# &begin[Database]
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
# &end[Database]


app = FastAPI(lifespan=lifespan)  # &line[Database]
app.include_router(applications.router)  # &line[Applications]

@app.get("/")
async def home():
    return {"message": "Hello, World!"}
