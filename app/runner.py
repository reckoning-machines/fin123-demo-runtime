"""DCF model runner.

This module implements the same DCF logic described in the fin123-examples
dcf-valuation example. The NPV calculation uses Excel semantics (discount
from t=1), matching fin123-core's _fn_npv in formulas/fn_finance.py.

--- fin123-core integration ---

To replace this standalone runner with fin123-core execution:

1. Create a project directory with workbook.yaml and fin123.yaml
2. Use the Workbook API:

    from pathlib import Path
    from fin123 import Workbook

    wb = Workbook(
        Path("path/to/dcf_project"),
        overrides={
            "revenue_prev": params.revenue_prev,
            "revenue_growth": params.revenue_growth,
            "margin": params.margin,
            "discount_rate": params.discount_rate,
        },
    )
    result = wb.run()
    scalars = result.scalars  # dict of all computed scalar values

The standalone implementation below uses the same math so results
will match when the integration is wired up.
"""

from app.models import DCFRequest, DCFResponse, YearRow

PROJECTION_YEARS = 5


def npv(rate: float, cashflows: list[float]) -> float:
    """NPV with Excel semantics: discount from t=1.

    Matches fin123-core formulas/fn_finance.py::_fn_npv exactly.
    NPV = sum(cf_i / (1 + rate) ^ i) for i in 1..n
    """
    total = 0.0
    for i, cf in enumerate(cashflows, start=1):
        total += cf / (1 + rate) ** i
    return total


def run_dcf(params: DCFRequest) -> DCFResponse:
    """Execute the DCF model and return projected values.

    Revenue projection: compound growth from revenue_prev.
    FCF: revenue * margin per year.
    Enterprise value: NPV of FCF stream at discount_rate.
    """
    # --- Build year-by-year projection ---
    years: list[YearRow] = []
    prev = params.revenue_prev
    for i in range(1, PROJECTION_YEARS + 1):
        rev = prev * (1 + params.revenue_growth)
        fcf = rev * params.margin
        df = 1 / (1 + params.discount_rate) ** i
        pv = fcf * df
        years.append(YearRow(
            year=i,
            revenue=round(rev, 2),
            fcf=round(fcf, 2),
            discount_factor=round(df, 6),
            pv_fcf=round(pv, 2),
        ))
        prev = rev

    # --- Enterprise value (NPV of FCF stream) ---
    ev = round(sum(y.pv_fcf for y in years), 2)

    return DCFResponse(
        years=years,
        enterprise_value=ev,
        params=params,
    )
