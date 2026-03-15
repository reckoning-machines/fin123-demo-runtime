"""fin123 demo runtime — interactive DCF model execution."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import DCFRequest, DCFResponse
from app.runner import run_dcf

app = FastAPI(
    title="fin123 Demo Runtime",
    description="Interactive DCF model execution using fin123 semantics.",
    version="0.1.0",
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/healthz")
def healthz() -> dict:
    """Health check for load balancers and uptime monitors."""
    return {"ok": True}


@app.post("/run-dcf", response_model=DCFResponse)
def post_run_dcf(params: DCFRequest) -> DCFResponse:
    """Run the DCF model with the given parameters.

    Validates inputs via Pydantic, executes the model, and returns
    projected revenue, projected FCF, and enterprise value (NPV).
    """
    return run_dcf(params)


@app.get("/")
def index() -> FileResponse:
    """Serve the frontend."""
    return FileResponse(FRONTEND_DIR / "index.html")


# Serve static assets (app.js, style.css)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
