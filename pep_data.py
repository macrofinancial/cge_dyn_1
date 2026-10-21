"""
pep_data.py
===========
GAMSPy translation of PEP_1-t-b_v2_1.gms, SECTIONS 1-4:
  1. Sets
  2. Parameters & benchmark ("O") values
  3. Data (from SAM-V2_0.xls and VAL_PAR.xlsx)
  4. Calibration

Every block below is commented with the GAMS line/section it mirrors so you
can cross-check line by line against the original .gms file while debugging.

Run standalone to sanity-check that calibration completes without error:
    python pep_data.py
"""
import gamspy as gp
from gamspy import Sum, Product, Ord, Number
import data_io

SAM_PATH = "SAM-V2_0.xls"       # pip install xlrd  (reads legacy .xls)
VAL_PAR_PATH = "VAL_PAR.xlsx"

m = gp.Container()

# ===========================================================================
# 1. SET DEFINITION  (.gms lines 24-150)
# ===========================================================================
j = gp.Set(m, "j", records=["agr", "ind", "ser", "adm"], description="All industries")
pub = gp.Set(m, "pub", domain=j, records=["adm"], description="Public industries")
bus = gp.Set(m, "bus", domain=j, records=["agr", "ind", "ser"], description="Private industries")

i = gp.Set(m, "i", records=["agr", "food", "othind", "ser", "adm"], description="All commodities")
i1 = gp.Set(m, "i1", domain=i, records=["food", "othind", "ser", "adm"],
            description="All commodities except agriculture")

l = gp.Set(m, "l", records=["usk", "sk"], description="Labor categories")
k = gp.Set(m, "k", records=["cap", "land"], description="Capital categories")

ag = gp.Set(m, "ag", records=["hrp", "hup", "hrr", "hur", "firm", "gvt", "row"],
            description="All agents")
agng = gp.Set(m, "agng", domain=ag, records=["hrp", "hup", "hrr", "hur", "firm", "row"],
              description="Non governmental agents")
agd = gp.Set(m, "agd", domain=ag, records=["hrp", "hup", "hrr", "hur", "firm", "gvt"],
             description="All domestic agents")
h = gp.Set(m, "h", domain=ag, records=["hrp", "hup", "hrr", "hur"], description="Households")
f = gp.Set(m, "f", domain=ag, records=["firm"], description="Firms")

TIME = gp.Set(m, "TIME", records=[str(x) for x in range(1, 11)], description="Time periods")
T = gp.Set(m, "T", domain=TIME, description="Active period(s) in the current solve")
T1 = gp.Set(m, "T1", domain=TIME, description="First period")
T1[TIME] = Ord(TIME) == 1

jj = gp.Alias(m, "jj", alias_with=j)
ij = gp.Alias(m, "ij", alias_with=i)
agj = gp.Alias(m, "agj", alias_with=ag)
hj = gp.Alias(m, "hj", alias_with=h)
lj = gp.Alias(m, "lj", alias_with=l)
kj = gp.Alias(m, "kj", alias_with=k)

# ===========================================================================
# 2.1 STRUCTURAL PARAMETERS  (.gms lines 157-345)
# ===========================================================================
aij = gp.Parameter(m, "aij", domain=[i, j])
alpha = gp.Parameter(m, "alpha")
A_K_PRI = gp.Parameter(m, "A_K_PRI")
A_K_PUB = gp.Parameter(m, "A_K_PUB")
B_KD = gp.Parameter(m, "B_KD", domain=j)
B_LD = gp.Parameter(m, "B_LD", domain=j)
B_M = gp.Parameter(m, "B_M", domain=i)
B_VA = gp.Parameter(m, "B_VA", domain=j)
B_X = gp.Parameter(m, "B_X", domain=[j, i])
B_XT = gp.Parameter(m, "B_XT", domain=j)
beta_KD = gp.Parameter(m, "beta_KD", domain=[k, j])
beta_LD = gp.Parameter(m, "beta_LD", domain=[l, j])
beta_M = gp.Parameter(m, "beta_M", domain=i)
beta_VA = gp.Parameter(m, "beta_VA", domain=j)
beta_X = gp.Parameter(m, "beta_X", domain=[j, i])
beta_XT = gp.Parameter(m, "beta_XT", domain=[j, i])
delta = gp.Parameter(m, "delta", domain=[k, j])
eta = gp.Parameter(m, "eta")
frisch = gp.Parameter(m, "frisch", domain=h)
gamma_GVT = gp.Parameter(m, "gamma_GVT", domain=i)
gamma_INVPRI = gp.Parameter(m, "gamma_INVPRI", domain=i)
gamma_INVPUB = gp.Parameter(m, "gamma_INVPUB", domain=i)
gamma_LES = gp.Parameter(m, "gamma_LES", domain=[i, h])
io_ = gp.Parameter(m, "io_", domain=j)          # 'io' shadows Python's io module
lambda_RK = gp.Parameter(m, "lambda_RK", domain=[ag, k])
lambda_TR = gp.Parameter(m, "lambda_TR", domain=[ag, agj])
lambda_WL = gp.Parameter(m, "lambda_WL", domain=[h, l])
n = gp.Parameter(m, "n", domain=TIME)
n1 = gp.Parameter(m, "n1")
phi = gp.Parameter(m, "phi", domain=[k, j])
pop = gp.Parameter(m, "pop", domain=TIME)
rho_KD = gp.Parameter(m, "rho_KD", domain=j)
rho_LD = gp.Parameter(m, "rho_LD", domain=j)
rho_M = gp.Parameter(m, "rho_M", domain=i)
rho_VA = gp.Parameter(m, "rho_VA", domain=j)
rho_X = gp.Parameter(m, "rho_X", domain=[j, i])
rho_XT = gp.Parameter(m, "rho_XT", domain=j)
sigma_INV = gp.Parameter(m, "sigma_INV", domain=[k, j])
sigma_KD = gp.Parameter(m, "sigma_KD", domain=j)
sigma_LD = gp.Parameter(m, "sigma_LD", domain=j)
sigma_M = gp.Parameter(m, "sigma_M", domain=i)
sigma_VA = gp.Parameter(m, "sigma_VA", domain=j)
sigma_X = gp.Parameter(m, "sigma_X", domain=[j, i])
sigma_XT = gp.Parameter(m, "sigma_XT", domain=j)
sigma_XD = gp.Parameter(m, "sigma_XD", domain=i)
sigma_Y = gp.Parameter(m, "sigma_Y", domain=[i, h])
tmrg = gp.Parameter(m, "tmrg", domain=[i, ij])
tmrg_X = gp.Parameter(m, "tmrg_X", domain=[i, ij])
v = gp.Parameter(m, "v", domain=j)

# ===========================================================================
# 2.2 BENCHMARK ("O") VALUES  (.gms lines 209-345) -- stored as Parameters
# ===========================================================================
CO = gp.Parameter(m, "CO", domain=[i, h])
CGO = gp.Parameter(m, "CGO", domain=i)
CIO = gp.Parameter(m, "CIO", domain=j)
CMINO = gp.Parameter(m, "CMINO", domain=[i, h])
CTH_REALO = gp.Parameter(m, "CTH_REALO", domain=h)
DDO = gp.Parameter(m, "DDO", domain=i)
DIO = gp.Parameter(m, "DIO", domain=[i, j])
DITO = gp.Parameter(m, "DITO", domain=i)
DSO = gp.Parameter(m, "DSO", domain=[j, i])
EXO = gp.Parameter(m, "EXO", domain=[j, i])
EXDO = gp.Parameter(m, "EXDO", domain=i)
G_REALO = gp.Parameter(m, "G_REALO")
GDP_BP_REALO = gp.Parameter(m, "GDP_BP_REALO")
GDP_MP_REALO = gp.Parameter(m, "GDP_MP_REALO")
GFCF_PRI_REALO = gp.Parameter(m, "GFCF_PRI_REALO")
GFCF_PUB_REALO = gp.Parameter(m, "GFCF_PUB_REALO")
IMO = gp.Parameter(m, "IMO", domain=i)
INDO = gp.Parameter(m, "INDO", domain=[k, j])
INVO = gp.Parameter(m, "INVO", domain=i)
INV_PRIO = gp.Parameter(m, "INV_PRIO", domain=i)
INV_PUBO = gp.Parameter(m, "INV_PUBO", domain=i)
KDO = gp.Parameter(m, "KDO", domain=[k, j])
KDCO = gp.Parameter(m, "KDCO", domain=j)
KSO = gp.Parameter(m, "KSO", domain=k)
LDO = gp.Parameter(m, "LDO", domain=[l, j])
LDCO = gp.Parameter(m, "LDCO", domain=j)
LSO = gp.Parameter(m, "LSO", domain=l)
MRGNO = gp.Parameter(m, "MRGNO", domain=i)
QO = gp.Parameter(m, "QO", domain=i)
VAO = gp.Parameter(m, "VAO", domain=j)
VSTKO = gp.Parameter(m, "VSTKO", domain=i)
XSO = gp.Parameter(m, "XSO", domain=[j, i])
XSTO = gp.Parameter(m, "XSTO", domain=j)

eO = gp.Parameter(m, "eO")
IRO = gp.Parameter(m, "IRO")
PO = gp.Parameter(m, "PO", domain=[j, i])
PCO = gp.Parameter(m, "PCO", domain=i)
PCIO = gp.Parameter(m, "PCIO", domain=j)
PDO = gp.Parameter(m, "PDO", domain=i)
PEO = gp.Parameter(m, "PEO", domain=i)
PE_FOBO = gp.Parameter(m, "PE_FOBO", domain=i)
PIXCONO = gp.Parameter(m, "PIXCONO")
PIXGDPO = gp.Parameter(m, "PIXGDPO")
PIXGVTO = gp.Parameter(m, "PIXGVTO")
PIXINV_PRIO = gp.Parameter(m, "PIXINV_PRIO")
PIXINV_PUBO = gp.Parameter(m, "PIXINV_PUBO")
PK_PRIO = gp.Parameter(m, "PK_PRIO")
PK_PUBO = gp.Parameter(m, "PK_PUBO")
PLO = gp.Parameter(m, "PLO", domain=i)
PMO = gp.Parameter(m, "PMO", domain=i)
PPO = gp.Parameter(m, "PPO", domain=j)
PTO = gp.Parameter(m, "PTO", domain=j)
PVAO = gp.Parameter(m, "PVAO", domain=j)
PWMO = gp.Parameter(m, "PWMO", domain=i)
PWXO = gp.Parameter(m, "PWXO", domain=i)
RO = gp.Parameter(m, "RO", domain=[k, j])
RCO = gp.Parameter(m, "RCO", domain=j)
RTIO = gp.Parameter(m, "RTIO", domain=[k, j])
UO = gp.Parameter(m, "UO", domain=[k, j])
WO = gp.Parameter(m, "WO", domain=l)
WCO = gp.Parameter(m, "WCO", domain=j)
WTIO = gp.Parameter(m, "WTIO", domain=[l, j])

CABO = gp.Parameter(m, "CABO")
CTHO = gp.Parameter(m, "CTHO", domain=h)
GO = gp.Parameter(m, "GO")
GDP_BPO = gp.Parameter(m, "GDP_BPO")
GDP_FDO = gp.Parameter(m, "GDP_FDO")
GDP_IBO = gp.Parameter(m, "GDP_IBO")
GDP_MPO = gp.Parameter(m, "GDP_MPO")
GFCFO = gp.Parameter(m, "GFCFO")
ITO = gp.Parameter(m, "ITO")
IT_PRIO = gp.Parameter(m, "IT_PRIO")
IT_PUBO = gp.Parameter(m, "IT_PUBO")
RKDO = gp.Parameter(m, "RKDO", domain=[k, j])
SFO = gp.Parameter(m, "SFO", domain=f)
SGO = gp.Parameter(m, "SGO")
SHO = gp.Parameter(m, "SHO", domain=h)
SROWO = gp.Parameter(m, "SROWO")
TDFO = gp.Parameter(m, "TDFO", domain=f)
TDFTO = gp.Parameter(m, "TDFTO")
TDHO = gp.Parameter(m, "TDHO", domain=h)
TDHTO = gp.Parameter(m, "TDHTO")
TICO = gp.Parameter(m, "TICO", domain=i)
TICTO = gp.Parameter(m, "TICTO")
TIKO = gp.Parameter(m, "TIKO", domain=[k, j])
TIKTO = gp.Parameter(m, "TIKTO")
TIMO = gp.Parameter(m, "TIMO", domain=i)
TIMTO = gp.Parameter(m, "TIMTO")
TIPO = gp.Parameter(m, "TIPO", domain=j)
TIPTO = gp.Parameter(m, "TIPTO")
TIWO = gp.Parameter(m, "TIWO", domain=[l, j])
TIWTO = gp.Parameter(m, "TIWTO")
TIXO = gp.Parameter(m, "TIXO", domain=i)
TIXTO = gp.Parameter(m, "TIXTO")
TPRCTSO = gp.Parameter(m, "TPRCTSO")
TPRODNO = gp.Parameter(m, "TPRODNO")
TRO = gp.Parameter(m, "TRO", domain=[ag, agj])
YDFO = gp.Parameter(m, "YDFO", domain=f)
YDHO = gp.Parameter(m, "YDHO", domain=h)
YFO = gp.Parameter(m, "YFO", domain=f)
YFKO = gp.Parameter(m, "YFKO", domain=f)
YFTRO = gp.Parameter(m, "YFTRO", domain=f)
YGO = gp.Parameter(m, "YGO")
YGKO = gp.Parameter(m, "YGKO")
YGTRO = gp.Parameter(m, "YGTRO")
YHO = gp.Parameter(m, "YHO", domain=h)
YHKO = gp.Parameter(m, "YHKO", domain=h)
YHLO = gp.Parameter(m, "YHLO", domain=h)
YHTRO = gp.Parameter(m, "YHTRO", domain=h)
YROWO = gp.Parameter(m, "YROWO")

sh0O = gp.Parameter(m, "sh0O", domain=h)
sh1O = gp.Parameter(m, "sh1O", domain=h)
tr0O = gp.Parameter(m, "tr0O", domain=h)
tr1O = gp.Parameter(m, "tr1O", domain=h)
ttdf0O = gp.Parameter(m, "ttdf0O", domain=f)
ttdf1O = gp.Parameter(m, "ttdf1O", domain=f)
ttdh0O = gp.Parameter(m, "ttdh0O", domain=h)
ttdh1O = gp.Parameter(m, "ttdh1O", domain=h)
tticO = gp.Parameter(m, "tticO", domain=i)
ttikO = gp.Parameter(m, "ttikO", domain=[k, j])
ttimO = gp.Parameter(m, "ttimO", domain=i)
ttipO = gp.Parameter(m, "ttipO", domain=j)
ttiwO = gp.Parameter(m, "ttiwO", domain=[l, j])
ttixO = gp.Parameter(m, "ttixO", domain=i)

# ===========================================================================
# 3.1 DATA FROM THE SAM  (.gms lines 356-393)
# ===========================================================================
sam = data_io.SAM(SAM_PATH, engine="xlrd")


def _fill_from_sam(par, fn):
    """fn(elem-tuple) -> float ; fills every record of `par` via sam()."""
    import itertools
    # par.domain already holds the actual Set objects passed in via domain=[...],
    # no need to look them up again in the Container.
    sets = list(par.domain)
    # Set.records is a DataFrame whose first column holds the element labels
    # (its name varies - "uni", the set's own name, etc.) - so grab it
    # positionally instead of by name. toList() is the documented fallback.
    elems = []
    for s in sets:
        if s.records is not None and len(s.records) > 0:
            elems.append(s.records.iloc[:, 0].tolist())
        else:
            elems.append(s.toList())
    recs = []
    for combo in itertools.product(*elems):
        val = fn(combo)
        if val:
            recs.append((*combo, val))
    par.setRecords(recs)


# CO, CGO, DSO, DDO, DIO, EXO, EXDO, INVO, VSTKO, IMO, RKDO, LDO, SFO, SGO,
# SHO, SROWO, TDFO, TDHO, TICO, TIKO, TIMO, TIPO, TIXO, TIWO, TRO,
# lambda_RK, lambda_WL, tmrg, tmrg_X   (.gms 365-393)
_fill_from_sam(CO, lambda e: sam("I", e[0], "AG", e[1]))
_fill_from_sam(CGO, lambda e: sam("I", e[0], "AG", "gvt"))
_fill_from_sam(DSO, lambda e: sam("J", e[0], "I", e[1]))
DDO[i] = Sum(j, DSO[j, i])
_fill_from_sam(DIO, lambda e: sam("I", e[0], "J", e[1]))
_fill_from_sam(EXO, lambda e: sam("J", e[0], "X", e[1]))
_fill_from_sam(EXDO, lambda e: sam("X", e[0], "AG", "row"))
_fill_from_sam(INVO, lambda e: sam("I", e[0], "OTH", "inv"))
_fill_from_sam(VSTKO, lambda e: sam("I", e[0], "OTH", "vstk"))
_fill_from_sam(IMO, lambda e: sam("AG", "row", "I", e[0]))
_fill_from_sam(RKDO, lambda e: sam("K", e[0], "J", e[1]))
_fill_from_sam(LDO, lambda e: sam("L", e[0], "J", e[1]))
_fill_from_sam(SFO, lambda e: sam("OTH", "inv", "AG", e[0]))
SGO[...] = sam("OTH", "inv", "AG", "gvt")
_fill_from_sam(SHO, lambda e: sam("OTH", "inv", "AG", e[0]))
SROWO[...] = sam("OTH", "inv", "AG", "row")
_fill_from_sam(TDFO, lambda e: sam("AG", "td", "AG", e[0]))
_fill_from_sam(TDHO, lambda e: sam("AG", "td", "AG", e[0]))
_fill_from_sam(TICO, lambda e: sam("AG", "ti", "I", e[0]))
_fill_from_sam(TIKO, lambda e: sam("AG", e[0], "J", e[1]))
_fill_from_sam(TIMO, lambda e: sam("AG", "tm", "I", e[0]))
_fill_from_sam(TIPO, lambda e: sam("AG", "gvt", "J", e[0]))
_fill_from_sam(TIXO, lambda e: sam("AG", "gvt", "X", e[0]))
_fill_from_sam(TIWO, lambda e: sam("AG", e[0], "J", e[1]))
_fill_from_sam(TRO, lambda e: sam("AG", e[0], "AG", e[1]))
_fill_from_sam(lambda_RK, lambda e: sam("AG", e[0], "K", e[1]))
_fill_from_sam(lambda_WL, lambda e: sam("AG", e[0], "L", e[1]))
_fill_from_sam(tmrg, lambda e: sam("I", e[0], "I", e[1]))
_fill_from_sam(tmrg_X, lambda e: sam("I", e[0], "X", e[1]))

# ===========================================================================
# 3.2 OTHER DATA (VAL_PAR.xlsx)  (.gms lines 399-457)
# ===========================================================================
par = data_io.load_val_par(VAL_PAR_PATH)
PARJ, PARI, PARJI, PARAG, PART = par["PARJ"], par["PARI"], par["PARJI"], par["PARAG"], par["PART"]
PARKJ1, PARKJ2 = par["PARKJ1"], par["PARKJ2"]

# Population growth (.gms 407-413)
n.setRecords([(str(t), v) for t, v in PART["n"].items()])
n1[...] = Sum(T1, n[T1])
pop[T1] = 1
for idx, t_str in enumerate([str(x) for x in range(1, 11)]):
    if idx == 0:
        continue
    prev = str(idx)  # time-1
    pop[t_str] = pop[prev] * (1 + n[prev])

IRO[...] = 0.04
sigma_INV.setRecords([(k_, j_, PARKJ2.loc[k_, j_]) for k_ in PARKJ2.index for j_ in PARKJ2.columns])
eta[...] = 1

sigma_KD.setRecords([(j_, PARJ.loc[j_, "sigma_kd"]) for j_ in PARJ.index])
sigma_LD.setRecords([(j_, PARJ.loc[j_, "sigma_ld"]) for j_ in PARJ.index])
sigma_M.setRecords([(i_, PARI.loc[i_, "sigma_m"]) for i_ in PARI.index])
sigma_VA.setRecords([(j_, PARJ.loc[j_, "sigma_va"]) for j_ in PARJ.index])
sigma_X.setRecords([(j_, i_, PARJI.loc[j_, i_]) for j_ in PARJI.index for i_ in PARJI.columns])
sigma_XT.setRecords([(j_, PARJ.loc[j_, "sigma_xt"]) for j_ in PARJ.index])
sigma_XD.setRecords([(i_, PARI.loc[i_, "sigma_xd"]) for i_ in PARI.index])

frisch.setRecords([(h_, PARAG.loc["frisch", h_]) for h_ in ["hrp", "hup", "hrr", "hur"]])
sigma_Y.setRecords([(i_, h_, PARAG.loc[i_, h_]) for i_ in ["agr", "food", "othind", "ser", "adm"]
                     for h_ in ["hrp", "hup", "hrr", "hur"]])

sh0O.setRecords([(h_, PARAG.loc["sh0o", h_]) for h_ in ["hrp", "hup", "hrr", "hur"]])
tr0O.setRecords([(h_, PARAG.loc["tr0o", h_]) for h_ in ["hrp", "hup", "hrr", "hur"]])
ttdf0O.setRecords([("firm", PARAG.loc["ttdf0o", "firm"])])
ttdh0O.setRecords([(h_, PARAG.loc["ttdh0o", h_]) for h_ in ["hrp", "hup", "hrr", "hur"]])

eO[...] = 1
PEO[i] = 1
PLO[i] = 1
PWMO[i] = 1
WO[l] = 1

# ===========================================================================
# 4. CALIBRATION  (.gms lines 460-820)
# ===========================================================================
agd_ = agd  # alias for readability below

# -- 4.1 Income and savings --------------------------------------------------
YHKO[h] = Sum(k, lambda_RK[h, k])
YHLO[h] = Sum(l, lambda_WL[h, l])
YHTRO[h] = Sum(ag, TRO[h, ag])
YHO[h] = YHLO[h] + YHKO[h] + YHTRO[h]
YDHO[h] = YHO[h] - TDHO[h] - TRO["gvt", h]
CTHO[h] = YDHO[h] - SHO[h] - Sum(agng, TRO[agng, h])

YFKO[f] = Sum(k, lambda_RK[f, k])
YFTRO[f] = Sum(ag, TRO[f, ag])
YFO[f] = YFKO[f] + YFTRO[f]
YDFO[f] = YFO[f] - TDFO[f]

YGKO[...] = Sum(k, lambda_RK["gvt", k])
TDHTO[...] = Sum(h, TDHO[h])
TDFTO[...] = Sum(f, TDFO[f])
TICTO[...] = Sum(i, TICO[i])
TIMTO[...] = Sum(i, TIMO[i])
TIXTO[...] = Sum(i, TIXO[i])
TIWTO[...] = Sum((l, j), TIWO[l, j])
TIKTO[...] = Sum((k, j), TIKO[k, j])
TIPTO[...] = Sum(j, TIPO[j])
TPRODNO[...] = TIKTO + TIWTO + TIPTO
TPRCTSO[...] = TICTO + TIMTO + TIXTO
YGTRO[...] = Sum(ag, TRO["gvt", ag])
YGO[...] = YGKO + TDHTO + TDFTO + TPRODNO + TPRCTSO + YGTRO

YROWO[...] = Sum(i, IMO[i]) + Sum(k, lambda_RK["row", k]) + Sum(ag, TRO["row", ag])
CABO[...] = -SROWO

ITO[...] = Sum(h, SHO[h]) + Sum(f, SFO[f]) + SGO + SROWO

lambda_RK[ag, k] = lambda_RK[ag, k] / Sum(j, RKDO[k, j])
lambda_WL[h, l] = lambda_WL[h, l] / Sum(j, LDO[l, j])
lambda_TR[agng, h] = TRO[agng, h] / YDHO[h]
lambda_TR[ag, f] = TRO[ag, f] / YDFO[f]

sh1O[h] = (SHO[h] - sh0O[h]) / YDHO[h]
tr1O[h] = (TRO["gvt", h] - tr0O[h]) / YHO[h]

# -- 4.2 Investment and government spending shares --------------------------
gamma_GVT[i] = CGO[i] / Sum(ij, CGO[ij])
gamma_INVPRI[i] = INVO[i] / Sum(ij, INVO[ij])
gamma_INVPUB[i] = gamma_INVPRI[i]

# -- 4.3 Income tax rates -----------------------------------------------------
ttdf1O[f] = (TDFO[f] - ttdf0O[f]) / YFKO[f]
ttdh1O[h] = (TDHO[h] - ttdh0O[h]) / YHO[h]

# -- 4.4 Margins, prices and volumes -----------------------------------------
PCO[i] = (DDO[i] + IMO[i] + Sum(ij, tmrg[ij, i]) + TICO[i] + TIMO[i]) / (DDO[i] + IMO[i])
tmrg[i, ij] = tmrg[i, ij] / PCO[i]
tmrg_X[i, ij] = tmrg_X[i, ij] / PCO[i]

DDO[i] = DDO[i] / PLO[i]
IMO[i] = IMO[i] / (PWMO[i] * eO)

tmrg[i, ij] = tmrg[i, ij] / (DDO[ij] + IMO[ij])

tticO[i] = TICO[i] / (
    (PLO[i] + Sum(ij, PCO[ij] * tmrg[ij, i])) * DDO[i]
    + (eO * PWMO[i] + Sum(ij, PCO[ij] * tmrg[ij, i])) * IMO[i]
    + TIMO[i]
)

PDO[i] = (PLO[i] + Sum(ij, PCO[ij] * tmrg[ij, i])) * (1 + tticO[i])

ttimO[i].where[IMO[i]] = TIMO[i] / (eO * PWMO[i] * IMO[i])

PMO[i] = ((1 + ttimO[i]) * eO * PWMO[i] + Sum(ij, PCO[ij] * tmrg[ij, i])) * (1 + tticO[i])

EXO[j, i] = EXO[j, i] / PEO[i]
tmrg_X[ij, i].where[EXDO[i]] = tmrg_X[ij, i] / Sum(j, EXO[j, i])
ttixO[i].where[EXDO[i]] = TIXO[i] / (EXDO[i] - TIXO[i])
PE_FOBO[i] = (1 + ttixO[i]) * (PEO[i] + Sum(ij, PCO[ij] * tmrg_X[ij, i]))
PWXO[i] = PE_FOBO[i] / eO
EXDO[i] = EXDO[i] / (PWXO[i] * eO)

DSO[j, i] = DSO[j, i] / PLO[i]
XSO[j, i] = DSO[j, i] + EXO[j, i]
PO[j, i].where[XSO[j, i]] = (PLO[i] * DSO[j, i] + PEO[i] * EXO[j, i]) / XSO[j, i]
XSTO[j] = Sum(i, XSO[j, i])
PTO[j] = Sum(i.where[XSO[j, i]], PO[j, i] * XSO[j, i]) / XSTO[j]

QO[i] = (PMO[i] * IMO[i] + PDO[i] * DDO[i]) / PCO[i]

MRGNO[i] = (
    Sum(ij, tmrg[i, ij] * DDO[ij])
    + Sum(ij, tmrg[i, ij] * IMO[ij])
    + Sum((j, ij), tmrg_X[i, ij] * EXO[j, ij])
)

CO[i, h] = CO[i, h] / PCO[i]
CGO[i] = CGO[i] / PCO[i]
DIO[i, j] = DIO[i, j] / PCO[i]
INVO[i] = INVO[i] / PCO[i]
VSTKO[i] = VSTKO[i] / PCO[i]
GFCFO[...] = ITO - Sum(i, PCO[i] * VSTKO[i])

CIO[j] = Sum(i, DIO[i, j])
DITO[i] = Sum(j, DIO[i, j])
GO[...] = Sum(i, PCO[i] * CGO[i])

PCIO[j] = Sum(i, PCO[i] * DIO[i, j]) / CIO[j]

ttiwO[l, j].where[LDO[l, j]] = TIWO[l, j] / LDO[l, j]
WTIO[l, j] = WO[l] * (1 + ttiwO[l, j])
ttikO[k, j].where[RKDO[k, j]] = TIKO[k, j] / RKDO[k, j]

LDO[l, j] = LDO[l, j] / WO[l]
LDCO[j] = Sum(l, LDO[l, j])
LSO[l] = Sum(j, LDO[l, j])
WCO[j].where[LDCO[j]] = Sum(l, WTIO[l, j] * LDO[l, j]) / LDCO[j]

# -- 4.5 Dynamic parameters ---------------------------------------------------
delta.setRecords([(k_, j_, PARKJ1.loc[k_, j_]) for k_ in PARKJ1.index for j_ in PARKJ1.columns])

PK_PRIO[...] = 1
PK_PUBO[...] = 1

A_K_PRI[...] = (1 / PK_PRIO) * Product(
    i.where[gamma_INVPRI[i]], (PCO[i] / gamma_INVPRI[i]) ** gamma_INVPRI[i]
)
A_K_PUB[...] = (1 / PK_PUBO) * Product(
    i.where[gamma_INVPUB[i]], (PCO[i] / gamma_INVPUB[i]) ** gamma_INVPUB[i]
)

UO[k, bus] = PK_PRIO * (IRO + delta[k, bus])
UO[k, pub] = PK_PUBO * (IRO + delta[k, pub])

alpha[...] = Sum(
    (k, j),
    RKDO[k, j] * ((n1 + delta[k, j]) / (delta[k, j] + IRO)) / (ITO - Sum(i, PCO[i] * VSTKO[i])),
)

RO[k, j] = alpha * UO[k, j]
KDO[k, j] = RKDO[k, j] / RO[k, j]
INDO[k, j] = KDO[k, j] * (n1 + delta[k, j])

IT_PUBO[...] = Sum((k, pub), INDO[k, pub]) * PK_PUBO
IT_PRIO[...] = ITO - IT_PUBO - Sum(i, VSTKO[i] * PCO[i])
INV_PUBO[i] = gamma_INVPUB[i] * IT_PUBO / PCO[i]
INV_PRIO[i] = gamma_INVPRI[i] * IT_PRIO / PCO[i]

phi[k, bus].where[KDO[k, bus]] = (
    INDO[k, bus] / KDO[k, bus] * (UO[k, bus] / RO[k, bus]) ** sigma_INV[k, bus]
)

# -- 4.6 Other prices and volumes --------------------------------------------
RTIO[k, j] = RO[k, j] * (1 + ttikO[k, j])
KDCO[j] = Sum(k, KDO[k, j])
KSO[k] = Sum(j, KDO[k, j])
RCO[j].where[KDCO[j]] = Sum(k, RTIO[k, j] * KDO[k, j]) / KDCO[j]

VAO[j] = LDCO[j] + KDCO[j]
PVAO[j] = (WCO[j] * LDCO[j] + RCO[j] * KDCO[j]) / VAO[j]

ttipO[j] = TIPO[j] / (PVAO[j] * VAO[j] + Sum(i, PCO[i] * DIO[i, j]))
PPO[j] = PTO[j] / (1 + ttipO[j])

PIXGDPO[...] = 1
PIXCONO[...] = 1
PIXGVTO[...] = 1
PIXINV_PRIO[...] = 1
PIXINV_PUBO[...] = 1

# -- 4.7 Indexed transfers and parameters ------------------------------------
TRO[agd_, "row"] = TRO[agd_, "row"] / PIXCONO ** eta
TRO[agng, "gvt"] = TRO[agng, "gvt"] / PIXCONO ** eta
ttdf0O[f] = ttdf0O[f] / PIXCONO ** eta
ttdh0O[h] = ttdh0O[h] / PIXCONO ** eta
sh0O[h] = sh0O[h] / PIXCONO ** eta
tr0O[h] = tr0O[h] / PIXCONO ** eta

# -- 4.8.1 Leontief -----------------------------------------------------------
io_[j] = CIO[j] / XSTO[j]
v[j] = VAO[j] / XSTO[j]
aij[i, j] = DIO[i, j] / CIO[j]

# -- 4.8.2 CET -----------------------------------------------------------------
rho_XT[j] = (1 + sigma_XT[j]) / sigma_XT[j]
beta_XT[j, i].where[(XSO[j, i] > 0) & (Sum(ij, XSO[j, ij]) > 0)] = (
    PO[j, i] * XSO[j, i] ** (1 - rho_XT[j]) / Sum(ij.where[XSO[j, ij]], PO[j, ij] * XSO[j, ij] ** (1 - rho_XT[j]))
)
B_XT[j] = XSTO[j] / Sum(i.where[XSO[j, i]], beta_XT[j, i] * XSO[j, i] ** rho_XT[j]) ** (1 / rho_XT[j])

rho_X[j, i].where[(EXO[j, i] > 0) & (DSO[j, i] > 0)] = (1 + sigma_X[j, i]) / sigma_X[j, i]
rho_X[j, i].where[(EXO[j, i] == 0) | (DSO[j, i] == 0)] = 1
beta_X[j, i].where[XSO[j, i]] = (
    PEO[i] * EXO[j, i] ** (1 - rho_X[j, i])
    / (PEO[i] * EXO[j, i] ** (1 - rho_X[j, i]) + PLO[i] * DSO[j, i] ** (1 - rho_X[j, i]))
)
B_X[j, i].where[XSO[j, i]] = XSO[j, i] / (
    beta_X[j, i] * EXO[j, i] ** rho_X[j, i] + (1 - beta_X[j, i]) * DSO[j, i] ** rho_X[j, i]
) ** (1 / rho_X[j, i])

# -- 4.8.3 CES ------------------------------------------------------------------
rho_M[i].where[(IMO[i] > 0) & (DDO[i] > 0)] = (1 - sigma_M[i]) / sigma_M[i]
rho_M[i].where[(IMO[i] == 0) | (DDO[i] == 0)] = -1
beta_M[i].where[QO[i]] = (
    PMO[i] * IMO[i] ** (rho_M[i] + 1)
    / (PMO[i] * IMO[i] ** (rho_M[i] + 1) + PDO[i] * DDO[i] ** (rho_M[i] + 1))
)
B_M[i].where[QO[i]] = QO[i] / (
    beta_M[i] * IMO[i] ** (-rho_M[i]) + (1 - beta_M[i]) * DDO[i] ** (-rho_M[i])
) ** (-1 / rho_M[i])

rho_KD[j].where[KDCO[j]] = (1 - sigma_KD[j]) / sigma_KD[j]
beta_KD[k, j].where[KDO[k, j]] = (
    RTIO[k, j] * KDO[k, j] ** (rho_KD[j] + 1) / Sum(kj, RTIO[kj, j] * KDO[kj, j] ** (rho_KD[j] + 1))
)
B_KD[j].where[KDCO[j]] = KDCO[j] / Sum(k.where[KDO[k, j]], beta_KD[k, j] * KDO[k, j] ** (-rho_KD[j])) ** (-1 / rho_KD[j])

rho_LD[j] = (1 - sigma_LD[j]) / sigma_LD[j]
beta_LD[l, j].where[LDO[l, j]] = (
    WTIO[l, j] * LDO[l, j] ** (rho_LD[j] + 1) / Sum(lj, WTIO[lj, j] * LDO[lj, j] ** (rho_LD[j] + 1))
)
B_LD[j].where[LDCO[j]] = LDCO[j] / Sum(l.where[LDO[l, j]], beta_LD[l, j] * LDO[l, j] ** (-rho_LD[j])) ** (-1 / rho_LD[j])

rho_VA[j].where[(KDCO[j] > 0) & (LDCO[j] > 0)] = (1 - sigma_VA[j]) / sigma_VA[j]
rho_VA[j].where[(KDCO[j] == 0) | (LDCO[j] == 0)] = -1
beta_VA[j] = (
    WCO[j] * LDCO[j] ** (rho_VA[j] + 1)
    / (WCO[j] * LDCO[j] ** (rho_VA[j] + 1) + RCO[j] * KDCO[j] ** (rho_VA[j] + 1))
)
B_VA[j] = VAO[j] / (
    beta_VA[j] * LDCO[j] ** (-rho_VA[j]) + (1 - beta_VA[j]) * KDCO[j] ** (-rho_VA[j])
) ** (-1 / rho_VA[j])

# -- 4.8.4 LES -------------------------------------------------------------------
sigma_Y[i, h] = sigma_Y[i, h] * CTHO[h] / Sum(ij, sigma_Y[ij, h] * PCO[ij] * CO[ij, h])
gamma_LES[i, h] = PCO[i] * CO[i, h] * sigma_Y[i, h] / CTHO[h]
CMINO[i, h] = CO[i, h] + gamma_LES[i, h] * (CTHO[h] / (PCO[i] * frisch[h]))

# -- 4.9 GDP -----------------------------------------------------------------------
GDP_BPO[...] = Sum(j, PVAO[j] * VAO[j]) + TIPTO
GDP_MPO[...] = GDP_BPO + TPRCTSO
GDP_IBO[...] = Sum((l, j), WO[l] * LDO[l, j]) + Sum((k, j), RO[k, j] * KDO[k, j]) + TPRODNO + TPRCTSO
GDP_FDO[...] = (
    Sum(i, PCO[i] * (Sum(h, CO[i, h]) + CGO[i] + INVO[i] + VSTKO[i]))
    + Sum(i, PE_FOBO[i] * EXDO[i]) - Sum(i, PWMO[i] * eO * IMO[i])
)

# -- 4.10 Real variables ------------------------------------------------------------
CTH_REALO[h] = CTHO[h] / PIXCONO
G_REALO[...] = GO / PIXGVTO
GDP_BP_REALO[...] = GDP_BPO / PIXGDPO
GDP_MP_REALO[...] = GDP_MPO / PIXCONO
GFCF_PRI_REALO[...] = IT_PRIO / PIXINV_PRIO
GFCF_PUB_REALO[...] = IT_PUBO / PIXINV_PUBO

print("pep_data.py: sets, parameters, data load and calibration built OK.")

if __name__ == "__main__":
    print("GDP_BPO =", GDP_BPO.records)
    print("n1 =", n1.records)
