"""core-ui Render service entrypoint.

Single Python process; fin123-pod is NOT installed here (it would
shadow fin123/ui/server.py). Mounts:

    /             -> JSON greeter
    /ui/          -> fin123-core spreadsheet/Surface/Terminal UI
    /lifecycle/   -> in-memory build → release → run beat
    /healthz      -> liveness (always 200 if process is alive)
    /healthz/seed -> readiness (200 only if seed project is intact)

The UI's HTML uses absolute asset paths (``/static/...``, ``/api/...``)
that don't know about the ``/ui`` mount prefix. The middleware below
rewrites those to ``/ui/static/...`` / ``/ui/api/...`` so a browser
loading ``/ui/`` resolves all assets and API calls correctly. The
public edge service (Phase 3) will continue to expose this surface
under ``/ui`` so URLs are stable across local + staging + production.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fin123.ui.server import create_app as create_core_ui_app

from core_ui_service.lifecycle import router as lifecycle_router

PROJECT_DIR = Path(
    os.environ.get(
        "FIN123_PROJECT_DIR",
        str(Path(__file__).resolve().parent / "seed" / "dcf_demo"),
    )
)

app = FastAPI(title="fin123 core-ui")


@app.middleware("http")
async def rewrite_ui_absolute_assets(request: Request, call_next):
    """Browser fetches /static/... and /api/... as absolute paths
    because core's HTML doesn't know it's mounted under /ui. Rewrite
    those to the /ui-prefixed path so the mount handles them.

    Lifecycle, healthz, root greeter, and the /ui mount itself are
    untouched.
    """
    path = request.scope.get("path", "")
    if path.startswith("/static/") or path.startswith("/api/"):
        new_path = "/ui" + path
        request.scope["path"] = new_path
        if "raw_path" in request.scope and request.scope["raw_path"]:
            request.scope["raw_path"] = b"/ui" + request.scope["raw_path"]
    return await call_next(request)


@app.get("/")
def root() -> dict:
    return {"message": "fin123 core-ui running", "ui": "/ui"}


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.get("/healthz/seed")
def healthz_seed():
    failures: list[str] = []
    if not PROJECT_DIR.exists():
        failures.append(f"project dir missing: {PROJECT_DIR}")
    else:
        if not (PROJECT_DIR / "workbook.yaml").exists():
            failures.append("workbook.yaml missing")
        if not (PROJECT_DIR / "fin123.yaml").exists():
            failures.append("fin123.yaml missing")
        runs_dir = PROJECT_DIR / "runs"
        if not runs_dir.exists() or not any(runs_dir.iterdir()):
            failures.append("no prior runs in seed project")
    if failures:
        return JSONResponse(
            status_code=500, content={"ok": False, "failures": failures}
        )
    return {"ok": True, "project_dir": str(PROJECT_DIR)}


app.include_router(lifecycle_router, prefix="/lifecycle")
app.mount("/ui", create_core_ui_app(PROJECT_DIR))
