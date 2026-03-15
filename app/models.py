"""Request and response models for the DCF demo endpoint."""

from pydantic import BaseModel, Field


class DCFRequest(BaseModel):
    """Parameters for a DCF valuation run."""

    revenue_prev: float = Field(
        ..., gt=0, description="Prior-year revenue (must be positive)"
    )
    revenue_growth: float = Field(
        ..., ge=-0.5, le=2.0, description="Annual revenue growth rate"
    )
    margin: float = Field(
        ..., gt=0, le=1.0, description="Operating margin (0 to 1)"
    )
    discount_rate: float = Field(
        ..., gt=0, lt=1.0, description="Discount rate for NPV (0 to 1)"
    )


class YearRow(BaseModel):
    """One year of DCF projection detail."""

    year: int
    revenue: float
    fcf: float
    discount_factor: float
    pv_fcf: float


class DCFResponse(BaseModel):
    """Results from a DCF valuation run."""

    years: list[YearRow]
    enterprise_value: float
    params: DCFRequest
