"""
pep_equations.py
=================
GAMSPy translation of PEP_1-t-b_v2_1.gms, SECTION 5 (Model):
  5.1 Variable definition
  5.2 Equation definition (declarations)
  5.3 Equations (definitions, EQ1-EQ109b + WALRAS)

Depends on pep_data.py (Container `m`, all Sets and calibrated Parameters).

IMPORTANT ON TIMING / "t" vs "T":
In the .gms file, equations are declared over the full TIME set but DEFINED
using the lowercase alias "t", which is GAMS's name for the dynamic subset
T(TIME) declared in section 1.4 (T and "t" are the same symbol - GAMS is
case-insensitive). T starts EMPTY and gets switched to a single active
period inside the solve loop (section 6). Because GAMS equations defined
over a dynamic set are regenerated against whatever the set currently
contains, this "define once, solve many times as T changes" pattern carries
over directly to GAMSPy: every equation below is defined ONCE using the `T`
Set from pep_data.py, and pep_solve.py (stage 3) will change T's membership
and call Model.solve() once per period - no redefinition needed each loop.

4 equations are commented out in the original (EQ71, EQ73, EQ75, EQ103 -
each noted there as redundant/implied by another equation) and are skipped
here too.

Dollar conditions ($cond) on an ADDITIVE TERM inside a formula (e.g.
"[beta_VA(j)*LDC(j,t)**(-rho_VA(j))]$LDCO(j)") have no direct GAMSPy
equivalent for arbitrary sub-expressions, so they are replaced by
precomputed 0/1 indicator Parameters (has_LDCO, has_KDCO, has_EXO, has_DSO,
has_IMO, has_DDO below) multiplied into the term - mathematically identical
to the GAMS dollar, and safe against 0**(negative) domain errors because the
term is multiplied by exactly 0 instead of being evaluated and discarded.
Dollar conditions on an EQUATION'S OWN DOMAIN (e.g. "EQ41(i,t)$IMO(i)..")
use `.where[...]` on the equation assignment itself, GAMSPy's documented
equivalent of a GAMS $ on an equation declaration.
"""
import gamspy as gp
from gamspy import Sum, Product, Domain

from pep_data import *  # noqa: F401,F403  (Container m, Sets, calibrated Parameters)

# ===========================================================================
# Indicator parameters replacing additive-term-level "$" conditions
# ===========================================================================
has_LDCO = gp.Parameter(m, "has_LDCO", domain=j)
has_LDCO[j].where[LDCO[j]] = 1
has_KDCO = gp.Parameter(m, "has_KDCO", domain=j)
has_KDCO[j].where[KDCO[j]] = 1
has_EXO = gp.Parameter(m, "has_EXO", domain=[j, i])
has_EXO[j, i].where[EXO[j, i]] = 1
has_DSO = gp.Parameter(m, "has_DSO", domain=[j, i])
has_DSO[j, i].where[DSO[j, i]] = 1
has_IMO = gp.Parameter(m, "has_IMO", domain=i)
has_IMO[i].where[IMO[i]] = 1
has_DDO = gp.Parameter(m, "has_DDO", domain=i)
has_DDO[i].where[DDO[i]] = 1

# ===========================================================================
# 5.1 VARIABLE DEFINITION  (.gms lines 824-960)
# ===========================================================================
# -- 5.1.1 Volume variables --
C = gp.Variable(m, "C", domain=[i, h, TIME])
CG = gp.Variable(m, "CG", domain=[i, TIME])
CI = gp.Variable(m, "CI", domain=[j, TIME])
CMIN = gp.Variable(m, "CMIN", domain=[i, h, TIME])
CTH_REAL = gp.Variable(m, "CTH_REAL", domain=[h, TIME])
DD = gp.Variable(m, "DD", domain=[i, TIME])
DI = gp.Variable(m, "DI", domain=[i, j, TIME])
DIT = gp.Variable(m, "DIT", domain=[i, TIME])
DS = gp.Variable(m, "DS", domain=[j, i, TIME])
EX = gp.Variable(m, "EX", domain=[j, i, TIME])
EXD = gp.Variable(m, "EXD", domain=[i, TIME])
G_REAL = gp.Variable(m, "G_REAL", domain=TIME)
GDP_BP_REAL = gp.Variable(m, "GDP_BP_REAL", domain=TIME)
GDP_MP_REAL = gp.Variable(m, "GDP_MP_REAL", domain=TIME)
GFCF_PRI_REAL = gp.Variable(m, "GFCF_PRI_REAL", domain=TIME)
GFCF_PUB_REAL = gp.Variable(m, "GFCF_PUB_REAL", domain=TIME)
IM = gp.Variable(m, "IM", domain=[i, TIME])
IND = gp.Variable(m, "IND", domain=[k, j, TIME])
INV = gp.Variable(m, "INV", domain=[i, TIME])
INV_PRI = gp.Variable(m, "INV_PRI", domain=[i, TIME])
INV_PUB = gp.Variable(m, "INV_PUB", domain=[i, TIME])
KD = gp.Variable(m, "KD", domain=[k, j, TIME])
KDC = gp.Variable(m, "KDC", domain=[j, TIME])
KS = gp.Variable(m, "KS", domain=[k, TIME])
LD = gp.Variable(m, "LD", domain=[l, j, TIME])
LDC = gp.Variable(m, "LDC", domain=[j, TIME])
LS = gp.Variable(m, "LS", domain=[l, TIME])
MRGN = gp.Variable(m, "MRGN", domain=[i, TIME])
Q = gp.Variable(m, "Q", domain=[i, TIME])
VA = gp.Variable(m, "VA", domain=[j, TIME])
VSTK = gp.Variable(m, "VSTK", domain=[i, TIME])
XS = gp.Variable(m, "XS", domain=[j, i, TIME])
XST = gp.Variable(m, "XST", domain=[j, TIME])

# -- 5.1.2 Price variables --
e = gp.Variable(m, "e", domain=TIME)
IR = gp.Variable(m, "IR", domain=TIME)
P = gp.Variable(m, "P", domain=[j, i, TIME])
PC = gp.Variable(m, "PC", domain=[i, TIME])
PCI = gp.Variable(m, "PCI", domain=[j, TIME])
PD = gp.Variable(m, "PD", domain=[i, TIME])
PE = gp.Variable(m, "PE", domain=[i, TIME])
PE_FOB = gp.Variable(m, "PE_FOB", domain=[i, TIME])
PIXCON = gp.Variable(m, "PIXCON", domain=TIME)
PIXGDP = gp.Variable(m, "PIXGDP", domain=TIME)
PIXGVT = gp.Variable(m, "PIXGVT", domain=TIME)
PIXINV_PRI = gp.Variable(m, "PIXINV_PRI", domain=TIME)
PIXINV_PUB = gp.Variable(m, "PIXINV_PUB", domain=TIME)
PK_PRI = gp.Variable(m, "PK_PRI", domain=TIME)
PK_PUB = gp.Variable(m, "PK_PUB", domain=TIME)
PL = gp.Variable(m, "PL", domain=[i, TIME])
PM = gp.Variable(m, "PM", domain=[i, TIME])
PP = gp.Variable(m, "PP", domain=[j, TIME])
PT = gp.Variable(m, "PT", domain=[j, TIME])
PVA = gp.Variable(m, "PVA", domain=[j, TIME])
PWM = gp.Variable(m, "PWM", domain=[i, TIME])
PWX = gp.Variable(m, "PWX", domain=[i, TIME])
R = gp.Variable(m, "R", domain=[k, j, TIME])
RC = gp.Variable(m, "RC", domain=[j, TIME])
RTI = gp.Variable(m, "RTI", domain=[k, j, TIME])
U = gp.Variable(m, "U", domain=[k, j, TIME])
W = gp.Variable(m, "W", domain=[l, TIME])
WC = gp.Variable(m, "WC", domain=[j, TIME])
WTI = gp.Variable(m, "WTI", domain=[l, j, TIME])

# -- 5.1.3 Nominal (value) variables --
CAB = gp.Variable(m, "CAB", domain=TIME)
CTH = gp.Variable(m, "CTH", domain=[h, TIME])
G = gp.Variable(m, "G", domain=TIME)
GDP_BP = gp.Variable(m, "GDP_BP", domain=TIME)
GDP_FD = gp.Variable(m, "GDP_FD", domain=TIME)
GDP_IB = gp.Variable(m, "GDP_IB", domain=TIME)
GDP_MP = gp.Variable(m, "GDP_MP", domain=TIME)
GFCF = gp.Variable(m, "GFCF", domain=TIME)
IT = gp.Variable(m, "IT", domain=TIME)
IT_PRI = gp.Variable(m, "IT_PRI", domain=TIME)
IT_PUB = gp.Variable(m, "IT_PUB", domain=TIME)
SF = gp.Variable(m, "SF", domain=[f, TIME])
SG = gp.Variable(m, "SG", domain=TIME)
SH = gp.Variable(m, "SH", domain=[h, TIME])
SROW = gp.Variable(m, "SROW", domain=TIME)
TDF = gp.Variable(m, "TDF", domain=[f, TIME])
TDFT = gp.Variable(m, "TDFT", domain=TIME)
TDH = gp.Variable(m, "TDH", domain=[h, TIME])
TDHT = gp.Variable(m, "TDHT", domain=TIME)
TIC = gp.Variable(m, "TIC", domain=[i, TIME])
TICT = gp.Variable(m, "TICT", domain=TIME)
TIK = gp.Variable(m, "TIK", domain=[k, j, TIME])
TIKT = gp.Variable(m, "TIKT", domain=TIME)
TIM = gp.Variable(m, "TIM", domain=[i, TIME])
TIMT = gp.Variable(m, "TIMT", domain=TIME)
TIP = gp.Variable(m, "TIP", domain=[j, TIME])
TIPT = gp.Variable(m, "TIPT", domain=TIME)
TIW = gp.Variable(m, "TIW", domain=[l, j, TIME])
TIWT = gp.Variable(m, "TIWT", domain=TIME)
TIX = gp.Variable(m, "TIX", domain=[i, TIME])
TIXT = gp.Variable(m, "TIXT", domain=TIME)
TPRCTS = gp.Variable(m, "TPRCTS", domain=TIME)
TPRODN = gp.Variable(m, "TPRODN", domain=TIME)
TR = gp.Variable(m, "TR", domain=[ag, agj, TIME])
YDF = gp.Variable(m, "YDF", domain=[f, TIME])
YDH = gp.Variable(m, "YDH", domain=[h, TIME])
YF = gp.Variable(m, "YF", domain=[f, TIME])
YFK = gp.Variable(m, "YFK", domain=[f, TIME])
YFTR = gp.Variable(m, "YFTR", domain=[f, TIME])
YG = gp.Variable(m, "YG", domain=TIME)
YGK = gp.Variable(m, "YGK", domain=TIME)
YGTR = gp.Variable(m, "YGTR", domain=TIME)
YH = gp.Variable(m, "YH", domain=[h, TIME])
YHK = gp.Variable(m, "YHK", domain=[h, TIME])
YHL = gp.Variable(m, "YHL", domain=[h, TIME])
YHTR = gp.Variable(m, "YHTR", domain=[h, TIME])
YROW = gp.Variable(m, "YROW", domain=TIME)

# -- 5.1.4 Rates and intercepts --
sh0 = gp.Variable(m, "sh0", domain=[h, TIME])
sh1 = gp.Variable(m, "sh1", domain=[h, TIME])
tr0 = gp.Variable(m, "tr0", domain=[h, TIME])
tr1 = gp.Variable(m, "tr1", domain=[h, TIME])
ttdf0 = gp.Variable(m, "ttdf0", domain=[f, TIME])
ttdf1 = gp.Variable(m, "ttdf1", domain=[f, TIME])
ttdh0 = gp.Variable(m, "ttdh0", domain=[h, TIME])
ttdh1 = gp.Variable(m, "ttdh1", domain=[h, TIME])
ttic = gp.Variable(m, "ttic", domain=[i, TIME])
ttik = gp.Variable(m, "ttik", domain=[k, j, TIME])
ttim = gp.Variable(m, "ttim", domain=[i, TIME])
ttip = gp.Variable(m, "ttip", domain=[j, TIME])
ttiw = gp.Variable(m, "ttiw", domain=[l, j, TIME])
ttix = gp.Variable(m, "ttix", domain=[i, TIME])

# -- 5.1.5 Other --
LEON = gp.Variable(m, "LEON", domain=TIME)

# ===========================================================================
# 5.2 / 5.3  EQUATIONS  (.gms lines 963-1427)
# ===========================================================================

# ---- 5.3.1 Production --------------------------------------------------
EQ1 = gp.Equation(m, "EQ1", domain=[j, TIME])
EQ1[j, T] = VA[j, T] == v[j] * XST[j, T]

EQ2 = gp.Equation(m, "EQ2", domain=[j, TIME])
EQ2[j, T] = CI[j, T] == io_[j] * XST[j, T]

EQ3 = gp.Equation(m, "EQ3", domain=[j, TIME])
EQ3[j, T] = VA[j, T] == B_VA[j] * (
    beta_VA[j] * LDC[j, T] ** (-rho_VA[j]) * has_LDCO[j]
    + (1 - beta_VA[j]) * KDC[j, T] ** (-rho_VA[j]) * has_KDCO[j]
) ** (-1 / rho_VA[j])

EQ4 = gp.Equation(m, "EQ4", domain=[j, TIME])
EQ4[j, T].where[(LDCO[j] > 0) & (KDCO[j] > 0)] = LDC[j, T] == (
    (beta_VA[j] / (1 - beta_VA[j])) * (RC[j, T] / WC[j, T])
) ** sigma_VA[j] * KDC[j, T]

EQ5 = gp.Equation(m, "EQ5", domain=[j, TIME])
EQ5[j, T].where[LDCO[j]] = LDC[j, T] == B_LD[j] * Sum(
    l.where[LDO[l, j]], beta_LD[l, j] * LD[l, j, T] ** (-rho_LD[j])
) ** (-1 / rho_LD[j])

EQ6 = gp.Equation(m, "EQ6", domain=[l, j, TIME])
EQ6[l, j, T].where[LDO[l, j]] = LD[l, j, T] == (
    beta_LD[l, j] * WC[j, T] / WTI[l, j, T]
) ** sigma_LD[j] * B_LD[j] ** (sigma_LD[j] - 1) * LDC[j, T]

EQ7 = gp.Equation(m, "EQ7", domain=[j, TIME])
EQ7[j, T].where[KDCO[j]] = KDC[j, T] == B_KD[j] * Sum(
    k.where[KDO[k, j]], beta_KD[k, j] * KD[k, j, T] ** (-rho_KD[j])
) ** (-1 / rho_KD[j])

EQ8 = gp.Equation(m, "EQ8", domain=[k, j, TIME])
EQ8[k, j, T].where[KDO[k, j]] = KD[k, j, T] == (
    beta_KD[k, j] * RC[j, T] / RTI[k, j, T]
) ** sigma_KD[j] * B_KD[j] ** (sigma_KD[j] - 1) * KDC[j, T]

EQ9 = gp.Equation(m, "EQ9", domain=[i, j, TIME])
EQ9[i, j, T] = DI[i, j, T] == aij[i, j] * CI[j, T]

# ---- 5.3.2.1 Households --------------------------------------------------
EQ10 = gp.Equation(m, "EQ10", domain=[h, TIME])
EQ10[h, T] = YH[h, T] == YHL[h, T] + YHK[h, T] + YHTR[h, T]

EQ11 = gp.Equation(m, "EQ11", domain=[h, TIME])
EQ11[h, T] = YHL[h, T] == Sum(
    l, lambda_WL[h, l] * W[l, T] * Sum(j.where[LDO[l, j]], LD[l, j, T])
)

EQ12 = gp.Equation(m, "EQ12", domain=[h, TIME])
EQ12[h, T] = YHK[h, T] == Sum(
    k, lambda_RK[h, k] * Sum(j.where[KDO[k, j]], R[k, j, T] * KD[k, j, T])
)

EQ13 = gp.Equation(m, "EQ13", domain=[h, TIME])
EQ13[h, T] = YHTR[h, T] == Sum(ag, TR[h, ag, T])

EQ14 = gp.Equation(m, "EQ14", domain=[h, TIME])
EQ14[h, T] = YDH[h, T] == YH[h, T] - TDH[h, T] - TR["gvt", h, T]

EQ15 = gp.Equation(m, "EQ15", domain=[h, TIME])
EQ15[h, T] = CTH[h, T] == YDH[h, T] - SH[h, T] - Sum(agng, TR[agng, h, T])

EQ16 = gp.Equation(m, "EQ16", domain=[h, TIME])
EQ16[h, T] = SH[h, T] == PIXCON[T] ** eta * sh0[h, T] + sh1[h, T] * YDH[h, T]

# ---- 5.3.2.2 Firms --------------------------------------------------------
EQ17 = gp.Equation(m, "EQ17", domain=[f, TIME])
EQ17[f, T] = YF[f, T] == YFK[f, T] + YFTR[f, T]

EQ18 = gp.Equation(m, "EQ18", domain=[f, TIME])
EQ18[f, T] = YFK[f, T] == Sum(
    k, lambda_RK[f, k] * Sum(j.where[KDO[k, j]], R[k, j, T] * KD[k, j, T])
)

EQ19 = gp.Equation(m, "EQ19", domain=[f, TIME])
EQ19[f, T] = YFTR[f, T] == Sum(ag, TR[f, ag, T])

EQ20 = gp.Equation(m, "EQ20", domain=[f, TIME])
EQ20[f, T] = YDF[f, T] == YF[f, T] - TDF[f, T]

EQ21 = gp.Equation(m, "EQ21", domain=[f, TIME])
EQ21[f, T] = SF[f, T] == YDF[f, T] - Sum(ag, TR[ag, f, T])

# ---- 5.3.2.3 Government ---------------------------------------------------
EQ22 = gp.Equation(m, "EQ22", domain=TIME)
EQ22[T] = YG[T] == YGK[T] + TDHT[T] + TDFT[T] + TPRODN[T] + TPRCTS[T] + YGTR[T]

EQ23 = gp.Equation(m, "EQ23", domain=TIME)
EQ23[T] = YGK[T] == Sum(
    k, lambda_RK["gvt", k] * Sum(j.where[KDO[k, j]], R[k, j, T] * KD[k, j, T])
)

EQ24 = gp.Equation(m, "EQ24", domain=TIME)
EQ24[T] = TDHT[T] == Sum(h, TDH[h, T])

EQ25 = gp.Equation(m, "EQ25", domain=TIME)
EQ25[T] = TDFT[T] == Sum(f, TDF[f, T])

EQ26 = gp.Equation(m, "EQ26", domain=TIME)
EQ26[T] = TPRODN[T] == TIWT[T] + TIKT[T] + TIPT[T]

EQ27 = gp.Equation(m, "EQ27", domain=TIME)
EQ27[T] = TIWT[T] == Sum(Domain(l, j).where[LDO[l, j]], TIW[l, j, T])

EQ28 = gp.Equation(m, "EQ28", domain=TIME)
EQ28[T] = TIKT[T] == Sum(Domain(k, j).where[KDO[k, j]], TIK[k, j, T])

EQ29 = gp.Equation(m, "EQ29", domain=TIME)
EQ29[T] = TIPT[T] == Sum(j, TIP[j, T])

EQ30 = gp.Equation(m, "EQ30", domain=TIME)
EQ30[T] = TPRCTS[T] == TICT[T] + TIMT[T] + TIXT[T]

EQ31 = gp.Equation(m, "EQ31", domain=TIME)
EQ31[T] = TICT[T] == Sum(i, TIC[i, T])

EQ32 = gp.Equation(m, "EQ32", domain=TIME)
EQ32[T] = TIMT[T] == Sum(i.where[IMO[i]], TIM[i, T])

EQ33 = gp.Equation(m, "EQ33", domain=TIME)
EQ33[T] = TIXT[T] == Sum(i.where[EXDO[i]], TIX[i, T])

EQ34 = gp.Equation(m, "EQ34", domain=TIME)
EQ34[T] = YGTR[T] == Sum(agng, TR["gvt", agng, T])

EQ35 = gp.Equation(m, "EQ35", domain=[h, TIME])
EQ35[h, T] = TDH[h, T] == PIXCON[T] ** eta * ttdh0[h, T] + ttdh1[h, T] * YH[h, T]

EQ36 = gp.Equation(m, "EQ36", domain=[f, TIME])
EQ36[f, T] = TDF[f, T] == PIXCON[T] ** eta * ttdf0[f, T] + ttdf1[f, T] * YFK[f, T]

EQ37 = gp.Equation(m, "EQ37", domain=[l, j, TIME])
EQ37[l, j, T].where[LDO[l, j]] = TIW[l, j, T] == ttiw[l, j, T] * W[l, T] * LD[l, j, T]

EQ38 = gp.Equation(m, "EQ38", domain=[k, j, TIME])
EQ38[k, j, T].where[KDO[k, j]] = TIK[k, j, T] == ttik[k, j, T] * R[k, j, T] * KD[k, j, T]

EQ39 = gp.Equation(m, "EQ39", domain=[j, TIME])
EQ39[j, T] = TIP[j, T] == ttip[j, T] * PP[j, T] * XST[j, T]

EQ40 = gp.Equation(m, "EQ40", domain=[i, TIME])
EQ40[i, T] = TIC[i, T] == ttic[i, T] * (
    (PL[i, T] + Sum(ij, PC[ij, T] * tmrg[ij, i])) * DD[i, T] * has_DDO[i]
    + ((1 + ttim[i, T]) * PWM[i, T] * e[T] + Sum(ij, PC[ij, T] * tmrg[ij, i])) * IM[i, T] * has_IMO[i]
)

EQ41 = gp.Equation(m, "EQ41", domain=[i, TIME])
EQ41[i, T].where[IMO[i]] = TIM[i, T] == ttim[i, T] * PWM[i, T] * e[T] * IM[i, T]

EQ42 = gp.Equation(m, "EQ42", domain=[i, TIME])
EQ42[i, T].where[EXDO[i]] = TIX[i, T] == ttix[i, T] * (
    PE[i, T] + Sum(ij, PC[ij, T] * tmrg_X[ij, i])
) * EXD[i, T]

EQ43 = gp.Equation(m, "EQ43", domain=TIME)
EQ43[T] = SG[T] == YG[T] - Sum(agng, TR[agng, "gvt", T]) - G[T]

# ---- 5.3.2.4 Rest of the world -------------------------------------------
EQ44 = gp.Equation(m, "EQ44", domain=TIME)
EQ44[T] = YROW[T] == (
    e[T] * Sum(i.where[IMO[i]], PWM[i, T] * IM[i, T])
    + Sum(k, lambda_RK["row", k] * Sum(j.where[KDO[k, j]], R[k, j, T] * KD[k, j, T]))
    + Sum(agd, TR["row", agd, T])
)

EQ45 = gp.Equation(m, "EQ45", domain=TIME)
EQ45[T] = SROW[T] == (
    YROW[T] - Sum(i.where[EXDO[i]], PE_FOB[i, T] * EXD[i, T]) - Sum(agd, TR[agd, "row", T])
)

EQ46 = gp.Equation(m, "EQ46", domain=TIME)
EQ46[T] = SROW[T] == -CAB[T]

# ---- 5.3.2.5 Transfers ----------------------------------------------------
EQ47 = gp.Equation(m, "EQ47", domain=[agng, h, TIME])
EQ47[agng, h, T] = TR[agng, h, T] == lambda_TR[agng, h] * YDH[h, T]

EQ48 = gp.Equation(m, "EQ48", domain=[h, TIME])
EQ48[h, T] = TR["gvt", h, T] == PIXCON[T] ** eta * tr0[h, T] + tr1[h, T] * YH[h, T]

EQ49 = gp.Equation(m, "EQ49", domain=[ag, f, TIME])
EQ49[ag, f, T] = TR[ag, f, T] == lambda_TR[ag, f] * YDF[f, T]

EQ50 = gp.Equation(m, "EQ50", domain=[agng, TIME])
EQ50[agng, T] = TR[agng, "gvt", T] == PIXCON[T] ** eta * TRO[agng, "gvt"] * pop[T]

EQ51 = gp.Equation(m, "EQ51", domain=[agd, TIME])
EQ51[agd, T] = TR[agd, "row", T] == PIXCON[T] ** eta * TRO[agd, "row"] * pop[T]

# ---- 5.3.3 Demand -----------------------------------------------------------
EQ52 = gp.Equation(m, "EQ52", domain=[i, h, TIME])
EQ52[i, h, T] = PC[i, T] * C[i, h, T] == PC[i, T] * CMIN[i, h, T] + gamma_LES[i, h] * (
    CTH[h, T] - Sum(ij, PC[ij, T] * CMIN[ij, h, T])
)

EQ53 = gp.Equation(m, "EQ53", domain=TIME)
EQ53[T] = GFCF[T] == IT[T] - Sum(i, PC[i, T] * VSTK[i, T])

EQ54 = gp.Equation(m, "EQ54", domain=[i, TIME])
EQ54[i, T] = PC[i, T] * INV_PRI[i, T] == gamma_INVPRI[i] * IT_PRI[T]

EQ55 = gp.Equation(m, "EQ55", domain=[i, TIME])
EQ55[i, T] = PC[i, T] * INV_PUB[i, T] == gamma_INVPUB[i] * IT_PUB[T]

EQ56 = gp.Equation(m, "EQ56", domain=[i, TIME])
EQ56[i, T] = INV[i, T] == INV_PRI[i, T] + INV_PUB[i, T]

EQ57 = gp.Equation(m, "EQ57", domain=[i, TIME])
EQ57[i, T] = PC[i, T] * CG[i, T] == gamma_GVT[i] * G[T]

EQ58 = gp.Equation(m, "EQ58", domain=[i, TIME])
EQ58[i, T] = DIT[i, T] == Sum(j, DI[i, j, T])

EQ59 = gp.Equation(m, "EQ59", domain=[i, TIME])
EQ59[i, T] = MRGN[i, T] == (
    Sum(ij.where[DDO[ij]], tmrg[i, ij] * DD[ij, T])
    + Sum(ij.where[IMO[ij]], tmrg[i, ij] * IM[ij, T])
    + Sum(ij.where[EXDO[ij]], tmrg_X[i, ij] * EXD[ij, T])
)

# ---- 5.3.4 International trade --------------------------------------------
EQ60 = gp.Equation(m, "EQ60", domain=[j, TIME])
EQ60[j, T] = XST[j, T] == B_XT[j] * Sum(
    i.where[XSO[j, i]], beta_XT[j, i] * XS[j, i, T] ** rho_XT[j]
) ** (1 / rho_XT[j])

EQ61 = gp.Equation(m, "EQ61", domain=[j, i, TIME])
EQ61[j, i, T].where[(XSO[j, i] > 0) & (XSO[j, i] != XSTO[j])] = XS[j, i, T] == (
    XST[j, T] / B_XT[j] ** (1 + sigma_XT[j])
    * (P[j, i, T] / (beta_XT[j, i] * PT[j, T])) ** sigma_XT[j]
)

EQ62 = gp.Equation(m, "EQ62", domain=[j, i, TIME])
EQ62[j, i, T].where[XSO[j, i]] = XS[j, i, T] == B_X[j, i] * (
    beta_X[j, i] * EX[j, i, T] ** rho_X[j, i] * has_EXO[j, i]
    + (1 - beta_X[j, i]) * DS[j, i, T] ** rho_X[j, i] * has_DSO[j, i]
) ** (1 / rho_X[j, i])

EQ63 = gp.Equation(m, "EQ63", domain=[j, i, TIME])
EQ63[j, i, T].where[(EXO[j, i] > 0) & (DSO[j, i] > 0)] = EX[j, i, T] == (
    ((1 - beta_X[j, i]) / beta_X[j, i]) * (PE[i, T] / PL[i, T])
) ** sigma_X[j, i] * DS[j, i, T]

EQ64 = gp.Equation(m, "EQ64", domain=[i, TIME])
EQ64[i, T].where[EXDO[i]] = EXD[i, T] == (
    EXDO[i] * pop[T] * (e[T] * PWX[i, T] / PE_FOB[i, T]) ** sigma_XD[i]
)

EQ65 = gp.Equation(m, "EQ65", domain=[i, TIME])
EQ65[i, T] = Q[i, T] == B_M[i] * (
    beta_M[i] * IM[i, T] ** (-rho_M[i]) * has_IMO[i]
    + (1 - beta_M[i]) * DD[i, T] ** (-rho_M[i]) * has_DDO[i]
) ** (-1 / rho_M[i])

EQ66 = gp.Equation(m, "EQ66", domain=[i, TIME])
EQ66[i, T].where[(IMO[i] > 0) & (DDO[i] > 0)] = IM[i, T] == (
    (beta_M[i] / (1 - beta_M[i])) * (PD[i, T] / PM[i, T])
) ** sigma_M[i] * DD[i, T]

# ---- 5.3.5 Prices -----------------------------------------------------------
EQ67 = gp.Equation(m, "EQ67", domain=[j, TIME])
EQ67[j, T] = PP[j, T] * XST[j, T] == PVA[j, T] * VA[j, T] + PCI[j, T] * CI[j, T]

EQ68 = gp.Equation(m, "EQ68", domain=[j, TIME])
EQ68[j, T] = PT[j, T] == (1 + ttip[j, T]) * PP[j, T]

EQ69 = gp.Equation(m, "EQ69", domain=[j, TIME])
EQ69[j, T] = PCI[j, T] * CI[j, T] == Sum(i, PC[i, T] * DI[i, j, T])

EQ70 = gp.Equation(m, "EQ70", domain=[j, TIME])
EQ70[j, T] = PVA[j, T] * VA[j, T] == (
    WC[j, T] * LDC[j, T] * has_LDCO[j] + RC[j, T] * KDC[j, T] * has_KDCO[j]
)

EQ72 = gp.Equation(m, "EQ72", domain=[l, j, TIME])
EQ72[l, j, T].where[LDO[l, j]] = WTI[l, j, T] == W[l, T] * (1 + ttiw[l, j, T])

EQ74 = gp.Equation(m, "EQ74", domain=[k, j, TIME])
EQ74[k, j, T].where[KDO[k, j]] = RTI[k, j, T] == R[k, j, T] * (1 + ttik[k, j, T])

EQ75a = gp.Equation(m, "EQ75a", domain=[j, i, TIME])
EQ75a[j, i, T].where[XSO[j, i] == XSTO[j]] = P[j, i, T] == PT[j, T]

EQ76 = gp.Equation(m, "EQ76", domain=[j, i, TIME])
EQ76[j, i, T].where[XSO[j, i]] = P[j, i, T] * XS[j, i, T] == (
    PE[i, T] * EX[j, i, T] * has_EXO[j, i] + PL[i, T] * DS[j, i, T] * has_DSO[j, i]
)

EQ77 = gp.Equation(m, "EQ77", domain=[i, TIME])
EQ77[i, T].where[EXDO[i]] = PE_FOB[i, T] == (1 + ttix[i, T]) * (
    PE[i, T] + Sum(ij, PC[ij, T] * tmrg_X[ij, i])
)

EQ78 = gp.Equation(m, "EQ78", domain=[i, TIME])
EQ78[i, T].where[DDO[i]] = PD[i, T] == (1 + ttic[i, T]) * (
    PL[i, T] + Sum(ij, PC[ij, T] * tmrg[ij, i])
)

EQ79 = gp.Equation(m, "EQ79", domain=[i, TIME])
EQ79[i, T].where[IMO[i]] = PM[i, T] == (1 + ttic[i, T]) * (
    (1 + ttim[i, T]) * e[T] * PWM[i, T] + Sum(ij, PC[ij, T] * tmrg[ij, i])
)

EQ80 = gp.Equation(m, "EQ80", domain=[i, TIME])
EQ80[i, T] = PC[i, T] * Q[i, T] == (
    PM[i, T] * IM[i, T] * has_IMO[i] + PD[i, T] * DD[i, T] * has_DDO[i]
)

EQ81 = gp.Equation(m, "EQ81", domain=TIME)
EQ81[T] = PIXGDP[T] == (
    Sum(j, ((PVA[j, T] * VA[j, T] + TIP[j, T]) / VA[j, T]) * VAO[j])
    / Sum(j, ((PVAO[j] * VAO[j] + TIPO[j]) / VAO[j]) * VAO[j])
    * Sum(j, ((PVA[j, T] * VA[j, T] + TIP[j, T]) / VA[j, T]) * VA[j, T])
    / Sum(j, ((PVAO[j] * VAO[j] + TIPO[j]) / VAO[j]) * VA[j, T])
) ** 0.5

EQ82 = gp.Equation(m, "EQ82", domain=TIME)
EQ82[T] = PIXCON[T] == (
    Sum(i, PC[i, T] * Sum(h, CO[i, h])) / Sum(i, PCO[i] * Sum(h, CO[i, h]))
)

EQ83 = gp.Equation(m, "EQ83", domain=TIME)
EQ83[T] = PIXINV_PRI[T] == Product(
    i.where[gamma_INVPRI[i]], (PC[i, T] / PCO[i]) ** gamma_INVPRI[i]
)

EQ84 = gp.Equation(m, "EQ84", domain=TIME)
EQ84[T] = PIXINV_PUB[T] == Product(
    i.where[gamma_INVPUB[i]], (PC[i, T] / PCO[i]) ** gamma_INVPUB[i]
)

EQ85 = gp.Equation(m, "EQ85", domain=TIME)
EQ85[T] = PIXGVT[T] == Product(i.where[gamma_GVT[i]], (PC[i, T] / PCO[i]) ** gamma_GVT[i])

# ---- 5.3.6 Equilibrium ------------------------------------------------------
EQ86 = gp.Equation(m, "EQ86", domain=[i1, TIME])
EQ86[i1, T] = Q[i1, T] == (
    Sum(h, C[i1, h, T]) + CG[i1, T] + INV[i1, T] + VSTK[i1, T] + DIT[i1, T] + MRGN[i1, T]
)

EQ87 = gp.Equation(m, "EQ87", domain=[l, TIME])
EQ87[l, T] = LS[l, T] == Sum(j.where[LDO[l, j]], LD[l, j, T])

EQ88 = gp.Equation(m, "EQ88", domain=[k, TIME])
EQ88[k, T] = KS[k, T] == Sum(j.where[KDO[k, j]], KD[k, j, T])

EQ89 = gp.Equation(m, "EQ89", domain=TIME)
EQ89[T] = IT[T] == Sum(h, SH[h, T]) + Sum(f, SF[f, T]) + SG[T] + SROW[T]

EQ90 = gp.Equation(m, "EQ90", domain=TIME)
EQ90[T] = IT_PRI[T] == IT[T] - IT_PUB[T] - Sum(i, PC[i, T] * VSTK[i, T])

EQ91 = gp.Equation(m, "EQ91", domain=[i, TIME])
EQ91[i, T].where[DDO[i]] = Sum(j.where[DSO[j, i]], DS[j, i, T]) == DD[i, T]

EQ92 = gp.Equation(m, "EQ92", domain=[i, TIME])
EQ92[i, T].where[EXDO[i]] = Sum(j.where[EXO[j, i]], EX[j, i, T]) == EXD[i, T]

# ---- 5.3.7 Gross domestic product ------------------------------------------
EQ93 = gp.Equation(m, "EQ93", domain=TIME)
EQ93[T] = GDP_BP[T] == Sum(j, PVA[j, T] * VA[j, T]) + TIPT[T]

EQ94 = gp.Equation(m, "EQ94", domain=TIME)
EQ94[T] = GDP_MP[T] == GDP_BP[T] + TPRCTS[T]

EQ95 = gp.Equation(m, "EQ95", domain=TIME)
EQ95[T] = GDP_IB[T] == (
    Sum(Domain(l, j).where[LDO[l, j]], W[l, T] * LD[l, j, T])
    + Sum(Domain(k, j).where[KDO[k, j]], R[k, j, T] * KD[k, j, T])
    + TPRODN[T] + TPRCTS[T]
)

EQ96 = gp.Equation(m, "EQ96", domain=TIME)
EQ96[T] = GDP_FD[T] == (
    Sum(i, PC[i, T] * (Sum(h, C[i, h, T]) + CG[i, T] + INV[i, T] + VSTK[i, T]))
    + Sum(i.where[EXDO[i]], PE_FOB[i, T] * EXD[i, T])
    - Sum(i.where[IMO[i]], PWM[i, T] * e[T] * IM[i, T])
)

# ---- 5.3.8 Real variables ---------------------------------------------------
EQ97 = gp.Equation(m, "EQ97", domain=[h, TIME])
EQ97[h, T] = CTH_REAL[h, T] == CTH[h, T] / PIXCON[T]

EQ98 = gp.Equation(m, "EQ98", domain=TIME)
EQ98[T] = G_REAL[T] == G[T] / PIXGVT[T]

EQ99 = gp.Equation(m, "EQ99", domain=TIME)
EQ99[T] = GDP_BP_REAL[T] == GDP_BP[T] / PIXGDP[T]

EQ100 = gp.Equation(m, "EQ100", domain=TIME)
EQ100[T] = GDP_MP_REAL[T] == GDP_MP[T] / PIXCON[T]

EQ101 = gp.Equation(m, "EQ101", domain=TIME)
EQ101[T] = GFCF_PRI_REAL[T] == IT_PRI[T] / PIXINV_PRI[T]

EQ102 = gp.Equation(m, "EQ102", domain=TIME)
EQ102[T] = GFCF_PUB_REAL[T] == IT_PUB[T] / PIXINV_PUB[T]

# ---- 5.3.9 Dynamic equations ------------------------------------------------
# EQ103 (capital accumulation) is commented out in the .gms file; capital
# accumulation is instead imposed via KD.fx(...) inside the solve loop
# (stage 3 / pep_solve.py), exactly as the original does.

EQ104 = gp.Equation(m, "EQ104", domain=TIME)
EQ104[T] = IT_PUB[T] == PK_PUB[T] * Sum(Domain(k, pub).where[KDO[k, pub]], IND[k, pub, T])

EQ105 = gp.Equation(m, "EQ105", domain=TIME)
EQ105[T] = IT_PRI[T] == PK_PRI[T] * Sum(Domain(k, bus).where[KDO[k, bus]], IND[k, bus, T])

EQ106 = gp.Equation(m, "EQ106", domain=TIME)
EQ106[T] = PK_PRI[T] == (1 / A_K_PRI) * Product(
    i.where[gamma_INVPRI[i]], (PC[i, T] / gamma_INVPRI[i]) ** gamma_INVPRI[i]
)

EQ107 = gp.Equation(m, "EQ107", domain=TIME)
EQ107[T] = PK_PUB[T] == (1 / A_K_PUB) * Product(
    i.where[gamma_INVPUB[i]], (PC[i, T] / gamma_INVPUB[i]) ** gamma_INVPUB[i]
)

EQ108 = gp.Equation(m, "EQ108", domain=[k, bus, TIME])
EQ108[k, bus, T].where[KDO[k, bus]] = IND[k, bus, T] == (
    phi[k, bus] * (R[k, bus, T] / U[k, bus, T]) ** sigma_INV[k, bus] * KD[k, bus, T]
)

EQ109a = gp.Equation(m, "EQ109a", domain=[k, bus, TIME])
EQ109a[k, bus, T].where[KDO[k, bus]] = U[k, bus, T] == PK_PRI[T] * (delta[k, bus] + IR[T])

EQ109b = gp.Equation(m, "EQ109b", domain=[k, pub, TIME])
EQ109b[k, pub, T].where[KDO[k, pub]] = U[k, pub, T] == PK_PUB[T] * (delta[k, pub] + IR[T])

# ---- 5.3.10 Other ------------------------------------------------------------
WALRAS = gp.Equation(m, "WALRAS", domain=TIME)
WALRAS[T] = LEON[T] == (
    Q["agr", T] - Sum(h, C["agr", h, T]) - CG["agr", T]
    - INV["agr", T] - VSTK["agr", T] - DIT["agr", T] - MRGN["agr", T]
)

print("pep_equations.py: all variables and equations declared OK.")
