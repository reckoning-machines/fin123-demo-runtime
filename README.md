# fin123-demo-runtime

Interactive demo of the fin123 financial model runtime. A user modifies
parameters for a DCF valuation model and runs it from the browser.

This is a thin demonstration app. It is not the hosted platform (fin123-pod).

## What This Is

A single-page web app that demonstrates deterministic financial model
execution. The user submits DCF parameters (revenue, growth, margin,
discount rate), the backend runs the model, and the frontend renders
projected revenue, free cash flow, discount factors, present values,
and enterprise value.

The NPV calculation uses Excel semantics (discount from t=1), matching
fin123-core's implementation in `formulas/fn_finance.py`.

## Architecture

```
Browser (HTML form)
    |
    |  POST /run-dcf  { revenue_prev, revenue_growth, margin, discount_rate }
    v
FastAPI backend (app/main.py)
    |
    |  validate inputs (Pydantic)
    v
DCF runner (app/runner.py)
    |
    |  project revenue (compound growth, 5 years)
    |  compute FCF (revenue * margin per year)
    |  compute discount factors and PV per year
    |  compute enterprise value (sum of PV)
    v
JSON response -> render in browser
```

## Run Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000.

## Deploy to Render

The repo includes `render.yaml` for one-click deploy. Or configure manually:

| Setting | Value |
|---------|-------|
| **Runtime** | Python |
| **Build command** | `pip install -r requirements.txt` |
| **Start command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Health check** | `/healthz` |
| **Environment variable** | `PYTHON_VERSION` = `3.12` |

Custom domain: point `app.fin123.dev` to the Render service in your
DNS settings and add the domain in the Render dashboard.

No Docker, no database, no environment secrets required.

## What Is Implemented

- Parameter input with validation (Pydantic bounds checking)
- 5-year DCF projection (compound revenue growth, flat margin)
- Per-year discount factor and present value of FCF
- Enterprise value as NPV of FCF stream (no terminal value)
- Summary panel with currency formatting (EV, Y5 revenue, Y5 FCF, discount rate)
- Yearly projection table (revenue, FCF, discount factor, PV of FCF)
- All values displayed in USD with consistent formatting
- Error display for invalid inputs
- Health check endpoint (`GET /healthz`)

## What Is Not Implemented

- Authentication, accounts, or sessions
- Database or persistence
- Multi-tenant or organization features
- Direct fin123-core Workbook execution (see integration seam below)
- Worksheet compilation or artifact generation
- Hosted delivery or registry

These belong in fin123-pod. This demo is for interactive exploration only.

## fin123-core Integration Seam

The runner in `app/runner.py` implements the DCF math directly. To swap
in fin123-core execution, replace `run_dcf()` with:

```python
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
# result.scalars contains all computed values
```

The standalone runner produces identical results to fin123-core's NPV
function, verified against `formulas/fn_finance.py::_fn_npv`.

## Structure

```
app/
  main.py          FastAPI app, routes, static file serving
  runner.py        DCF model execution with fin123-core integration notes
  models.py        Pydantic request/response models (YearRow detail)

frontend/
  index.html       Single-page UI with parameter form and results
  app.js           Form submission, summary + table rendering
  style.css        Dark institutional theme (matches fin123.dev)

examples/
  dcf_example_inputs.json   Sample parameters
```

## License

Apache-2.0
