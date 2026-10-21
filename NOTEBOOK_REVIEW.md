# Notebook review — `dyn_cge_main.ipynb`

This repo's dashboard (`index.html`) is built on top of a dynamic recursive
CGE model (`dyn_cge_main.ipynb`) that simulates abolishing import tariffs in
a 4-sector, 2-factor economy over 31 annual periods, using GAMSPy.

The notebook could not be executed in the environment where this review was
first done (no path to PyPI for `gamspy`, and no GAMS solver license/engine
installed), so this is a static code review, cross-checked against the
notebook's own saved output from a prior run with real GAMS.

## Bugs

### 1. The notebook's primary entry point silently produces a near-zero result

Cell 6 of the notebook runs the pipeline twice in the same kernel:

```python
from results import main
main()
# ...then, separately...
ctx = build_model()
ctx = run_simulation(ctx)
out = compute_results(ctx)
```

The notebook's own saved output shows:

- First call (`main()`): `EV_TTL: -0.0`, every reported deviation at `0.000%`.
- Second call (manual rebuild): `EV_TTL: 5,741.29`, with real, nonzero
  sectoral/price/capital deviations.

The tariff shock (`taum[i] = 0`) is identical in both calls, so the first
run isn't a different scenario — something about building two
`Container()`/`Model()` instances in one GAMSPy process is leaking state
between them. **The notebook's `main()` entry point cannot currently be
trusted on its own** — only the redundant second rebuild gives the correct
answer. Worth filing against GAMSPy, or at minimum isolating each
`build_model()` call in its own process/workspace.

### 2. `compute_results()` drops `dF` from its return value

`results.py` computes a factor-allocation deviation parameter (`dF`)
internally but its `return` statement omits it:

```python
return {"EV": EV, "EV_TTL": EV_TTL, "dCC": dCC, "dZ": dZ,
        "dpq": dpq, "depsilon": depsilon, "dKK": dKK}
```

The notebook's own later cell expects it:

```python
dF = out.get("dF", None)  # only if you returned it; see note below
df = dF.records.copy()    # AttributeError: 'NoneType' object has no attribute 'records'
```

This will raise on a fresh run. Fix: add `"dF": dF` to the returned dict.

## Lower-severity findings

- **`eqpf2[h_mob, i, j]`** equates `pf[h_mob, j] == pf[h_mob, i]` for every
  `(i, j)` pair rather than pinning to one reference sector — the code
  comment itself flags this as "kept as in original" from the source GAMS
  model. It still solves (redundant but consistent equations), but is worth
  re-deriving against the original source rather than carrying forward
  unexamined.
- **`eqPRICE`** weights `pq[j]` by the alias `j` where the rest of the
  equation block uses `i` for goods — also flagged "kept as in original."
- The baseline solve is pinned to an exact assertion
  (`math.isclose(dyncge.objective_value, 539570.5027, rel_tol=0.001)`).
  Useful as a regression guard today, but it will hard-fail the whole
  pipeline the moment the SAM, elasticities, or growth assumptions change.

## How the dashboard's data was produced

Since the model couldn't be solved in the sandbox that first built this
dashboard, every series in `data/*.json` was digitized from the notebook's
own saved matplotlib output: each figure was pixel-calibrated against its
own axes (tick positions, zero-lines, and known data-point markers), then
cross-checked against the notebook's printed period-0, period-30, and
total-EV figures. Values at period 0 and 30 match the printed text exactly;
periods 1–29 were read off the plotted curves.

**To replace this with exact, full-precision data:** run
`export_for_dashboard.py` in a notebook/environment with GAMSPy and a real
GAMS engine, right after `ctx = run_simulation(ctx)`. It reads every series
straight from `ctx`'s raw level parameters (so it also sidesteps the
missing-`dF` bug above) and writes `cge_dashboard_export.json` with the full
31-period paths for welfare, sectoral output, factor demand, capital,
prices, exchange rate, and trade. Swap that in for the files under `data/`
to make `index.html` exact.
