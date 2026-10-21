"""
pep_results.py
===============
GAMSPy translation of RESULTS_PEP_1-t-b_BAU.gms and RESULTS_PEP_1-t-b_SIM1.GMS.

Those two .gms files:
  - snapshot every model variable's solved level into valX(...,'bau') /
    valX(...,'sim1') parameters,
  - compute four "chained" price indices recursively over time
    (valPIXCON_C, valPIXGDP_C, valPIXINV_PRI_C, valPIXINV_PUB_C),
  - compute valX(...,'var') = percentage deviation of sim1 from bau
    wherever the bau value is nonzero (the GAMS $ dollar guard),
  - write everything to a GDX file and convert it to .xls with gdx2xls.

Since every PEP1T variable is declared over the FULL TIME domain and each
period's solve only touches that period, by the time pep_solve.py's BAU and
SIM1 loops finish, each variable's `.records` already holds its complete
ten-period time series - `bau_panel`/`sim1_panel` (built in pep_solve.py)
are exactly the "valX(...,'bau')" / "valX(...,'sim1')" tables, just not yet
flattened into one long table. This script does that flattening, the
chained-index recursion, the var(%) comparison, and an Excel export (no
GDX/gdx2xls available outside GAMS, so this writes pep1t_results.xlsx /
pep1t_parameters.xlsx directly with pandas/openpyxl instead).

Run (after Stage 3, which this imports and therefore re-runs automatically):
    python pep_results.py
"""
import pandas as pd

from pep_solve import *  # noqa: F401,F403  (runs BAU+SIM1, gives bau_panel/sim1_panel)

ATTR_COLS = {"level", "marginal", "lower", "upper", "scale"}


def dim_names(varname: str):
    """Column names for a variable's domain, in GAMSPy's convention of
    naming each column after its domain Set."""
    v = m[varname]
    return [d.name for d in v.domain]


def to_long(panel: dict, scen: str) -> pd.DataFrame:
    """Flatten {varname: records_df} into one long table:
    variable | dims (joined as one string key) | time | value | scen
    """
    frames = []
    for name, df in panel.items():
        dims = dim_names(name)
        d = df.copy()
        if "TIME" in dims:
            time_col = "TIME"
            other = [c for c in dims if c != "TIME"]
        else:
            time_col = None
            other = dims
        d["variable"] = name
        d["dims"] = d[other].astype(str).agg(",".join, axis=1) if other else ""
        d["time"] = d[time_col] if time_col else ""
        d["value"] = d["level"]
        d["scen"] = scen
        frames.append(d[["variable", "dims", "time", "value", "scen"]])
    return pd.concat(frames, ignore_index=True)


# ===========================================================================
# Chained price indices (recursive over time, computed separately per
# scenario - .gms "loop[time$(ord(time) gt 1), ...]" blocks)
# ===========================================================================
def _sum_by(df: pd.DataFrame, group_cols: list, value_col="level"):
    return df.groupby(group_cols)[value_col].sum()


def chained_indices(panel: dict) -> pd.DataFrame:
    """Returns a DataFrame indexed by period with columns
    PIXCON_C, PIXGDP_C, PIXINV_PRI_C, PIXINV_PUB_C for one scenario's panel."""
    PC_df, C_df = panel["PC"], panel["C"]
    PVA_df, VA_df = panel["PVA"], panel["VA"]

    # sum_h C(i,h,t) per (i,t)
    C_by_it = _sum_by(C_df, ["i", "TIME"])

    out = {}
    out[PERIODS[0]] = {"PIXCON_C": 1.0, "PIXGDP_C": 1.0,
                        "PIXINV_PRI_C": 1.0, "PIXINV_PUB_C": 1.0}
    # .gms seeds valPIXCON_C(t1,...) = PIXCON.l(t1) (==1 at the benchmark,
    # since PIXCONO etc. are normalised to 1 and period 1 starts there too)

    # gamma_INVPRI/gamma_INVPUB are Parameters, whose .records columns are
    # [domain..., "value"] (not "level" - that's for Variables).
    gINVPRI = (dict(zip(gamma_INVPRI.records["i"], gamma_INVPRI.records["value"]))
               if gamma_INVPRI.records is not None else {})
    gINVPUB = (dict(zip(gamma_INVPUB.records["i"], gamma_INVPUB.records["value"]))
               if gamma_INVPUB.records is not None else {})

    PC_pivot = PC_df.pivot(index="i", columns="TIME", values="level")

    for idx in range(1, len(PERIODS)):
        t_cur, t_prev = PERIODS[idx], PERIODS[idx - 1]

        num = sum(PC_pivot.loc[i_, t_cur] * C_by_it.get((i_, t_prev), 0.0) for i_ in PC_pivot.index)
        den = sum(PC_pivot.loc[i_, t_prev] * C_by_it.get((i_, t_prev), 0.0) for i_ in PC_pivot.index)
        pixcon_c = out[t_prev]["PIXCON_C"] * (num / den if den else 1.0)

        va_prev = VA_df[VA_df["TIME"] == t_prev].set_index("j")["level"]
        va_cur = VA_df[VA_df["TIME"] == t_cur].set_index("j")["level"]
        pva_prev = PVA_df[PVA_df["TIME"] == t_prev].set_index("j")["level"]
        pva_cur = PVA_df[PVA_df["TIME"] == t_cur].set_index("j")["level"]
        s1 = (pva_cur * va_prev).sum()
        s2 = (pva_prev * va_prev).sum()
        s3 = (pva_cur * va_cur).sum()
        s4 = (pva_prev * va_cur).sum()
        pixgdp_c = out[t_prev]["PIXGDP_C"] * ((s1 / s2) * (s3 / s4)) ** 0.5 if s2 and s4 else out[t_prev]["PIXGDP_C"]

        prod_pri = 1.0
        for i_, share in gINVPRI.items():
            if share and PC_pivot.loc[i_, t_prev]:
                prod_pri *= (PC_pivot.loc[i_, t_cur] / PC_pivot.loc[i_, t_prev]) ** share
        pixinvpri_c = out[t_prev]["PIXINV_PRI_C"] * prod_pri

        prod_pub = 1.0
        for i_, share in gINVPUB.items():
            if share and PC_pivot.loc[i_, t_prev]:
                prod_pub *= (PC_pivot.loc[i_, t_cur] / PC_pivot.loc[i_, t_prev]) ** share
        pixinvpub_c = out[t_prev]["PIXINV_PUB_C"] * prod_pub

        out[t_cur] = {"PIXCON_C": pixcon_c, "PIXGDP_C": pixgdp_c,
                      "PIXINV_PRI_C": pixinvpri_c, "PIXINV_PUB_C": pixinvpub_c}

    return pd.DataFrame(out).T.rename_axis("time").reset_index()


def compute_results(bau_panel: dict, sim1_panel: dict) -> pd.DataFrame:
    """Everything from 'flatten the two panels' through the merged
    BAU/SIM1/var(%) table, as a function of the two panels rather than the
    module-level globals - so the Stage 6 interactive dashboard can call
    this again with a freshly re-solved `sim1_panel` (same `bau_panel`,
    since the shock doesn't touch BAU) without re-running anything else."""
    print("Computing chained price indices (BAU)...")
    bau_chained = chained_indices(bau_panel)
    print("Computing chained price indices (SIM1)...")
    sim1_chained = chained_indices(sim1_panel)

    print("Flattening BAU and SIM1 panels...")
    bau_long = to_long(bau_panel, "bau")
    sim1_long = to_long(sim1_panel, "sim1")

    merged = pd.merge(
        bau_long[["variable", "dims", "time", "value"]].rename(columns={"value": "bau"}),
        sim1_long[["variable", "dims", "time", "value"]].rename(columns={"value": "sim1"}),
        on=["variable", "dims", "time"], how="outer",
    )
    merged["var_pct"] = None
    mask = merged["bau"].notna() & (merged["bau"] != 0) & merged["sim1"].notna()
    merged.loc[mask, "var_pct"] = (merged.loc[mask, "sim1"] / merged.loc[mask, "bau"] - 1) * 100

    chained_long = pd.concat([
        bau_chained.melt(id_vars="time", var_name="variable", value_name="bau"),
        sim1_chained.melt(id_vars="time", var_name="variable", value_name="sim1"),
    ]).groupby(["variable", "time"], as_index=False).first()
    chained_long["dims"] = ""
    chained_long["var_pct"] = None
    cmask = chained_long["bau"].notna() & (chained_long["bau"] != 0) & chained_long["sim1"].notna()
    chained_long.loc[cmask, "var_pct"] = (chained_long.loc[cmask, "sim1"] / chained_long.loc[cmask, "bau"] - 1) * 100

    return pd.concat([merged, chained_long[["variable", "dims", "time", "bau", "sim1", "var_pct"]]],
                      ignore_index=True)


results = compute_results(bau_panel, sim1_panel)

results.to_excel("pep1t_results.xlsx", index=False, sheet_name="Results")
print(f"Saved pep1t_results.xlsx - {len(results)} rows "
      f"(variable | dims | time | bau | sim1 | var_pct).")

# ===========================================================================
# Parameters export (.gms "execute_unload Parameters, ..." block)
# ===========================================================================
param_frames = []
for name in m.listParameters():
    p = m[name]
    recs = p.records
    if recs is None or len(recs) == 0:
        continue
    dims = [d.name for d in p.domain] if p.domain else []
    d = recs.copy()
    d["variable"] = name
    d["dims"] = d[dims].astype(str).agg(",".join, axis=1) if dims else ""
    param_frames.append(d[["variable", "dims", "value"]])
params_long = pd.concat(param_frames, ignore_index=True)
params_long.to_excel("pep1t_parameters.xlsx", index=False, sheet_name="Parameters")
print(f"Saved pep1t_parameters.xlsx - {len(params_long)} rows.")
