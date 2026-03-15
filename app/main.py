"""fin123 demo runtime — interactive DCF model execution."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import (
    BuildResponse,
    DCFRequest,
    DCFResponse,
    ReleaseResponse,
    StateResponse,
)
from fin123.worksheet.compiled import CompiledWorksheet

from app.runner import compile_dcf_worksheet, run_dcf

app = FastAPI(
    title="fin123 Demo Runtime",
    description="Interactive DCF model execution using fin123 semantics.",
    version="0.1.0",
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# --- In-memory lifecycle state (resets on process restart) ---
_draft: BuildResponse | None = None
_draft_compiled: CompiledWorksheet | None = None
_released: ReleaseResponse | None = None
_released_compiled: CompiledWorksheet | None = None
_version: int = 0


def _artifact_hash(compiled: CompiledWorksheet) -> str:
    """Hash the compiled worksheet artifact (excluding timestamp)."""
    return hashlib.sha256(compiled.content_hash_data().encode()).hexdigest()[:12]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@app.get("/healthz")
def healthz() -> dict:
    """Health check for load balancers and uptime monitors."""
    return {"ok": True}


@app.post("/build", response_model=BuildResponse)
def post_build(params: DCFRequest) -> BuildResponse:
    """Build a draft artifact with real fin123 worksheet compilation."""
    global _draft, _draft_compiled
    results = run_dcf(params)
    compiled = compile_dcf_worksheet(results)
    _draft_compiled = compiled
    _draft = BuildResponse(
        params=params,
        results=results,
        content_hash=_artifact_hash(compiled),
        built_at=_now(),
    )
    return _draft


@app.post("/release", response_model=ReleaseResponse)
def post_release() -> ReleaseResponse:
    """Promote the current draft to a released artifact."""
    global _released, _released_compiled, _version
    if _draft is None:
        raise HTTPException(409, "No draft artifact to release")
    _version += 1
    _released_compiled = _draft_compiled
    _released = ReleaseResponse(
        params=_draft.params,
        results=_draft.results,
        content_hash=_draft.content_hash,
        built_at=_draft.built_at,
        released_at=_now(),
        version=_version,
    )
    return _released


@app.post("/run", response_model=DCFResponse)
def post_run() -> DCFResponse:
    """Return results from the released artifact (no recomputation)."""
    if _released is None:
        raise HTTPException(409, "No released artifact")
    return _released.results


@app.get("/state", response_model=StateResponse)
def get_state() -> StateResponse:
    """Return current draft and released metadata."""
    return StateResponse(draft=_draft, released=_released)


@app.get("/artifact/released")
def get_released_artifact() -> dict:
    """Return the released compiled worksheet artifact."""
    if _released_compiled is None:
        raise HTTPException(409, "No released artifact")
    return _released_compiled.model_dump()


@app.post("/run-dcf", response_model=DCFResponse)
def post_run_dcf(params: DCFRequest) -> DCFResponse:
    """Run the DCF model with the given parameters (legacy endpoint)."""
    return run_dcf(params)


@app.get("/")
def index() -> FileResponse:
    """Serve the frontend."""
    return FileResponse(FRONTEND_DIR / "index.html")


# Serve static assets (app.js, style.css)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
