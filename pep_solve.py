"""
pep_solve.py
============
GAMSPy translation of PEP_1-t-b_v2_1.gms, SECTION 6 (Resolution):
  6.1 BAU   - solve the model one period at a time to generate a baseline
  6.2 Simulation - same, but with a gradual tariff-elimination shock

Depends on pep_equations.py (which depends on pep_data.py).

GAMS's `LOOP(time, ...)` re-binds the symbol "time" to a single element on
each pass; GAMSPy has no symbolic equivalent, so this becomes an ordinary
Python `for` loop over the ten period labels "1".."10". Inside each
iteration we:
  1. point the dynamic subset T at just that one period (T.setRecords),
     which is what makes EQ1..WALRAS (defined with domain T - see
     pep_equations.py) generate only for the active period;
  2. set initial variable LEVELS (.l) and fixed values (.fx) exactly as the
     .gms file's loop body does, substituting the literal "time-1" lag with
     the previous period's string label (since it's known at each step);
  3. call PEP1T.solve().

Run (after Stage 1 & 2, which this script imports automatically):
    python pep_solve.py
"""
import pandas as pd
import gamspy as gp
from gamspy import Sum, Options, Problem

try:
    from tqdm.auto import tqdm  # nice widget bar in Jupyter, plain text bar elsewhere
except ImportError:  # pragma: no cover
    class _NoBar(list):
        """Fallback when tqdm isn't installed: behaves like the plain list of
        periods so the `for t_cur in bar:` loop still works, and swallows
        `.set_postfix(...)` calls so run_loop() doesn't need two code paths."""
        def set_postfix(self, *args, **kwargs):
            pass

    def tqdm(iterable, desc="", **kwargs):
        print(f"(tqdm not installed - run `pip install tqdm` for a progress bar; "
              f"continuing without one for '{desc}')")
        return _NoBar(iterable)

from pep_equations import *  # noqa: F401,F403

PERIODS = [str(t) for t in range(1, 11)]

# ===========================================================================
# 6. MODEL STATEMENT  (.gms lines 1429-1432)
# ===========================================================================
PEP1T = gp.Model(
    m,
    name="PEP1T",
    equations=m.getEquations(),
    problem=Problem.CNS,
)
# GAMS: PEP1T.HOLDFIXED=1;  -- keep fixed variables' marginals consistent
# across re-solves. GAMSPy's attribute name for this is unconfirmed in this
# sandbox (no GAMSPy install here) - if this line errors, drop it and tell
# me the exact AttributeError; it's a minor technical setting, not required
# for the model to solve correctly as a square CNS system.
try:
    PEP1T.hold_fixed = True
except Exception as exc:  # pragma: no cover
    print("NOTE: could not set hold_fixed on the model:", exc)

SOLVER = "conopt"  # .gms: OPTION NLP = conopt (GAMS uses this for CNS too)


# ===========================================================================
# Helpers
# ===========================================================================
def activate_period(t_cur: str):
    """GAMS: T(time) = YES;  (at top of each LOOP pass)"""
    T.setRecords([t_cur])


def deactivate_period():
    """GAMS: T(time) = NO;  (at bottom of each LOOP pass)"""
    T.setRecords([])


def init_levels(t_cur: str):
    """6.1.1 Variable initialisation (.gms lines 1446-1555).
    Every volume/nominal variable starts at its benchmark value scaled by
    population; every price variable starts at its (constant) benchmark
    value."""
    p = pop[t_cur]

    # -- volumes & nominal flows: benchmark * pop(t) --
    C.l[i, h, t_cur] = CO[i, h] * p
    CAB.l[t_cur] = CABO * p
    CG.l[i, t_cur] = CGO[i] * p
    CI.l[j, t_cur] = CIO[j] * p
    CMIN.l[i, h, t_cur] = CMINO[i, h] * p
    CTH.l[h, t_cur] = CTHO[h] * p
    CTH_REAL.l[h, t_cur] = CTH_REALO[h] * p
    DD.l[i, t_cur] = DDO[i] * p
    DI.l[i, j, t_cur] = DIO[i, j] * p
    DIT.l[i, t_cur] = DITO[i] * p
    DS.l[j, i, t_cur] = DSO[j, i] * p
    EX.l[j, i, t_cur] = EXO[j, i] * p
    EXD.l[i, t_cur] = EXDO[i] * p
    G.l[t_cur] = GO * p
    G_REAL.l[t_cur] = G_REALO * p
    GDP_BP.l[t_cur] = GDP_BPO * p
    GDP_BP_REAL.l[t_cur] = GDP_BP_REALO * p
    GDP_FD.l[t_cur] = GDP_FDO * p
    GDP_IB.l[t_cur] = GDP_IBO * p
    GDP_MP.l[t_cur] = GDP_MPO * p
    GDP_MP_REAL.l[t_cur] = GDP_MP_REALO * p
    GFCF.l[t_cur] = GFCFO * p
    GFCF_PRI_REAL.l[t_cur] = GFCF_PRI_REALO * p
    GFCF_PUB_REAL.l[t_cur] = GFCF_PUB_REALO * p
    IM.l[i, t_cur] = IMO[i] * p
    IND.l[k, j, t_cur] = INDO[k, j] * p
    INV.l[i, t_cur] = INVO[i] * p
    INV_PRI.l[i, t_cur] = INV_PRIO[i] * p
    INV_PUB.l[i, t_cur] = INV_PUBO[i] * p
    IT.l[t_cur] = ITO * p
    IT_PRI.l[t_cur] = IT_PRIO * p
    IT_PUB.l[t_cur] = IT_PUBO * p
    KDC.l[j, t_cur] = KDCO[j] * p
    KS.l[k, t_cur] = KSO[k] * p
    LD.l[l, j, t_cur] = LDO[l, j] * p
    LDC.l[j, t_cur] = LDCO[j] * p
    LS.l[l, t_cur] = LSO[l] * p
    MRGN.l[i, t_cur] = MRGNO[i] * p
    Q.l[i, t_cur] = QO[i] * p
    SF.l[f, t_cur] = SFO[f] * p
    SG.l[t_cur] = SGO * p
    SH.l[h, t_cur] = SHO[h] * p
    SROW.l[t_cur] = SROWO * p
    TDF.l[f, t_cur] = TDFO[f] * p
    TDFT.l[t_cur] = TDFTO * p
    TDH.l[h, t_cur] = TDHO[h] * p
    TDHT.l[t_cur] = TDHTO * p
    TIC.l[i, t_cur] = TICO[i] * p
    TICT.l[t_cur] = TICTO * p
    TIK.l[k, j, t_cur] = TIKO[k, j] * p
    TIKT.l[t_cur] = TIKTO * p
    TIM.l[i, t_cur] = TIMO[i] * p
    TIMT.l[t_cur] = TIMTO * p
    TIP.l[j, t_cur] = TIPO[j] * p
    TIPT.l[t_cur] = TIPTO * p
    TIW.l[l, j, t_cur] = TIWO[l, j] * p
    TIWT.l[t_cur] = TIWTO * p
    TIX.l[i, t_cur] = TIXO[i] * p
    TIXT.l[t_cur] = TIXTO * p
    TPRODN.l[t_cur] = TPRODNO * p
    TPRCTS.l[t_cur] = TPRCTSO * p
    TR.l[ag, agj, t_cur] = TRO[ag, agj] * p
    TR.l[agd, "row", t_cur] = TRO[agd, "row"] * PIXCONO ** eta * p
    TR.l[agng, "gvt", t_cur] = TRO[agng, "gvt"] * PIXCONO ** eta * p
    VA.l[j, t_cur] = VAO[j] * p
    VSTK.l[i, t_cur] = VSTKO[i] * p
    XS.l[j, i, t_cur] = XSO[j, i] * p
    XST.l[j, t_cur] = XSTO[j] * p
    YDF.l[f, t_cur] = YDFO[f] * p
    YDH.l[h, t_cur] = YDHO[h] * p
    YF.l[f, t_cur] = YFO[f] * p
    YFK.l[f, t_cur] = YFKO[f] * p
    YFTR.l[f, t_cur] = YFTRO[f] * p
    YG.l[t_cur] = YGO * p
    YGK.l[t_cur] = YGKO * p
    YGTR.l[t_cur] = YGTRO * p
    YH.l[h, t_cur] = YHO[h] * p
    YHK.l[h, t_cur] = YHKO[h] * p
    YHL.l[h, t_cur] = YHLO[h] * p
    YHTR.l[h, t_cur] = YHTRO[h] * p
    YROW.l[t_cur] = YROWO * p

    # -- prices: benchmark value, no population scaling --
    e.l[t_cur] = eO
    IR.l[t_cur] = IRO
    P.l[j, i, t_cur] = PO[j, i]
    PC.l[i, t_cur] = PCO[i]
    PCI.l[j, t_cur] = PCIO[j]
    PD.l[i, t_cur] = PDO[i]
    PE.l[i, t_cur] = PEO[i]
    PE_FOB.l[i, t_cur] = PE_FOBO[i]
    PIXCON.l[t_cur] = PIXCONO
    PIXGDP.l[t_cur] = PIXGDPO
    PIXGVT.l[t_cur] = PIXGVTO
    PIXINV_PRI.l[t_cur] = PIXINV_PRIO
    PIXINV_PUB.l[t_cur] = PIXINV_PUBO
    PK_PRI.l[t_cur] = PK_PRIO
    PK_PUB.l[t_cur] = PK_PUBO
    PL.l[i, t_cur] = PLO[i]
    PM.l[i, t_cur] = PMO[i]
    PP.l[j, t_cur] = PPO[j]
    PT.l[j, t_cur] = PTO[j]
    PVA.l[j, t_cur] = PVAO[j]
    PWM.l[i, t_cur] = PWMO[i]
    PWX.l[i, t_cur] = PWXO[i]
    R.l[k, j, t_cur] = RO[k, j]
    RC.l[j, t_cur] = RCO[j]
    RTI.l[k, j, t_cur] = RTIO[k, j]
    U.l[k, j, t_cur] = UO[k, j]
    W.l[l, t_cur] = WO[l]
    WC.l[j, t_cur] = WCO[j]
    WTI.l[l, j, t_cur] = WTIO[l, j]


def apply_closures_and_rates(t_cur: str, prev: str | None):
    """6.1.2 Closures + 6.1.3 Rates and intercepts (.gms lines 1557-1588).
    Same block is re-applied (harmlessly) in the simulation loop too."""
    p = pop[t_cur]

    # Closures (numeraire = nominal exchange rate; several exogenous volumes)
    e.fx[t_cur] = 1
    CAB.fx[t_cur] = CABO * p
    CMIN.fx[i, h, t_cur] = CMINO[i, h] * p
    G.fx[t_cur] = GO * p
    IND.fx[k, pub, t_cur].where[KDO[k, pub]] = INDO[k, pub] * p

    # Capital stock recursion: KD is fixed, not solved, consistent with the
    # "loop one period at a time" method - KD.fx(k,j,t1) seeds period 1;
    # for t>1 it is built from the PREVIOUS period's solved KD.l and IND.l.
    KD.fx[k, j, "1"].where[KDO[k, j]] = KDO[k, j]
    if prev is not None:
        KD.fx[k, j, t_cur].where[KDO[k, j]] = (
            KD.l[k, j, prev] * (1 - delta[k, j]) + IND.l[k, j, prev]
        )

    LS.fx[l, t_cur] = LSO[l] * p
    PWM.fx[i, t_cur] = PWMO[i]
    PWX.fx[i, t_cur] = PWXO[i]
    VSTK.fx[i, t_cur] = VSTKO[i] * p

    # Rates and intercepts (all exogenous / fixed over time unless shocked)
    sh0.fx[h, t_cur] = sh0O[h] * p
    sh1.fx[h, t_cur] = sh1O[h]
    tr0.fx[h, t_cur] = tr0O[h] * p
    tr1.fx[h, t_cur] = tr1O[h]
    ttdf0.fx[f, t_cur] = ttdf0O[f] * p
    ttdf1.fx[f, t_cur] = ttdf1O[f]
    ttdh0.fx[h, t_cur] = ttdh0O[h] * p
    ttdh1.fx[h, t_cur] = ttdh1O[h]
    ttic.fx[i, t_cur] = tticO[i]
    ttik.fx[k, j, t_cur] = ttikO[k, j]
    ttim.fx[i, t_cur] = ttimO[i]
    ttip.fx[j, t_cur] = ttipO[j]
    ttiw.fx[l, j, t_cur] = ttiwO[l, j]
    ttix.fx[i, t_cur] = ttixO[i]


def snapshot_all_variables() -> dict:
    """Capture every declared Variable's full .records panel (all periods
    solved so far) into a plain dict {name: DataFrame}. Since every variable
    is declared over the full TIME domain and each period's solve only
    touches the currently-active period t_cur, by the time a full BAU or
    SIM1 loop over all ten periods has finished, each variable's .records
    already holds the complete ten-period time series - exactly what the
    .gms RESULTS include files read with plain "VAR.l(...)" (no loop needed
    on our side to re-collect it period by period)."""
    panel = {}
    for name in m.listVariables():
        v = m[name]
        recs = v.records
        if recs is not None and len(recs):
            panel[name] = recs.copy()
    return panel


def run_loop_steps(scenario: str, shock_fn=None):
    """Generator version of run_loop(): solves one period, then yields a
    small progress dict - {"period", "index", "total", "status"} - before
    moving to the next. run_loop() below just drives this under a tqdm bar
    (used by Stages 3 & 6); the Stage 7 dashboard server drives it directly
    so it can push each period's completion to the browser as a live
    progress bar, over a streaming HTTP response, as each one finishes."""
    prev = None
    total = len(PERIODS)
    for idx, t_cur in enumerate(PERIODS, start=1):
        activate_period(t_cur)
        if scenario == "BAU":
            init_levels(t_cur)
        apply_closures_and_rates(t_cur, prev)
        if shock_fn is not None:
            shock_fn(t_cur)
        PEP1T.solve(solver=SOLVER)
        try:
            status = PEP1T.status
        except Exception:
            status = ""
        deactivate_period()
        prev = t_cur
        yield {"period": t_cur, "index": idx, "total": total, "status": str(status)}


def run_loop(scenario: str, shock_fn=None):
    bar = tqdm(total=len(PERIODS), desc=scenario, unit="period")
    for step in run_loop_steps(scenario, shock_fn=shock_fn):
        bar.set_postfix(period=step["period"], status=step["status"])
        bar.update(1)
    bar.close()


# ===========================================================================
# 6.1 BAU  (.gms lines 1434-1593)
# ===========================================================================
print("Solving BAU (one period at a time)...")
run_loop("BAU")
bau_panel = snapshot_all_variables()
print(f"BAU done - captured {len(bau_panel)} variables' full 10-period panels.")

# ===========================================================================
# 6.2 Simulation: gradual elimination of import duties (.gms lines 1603-1639)
# ===========================================================================
def make_shock_schedule(depth: float = 1.0) -> dict:
    """Gradual import-tariff reduction schedule, as a fraction of the
    original schedule's strength. depth=1.0 reproduces the .gms shock
    exactly (tariffs fall linearly to 0 by the final period); depth=0.0
    means no shock at all (SIM1 collapses onto BAU); anything in between
    scales the whole path. Factored out so both the one-shot run below and
    the interactive Stage 6 dashboard (which re-solves SIM1 with a new
    depth every time a slider moves) build the schedule the same way."""
    n = len(PERIODS)
    return {t: max(0.0, 1 - depth * (int(t) / n)) for t in PERIODS}


def make_tariff_shock(schedule: dict):
    """Returns a shock_fn closed over `schedule`, for run_loop(shock_fn=...)."""
    def _shock(t_cur: str):
        ttim.fx[i, t_cur] = schedule[t_cur] * ttimO[i]
    return _shock


SHOCK_SCHEDULE = make_shock_schedule(depth=1.0)  # kept as a name for backward compat
tariff_shock = make_tariff_shock(SHOCK_SCHEDULE)

print("Solving simulation (gradual tariff elimination)...")
run_loop("SIM1", shock_fn=tariff_shock)
sim1_panel = snapshot_all_variables()
print(f"SIM1 done - captured {len(sim1_panel)} variables' full 10-period panels.")


def resolve_sim1_steps(depth: float = 1.0):
    """Generator version of resolve_sim1(): yields a progress dict after
    each of SIM1's ten periods, then a final {"done": True, "panel": ...}
    once snapshot_all_variables() has been captured. This is what the
    Stage 7 dashboard server drives directly, so it can stream period-by-
    period progress to the browser over one HTTP response."""
    schedule = make_shock_schedule(depth)
    shock_fn = make_tariff_shock(schedule)
    yield from run_loop_steps("SIM1", shock_fn=shock_fn)
    yield {"done": True, "panel": snapshot_all_variables()}


def resolve_sim1(depth: float = 1.0) -> dict:
    """Re-solve SIM1 from scratch with a different shock depth and return
    the new sim1_panel - BAU is untouched (the shock doesn't affect it, so
    there's no need to re-solve ten more BAU periods every time a slider
    moves). Reuses the already-built PEP1T model; each solve warm-starts
    from whatever .l values are currently sitting in the Variables, which is
    fine for a CNS re-solve. This is what the Stage 6 interactive dashboard
    calls on every "Run simulation" click (no live progress - see
    resolve_sim1_steps() for that, used by Stage 7)."""
    panel = None
    for step in resolve_sim1_steps(depth=depth):
        if step.get("done"):
            panel = step["panel"]
    return panel


# `bau_panel` and `sim1_panel` (dict[name -> DataFrame]) are what
# pep_results.py consumes to build the chained price indices, the BAU/SIM1/
# var(%) comparison table, and the Excel export - the equivalent of the
# .gms RESULTS_PEP_1-t-b_BAU.gms / RESULTS_PEP_1-t-b_SIM1.GMS include files.
