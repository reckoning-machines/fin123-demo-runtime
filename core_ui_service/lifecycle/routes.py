"""Lifecycle (build → release → run) FastAPI routes.

Vendored from fin123-demo-runtime/app/main.py. State is in-memory and
process-local; pod-app's nightly reset cron (separate service) does
not touch this — restart the core-ui service to clear lifecycle state.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from .models import (
    BuildResponse,
    DCFRequest,
    DCFResponse,
    ReleaseResponse,
    StateResponse,
)
from .runner import compile_dcf_worksheet, run_dcf

from fin123.worksheet.compiled import CompiledWorksheet

router = APIRouter(tags=["lifecycle"])

_draft: BuildResponse | None = None
_draft_compiled: CompiledWorksheet | None = None
_released: ReleaseResponse | None = None
_released_compiled: CompiledWorksheet | None = None
_version: int = 0


def _artifact_hash(compiled: CompiledWorksheet) -> str:
    return hashlib.sha256(compiled.content_hash_data().encode()).hexdigest()[:12]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@router.post("/build", response_model=BuildResponse)
def post_build(params: DCFRequest) -> BuildResponse:
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


@router.post("/release", response_model=ReleaseResponse)
def post_release() -> ReleaseResponse:
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


@router.post("/run", response_model=DCFResponse)
def post_run() -> DCFResponse:
    if _released is None:
        raise HTTPException(409, "No released artifact")
    return _released.results


@router.get("/state", response_model=StateResponse)
def get_state() -> StateResponse:
    return StateResponse(draft=_draft, released=_released)


@router.get("/artifact/released")
def get_released_artifact() -> dict:
    if _released_compiled is None:
        raise HTTPException(409, "No released artifact")
    return _released_compiled.model_dump()


@router.post("/reset")
def post_reset() -> dict:
    global _draft, _draft_compiled, _released, _released_compiled, _version
    _draft = None
    _draft_compiled = None
    _released = None
    _released_compiled = None
    _version = 0
    return {"ok": True}
