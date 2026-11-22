from contextlib import asynccontextmanager

from fastapi import FastAPI

# &begin[Database]
from app.applications import models  # noqa: F401  (registers models on Base.metadata)
from app.companies import models as company_models  # noqa: F401  &line[Companies]
from app.core.db import init_db
# &end[Database]
from app.applications import router as applications  # &line[Applications]
from app.interviews import router as interviews  # &line[Interviews]
from app.companies import router as companies  # &line[Companies]

# &begin[Database]
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
# &end[Database]


app = FastAPI(lifespan=lifespan)  # &line[Database]
app.include_router(applications.router)  # &line[Applications]
app.include_router(interviews.router)  # &line[Interviews]
app.include_router(companies.router)  # &line[Companies]

@app.get("/")
async def home():
    return {"message": "Hello, World!"}
