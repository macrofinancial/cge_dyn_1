# ---------------------------------------------------------------
# Run this AFTER: ctx = build_model(); ctx = run_simulation(ctx)
# (compute_results(ctx) is optional - this re-derives everything
# it needs directly from ctx, so it also fixes the missing-dF bug.)
# Produces one file: cge_dashboard_export.json
# ---------------------------------------------------------------
import json
import math

def recs(param, value_col="value"):
    """Parameter -> {tuple(index): value} dict, robust to 0-d / n-d domains."""
    df = param.records
    if df is None or len(df) == 0:
        return {}
    idx_cols = [c for c in df.columns if c != value_col]
    out = {}
    for row in df.itertuples(index=False):
        d = row._asdict()
        key = tuple(d[c] for c in idx_cols)
        out[key if len(key) > 1 else (key[0] if key else "scalar")] = d[value_col]
    return out

periods = [str(p) for p in range(31)]
sectors = ["AGR", "LMN", "HMN", "SRV"]
factors = ["CAP", "LAB"]

def series_by_sector(p0, p1, sectors=sectors, periods=periods):
    """% deviation path for a [sector, t] parameter pair."""
    d0, d1 = recs(p0), recs(p1)
    out = {}
    for s in sectors:
        path = []
        for t in periods:
            v0 = d0.get((s, t))
            v1 = d1.get((s, t))
            if v0 is None or v1 is None:
                path.append(None)
            elif abs(v0) < 1e-9:
                path.append(None)
            else:
                path.append((v1 / v0 - 1) * 100)
        out[s] = path
    return out

def scalar_series(p0, p1, periods=periods):
    d0, d1 = recs(p0), recs(p1)
    out = []
    for t in periods:
        v0 = d0.get(t)
        v1 = d1.get(t)
        out.append((v1 / v0 - 1) * 100 if v0 else None)
    return out

export = {}

# --- welfare: utility % change + EV level by period ---
dCC = scalar_series(ctx["CC0"], ctx["CC1"])
a = ctx["m"]["a"]
alpha = ctx["m"]["alpha"]
denom = a.records["value"].iloc[0] * math.prod(
    (alpha.records.set_index("i")["value"][s]) ** (alpha.records.set_index("i")["value"][s])
    for s in sectors
)
CC0d, CC1d = recs(ctx["CC0"]), recs(ctx["CC1"])
EV = [(CC1d[t] - CC0d[t]) / denom for t in periods]
ror = ctx["ror"].records["value"].iloc[0]
EV_TTL = sum(EV[int(t)] / (1 + ror) ** (int(t)) for t in periods)

export["welfare_path"] = [
    {"period": int(t), "utility_change_pct": dCC[i], "ev_level": EV[i]}
    for i, t in enumerate(periods)
]
export["ev_ttl"] = EV_TTL

# --- sectoral output path (dZ) ---
dZ = series_by_sector(ctx["Z0"], ctx["Z1"])
export["sectoral_path"] = [
    {"period": int(t), **{s: dZ[s][i] for s in sectors}}
    for i, t in enumerate(periods)
]

# --- factor demand path (dF) by factor x sector x period - THE MISSING PIECE ---
F0d, F1d = recs(ctx["F0"]), recs(ctx["F1"])
dF_path = {}
for h in factors:
    dF_path[h] = {}
    for s in sectors:
        path = []
        for t in periods:
            v0 = F0d.get((h, s, t))
            v1 = F1d.get((h, s, t))
            path.append((v1 / v0 - 1) * 100 if v0 else None)
        dF_path[h][s] = path
export["factor_path"] = dF_path

# --- capital stock path (dKK) ---
dKK = series_by_sector(ctx["KK0"], ctx["KK1"])
export["capital_path"] = [
    {"period": int(t), **{s: dKK[s][i] for s in sectors}}
    for i, t in enumerate(periods)
]

# --- composite good price path (dpq) ---
dpq = series_by_sector(ctx["pq0"], ctx["pq1"])
export["price_path"] = [
    {"period": int(t), **{s: dpq[s][i] for s in sectors}}
    for i, t in enumerate(periods)
]

# --- exchange rate path ---
export["exchange_rate_path"] = scalar_series(ctx["epsilon0"], ctx["epsilon1"])

# --- trade (levels, not deviations) every period ---
E1d, M1d = recs(ctx["E1"]), recs(ctx["M1"])
pWe = recs(ctx["pWe"]) if "pWe" in ctx else None
trade = []
for t in periods:
    exp = sum(E1d.get((s, t), 0) for s in sectors)
    imp = sum(M1d.get((s, t), 0) for s in sectors)
    trade.append({"period": int(t), "exports": exp, "imports": imp, "balance": exp - imp})
export["trade_path"] = trade

# --- SAM / calibration metadata, for context ---
export["meta"] = {
    "ror": ror,
    "dep": ctx["dep"].records["value"].iloc[0],
    "pop": ctx["pop"].records["value"].iloc[0],
    "sectors": sectors,
    "factors": factors,
}

with open("cge_dashboard_export.json", "w") as f:
    json.dump(export, f, indent=2)

print("Wrote cge_dashboard_export.json")
print("EV_TTL =", EV_TTL)
print("Utility change at t=30:", dCC[-1])
