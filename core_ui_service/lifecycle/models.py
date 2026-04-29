"""Lifecycle (build/release/run) request/response models.

Vendored from fin123-demo-runtime/app/models.py with no behavioral
changes; namespace moved to core_ui_service.lifecycle to avoid the
``app.*`` namespace clash with reckoning-machine's standalone app.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DCFRequest(BaseModel):
    revenue_prev: float = Field(..., gt=0)
    revenue_growth: float = Field(..., ge=-0.5, le=2.0)
    margin: float = Field(..., gt=0, le=1.0)
    discount_rate: float = Field(..., gt=0, lt=1.0)


class YearRow(BaseModel):
    year: int
    revenue: float
    fcf: float
    discount_factor: float
    pv_fcf: float


class DCFResponse(BaseModel):
    years: list[YearRow]
    enterprise_value: float
    params: DCFRequest


class BuildResponse(BaseModel):
    params: DCFRequest
    results: DCFResponse
    content_hash: str
    built_at: str
    status: str = "draft"


class ReleaseResponse(BaseModel):
    params: DCFRequest
    results: DCFResponse
    content_hash: str
    built_at: str
    released_at: str
    version: int
    status: str = "released"


class StateResponse(BaseModel):
    draft: BuildResponse | None = None
    released: ReleaseResponse | None = None
