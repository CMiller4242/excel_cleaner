"""
Smart Mapping Engine – Mail File Standard

Provides header normalization, synonym-based mapping, confidence scoring,
contact derivation, and schema enforcement for the required 24-column
mail-file output format.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Required output schema – exact order must be preserved
# ---------------------------------------------------------------------------
REQUIRED_SCHEMA: List[str] = [
    "KeyCode",
    "Cust",
    "Seg",
    "Sls#",
    "Rep Name",
    "Company",
    "Address1",
    "Address2",
    "City",
    "State",
    "Zip",
    "Contact",
    "Title",
    "Telephone",
    "Seqno",
    "Ssqno",
    "Service",
    "Wt",
    "Type",
    "Billto",
    "USPSConf",
    "Email Address",
    "SQL",
    "Sugar Lead Source",
]

# Columns that are commonly absent in raw files and should be silently created
# as blank without raising a high-severity issue.
TYPICALLY_BLANK: frozenset = frozenset({
    "KeyCode", "Seqno", "Ssqno", "Service", "Wt", "Type", "Billto", "USPSConf",
})

# ---------------------------------------------------------------------------
# BCC Mail File output schema – exact order must be preserved
# ---------------------------------------------------------------------------
BCC_REQUIRED_SCHEMA: List[str] = [
    "KC",
    "Cust No",
    "SegNo",
    "SLS ID",
    "REP NAME",
    "COMPANY",
    "DELADDR",
    "ALTADDR",
    "CITY",
    "STATE",
    "ZIP+4",
    "FULLNAME",
    "Title",
    "Phone",
    "SEG_NO",
    "SSQ_NO",
    "SERVICE",
    "WT",
    "TYPE",
    "BILL TO",
    "USPS_CONF",
]

BCC_TYPICALLY_BLANK: frozenset = frozenset({
    "KC", "SEG_NO", "SSQ_NO", "SERVICE", "WT", "TYPE", "BILL TO", "USPS_CONF",
})

# ---------------------------------------------------------------------------
# Synonym dictionary (target col → list of normalised synonyms)
# ---------------------------------------------------------------------------

def build_synonyms() -> Dict[str, List[str]]:
    """Return the canonical synonym map for each target column."""
    return {
        "KeyCode":           ["key code", "keycode", "key_code", "key"],
        "Cust":              ["customer number", "customer #", "cust number",
                              "cust #", "customer no", "customernumber",
                              "custno", "cust no", "customer id", "custid"],
        "Seg":               ["customer segment", "segment", "seg",
                              "cust segment", "customerseg"],
        "Sls#":              ["sls#", "sls #", "sales #", "sales rep #",
                              "salesrep", "sales rep number", "slsnum",
                              "sales number", "slsno"],
        "Rep Name":          ["rep name", "sales rep", "sales rep name", "rep",
                              "salesperson", "sales person"],
        "Company":           ["company", "company name", "organization", "org",
                              "account name", "business name", "firm"],
        "Address1":          ["address1", "address 1", "street",
                              "street address", "address line 1", "addr1",
                              "address line1", "mailing address", "address"],
        "Address2":          ["address2", "address 2", "address line 2",
                              "addr2", "suite", "unit", "apt", "address line2"],
        "City":              ["city", "town", "municipality"],
        "State":             ["state", "st", "province", "state code"],
        "Zip":               ["zip", "zip code", "postal", "postal code",
                              "zipcode", "postcode", "zip+4"],
        "Contact":           ["contact", "contact name", "full name", "name",
                              "attn", "attention"],
        "Title":             ["title", "job title", "position", "role",
                              "job role", "designation"],
        "Telephone":         ["telephone", "phone", "phone number", "tel",
                              "mobile", "cell", "fax", "direct", "phone #"],
        "Seqno":             ["seqno", "seq no", "sequence", "seq number",
                              "sequence number"],
        "Ssqno":             ["ssqno", "ssq no", "subsequence", "ssq number"],
        "Service":           ["service", "svc", "service type"],
        "Wt":                ["wt", "weight", "mail weight"],
        "Type":              ["type", "record type", "rec type"],
        "Billto":            ["billto", "bill to", "billing", "bill-to",
                              "billing account"],
        "USPSConf":          ["uspsconf", "usps conf", "usps confirmation",
                              "usps", "postal confirmation"],
        "Email Address":     ["email", "email address", "e-mail",
                              "emailaddress", "e mail", "email addr",
                              "email_address"],
        "SQL":               ["sql", "sales qualified lead", "qualified lead",
                              "sql flag"],
        "Sugar Lead Source": ["sugar lead source", "lead source", "source",
                              "crm lead source", "lead_source"],
    }


def build_bcc_synonyms() -> Dict[str, List[str]]:
    """Return the canonical synonym map for each BCC target column."""
    return {
        "KC":        ["kc", "key code", "keycode", "key", "key_code"],
        "Cust No":   ["cust no", "customer number", "cust number", "custno",
                      "customer #", "cust #", "customer no", "customer id", "custid"],
        "SegNo":     ["segno", "seg no", "segment number", "segment no",
                      "customer segment", "seg", "cust segment", "customerseg"],
        "SLS ID":    ["sls id", "sls#", "sls #", "sales #", "sales id",
                      "sales rep #", "salesperson id", "salesrep", "slsid",
                      "sales number", "slsno"],
        "REP NAME":  ["rep name", "sales rep", "sales rep name", "rep",
                      "salesperson", "sales person"],
        "COMPANY":   ["company", "company name", "organization", "org",
                      "account name", "business name", "firm"],
        "DELADDR":   ["deladdr", "del addr", "delivery address", "address1",
                      "address 1", "street", "street address", "address line 1",
                      "addr1", "address line1", "mailing address", "address"],
        "ALTADDR":   ["altaddr", "alt addr", "address2", "address 2",
                      "address line 2", "addr2", "suite", "unit", "apt",
                      "alt address", "address line2"],
        "CITY":      ["city", "town", "municipality"],
        "STATE":     ["state", "st", "province", "state code"],
        "ZIP+4":     ["zip+4", "zip4", "zip", "zip code", "postal", "postal code",
                      "zipcode", "postcode"],
        "FULLNAME":  ["fullname", "full name", "contact", "contact name",
                      "name", "attn", "attention"],
        "Title":     ["title", "job title", "position", "role",
                      "job role", "designation"],
        "Phone":     ["phone", "telephone", "phone number", "tel",
                      "mobile", "cell", "direct", "phone #"],
        "SEG_NO":    ["seg_no", "seqno", "seq no", "sequence",
                      "seq number", "sequence number"],
        "SSQ_NO":    ["ssq_no", "ssqno", "ssq no", "subsequence", "ssq number"],
        "SERVICE":   ["service", "svc", "service type"],
        "WT":        ["wt", "weight", "mail weight"],
        "TYPE":      ["type", "record type", "rec type"],
        "BILL TO":   ["bill to", "billto", "billing", "bill-to", "billing account"],
        "USPS_CONF": ["usps_conf", "uspsconf", "usps conf", "usps confirmation",
                      "usps", "postal confirmation"],
    }


# First-name / last-name detection synonyms
_FIRST_SYNONYMS = {"first name", "firstname", "fname", "given name",
                   "first", "givenname"}
_LAST_SYNONYMS  = {"last name", "lastname", "lname", "surname",
                   "family name", "last", "familyname"}


# ---------------------------------------------------------------------------
# Normalisation helper
# ---------------------------------------------------------------------------

def normalize_header(name: str) -> str:
    """
    Normalise a column header for comparison:
    - lowercase
    - replace underscores/hyphens with spaces
    - strip leading/trailing whitespace
    - collapse multiple spaces to one
    - remove non-alphanumeric chars except spaces and #
    """
    if not isinstance(name, str):
        name = str(name)
    name = name.lower()
    name = re.sub(r"[_\-]+", " ", name)         # underscores/hyphens → space
    name = re.sub(r"[^\w\s#]", " ", name)        # drop other punct (keep #)
    name = re.sub(r"\s+", " ", name).strip()     # collapse whitespace
    return name


# ---------------------------------------------------------------------------
# Confidence scoring helpers
# ---------------------------------------------------------------------------

def _fuzzy_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _score_candidate(raw_norm: str, synonyms: List[str]) -> float:
    """Return best match ratio of raw_norm against a list of normalised synonyms."""
    best = 0.0
    for syn in synonyms:
        r = _fuzzy_ratio(raw_norm, syn)
        if r > best:
            best = r
    return best


# Minimum score to consider a match at all (coarse filter)
_CANDIDATE_FLOOR = 0.62
# Minimum score to actually assign a mapping (avoids false positives).
# Set conservatively to prevent generic words like "number" from causing
# cross-column false positives (e.g. "Phone Number" → Seqno via "seq number").
_ASSIGNMENT_MIN  = 0.75


def _confidence_label(score: float) -> str:
    if score >= 0.92:
        return "high"
    if score >= 0.72:
        return "med"
    return "low"


# ---------------------------------------------------------------------------
# Core mapping dataclass
# ---------------------------------------------------------------------------

@dataclass
class MappingResult:
    """Output of infer_mapping()."""
    # {target_col: source_col or None}  – None means "create blank"
    suggested_map: Dict[str, Optional[str]] = field(default_factory=dict)
    # {target_col: "high"|"med"|"low"}
    confidences: Dict[str, str] = field(default_factory=dict)
    # List of conflict descriptors {target_col, candidates, chosen}
    conflicts: List[Dict] = field(default_factory=list)
    # Contact derivation plan
    derivation_plan: str = "blank"          # "use_contact"|"build_first_last"|"blank"
    first_col: Optional[str] = None         # detected first-name raw column
    last_col:  Optional[str]  = None        # detected last-name raw column
    # Raw columns that will be dropped (not in schema)
    dropped_columns: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Main inference function
# ---------------------------------------------------------------------------

def infer_mapping(raw_columns: List[str]) -> MappingResult:
    """
    Infer the best mapping from raw_columns → REQUIRED_SCHEMA.

    Returns a MappingResult with suggested_map, confidences, conflicts,
    derivation_plan, and dropped_columns.
    """
    synonyms_map = build_synonyms()
    result = MappingResult()

    # Normalise raw column names once
    raw_norm_map: Dict[str, str] = {col: normalize_header(col) for col in raw_columns}

    # Detect first / last name columns for Contact derivation
    _detect_first_last(raw_norm_map, result)

    # For each target column, score every raw column
    # target → {raw_col: score}
    target_scores: Dict[str, Dict[str, float]] = {}

    for target in REQUIRED_SCHEMA:
        if target not in synonyms_map:
            continue
        syns = [normalize_header(s) for s in synonyms_map[target]]
        target_norm = normalize_header(target)
        # Include the target name itself as a synonym at high weight
        all_syns = syns + [target_norm]

        col_scores: Dict[str, float] = {}
        for raw_col, raw_norm in raw_norm_map.items():
            score = _score_candidate(raw_norm, all_syns)
            if score >= _CANDIDATE_FLOOR:
                col_scores[raw_col] = score

        target_scores[target] = col_scores

    # Greedy assignment: highest-score wins, avoid double-assigning raw cols
    # (but we still flag if forced to share – DUPLICATE_SOURCE_USED)
    assigned: Dict[str, str] = {}       # raw_col → target it was assigned to
    result.suggested_map = {}
    result.confidences = {}
    result.conflicts = []

    # Sort targets by their best score descending for greedy assignment
    def _best_score(target: str) -> float:
        scores = target_scores.get(target, {})
        return max(scores.values()) if scores else 0.0

    sorted_targets = sorted(REQUIRED_SCHEMA, key=_best_score, reverse=True)

    for target in sorted_targets:
        scores = target_scores.get(target, {})
        best_in_scores = max(scores.values()) if scores else 0.0
        if not scores or best_in_scores < _ASSIGNMENT_MIN:
            result.suggested_map[target] = None
            result.confidences[target] = "low"
            continue

        # Sort candidates by score
        candidates_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_raw, best_score = candidates_sorted[0]

        # Check for conflicts (multiple raw cols with high score for same target)
        close_candidates = [c for c, s in candidates_sorted if s >= best_score - 0.10 and c != best_raw]
        if close_candidates and best_score >= 0.72:
            result.conflicts.append({
                "target_col": target,
                "candidates": [best_raw] + close_candidates,
                "chosen": best_raw,
                "chosen_score": best_score,
            })

        result.suggested_map[target] = best_raw
        result.confidences[target] = _confidence_label(best_score)

    # Contact override: if we determined a derivation plan, mark Contact as derived
    if result.derivation_plan != "use_contact":
        # Don't use the greedy assignment for Contact; it will be derived
        if result.derivation_plan == "build_first_last":
            result.suggested_map["Contact"] = "__derived__"
            result.confidences["Contact"] = "high"
        else:
            result.suggested_map["Contact"] = None
            result.confidences["Contact"] = "low"

    # Determine dropped columns (raw cols not mapped to any target)
    all_mapped_sources = {v for v in result.suggested_map.values()
                          if v and v != "__derived__"}
    result.dropped_columns = [c for c in raw_columns if c not in all_mapped_sources]

    return result


def _detect_first_last(raw_norm_map: Dict[str, str], result: MappingResult):
    """
    Detect contact, first-name and last-name columns from raw headers.
    Populates result.derivation_plan, first_col, last_col.
    """
    contact_col = None
    first_col = None
    last_col = None

    for raw_col, norm in raw_norm_map.items():
        if norm in _LAST_SYNONYMS or _fuzzy_ratio(norm, "last name") >= 0.88:
            last_col = raw_col
        if norm in _FIRST_SYNONYMS or _fuzzy_ratio(norm, "first name") >= 0.88:
            first_col = raw_col
        if norm in {"contact", "contact name", "full name", "attn"}:
            contact_col = raw_col

    if contact_col:
        result.derivation_plan = "use_contact"
        result.first_col = first_col
        result.last_col  = last_col
    elif first_col or last_col:
        result.derivation_plan = "build_first_last"
        result.first_col = first_col
        result.last_col  = last_col
    else:
        result.derivation_plan = "blank"
        result.first_col = None
        result.last_col  = None


# ---------------------------------------------------------------------------
# Schema application
# ---------------------------------------------------------------------------

def apply_mail_standard(
    df: pd.DataFrame,
    mapping_config: Dict,
    required_schema: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, List[Dict], Dict]:
    """
    Apply the mail-file standard to df using mapping_config.

    Parameters
    ----------
    df : pd.DataFrame
        Raw input DataFrame.
    mapping_config : dict
        Keys:
          "column_map":      {target: source_or_None_or___derived__}
          "derivation_plan": "use_contact" | "build_first_last" | "blank"
          "first_col":       raw column name for first name (or None)
          "last_col":        raw column name for last name (or None)
    required_schema : list[str] or None
        Ordered list of target columns. Defaults to REQUIRED_SCHEMA.

    Returns
    -------
    df_out : pd.DataFrame
        DataFrame with exactly the required_schema columns in order.
    issues : list[dict]
        Each issue is a dict with keys: code, message, details.
    meta : dict
        "dropped_columns": list of raw columns not used in output.
        "created_blank":   list of target columns created as blank.
        "derived_contact": bool
    """
    if required_schema is None:
        required_schema = REQUIRED_SCHEMA

    col_map: Dict[str, Optional[str]] = mapping_config.get("column_map", {})
    derivation_plan: str = mapping_config.get("derivation_plan", "blank")
    first_col: Optional[str] = mapping_config.get("first_col")
    last_col:  Optional[str] = mapping_config.get("last_col")

    issues: List[Dict] = []
    created_blank: List[str] = []
    meta: Dict = {}

    working = df.copy()

    # -----------------------------------------------------------------------
    # 1. Build the output DataFrame column by column
    # -----------------------------------------------------------------------
    out_data: Dict[str, pd.Series] = {}

    # Track source columns actually used to detect duplicates
    used_sources: Dict[str, str] = {}   # source_col → first target that used it

    for target in required_schema:
        source = col_map.get(target)

        # --- Contact special handling ---
        if target == "Contact":
            series = _build_contact(
                working, derivation_plan, first_col, last_col,
                source, issues
            )
            out_data[target] = series
            continue

        # --- Normal mapping ---
        if source == "__derived__":
            # Shouldn't happen for non-Contact targets; treat as blank
            source = None

        if source and source in working.columns:
            # Detect duplicate source usage
            if source in used_sources:
                issues.append({
                    "code": "DUPLICATE_SOURCE_USED",
                    "message": (f"Source column '{source}' is mapped to both "
                                f"'{used_sources[source]}' and '{target}'."),
                    "details": {
                        "source_column": source,
                        "targets": [used_sources[source], target],
                    },
                })
            else:
                used_sources[source] = target

            out_data[target] = working[source].copy()
        else:
            # Missing – create blank
            out_data[target] = pd.Series([""] * len(working), index=working.index)
            created_blank.append(target)

            # Flag – but only warn for non-trivially-blank columns
            if target not in TYPICALLY_BLANK:
                issues.append({
                    "code": "MISSING_REQUIRED_FIELD",
                    "message": (f"Required column '{target}' could not be mapped "
                                f"from raw input; created blank."),
                    "details": {
                        "target_column": target,
                        "source_attempted": source,
                    },
                })

    # -----------------------------------------------------------------------
    # 2. Assemble output DataFrame in exact schema order
    # -----------------------------------------------------------------------
    df_out = pd.DataFrame(out_data, index=working.index)
    # Ensure column order
    df_out = df_out[required_schema]

    # -----------------------------------------------------------------------
    # 3. Compute dropped columns
    # -----------------------------------------------------------------------
    all_used_sources = set(used_sources.keys())
    if first_col and derivation_plan in ("build_first_last",):
        all_used_sources.add(first_col)
    if last_col and derivation_plan in ("build_first_last",):
        all_used_sources.add(last_col)
    if derivation_plan == "use_contact" and source:
        pass  # already tracked

    dropped = [c for c in df.columns if c not in all_used_sources]

    meta["dropped_columns"] = dropped
    meta["created_blank"] = created_blank
    meta["derived_contact"] = (derivation_plan == "build_first_last")

    logging.info(
        f"[SmartFormat] Applied mail standard: {len(df_out.columns)} cols, "
        f"{len(created_blank)} created blank, {len(dropped)} dropped, "
        f"{len(issues)} issues."
    )

    return df_out, issues, meta


# ---------------------------------------------------------------------------
# Contact derivation helper
# ---------------------------------------------------------------------------

def _build_contact(
    df: pd.DataFrame,
    plan: str,
    first_col: Optional[str],
    last_col: Optional[str],
    contact_source: Optional[str],
    issues: List[Dict],
) -> pd.Series:
    """Build the Contact series according to the derivation plan."""
    idx = df.index

    if plan == "use_contact" and contact_source and contact_source in df.columns:
        return df[contact_source].copy()

    if plan == "build_first_last":
        # Build combined contact name row-by-row to avoid pandas str operator edge cases
        first_vals = (
            [str(v).strip() for v in df[first_col]]
            if first_col and first_col in df.columns
            else [""] * len(df)
        )
        last_vals = (
            [str(v).strip() for v in df[last_col]]
            if last_col and last_col in df.columns
            else [""] * len(df)
        )
        combined_vals = [
            f"{f} {l}".strip() for f, l in zip(first_vals, last_vals)
        ]
        return pd.Series(combined_vals, index=idx)

    # Blank
    issues.append({
        "code": "MISSING_REQUIRED_FIELD",
        "message": "Required column 'Contact' could not be derived; created blank.",
        "details": {
            "target_column": "Contact",
            "derivation_plan": plan,
        },
    })
    return pd.Series([""] * len(df), index=idx)


# ---------------------------------------------------------------------------
# BCC Mail File inference
# ---------------------------------------------------------------------------

def infer_mapping_bcc(raw_columns: List[str]) -> MappingResult:
    """
    Infer the best mapping from raw_columns → BCC_REQUIRED_SCHEMA.

    Returns a MappingResult with suggested_map, confidences, conflicts,
    and dropped_columns.  No Contact derivation logic (FULLNAME is a plain
    mapped field in the BCC schema).
    """
    synonyms_map = build_bcc_synonyms()
    result = MappingResult()

    raw_norm_map: Dict[str, str] = {col: normalize_header(col) for col in raw_columns}

    # Score each target column against every raw column
    target_scores: Dict[str, Dict[str, float]] = {}

    for target in BCC_REQUIRED_SCHEMA:
        if target not in synonyms_map:
            continue
        syns = [normalize_header(s) for s in synonyms_map[target]]
        target_norm = normalize_header(target)
        all_syns = syns + [target_norm]

        col_scores: Dict[str, float] = {}
        for raw_col, raw_norm in raw_norm_map.items():
            score = _score_candidate(raw_norm, all_syns)
            if score >= _CANDIDATE_FLOOR:
                col_scores[raw_col] = score

        target_scores[target] = col_scores

    # Greedy assignment: highest score wins; flag close conflicts
    result.suggested_map = {}
    result.confidences = {}
    result.conflicts = []

    def _best_score(target: str) -> float:
        scores = target_scores.get(target, {})
        return max(scores.values()) if scores else 0.0

    sorted_targets = sorted(BCC_REQUIRED_SCHEMA, key=_best_score, reverse=True)

    for target in sorted_targets:
        scores = target_scores.get(target, {})
        best_in_scores = max(scores.values()) if scores else 0.0
        if not scores or best_in_scores < _ASSIGNMENT_MIN:
            result.suggested_map[target] = None
            result.confidences[target] = "low"
            continue

        candidates_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_raw, best_score = candidates_sorted[0]

        close_candidates = [c for c, s in candidates_sorted
                            if s >= best_score - 0.10 and c != best_raw]
        if close_candidates and best_score >= 0.72:
            result.conflicts.append({
                "target_col": target,
                "candidates": [best_raw] + close_candidates,
                "chosen": best_raw,
                "chosen_score": best_score,
            })

        result.suggested_map[target] = best_raw
        result.confidences[target] = _confidence_label(best_score)

    # BCC has no Contact derivation
    result.derivation_plan = "blank"
    result.first_col = None
    result.last_col = None

    all_mapped_sources = {v for v in result.suggested_map.values() if v}
    result.dropped_columns = [c for c in raw_columns if c not in all_mapped_sources]

    return result
