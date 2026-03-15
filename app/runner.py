"""DCF model runner and worksheet compiler.

The DCF runner implements the same logic described in the fin123-examples
dcf-valuation example. NPV uses Excel semantics (discount from t=1),
matching fin123-core's formulas/fn_finance.py.

The worksheet compiler wraps DCF results into a real fin123 compiled
worksheet artifact using the fin123-core worksheet pipeline. No project
directory or filesystem required — everything runs in memory.
"""

from fin123.worksheet import compile_worksheet, from_json_records, parse_worksheet_view
from fin123.worksheet.compiled import CompiledWorksheet
from fin123.worksheet.types import ColumnSchema, ColumnType

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


# --- Worksheet compilation ---

_DCF_SCHEMA = [
    ColumnSchema(name="year", dtype=ColumnType.INT64),
    ColumnSchema(name="revenue", dtype=ColumnType.FLOAT64),
    ColumnSchema(name="fcf", dtype=ColumnType.FLOAT64),
    ColumnSchema(name="discount_factor", dtype=ColumnType.FLOAT64),
    ColumnSchema(name="pv_fcf", dtype=ColumnType.FLOAT64),
]

_DCF_SPEC = {
    "name": "dcf_projection",
    "title": "DCF Projection",
    "columns": [
        {"source": "year", "label": "Year"},
        {"source": "revenue", "label": "Revenue",
         "display_format": {"type": "currency", "symbol": "$", "places": 2}},
        {"source": "fcf", "label": "Free Cash Flow",
         "display_format": {"type": "currency", "symbol": "$", "places": 2}},
        {"source": "discount_factor", "label": "Discount Factor",
         "display_format": {"type": "decimal", "places": 4}},
        {"source": "pv_fcf", "label": "PV of FCF",
         "display_format": {"type": "currency", "symbol": "$", "places": 2}},
    ],
}


def compile_dcf_worksheet(response: DCFResponse) -> CompiledWorksheet:
    """Compile DCF results into a real fin123 worksheet artifact.

    Converts year-by-year projections into a ViewTable, applies a static
    worksheet spec, and produces a CompiledWorksheet with genuine provenance
    and a deterministic content hash.
    """
    records = [y.model_dump() for y in response.years]
    vt = from_json_records(records, _DCF_SCHEMA, source_label="dcf-demo-build")
    spec = parse_worksheet_view(_DCF_SPEC)
    return compile_worksheet(vt, spec)
