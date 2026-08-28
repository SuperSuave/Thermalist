from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.health import router as health_router
from app.api.routes.labels import router as labels_router
from app.api.routes.theme_designer import router as theme_designer_router
from app.api.routes.preview import router as preview_router
from app.api.routes.printing import router as printing_router
from app.api.routes.donetick_labels import router as donetick_labels
from app.api.routes.recipes import router as recipes_router
from app.core.config import load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
INDEX_FILE = STATIC_DIR / "index.html"
CONFIG_FILE = PROJECT_ROOT / "config.yaml"
GENERATED_DIR = PROJECT_ROOT / "app" / "generated_images"
GENERATED_DIR.mkdir(exist_ok=True)

if not STATIC_DIR.exists():
    raise RuntimeError(f"Static directory not found: {STATIC_DIR}")

if not INDEX_FILE.exists():
    raise RuntimeError(f"Index file not found: {INDEX_FILE}")

if not CONFIG_FILE.exists():
    raise RuntimeError(f"Config file not found: {CONFIG_FILE}")

app = FastAPI(title="ThermaList")
app.state.config = load_config(CONFIG_FILE)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount(
    "/generated_images", StaticFiles(directory=GENERATED_DIR), name="generated_images"
)


@app.get("/")
async def index():
    return FileResponse(INDEX_FILE)


app.include_router(donetick_labels)
app.include_router(health_router)
app.include_router(labels_router, prefix="/api", tags=["labels"])
app.include_router(preview_router)
app.include_router(printing_router)
app.include_router(recipes_router)
app.include_router(theme_designer_router)
