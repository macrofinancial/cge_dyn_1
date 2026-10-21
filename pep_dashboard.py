"""
pep_dashboard.py
=================
Stage 5: a single self-contained HTML dashboard summarising the BAU vs SIM1
results produced by pep_results.py - Real GDP, sectoral output (volume and
price), and household income, plus four headline KPI tiles.

Variable mapping (from PEP_1-t-b_v2_1.gms section 5.9/5.10):
  GDP_MP_REAL(time)   Real GDP at market prices           -> KPI tile + line chart
  PIXGDP(time)        GDP deflator (Fischer index)         -> KPI tile
  XST(j,time)         Total aggregate output of industry j -> sectoral quantity chart
  PT(j,time)          Basic price of industry j's output   -> sectoral price chart
  YH(h,time)          Total income of household type h     -> KPI tile + income chart

Run (after Stage 4, which this imports and therefore re-runs automatically):
    pip install plotly
    python pep_dashboard.py
This writes `pep1t_dashboard.html` - open it in any browser (no internet
needed; the chart library is embedded in the file).
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs

from pep_results import *  # noqa: F401,F403  (runs BAU+SIM1+Stage4, gives `results`)

# ===========================================================================
# Palette (fixed categorical order - see the data-viz skill's reference
# palette). Two roles only: a hue per entity (sector / household), and a
# dash style per scenario (color stays constant across scenarios so a
# reader compares BAU vs SIM1 by line style, not by hunting for a new hue).
# ===========================================================================
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
               "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"
GOOD = "#0ca30c"
CRITICAL = "#d03b3b"

SCEN_DASH = {"bau": "solid", "sim1": "dash"}
SCEN_LABEL = {"bau": "BAU", "sim1": "SIM1"}


def color_for(labels):
    """Fixed-order hue assignment; falls back to 'Other' past 8 entities."""
    labels = list(labels)
    mapping = {lab: CATEGORICAL[i % len(CATEGORICAL)] for i, lab in enumerate(labels)}
    return mapping


def period_sort(times):
    return sorted(times, key=lambda t: int(t))


# ===========================================================================
# Pull the slices we need straight out of `results` (variable | dims | time
# | bau | sim1 | var_pct), which pep_results.py already built.
# ===========================================================================
def series(results_df, varname, dims_filter=None):
    df = results_df[results_df["variable"] == varname].copy()
    if dims_filter is not None:
        df = df[df["dims"] == dims_filter]
    df["t"] = df["time"].astype(int)
    return df.sort_values("t")


def pivot_by_dims(results_df, varname):
    """variable with a j/h/i domain -> {dims_value: df sorted by time}."""
    df = results_df[results_df["variable"] == varname].copy()
    df["t"] = df["time"].astype(int)
    out = {}
    for dims_val, g in df.groupby("dims"):
        out[dims_val] = g.sort_values("t")
    return out


# ===========================================================================
# KPI tiles
# ===========================================================================
def fmt(v, decimals=1):
    if v is None or pd.isna(v):
        return "-"
    return f"{v:,.{decimals}f}"


def kpi_tile(label, bau_val, sim1_val, unit="", decimals=1, higher_is_good=True):
    delta_pct = None
    if bau_val not in (None,) and bau_val not in (0,) and not pd.isna(bau_val) and not pd.isna(sim1_val):
        delta_pct = (sim1_val / bau_val - 1) * 100
    delta_html = ""
    if delta_pct is not None:
        good = (delta_pct >= 0) == higher_is_good
        color = GOOD if good else CRITICAL
        arrow = "▲" if delta_pct >= 0 else "▼"
        delta_html = (f'<span class="kpi-delta" style="color:{color}">'
                      f'{arrow} {abs(delta_pct):,.1f}%</span>')
    return f"""
    <div class="kpi-tile">
      <div class="kpi-label">{label}</div>
      <div class="kpi-row"><span class="kpi-scen">BAU</span>
        <span class="kpi-value">{fmt(bau_val, decimals)}{unit}</span></div>
      <div class="kpi-row"><span class="kpi-scen">SIM1</span>
        <span class="kpi-value">{fmt(sim1_val, decimals)}{unit}</span> {delta_html}</div>
    </div>"""


def build_kpis(results_df):
    last_t = period_sort(results_df["time"].dropna().unique())[-1]

    gdp = series(results_df, "GDP_MP_REAL", dims_filter="")
    gdp_last = gdp[gdp["time"] == last_t].iloc[0] if not gdp.empty else None
    gdp_first = gdp[gdp["t"] == gdp["t"].min()].iloc[0] if not gdp.empty else None

    defl = series(results_df, "PIXGDP", dims_filter="")
    defl_last = defl[defl["time"] == last_t].iloc[0] if not defl.empty else None

    yh = results_df[results_df["variable"] == "YH"].copy()
    yh_last = yh[yh["time"] == last_t]
    yh_bau_tot = yh_last["bau"].sum() if not yh_last.empty else None
    yh_sim1_tot = yh_last["sim1"].sum() if not yh_last.empty else None

    tiles = []
    tiles.append(kpi_tile(f"Real GDP, market prices (period {last_t})",
                           gdp_last["bau"] if gdp_last is not None else None,
                           gdp_last["sim1"] if gdp_last is not None else None))
    if gdp_last is not None and gdp_first is not None:
        bau_growth = (gdp_last["bau"] / gdp_first["bau"] - 1) * 100 if gdp_first["bau"] else None
        sim1_growth = (gdp_last["sim1"] / gdp_first["sim1"] - 1) * 100 if gdp_first["sim1"] else None
        tiles.append(kpi_tile(f"Cumulative real GDP growth (period {gdp_first['time']}→{last_t})",
                               bau_growth, sim1_growth, unit="%", decimals=1))
    tiles.append(kpi_tile(f"GDP deflator, Fischer index (period {last_t})",
                           defl_last["bau"] if defl_last is not None else None,
                           defl_last["sim1"] if defl_last is not None else None,
                           decimals=3))
    tiles.append(kpi_tile(f"Total household income (period {last_t})",
                           yh_bau_tot, yh_sim1_tot))
    return "\n".join(tiles)


# ===========================================================================
# Charts
# ===========================================================================
def line_chart(title, subtitle, series_dict, y_title):
    """series_dict: {entity_label: df with columns t,time,bau,sim1}"""
    colors = color_for(series_dict.keys())
    fig = go.Figure()
    for label, df in series_dict.items():
        for scen in ("bau", "sim1"):
            fig.add_trace(go.Scatter(
                x=df["t"], y=df[scen],
                name=f"{label} – {SCEN_LABEL[scen]}",
                legendgroup=label,
                mode="lines",
                line=dict(color=colors[label], width=2, dash=SCEN_DASH[scen]),
                hovertemplate=f"%{{y:,.1f}}<extra>{label} – {SCEN_LABEL[scen]}</extra>",
            ))
    fig.update_layout(
        title=dict(text=f"{title}<br><span style='font-size:12px;color:{INK_SECONDARY}'>{subtitle}</span>"),
        plot_bgcolor=SURFACE, paper_bgcolor=SURFACE,
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK_PRIMARY, size=13),
        xaxis=dict(title="Period", gridcolor=GRID, zeroline=False, linecolor=GRID),
        yaxis=dict(title=y_title, gridcolor=GRID, zeroline=False, linecolor=GRID),
        hovermode="x unified",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=60, r=20, t=70, b=40),
        height=420,
    )
    return fig


def build_charts(results_df):
    gdp = series(results_df, "GDP_MP_REAL", dims_filter="")
    gdp_fig = line_chart("Real GDP (market prices)", "Solid = BAU, dashed = SIM1",
                          {"Real GDP": gdp}, "Real GDP")

    xst = pivot_by_dims(results_df, "XST")
    xst_fig = line_chart("Sectoral output – volume", "Solid = BAU, dashed = SIM1 · color = sector",
                          xst, "Output volume (XST)")

    pt = pivot_by_dims(results_df, "PT")
    pt_fig = line_chart("Sectoral output – price", "Solid = BAU, dashed = SIM1 · color = sector",
                         pt, "Basic price (PT)")

    yh = pivot_by_dims(results_df, "YH")
    yh_fig = line_chart("Household income", "Solid = BAU, dashed = SIM1 · color = household type",
                         yh, "Income (YH)")
    return gdp_fig, xst_fig, pt_fig, yh_fig


# ===========================================================================
# Assemble the page
# ===========================================================================
def to_div(fig, div_id):
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, div_id=div_id)


def build_dashboard(results_df, out_path="pep1t_dashboard.html"):
    kpis_html = build_kpis(results_df)
    gdp_fig, xst_fig, pt_fig, yh_fig = build_charts(results_df)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PEP-1-t results dashboard</title>
<script>{get_plotlyjs()}</script>
<style>
  :root {{
    --surface-1: {SURFACE}; --page: #f9f9f7; --ink-1: {INK_PRIMARY};
    --ink-2: {INK_SECONDARY}; --ink-muted: {INK_MUTED}; --border: #e1e0d9;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--page); color: var(--ink-1);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  .wrap {{ max-width: 1180px; margin: 0 auto; padding: 24px 16px 48px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  .lede {{ color: var(--ink-2); margin: 0 0 24px; font-size: 14px; }}
  .kpi-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    margin-bottom: 28px;
  }}
  @media (max-width: 900px) {{ .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  .kpi-tile {{
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px 16px;
  }}
  .kpi-label {{ font-size: 12px; color: var(--ink-2); margin-bottom: 8px; min-height: 32px; }}
  .kpi-row {{ display: flex; align-items: baseline; justify-content: space-between; }}
  .kpi-scen {{ font-size: 11px; color: var(--ink-muted); text-transform: uppercase; letter-spacing: .03em; }}
  .kpi-value {{ font-size: 18px; font-weight: 600; font-variant-numeric: tabular-nums; }}
  .kpi-delta {{ font-size: 12px; font-weight: 600; margin-left: 6px; }}
  .chart-card {{
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 8px; margin-bottom: 20px;
  }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  @media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
  footer {{ color: var(--ink-muted); font-size: 12px; margin-top: 8px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>PEP-1-t: BAU vs SIM1 results</h1>
  <p class="lede">Tariff-elimination simulation vs business-as-usual, generated from
     pep1t_results.xlsx. Hover any chart for exact values.</p>

  <div class="kpi-grid">{kpis_html}</div>

  <div class="chart-card">{to_div(gdp_fig, "gdp")}</div>
  <div class="grid-2">
    <div class="chart-card">{to_div(xst_fig, "xst")}</div>
    <div class="chart-card">{to_div(pt_fig, "pt")}</div>
  </div>
  <div class="chart-card">{to_div(yh_fig, "yh")}</div>

  <footer>Generated by pep_dashboard.py. BAU = baseline; SIM1 = gradual tariff-elimination simulation.</footer>
</div>
</body>
</html>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved {out_path} - open it in any browser.")


if __name__ == "__main__":
    build_dashboard(results)
else:
    build_dashboard(results)
