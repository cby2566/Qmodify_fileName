from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from services import log_service
from routers import files, regex, rename, favorites, logs, export, settings, desktop
from routers import open as open_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_service.init_db()
    yield


app = FastAPI(
    title="File Renamer Backend",
    description="FastAPI backend for batch file renaming tool.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router)
app.include_router(regex.router)
app.include_router(rename.router)
app.include_router(favorites.router)
app.include_router(logs.router)
app.include_router(export.router)
app.include_router(settings.router)
app.include_router(open_router.router)
app.include_router(desktop.router)


@app.get("/health")
def health():
    return {"status": "ok"}
