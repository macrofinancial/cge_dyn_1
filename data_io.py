"""
data_io.py
----------
Replaces the GAMS $CALL GDXXRW.EXE ... / $GDXIN ... / $LOAD ... pattern used in
PEP_1-t-b_v2_1.gms to pull data out of the two Excel workbooks:

    SAM-V2_0.xls   ->  SAM(*,*,*,*)                       (the Social Accounting Matrix)
    VAL_PAR.xlsx   ->  PARJ, PARI, PARJI, PARAG, PART, PARKJ1, PARKJ2

GAMSPy has no GDXXRW equivalent, so instead of writing a .gdx file we read the
workbooks straight into pandas DataFrames that mimic GAMS's sparse, multi-
dimensional PARAMETER lookup (SAM('I',i,'AG',h), PARJ(j,'sigma_KD'), ...).

NOTE: SAM-V2_0.xls is a legacy BIFF (.xls) file. Reading it with pandas needs
the 'xlrd' engine (xlrd>=2.0 only reads .xls, not .xlsx):

    pip install xlrd openpyxl

If you'd rather not install xlrd, just open SAM-V2_0.xls once in Excel and
"Save As" SAM-V2_0.xlsx - set SAM_PATH below to that file instead; the ranges
are identical.
"""
from __future__ import annotations
import pandas as pd


# ---------------------------------------------------------------------------
# 1. The SAM: SAM-V2_0.xls, sheet "SAM", range A4:AJ39, Rdim=2, Cdim=2
#    (2-level row labels in columns A:B, 2-level column labels in rows 4:5)
# ---------------------------------------------------------------------------
class SAM:
    """Sparse 4-key lookup replicating GAMS's SAM('cat1',elem1,'cat2',elem2)."""

    def __init__(self, path: str, sheet: str = "SAM", engine: str | None = None):
        # header=[0,1] -> columns become a 2-level MultiIndex from rows 4-5
        # index_col=[0,1] -> rows become a 2-level MultiIndex from cols A-B
        # skiprows=2 drops the two title rows above the A4:AJ39 range
        df = pd.read_excel(
            path, sheet_name=sheet, header=[0, 1], index_col=[0, 1],
            skiprows=3, nrows=34, engine=engine,
        )
        df = df.dropna(how="all").dropna(how="all", axis=1)
        # normalize labels: GAMS element names in the .gms file are lowercase
        df.index = pd.MultiIndex.from_tuples(
            [(str(a).strip().lower(), str(b).strip().lower()) for a, b in df.index]
        )
        df.columns = pd.MultiIndex.from_tuples(
            [(str(a).strip().lower(), str(b).strip().lower()) for a, b in df.columns]
        )
        self.df = df.fillna(0.0)

    def __call__(self, cat1: str, elem1: str, cat2: str, elem2: str) -> float:
        key_r = (cat1.lower(), elem1.lower())
        key_c = (cat2.lower(), elem2.lower())
        if key_r not in self.df.index or key_c not in self.df.columns:
            return 0.0  # GAMS returns 0 for an undefined parameter record
        return float(self.df.loc[key_r, key_c])


# ---------------------------------------------------------------------------
# 2. VAL_PAR.xlsx, sheet "PAR": seven small tables at fixed ranges, exactly
#    mirroring the seven $CALL GDXXRW ... par=... rng=PAR!... clauses.
# ---------------------------------------------------------------------------
def _block(path, sheet, rng, index_name, engine=None):
    """Read one PAR!A#:#C# block as a DataFrame indexed by its row labels
    (lower-cased) with columns = the header row (lower-cased)."""
    # rng like "A5:E9" -> header is row 5 (first row), data rows 6-9
    import re
    m = re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", rng)
    c1, r1, c2, r2 = m.groups()
    r1, r2 = int(r1), int(r2)
    usecols = f"{c1}:{c2}"
    raw = pd.read_excel(
        path, sheet_name=sheet, header=None, usecols=usecols,
        skiprows=r1 - 1, nrows=r2 - r1 + 1, engine=engine,
    )
    raw.columns = [str(c).strip().lower() if c is not None else "" for c in raw.iloc[0]]
    raw = raw.iloc[1:].reset_index(drop=True)
    raw = raw.rename(columns={raw.columns[0]: index_name})

    def _label(v):
        # Excel stores the "time" column (1,2,...,10) as floats (1.0, 2.0, ...);
        # str(1.0) == "1.0" which won't match the TIME set's "1".."10" labels,
        # so collapse whole-number floats to plain integer strings first.
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v).strip().lower()

    raw[index_name] = raw[index_name].apply(_label)
    raw = raw.set_index(index_name)
    return raw.astype(float)


def load_val_par(path: str, engine: str | None = None) -> dict[str, pd.DataFrame]:
    """Returns dict with keys PARJ, PARI, PARJI, PARAG, PART, PARKJ1, PARKJ2,
    each a DataFrame you can index like PARJ.loc['agr', 'sigma_KD'.lower()]."""
    ranges = {
        "PARJ":   "A5:E9",
        "PARI":   "A12:C17",
        "PARJI":  "A20:F24",
        "PARAG":  "A27:F37",
        "PART":   "A40:B50",
        "PARKJ1": "A53:E55",
        "PARKJ2": "A58:E60",
    }
    index_names = {
        "PARJ": "j", "PARI": "i", "PARJI": "j", "PARAG": "row",
        "PART": "time", "PARKJ1": "k", "PARKJ2": "k",
    }
    out = {}
    for name, rng in ranges.items():
        out[name] = _block(path, "PAR", rng, index_names[name], engine=engine)
    return out


if __name__ == "__main__":
    # Quick self-test. On the actual SAM-V2_0.xls, set engine="xlrd".
    sam = SAM("SAM-V2_0.xls", engine="xlrd")
    print("CO(agr,hrp) =", sam("I", "agr", "AG", "hrp"))
    print("DSO(agr,agr) =", sam("J", "agr", "I", "agr"))

    par = load_val_par("VAL_PAR.xlsx")
    print(par["PARJ"])
    print(par["PART"].head())
