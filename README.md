# Tariff Abolition CGE Explorer

An interactive dashboard for a dynamic recursive computable general
equilibrium (CGE) model — 4 sectors, 2 factors, 31 annual periods — that
simulates abolishing import tariffs in a small economy.

**[Open the dashboard](index.html)** (or enable GitHub Pages on this repo
for a hosted link — see below).

## What's here

- `index.html` — the self-contained interactive dashboard (plain HTML/JS, d3.js from CDN, no build step).
- `data/*.json` — the data behind the charts (welfare path, sectoral output path, trade volumes, prices/capital/factor demand at period 30, headline summary).
- `dyn_cge_main.ipynb` — the source GAMSPy notebook: builds, calibrates and solves the model, runs the tariff-abolition simulation, and reports results.
- `NOTEBOOK_REVIEW.md` — a code review of the notebook, including two real bugs found by inspection and cross-checking its own saved output.
- `export_for_dashboard.py` — run this in a GAMSPy-capable environment (after `ctx = run_simulation(ctx)`) to export exact, full-precision results and replace the digitized data under `data/` with the real thing.

## Data provenance

The dashboard's current numbers were digitized from the notebook's own
saved chart output (from a run with a real GAMS engine), not freshly solved,
because the environment that first built this dashboard had no GAMS
license/engine available. Values at period 0 and period 30 match the
notebook's printed summary exactly; the path in between was read off the
plotted curves. See `NOTEBOOK_REVIEW.md` for details and for how to swap in
an exact, full-resolution export once you can run the model yourself.

## Hosting on GitHub Pages

Settings → Pages → Deploy from branch → `main` / root. The dashboard will
then be reachable at `https://macrofinancial.github.io/cge_dyn_1/`.
