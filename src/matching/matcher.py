"""Pure entity matching functions for MoSPI PAIMANA Flash Report records.

Canonical ID Resolution Strategy:
- Primary key: `project_code`. Since project_code is 100% populated in ongoing tables,
  unique per month, and stable across months, `canonical_project_id` is assigned directly
  from `project_code` with match_confidence = "exact_code".
- Fallback cascade (Exception Handler): If `project_code` is missing, resolves via:
  1. Unique non-umbrella `legacy_ocms_code`
  2. Unique `pmgid`
  3. Deterministic match on normalized `(project_name, implementing_agency, date_of_approval)`
  Flagged with match_confidence = "fallback".
- Safety Invariants:
  1. NEVER collapse umbrella legacy codes or legacy-swap anomalies: two distinct project_codes
     must NEVER be merged into the same canonical_project_id.
  2. Concurrency: Two records in the same report_month must never share a canonical_project_id.
"""

import hashlib
import re
from typing import Any


def normalize_text(text: Any) -> str:
    """Normalize text by stripping whitespace, removing punctuation, and lowercasing."""
    if text is None:
        return ""
    s = str(text).strip().lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())


def compute_fallback_id(name: str, agency: str | None, approval: str | None) -> str:
    """Compute a deterministic pseudo-ID for records lacking project_code."""
    key = f"{normalize_text(name)}|{normalize_text(agency)}|{normalize_text(approval)}"
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:10]
    return f"FALLBACK_{h}"


def assign_canonical_id(
    record: dict[str, Any] | Any,
    registry: dict[str, str] | None = None,
    umbrella_legacy_codes: set[str] | None = None,
) -> tuple[str, str, str, str | None]:
    """Assign canonical_project_id, match_confidence, match_rule, and match_evidence.

    Args:
        record: A dict-like record with project_code, legacy_ocms_code, pmgid, etc.
        registry: Optional dict mapping (lookup_key -> canonical_project_id) for fallbacks.
        umbrella_legacy_codes: Set of legacy codes known to be one-to-many (never use for matching).

    Returns:
        (canonical_project_id, match_confidence, match_rule, match_evidence)
    """
    raw_code = record.get("project_code") if hasattr(record, "get") else record["project_code"]
    code_str = (
        str(raw_code).strip()
        if raw_code is not None
        and str(raw_code).strip() != ""
        and str(raw_code).strip().lower() != "nan"
        and str(raw_code).strip() != "None"
        else None
    )

    # 1. Primary path: Direct exact join on project_code
    if code_str:
        return code_str, "exact_code", "exact_project_code", None

    # 2. Exception Handler: Fallback cascade for records lacking project_code
    legacy = (
        record.get("legacy_ocms_code")
        if hasattr(record, "get")
        else record.get("legacy_ocms_code", None)
    )
    legacy_str = (
        str(legacy).strip()
        if legacy is not None and str(legacy).strip() not in ("-", "--", "", "None", "nan")
        else None
    )

    pmgid = record.get("pmgid") if hasattr(record, "get") else record.get("pmgid", None)
    pmgid_str = (
        str(pmgid).strip()
        if pmgid is not None and str(pmgid).strip() not in ("-", "--", "", "None", "nan")
        else None
    )

    name = (
        record.get("project_name", "") if hasattr(record, "get") else record.get("project_name", "")
    )
    agency = (
        record.get("implementing_agency")
        if hasattr(record, "get")
        else record.get("implementing_agency", None)
    )
    approval = (
        record.get("date_of_approval")
        if hasattr(record, "get")
        else record.get("date_of_approval", None)
    )

    umbrellas = umbrella_legacy_codes or set()

    # Step 2a: Lookup via Legacy OCMS Code (ONLY if NOT an umbrella code!)
    if (
        legacy_str
        and legacy_str not in umbrellas
        and registry
        and f"legacy:{legacy_str}" in registry
    ):
        cid = registry[f"legacy:{legacy_str}"]
        return (
            cid,
            "fallback",
            "fallback_legacy_ocms_code",
            f"Matched on unique legacy code {legacy_str}",
        )

    # Step 2b: Lookup via PMGID
    if pmgid_str and registry and f"pmgid:{pmgid_str}" in registry:
        cid = registry[f"pmgid:{pmgid_str}"]
        return cid, "fallback", "fallback_pmgid", f"Matched on PMGID {pmgid_str}"

    # Step 2c: Lookup via normalized (name, agency, approval)
    name_key = f"name:{normalize_text(name)}|{normalize_text(agency)}|{normalize_text(approval)}"
    if registry and name_key in registry:
        cid = registry[name_key]
        return (
            cid,
            "fallback",
            "fallback_name_agency_approval",
            "Matched on composite name+agency+approval key",
        )

    # Step 2d: Unmatched new fallback ID
    fallback_cid = compute_fallback_id(name or "", agency, approval)
    return (
        fallback_cid,
        "fallback",
        "fallback_new_synthetic",
        "Generated deterministic fallback ID from attributes",
    )
