"""
pep_dashboard_server.py
========================
Stage 7: puts the "shock depth" slider *inside* the dashboard page itself,
instead of next to it in a Jupyter widget (Stage 6).

Moving the slider still has to trigger a real GAMSPy re-solve of SIM1 (ten
CNS periods) - a static HTML file has no solver, so there's no way around
running Python somewhere. What this does is run a tiny local web server
(Flask) in this same process, right alongside the already-solved GAMSPy
model: the page's own JavaScript calls back into this process over HTTP
when you release the slider, the server re-solves SIM1 at the new depth,
and the page updates its KPI tiles and charts in place (Plotly.react(), no
full reload) - open http://127.0.0.1:5000 and the slider lives right there
on the page, no separate notebook cell needed.

Run (after Stage 5, which this imports):
    pip install flask
    python pep_dashboard_server.py
then open the URL it prints. Leave the terminal running - closing it (or
Ctrl+C) stops the server.

In Jupyter: just run PEP1T_Stage7.ipynb - importing this module starts the
server on a background thread automatically, so the kernel stays usable.
"""
import json
import threading
import time
import webbrowser

import plotly.utils

from pep_dashboard import *  # noqa: F401,F403  (bau_panel, resolve_sim1, compute_results,
                              # build_kpis, build_charts, results, CATEGORICAL, etc.)

try:
    from flask import Flask, Response, jsonify, request, stream_with_context
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pep_dashboard_server.py needs Flask to serve the interactive page - "
        "run `pip install flask` and try again."
    ) from exc

app = Flask(__name__)
_solve_lock = threading.Lock()  # GAMSPy's Container/Variables aren't thread-safe;
                                 # this plus the single-threaded dev server below
                                 # guarantees only one solve runs at a time.

# ===========================================================================
# Turning a results table into what the page needs
# ===========================================================================
CHART_IDS = ["gdp", "xst", "pt", "yh"]


def _payload(results_df) -> dict:
    kpis_html = build_kpis(results_df)
    figs = build_charts(results_df)
    charts = {
        name: json.loads(json.dumps(fig.to_plotly_json(), cls=plotly.utils.PlotlyJSONEncoder))
        for name, fig in zip(CHART_IDS, figs)
    }
    return {"kpis_html": kpis_html, "charts": charts}


_INITIAL_PAYLOAD = _payload(results)  # the depth=1.0 run already solved on import - free


# ===========================================================================
# Routes
# ===========================================================================
@app.route("/api/resolve_stream")
def api_resolve_stream():
    """Server-Sent Events: solves SIM1 one period at a time and streams a
    "progress" event after each one, then a final "result" event carrying
    the KPI tiles + chart JSON - so the browser can show a live progress
    bar across the whole re-solve instead of one opaque "Solving..." spinner."""
    try:
        depth = float(request.args.get("depth", "1.0"))
    except ValueError:
        return jsonify({"error": "depth must be a number"}), 400

    def generate():
        with _solve_lock:
            print(f"[server] re-solving SIM1 at depth={depth:.2f} ...")
            new_sim1_panel = None
            for step in resolve_sim1_steps(depth=depth):
                if step.get("done"):
                    new_sim1_panel = step["panel"]
                else:
                    yield f"event: progress\ndata: {json.dumps(step)}\n\n"
            new_results = compute_results(bau_panel, new_sim1_panel)
            payload = _payload(new_results)
            yield f"event: result\ndata: {json.dumps(payload)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/")
def index():
    return PAGE_HTML


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PEP-1-t results dashboard</title>
<script>__PLOTLYJS__</script>
<style>
  :root {
    --surface-1: #fcfcfb; --page: #f9f9f7; --ink-1: #0b0b0b;
    --ink-2: #52514e; --ink-muted: #898781; --border: #e1e0d9;
    --accent: #2a78d6; --good: #0ca30c; --critical: #d03b3b;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--page); color: var(--ink-1);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  .wrap { max-width: 1180px; margin: 0 auto; padding: 24px 16px 48px; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  .lede { color: var(--ink-2); margin: 0 0 20px; font-size: 14px; }
  .control-bar {
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px 18px; margin-bottom: 24px;
  }
  .control-bar label { font-size: 13px; color: var(--ink-2); white-space: nowrap; }
  .control-bar input[type=range] { width: 320px; accent-color: var(--accent); }
  #depthValue { font-variant-numeric: tabular-nums; font-weight: 600; min-width: 2.6em; display: inline-block; }
  #runBtn {
    background: var(--accent); color: #fff; border: none; border-radius: 8px;
    padding: 9px 18px; font-size: 14px; font-weight: 600; cursor: pointer;
  }
  #runBtn:disabled { opacity: .55; cursor: progress; }
  #status { font-size: 13px; color: var(--ink-muted); }
  .hint { font-size: 12px; color: var(--ink-muted); width: 100%; }
  .progress-wrap { width: 100%; display: none; align-items: center; gap: 10px; }
  .progress-track { flex: 1; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
  .progress-fill { height: 100%; width: 0%; background: var(--accent); transition: width .2s ease; }
  .progress-label { font-size: 12px; color: var(--ink-muted); white-space: nowrap; font-variant-numeric: tabular-nums; }
  .kpi-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    margin-bottom: 28px;
  }
  @media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
  .kpi-tile {
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px 16px;
  }
  .kpi-label { font-size: 12px; color: var(--ink-2); margin-bottom: 8px; min-height: 32px; }
  .kpi-row { display: flex; align-items: baseline; justify-content: space-between; }
  .kpi-scen { font-size: 11px; color: var(--ink-muted); text-transform: uppercase; letter-spacing: .03em; }
  .kpi-value { font-size: 18px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .kpi-delta { font-size: 12px; font-weight: 600; margin-left: 6px; }
  .chart-card {
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 8px; margin-bottom: 20px; position: relative;
  }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }
  footer { color: var(--ink-muted); font-size: 12px; margin-top: 8px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>PEP-1-t: BAU vs SIM1 results</h1>
  <p class="lede">Tariff-elimination simulation vs business-as-usual. Drag the
     slider and click Run to re-solve SIM1 at a different shock strength.</p>

  <div class="control-bar">
    <label for="depthSlider">Shock depth</label>
    <input type="range" id="depthSlider" min="0" max="1.5" step="0.05" value="1.0">
    <span id="depthValue">1.00</span>
    <button id="runBtn">Run simulation</button>
    <span id="status">Showing the initial run (depth 1.00 — the original .gms shock).</span>
    <span class="hint">0 = no shock (SIM1 = BAU) &nbsp;·&nbsp; 1 = original shock (tariffs → 0 by the
      final period) &nbsp;·&nbsp; above 1 = faster/deeper than the original.</span>
    <div class="progress-wrap" id="progressWrap">
      <div class="progress-track"><div class="progress-fill" id="progressFill"></div></div>
      <span class="progress-label" id="progressLabel"></span>
    </div>
  </div>

  <div id="kpis" class="kpi-grid"></div>

  <div class="chart-card"><div id="gdp"></div></div>
  <div class="grid-2">
    <div class="chart-card"><div id="xst"></div></div>
    <div class="chart-card"><div id="pt"></div></div>
  </div>
  <div class="chart-card"><div id="yh"></div></div>

  <footer>Served by pep_dashboard_server.py. BAU = baseline; SIM1 = tariff-elimination simulation at the chosen depth.</footer>
</div>

<script>
window.__INITIAL__ = __INITIAL_PAYLOAD__;

function renderKpis(html) {
  document.getElementById('kpis').innerHTML = html;
}
function renderCharts(charts) {
  for (const [id, fig] of Object.entries(charts)) {
    Plotly.react(id, fig.data, fig.layout, {responsive: true});
  }
}
function setBusy(busy, text) {
  document.getElementById('runBtn').disabled = busy;
  document.getElementById('depthSlider').disabled = busy;
  if (text) document.getElementById('status').textContent = text;
}
function showProgress() {
  document.getElementById('progressWrap').style.display = 'flex';
  document.getElementById('progressFill').style.width = '0%';
  document.getElementById('progressLabel').textContent = 'Starting…';
}
function updateProgress(step) {
  const pct = Math.round((step.index / step.total) * 100);
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressLabel').textContent =
    `Period ${step.period} of ${step.total} (${pct}%)` + (step.status ? ` — ${step.status}` : '');
}

document.addEventListener('DOMContentLoaded', () => {
  renderKpis(window.__INITIAL__.kpis_html);
  renderCharts(window.__INITIAL__.charts);

  const slider = document.getElementById('depthSlider');
  const valueLabel = document.getElementById('depthValue');
  const runBtn = document.getElementById('runBtn');

  slider.addEventListener('input', () => {
    valueLabel.textContent = parseFloat(slider.value).toFixed(2);
  });

  function run() {
    const depth = parseFloat(slider.value);
    setBusy(true, `Solving SIM1 at depth ${depth.toFixed(2)}…`);
    showProgress();

    const es = new EventSource(`/api/resolve_stream?depth=${depth}`);
    es.addEventListener('progress', (e) => {
      updateProgress(JSON.parse(e.data));
    });
    es.addEventListener('result', (e) => {
      const payload = JSON.parse(e.data);
      renderKpis(payload.kpis_html);
      renderCharts(payload.charts);
      document.getElementById('progressFill').style.width = '100%';
      document.getElementById('progressLabel').textContent = 'Done';
      setBusy(false, `Done — shock depth ${depth.toFixed(2)}.`);
      es.close();
    });
    es.onerror = () => {
      setBusy(false, 'Error while solving — check the terminal/notebook running the server.');
      es.close();
    };
  }

  runBtn.addEventListener('click', run);
  // Also run when the slider is released (mouse/touch/keyboard), so a drag
  // + release behaves the same as drag + click Run.
  slider.addEventListener('change', run);
});
</script>
</body>
</html>"""


def _get_plotlyjs():
    from plotly.offline import get_plotlyjs
    return get_plotlyjs()


PAGE_HTML = (PAGE_TEMPLATE
             .replace("__PLOTLYJS__", _get_plotlyjs())
             .replace("__INITIAL_PAYLOAD__", json.dumps(_INITIAL_PAYLOAD)))


# ===========================================================================
# Starting the server
# ===========================================================================
_SERVER_THREAD = None


def start_in_thread(port=5000, open_browser=True):
    """Starts the server on a background thread and returns immediately -
    what the Stage 7 notebook calls, so the kernel stays usable."""
    global _SERVER_THREAD
    url = f"http://127.0.0.1:{port}"
    if _SERVER_THREAD is not None:
        print(f"Already running at {url}")
        return _SERVER_THREAD
    _SERVER_THREAD = threading.Thread(
        target=lambda: app.run(port=port, debug=False, use_reloader=False, threaded=False),
        daemon=True,
    )
    _SERVER_THREAD.start()
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"Serving the interactive dashboard at {url}")
    return _SERVER_THREAD


start_in_thread()

if __name__ == "__main__":
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped.")
