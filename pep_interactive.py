"""
pep_interactive.py
===================
Stage 6: an ipywidgets control panel that makes the dashboard interactive -
move the "tariff shock depth" slider, click "Run simulation", and the KPI
tiles + charts re-render against a freshly re-solved SIM1.

Why this can't be a slider inside the static HTML file: SIM1 isn't a
post-processing step on numbers that already exist - it's a GAMSPy CNS
solve of ~108 equations, one period at a time. A browser has nothing to
solve that with. So "interactive" here means: the slider lives in Jupyter
(where GAMSPy actually runs), re-solving is one click away, and the result
re-renders inline - plus still writes a fresh pep1t_dashboard.html each
time, in case you want to share a specific run as a standalone file.

BAU is untouched by the shock, so only SIM1 (ten CNS solves) re-runs on
each click - the slower one-time cost (BAU + first SIM1) already happened
on import, same as Stages 3-5.

Run (after Stage 5, which this imports):
    pip install ipywidgets
    python pep_interactive.py        # prints instead of rendering widgets
Or, better, open PEP1T_Stage6.ipynb in Jupyter and run all cells - the
slider only renders in a notebook.
"""
import plotly.graph_objects as go
from IPython.display import display, clear_output, HTML

from pep_dashboard import *  # noqa: F401,F403  (bau_panel, resolve_sim1, compute_results,
                              # build_kpis, build_charts, build_dashboard, results, PERIODS)

try:
    import ipywidgets as widgets
except ImportError:  # pragma: no cover
    widgets = None
    print("ipywidgets isn't installed - run `pip install ipywidgets` to use "
          "the interactive panel. Falling back to one static render below.")

KPI_STYLE = """
<style>
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 8px 0 20px; }
  .kpi-tile { background: #fcfcfb; border: 1px solid #e1e0d9; border-radius: 10px; padding: 14px 16px;
              font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }
  .kpi-label { font-size: 12px; color: #52514e; margin-bottom: 8px; min-height: 32px; }
  .kpi-row { display: flex; align-items: baseline; justify-content: space-between; }
  .kpi-scen { font-size: 11px; color: #898781; text-transform: uppercase; letter-spacing: .03em; }
  .kpi-value { font-size: 18px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .kpi-delta { font-size: 12px; font-weight: 600; margin-left: 6px; }
</style>
"""


def render(results_df, title="Results"):
    """Show the KPI tiles + the four charts inline in the current cell
    output, and (re)write the standalone pep1t_dashboard.html alongside."""
    kpis_html = build_kpis(results_df)
    display(HTML(f"{KPI_STYLE}<h3>{title}</h3><div class='kpi-grid'>{kpis_html}</div>"))
    for fig in build_charts(results_df):
        display(fig)
    build_dashboard(results_df)  # also refreshes the shareable standalone file
    print("Saved pep1t_dashboard.html")


def run_and_render(depth: float):
    """Re-solve SIM1 at the given shock depth, rebuild the results table
    (BAU is reused as-is), and render."""
    print(f"Re-solving SIM1 at shock depth {depth:.2f} "
          f"({'no shock' if depth == 0 else f'tariffs reach {100*(1-depth):.0f}% of original by period ' + PERIODS[-1]})...")
    new_sim1_panel = resolve_sim1(depth=depth)
    new_results = compute_results(bau_panel, new_sim1_panel)
    render(new_results, title=f"Results – shock depth {depth:.2f}")
    return new_results


# ===========================================================================
# ipywidgets panel
# ===========================================================================
if widgets is not None:
    depth_slider = widgets.FloatSlider(
        value=1.0, min=0.0, max=1.5, step=0.05,
        description="Shock depth", continuous_update=False,  # fire only on release, not every pixel
        style={"description_width": "initial"}, layout=widgets.Layout(width="420px"),
    )
    run_button = widgets.Button(description="Run simulation", button_style="primary")
    out = widgets.Output()

    def _on_click(_):
        with out:
            clear_output(wait=True)
            run_and_render(depth_slider.value)

    run_button.on_click(_on_click)

    hint = widgets.HTML(
        "<span style='color:#52514e;font-size:12px'>0 = no shock (SIM1 = BAU) &nbsp;·&nbsp; "
        "1 = original .gms shock (tariffs → 0 by the final period) &nbsp;·&nbsp; "
        "&gt;1 = a deeper/faster cut than the original. Drag, then click Run.</span>"
    )
    panel = widgets.VBox([widgets.HBox([depth_slider, run_button]), hint, out])
    display(panel)
    # Show the already-solved depth=1.0 run once on load, so there's
    # something on screen before the first click.
    with out:
        render(results, title="Results – shock depth 1.00 (initial run)")
else:
    render(results, title="Results (depth=1.00, static - install ipywidgets for the slider)")
