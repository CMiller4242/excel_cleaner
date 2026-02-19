#!/usr/bin/env python3
"""
Acceptance tests for utils/smart_mapping.py
Runs without requiring pandas (uses a minimal DataFrame stub).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

# ── Minimal pandas stub ──────────────────────────────────────────────────
class _Series:
    def __init__(self, data, index=None):
        self._data = list(data)
        self.index = index or list(range(len(data)))
    def __eq__(self, val):
        return [x == val for x in self._data]
    def __iter__(self): return iter(self._data)
    def __getitem__(self, i): return self._data[i]
    def __len__(self): return len(self._data)
    def fillna(self, v): return _Series([x if x is not None else v for x in self._data], self.index)
    def astype(self, t): return _Series([t(x) for x in self._data], self.index)
    @property
    def str(self): return _StrAccessor(self)
    def copy(self): return _Series(list(self._data), list(self.index))

class _StrAccessor:
    def __init__(self, s): self._s = s
    def strip(self): return _Series([x.strip() for x in self._s], self._s.index)
    def __add__(self, other):
        if isinstance(other, _Series):
            return _Series([a + b for a,b in zip(self._s, other)], self._s.index)
        return _Series([x + other for x in self._s], self._s.index)

class _DataFrame:
    def __init__(self, data=None, index=None):
        data = data or {}
        self._data = {k: list(v) for k,v in data.items()}
        n = len(next(iter(self._data.values()), []))
        self.index = index or list(range(n))
        self.columns = list(self._data.keys())
    def __contains__(self, k): return k in self._data
    def __getitem__(self, key):
        if isinstance(key, list):
            return _DataFrame({k: self._data[k] for k in key}, self.index)
        return _Series(self._data[key], self.index)
    def copy(self):
        return _DataFrame({k: list(v) for k,v in self._data.items()}, list(self.index))
    def __len__(self): return len(self.index)
    def __repr__(self): return f"DataFrame(columns={self.columns})"

class _pd:
    DataFrame = _DataFrame
    Series    = _Series

# Inject stub before importing smart_mapping
sys.modules.setdefault('pandas', _pd)
import pandas as pd  # noqa – ensures smart_mapping can `import pandas as pd`
sys.modules['pandas'] = _pd()

# Patch the module's pd reference after import
import importlib.util, types

# Load smart_mapping manually so we can patch pd
spec = importlib.util.spec_from_file_location(
    "utils.smart_mapping",
    str(pathlib.Path(__file__).parent / "utils" / "smart_mapping.py")
)
mod = importlib.util.module_from_spec(spec)
# Give it our stub
mod_pd = _pd()
mod_pd.DataFrame = _DataFrame
mod_pd.Series    = _Series
mod.pd = mod_pd   # pre-inject before exec
sys.modules["utils.smart_mapping"] = mod
spec.loader.exec_module(mod)

from utils.smart_mapping import (
    normalize_header,
    infer_mapping,
    apply_mail_standard,
    REQUIRED_SCHEMA,
)

PASS = []
FAIL = []

def check(label, condition, detail=""):
    if condition:
        PASS.append(label)
        print(f"  PASS  {label}")
    else:
        FAIL.append(label)
        print(f"  FAIL  {label}" + (f" — {detail}" if detail else ""))

def all_eq(series, val):
    return all(x == val for x in series)

# ──────────────────────────────────────────────────────────────────────────
# 1. normalize_header
# ──────────────────────────────────────────────────────────────────────────
print("\n=== normalize_header ===")
check("lower + strip",      normalize_header("  Email Address  ") == "email address")
check("underscore→space",   normalize_header("Email_Address")     == "email address")
check("hyphen→space",       normalize_header("E-Mail")            == "e mail")
check("collapse spaces",    normalize_header("Company  Name")     == "company name")
check("preserve #",         normalize_header("Sls#")              == "sls#")


# ──────────────────────────────────────────────────────────────────────────
# 2. infer_mapping – typical messy headers
# ──────────────────────────────────────────────────────────────────────────
print("\n=== infer_mapping – typical raw file ===")
RAW1 = [
    "Customer Number", "Customer Segment", "Company Name",
    "Address Line 1", "Address Line 2", "City", "State", "Zip Code",
    "Email", "Phone Number", "Job Title",
    "First Name", "Last Name",
    "Sales Rep", "SQL", "Lead Source",
]

mr = infer_mapping(RAW1)

check("Cust ← Customer Number",    mr.suggested_map.get("Cust")     == "Customer Number")
check("Seg ← Customer Segment",    mr.suggested_map.get("Seg")      == "Customer Segment")
check("Company ← Company Name",    mr.suggested_map.get("Company")  == "Company Name")
check("Address1 ← Address Line 1", mr.suggested_map.get("Address1") == "Address Line 1")
check("Address2 ← Address Line 2", mr.suggested_map.get("Address2") == "Address Line 2")
check("State ← State",             mr.suggested_map.get("State")    == "State")
check("Zip ← Zip Code",            mr.suggested_map.get("Zip")      == "Zip Code")
check("Email Address ← Email",     mr.suggested_map.get("Email Address") == "Email")
check("Telephone ← Phone Number",  mr.suggested_map.get("Telephone") == "Phone Number")
check("Title ← Job Title",         mr.suggested_map.get("Title")    == "Job Title")
check("Rep Name ← Sales Rep",      mr.suggested_map.get("Rep Name") == "Sales Rep")
check("SQL ← SQL",                 mr.suggested_map.get("SQL")      == "SQL")
check("Sugar Lead Source ← Lead Source",
      mr.suggested_map.get("Sugar Lead Source") == "Lead Source")
check("Contact plan = build_first_last", mr.derivation_plan == "build_first_last")
check("first_col == First Name",    mr.first_col == "First Name")
check("last_col  == Last Name",     mr.last_col  == "Last Name")
check("KeyCode → None",   mr.suggested_map.get("KeyCode") is None)
check("Seqno → None",     mr.suggested_map.get("Seqno")  is None)


# ──────────────────────────────────────────────────────────────────────────
# 3. infer_mapping – existing Contact column
# ──────────────────────────────────────────────────────────────────────────
print("\n=== infer_mapping – existing Contact col ===")
mr2 = infer_mapping(["Contact", "Email", "Company"])
check("plan = use_contact when Contact present", mr2.derivation_plan == "use_contact")


# ──────────────────────────────────────────────────────────────────────────
# 4. apply_mail_standard – schema order + blank creation
# ──────────────────────────────────────────────────────────────────────────
print("\n=== apply_mail_standard – schema + blanks ===")

raw_df = _DataFrame({
    "Customer Number": ["C001", "C002"],
    "Company Name":    ["ACME", "Globex"],
    "Email":           ["a@a.com", "b@b.com"],
    "City":            ["Boston", "NY"],
    "State":           ["MA", "NY"],
    "Zip Code":        ["02101", "10001"],
    "First Name":      ["Alice", "Bob"],
    "Last Name":       ["Smith", "Jones"],
})

mr3 = infer_mapping(raw_df.columns)
mapping_config = {
    "column_map":      mr3.suggested_map,
    "derivation_plan": mr3.derivation_plan,
    "first_col":       mr3.first_col,
    "last_col":        mr3.last_col,
}

df_out, issues, meta = apply_mail_standard(raw_df, mapping_config)

check("Output has 24 columns",             len(df_out.columns) == 24)
check("Columns == REQUIRED_SCHEMA",        list(df_out.columns) == REQUIRED_SCHEMA)
check("Cust values correct",               list(df_out["Cust"]) == ["C001", "C002"])
check("Company values correct",            list(df_out["Company"]) == ["ACME", "Globex"])
check("Email Address values correct",      list(df_out["Email Address"]) == ["a@a.com", "b@b.com"])
check("Contact derived correctly",         list(df_out["Contact"]) == ["Alice Smith", "Bob Jones"])
check("KeyCode is blank",                  all_eq(df_out["KeyCode"], ""))
check("Seqno is blank",                    all_eq(df_out["Seqno"],   ""))
check("meta has dropped_columns",          "dropped_columns" in meta)
check("meta has created_blank",            "created_blank"   in meta)
check("derived_contact is True",           meta["derived_contact"] is True)


# ──────────────────────────────────────────────────────────────────────────
# 5. Typically-blank cols do NOT raise MISSING_REQUIRED_FIELD
# ──────────────────────────────────────────────────────────────────────────
print("\n=== Issues – no spurious MISSING_REQUIRED_FIELD for typically-blank cols ===")
trivially_bad = [
    i for i in issues
    if i["code"] == "MISSING_REQUIRED_FIELD"
    and i["details"].get("target_column") in (
        "KeyCode","Seqno","Ssqno","Wt","Type","Billto","USPSConf","Service")
]
check("Typically-blank cols silent",  len(trivially_bad) == 0)


# ──────────────────────────────────────────────────────────────────────────
# 6. Extra columns dropped
# ──────────────────────────────────────────────────────────────────────────
print("\n=== Extra columns dropped ===")
raw_extra = _DataFrame({
    "Customer Number": ["X"],
    "Email":           ["x@x.com"],
    "My Extra Column": ["extra"],
    "Another Extra":   ["foo"],
})
mr_e = infer_mapping(raw_extra.columns)
cfg_e = {
    "column_map":      mr_e.suggested_map,
    "derivation_plan": mr_e.derivation_plan,
    "first_col":       mr_e.first_col,
    "last_col":        mr_e.last_col,
}
df_e, iss_e, meta_e = apply_mail_standard(raw_extra, cfg_e)

check("Output still 24 cols when extras present",   len(df_e.columns) == 24)
check("Extra cols appear in meta['dropped_columns']",
      "My Extra Column" in meta_e["dropped_columns"]
      or "Another Extra" in meta_e["dropped_columns"])


# ──────────────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Results: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILURES:")
    for f in FAIL: print(f"  - {f}")
    sys.exit(1)
else:
    print("All tests passed!")
