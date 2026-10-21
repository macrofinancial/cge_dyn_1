# PEP-1-t: GAMS → GAMSPy conversion

Full conversion of `PEP_1-t-b_v2_1.gms` (the PEP standard dynamic CGE model,
version B), plus its two RESULTS include files, done in four stages.

## Files
| File | GAMS source | What it does |
|---|---|---|
| `data_io.py` | — | Reads `SAM-V2_0.xls` / `VAL_PAR.xlsx`, replacing `$CALL GDXXRW`. Tested against your real workbooks. |
| `pep_data.py` / `PEP1T_Stage1.ipynb` | sections 1-4 | Sets, parameters, data loading, calibration. **Confirmed working.** |
| `pep_equations.py` / `PEP1T_Stage2.ipynb` | section 5 | ~90 Variables + ~108 Equations. **Confirmed working.** |
| `pep_solve.py` / `PEP1T_Stage3.ipynb` | section 6 | `Model` + BAU/simulation solve loops, one period at a time. **Not yet run.** |
| `pep_results.py` / `PEP1T_Stage4.ipynb` | `RESULTS_PEP_1-t-b_BAU.gms` + `RESULTS_PEP_1-t-b_SIM1.GMS` | Flattens results, chained price indices, BAU/SIM1/var(%) table, Excel export. **Not yet run.** |
| `pep_dashboard.py` / `PEP1T_Stage5.ipynb` | — (new) | Builds `pep1t_dashboard.html` — a one-file static dashboard: GDP, sectoral output/price, income. **Not yet run.** |
| `pep_interactive.py` / `PEP1T_Stage6.ipynb` | — (new) | Jupyter `ipywidgets` panel next to the notebook: drag a "shock depth" slider, click Run, SIM1 re-solves and the dashboard updates inline. **Not yet run.** |
| `pep_dashboard_server.py` / `PEP1T_Stage7.ipynb` | — (new) | The slider **inside** `pep1t_dashboard.html` itself: a small local web server re-solves SIM1 on request and updates the page in place. **Not yet run.** |
| `SAM-V2_0.xls`, `VAL_PAR.xlsx` | — | Your original data files. |

Each notebook imports the previous stage's module, so opening
`PEP1T_Stage7.ipynb` alone runs the whole pipeline — but all files above
must sit in the same folder.

## Setup
```
pip install gamspy xlrd openpyxl pandas plotly ipywidgets flask
```
Plus a GAMS/GAMSPy solver license for a CNS-capable solver (CONOPT or PATH;
`pep_solve.py` defaults to `solver="conopt"`).

## Stage 3 (solve loop) specifics
- GAMS's `LOOP(time, ...)` is a plain Python `for` loop over periods
  "1".."10"; each iteration points the dynamic subset `T` at just that
  period (`T.setRecords([t_cur])`), which is what makes the Stage-2
  equations (defined over `T`, declared over `TIME`) generate for only the
  active period.
- `KD.fx(k,j,time-1)` becomes a direct reference to the previous loop
  iteration's period label.
- `PEP1T.hold_fixed = True` mirrors `PEP1T.HOLDFIXED=1` — **unconfirmed
  attribute name**, no GAMSPy install here to check it.

## Stage 4 (results) specifics
- Because every variable is declared over the full `TIME` set, by the end
  of a complete BAU (or SIM1) loop its `.records` already holds the whole
  ten-period series — so `snapshot_all_variables()` (in `pep_solve.py`,
  called right after each loop finishes) just reads every variable once,
  rather than re-collecting period by period. This is called **before**
  SIM1 runs, specifically so SIM1 solving over the same variables doesn't
  overwrite the BAU values first.
- `pep1t_results.xlsx` is one long table — `variable | dims | time | bau |
  sim1 | var_pct` — instead of the original's one-sheet-per-parameter GDX
  (easier to filter/pivot in Excel or pandas than 140 separate parameters).
- The four chained price indices (`PIXCON_C`, `PIXGDP_C`, `PIXINV_PRI_C`,
  `PIXINV_PUB_C`) are computed in plain pandas from the captured panels,
  not through GAMSPy, since they're pure post-hoc arithmetic on already-
  solved values — this sidesteps needing any more untested GAMSPy syntax
  for that part, at the cost of being the one function in the whole project
  I'd most want you to double-check (`chained_indices()` in
  `pep_results.py`) once you see real numbers.
- No `gdx2xls` outside GAMS, so everything is written directly with pandas/
  openpyxl instead of GDX → GAMS → Excel.

## What's verified vs. not
- **Verified** (Stages 1 & 2): run successfully against your real data,
  after fixing a column-name lookup, a float-vs-int label mismatch, and a
  genuine `0**(negative)` domain error in the labor CES calibration.
- **Not verified** (Stages 3 & 4): no GAMSPy/solver license in this
  sandbox. Likely trouble spots: the `hold_fixed` attribute name, the
  `.solve()` call shape for CNS, exactly which column names GAMSPy uses in
  `Variable.records`/`Parameter.records` (assumed `"level"` and `"value"`
  respectively, plus each domain Set's own name) — `dim_names()`,
  `to_long()` and `chained_indices()` in `pep_results.py` all lean on that
  assumption and are the most likely things to need a one-line fix.

## Stage 5 (dashboard) specifics
- Reads straight from the `results` DataFrame that `pep_results.py` already
  built — no re-parsing of Excel — so Stage 5 just needs Stages 1-4 to run
  clean first.
- Four KPI tiles (Real GDP, cumulative GDP growth, GDP deflator, total
  household income) comparing BAU vs SIM1 at the final period, plus four
  charts: Real GDP over time, sectoral output **volume** (`XST`), sectoral
  output **price** (`PT`), and household **income** (`YH`) — each chart
  encodes scenario as line style (solid = BAU, dashed = SIM1) and entity
  (sector or household type) as color, so quantity and price stay on
  separate charts rather than one dual-axis chart.
- One self-contained `pep1t_dashboard.html` — Plotly's JS is embedded in
  the file itself, so it opens in any browser with no internet connection
  and nothing else to install beyond `pip install plotly`.
- Not GAMSPy-dependent in itself (pure pandas/Plotly on already-solved
  values), but it imports `pep_results`, so it re-runs the whole BAU+SIM1
  solve each time you run it — same as Stage 4.

## Stage 6 (interactive dashboard) specifics
- Why this is a notebook widget and not a slider inside the HTML file: the
  "shock" isn't post-processing on numbers that already exist, it's a
  GAMSPy CNS solve of ~108 equations, one period at a time. A browser can't
  run that — only your Python/GAMSPy environment can, which is why the
  slider lives in Jupyter.
- `pep_solve.py`'s `SHOCK_SCHEDULE`/`tariff_shock` are now built by
  `make_shock_schedule(depth)` / `make_tariff_shock(schedule)` — `depth=1.0`
  reproduces the original .gms shock exactly (tariffs → 0 by the final
  period); `0.0` means no shock (SIM1 collapses onto BAU); values above 1
  cut tariffs faster/deeper than the original.
- `resolve_sim1(depth)` (also in `pep_solve.py`) re-solves **only** SIM1 at
  a new depth and returns a fresh `sim1_panel` — BAU isn't re-solved, since
  the shock doesn't touch it. Each re-solve warm-starts from whatever `.l`
  values are already sitting in the Variables from the previous run, which
  is a reasonable starting point for a CNS resolve.
- `pep_results.py`'s merge/chained-index logic is now a function,
  `compute_results(bau_panel, sim1_panel)`, so Stage 6 can rebuild the
  BAU/SIM1/var(%) table from the new `sim1_panel` without re-running Stage 4
  from scratch.
- `pep_interactive.py` wires an `ipywidgets.FloatSlider` + a "Run
  simulation" button to `resolve_sim1()` → `compute_results()` →
  `build_kpis()`/`build_charts()` (all reused from Stage 5, now parameterised
  on a `results` DataFrame instead of a global), and re-renders the KPI
  tiles and charts inline in the notebook cell. It also calls
  `build_dashboard()` on every run, so `pep1t_dashboard.html` always reflects
  the most recently run depth if you want to share that one scenario.
- `continuous_update=False` on the slider means it only fires when you
  release it (or click Run), not on every pixel of drag — each move is a
  real 10-period CNS re-solve, not a cheap redraw.

## Stage 7 (slider inside the HTML page) specifics
- Stage 6's slider sits next to the notebook, outside the dashboard; this
  puts it **on the page** by running a tiny local Flask server in the same
  Python process as the already-solved GAMSPy model. The page's own JS
  calls `/api/resolve?depth=...` on the slider's `change` event (release)
  or the Run button; the server re-solves SIM1 (BAU is reused, same as
  Stage 6) and returns fresh KPI HTML + Plotly figure JSON, which the page
  swaps in with `Plotly.react()` — no page reload.
- `pep1t_dashboard.html` from Stage 5 is still the file to **share** (one
  frozen scenario, works anywhere, no server). This page only works while
  `pep_dashboard_server.py` is running — it's a local tool for *exploring*
  shock depths interactively, not something you can send someone else.
- A `threading.Lock` plus a single-threaded Flask dev server
  (`threaded=False`) guarantee only one re-solve runs at a time — GAMSPy's
  `Container`/`Variable` objects aren't thread-safe, so two overlapping
  solves would corrupt each other's results.
- Run `python pep_dashboard_server.py` and leave the terminal open (Ctrl+C
  stops it), or run `PEP1T_Stage7.ipynb` in Jupyter — importing the module
  starts the server on a background thread automatically, so the notebook
  stays usable. Either way it opens `http://127.0.0.1:5000` in your browser.
- Needs `pip install flask` in addition to everything else.
- The page shows a **live progress bar** while re-solving (Period *n* of 10,
  plus the solver status) instead of a single opaque "Solving..." message.
  This needed `run_loop()` (in `pep_solve.py`) split into a generator,
  `run_loop_steps()`, that yields a small progress dict after each period
  instead of just looping silently; `run_loop()` itself is now a thin
  wrapper that drives that generator under the existing tqdm bar (Stages 3
  & 6 are unaffected). The server streams those same per-period events to
  the browser over Server-Sent Events (`/api/resolve_stream`, one HTTP
  connection, `event: progress` per period then one final `event: result`
  with the KPI/chart payload) so the bar updates live as each period
  finishes, rather than polling or waiting for one big response at the end.

## Next step
Run `PEP1T_Stage3.ipynb` first and send me the first error. Once BAU and
SIM1 both solve, run `PEP1T_Stage4.ipynb` for the results table (expect a
second short round of fixes there given the column-name assumptions above),
then `PEP1T_Stage5.ipynb` for the static dashboard, `PEP1T_Stage6.ipynb` for
the notebook-widget slider, and `PEP1T_Stage7.ipynb` for the slider embedded
in the dashboard page itself.
