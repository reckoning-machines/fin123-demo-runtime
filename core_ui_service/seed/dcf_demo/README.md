# Benchmark DCF Operating Model

A quarterly multi-segment DCF model running on fin123's calculation engine.
66,000-row historical dataset. Benchmarks the deterministic execution of
spreadsheet-model logic at scale -- what Excel recalculates in seconds,
fin123 executes in milliseconds as a compiled, auditable run.

## Dataset

10 tickers × 5 segments × 3 regions × 5 products × 22 years × 4 quarters = 66,000 rows.

Columns: ticker, segment, region, product, year, quarter, revenue, cogs,
opex, capex, da, interest, shares, price.

## Model

The model runs on two components of fin123's calculation engine:

**Table graph** (Polars): derives gross_profit, ebit, ebitda, nopat, fcf, margins
across all 66K rows, then aggregates by ticker (10 summary rows). This is not a
spreadsheet formula range -- it is a compiled computation graph executed by the runtime.

**Scalar graph**: looks up base financials for the active ticker, projects 5 years of
revenue/EBIT/NOPAT/FCF, and computes DCF enterprise value with terminal value. Each
scalar evaluation is a deterministic step in the execution plan.

## Quick start

```bash
fin123 init bench --template benchmark_dcf
fin123 build bench
fin123 --verbose build bench
```

## Change active ticker

```bash
fin123 build bench --set active_ticker=MSFT
```

The `active_ticker` param controls which ticker's financials are used
for the DCF valuation. All 10 tickers are always processed in the table
graph; the scalar lookups read from the selected ticker's summary row.

## Scenarios

```bash
fin123 build bench --scenario bull
fin123 build bench --all-scenarios
```

## Batch sweep (20 scenarios across tickers)

```bash
fin123 batch build bench --params-file bench/inputs/scenarios.csv
```

Each row in the CSV triggers a full model execution -- not a recalculated
cell range. The batch CSV includes `active_ticker` so each run can target
a different company with different assumptions.

## Sensitivity grid (5x5 wacc x terminal_growth)

```bash
fin123 batch build bench --params-file bench/inputs/sensitivity.csv
```

Every point in the grid is a complete execution of the model with its own
build ID, content hash, and outputs.

## Timing

Use `--verbose` for per-phase timing or `--json` for machine-readable output:

```bash
fin123 --json build bench | python -m json.tool
```

The `timings_ms` field breaks down the runtime's execution phases:
resolve_params, hash_inputs, eval_tables, eval_scalars, export_outputs.
