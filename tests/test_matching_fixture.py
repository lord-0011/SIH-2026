"""CI Test Suite for Entity Matching on Synthetic Fixtures.

This test suite executes on every CI run without requiring external DVC data.
It NEVER skips.

Verifies:
1. ADVERSARIAL TEST: Legacy-swap anomaly (the Bokaro/Bhilai pattern where two records
   in DIFFERENT months share a legacy_ocms_code but have DIFFERENT project_codes and names)
   must NEVER merge into the same canonical_project_id.
2. Umbrella corridor packages: Multiple projects sharing a legacy code in the SAME month
   must receive distinct canonical_project_ids.
3. Fallback cascade exception handler: Records lacking project_code resolve safely via
   non-umbrella legacy codes or deterministic fallback pseudo-IDs.
4. Concurrency Invariant: Two records in the same month must never share a canonical_project_id.
5. No-Merge Invariant: Distinct project_codes must never map to the same canonical_project_id.
"""

import pytest

from src.matching.matcher import assign_canonical_id


@pytest.fixture
def synthetic_records():
    """Construct synthetic records capturing all real matching hazards."""
    return [
        # Normal record Month 1
        {
            "report_month": "2026-02",
            "project_code": "612786",
            "legacy_ocms_code": "N04000106",
            "pmgid": "PMG12345",
            "project_name": "Kadapa Airport Domestic Terminal",
            "implementing_agency": "AAI",
            "ministry": "Ministry of Civil Aviation",
            "date_of_approval": "03/2023",
            "start_date": "01/2024",
        },
        # Normal record Month 2 (same project carrying forward)
        {
            "report_month": "2026-03",
            "project_code": "612786",
            "legacy_ocms_code": "N04000106",
            "pmgid": "PMG12345",
            "project_name": "Kadapa Airport Domestic Terminal Building",
            "implementing_agency": "AAI",
            "ministry": "Ministry of Civil Aviation",
            "date_of_approval": "03/2023",
            "start_date": "01/2024",
        },
        # ADVERSARIAL CASE 1: Bokaro in Feb (Project 617257, legacy N12000133)
        {
            "report_month": "2026-02",
            "project_code": "617257",
            "legacy_ocms_code": "N12000133",
            "pmgid": None,
            "project_name": "Rebuilding of Coke Oven Battery No.6 at Bokaro Steel",
            "implementing_agency": "SAIL",
            "ministry": "Ministry of Steel",
            "date_of_approval": "05/2021",
            "start_date": "10/2021",
        },
        # ADVERSARIAL CASE 2: Bhilai in Mar (Project 617256, ALSO legacy N12000133 in source!)
        {
            "report_month": "2026-03",
            "project_code": "617256",
            "legacy_ocms_code": "N12000133",  # Swapped in source!
            "pmgid": None,
            "project_name": "Rebuilding of Coke Oven Battery No.7 & 8 at Bhilai",
            "implementing_agency": "SAIL",
            "ministry": "Ministry of Steel",
            "date_of_approval": "08/2020",
            "start_date": "01/2021",
        },
        # Umbrella Corridor Package A in Feb (Project 618881, legacy N16000001)
        {
            "report_month": "2026-02",
            "project_code": "618881",
            "legacy_ocms_code": "N16000001",
            "pmgid": None,
            "project_name": "Four Laning of Corridor Package 1",
            "implementing_agency": "NHAI",
            "ministry": "Ministry of Road Transport & Highways",
            "date_of_approval": "01/2022",
            "start_date": "06/2022",
        },
        # Umbrella Corridor Package B in Feb (Project 618882, ALSO legacy N16000001 in SAME month)
        {
            "report_month": "2026-02",
            "project_code": "618882",
            "legacy_ocms_code": "N16000001",
            "pmgid": None,
            "project_name": "Four Laning of Corridor Package 2",
            "implementing_agency": "NHAI",
            "ministry": "Ministry of Road Transport & Highways",
            "date_of_approval": "01/2022",
            "start_date": "07/2022",
        },
    ]


def test_direct_exact_code_matching(synthetic_records):
    """Verify that records with project_code receive canonical_project_id = project_code."""
    r0 = synthetic_records[0]
    cid, conf, rule, evid = assign_canonical_id(r0)
    assert cid == "612786"
    assert conf == "exact_code"
    assert rule == "exact_project_code"
    assert evid is None


def test_adversarial_legacy_swap_no_merge(synthetic_records):
    """ADVERSARIAL TEST: Legacy-swap anomaly (Bokaro vs Bhilai) must NEVER merge.

    In the real dataset, legacy code N12000133 pointed to Bokaro (project 617257) in Feb
    but Bhilai (project 617256) in Mar due to reporting error.
    A matcher trusting legacy_ocms_code would corrupt the time series by merging them.
    Assert that both projects receive strictly distinct canonical IDs.
    """
    bokaro_record = synthetic_records[2]  # Project 617257, legacy N12000133
    bhilai_record = synthetic_records[3]  # Project 617256, legacy N12000133

    cid_bokaro, conf_bokaro, _, _ = assign_canonical_id(bokaro_record)
    cid_bhilai, conf_bhilai, _, _ = assign_canonical_id(bhilai_record)

    # Must be exact code matches
    assert conf_bokaro == "exact_code"
    assert conf_bhilai == "exact_code"

    # Distinct physical projects must have distinct canonical IDs
    assert cid_bokaro == "617257"
    assert cid_bhilai == "617256"
    assert (
        cid_bokaro != cid_bhilai
    ), "ADVERSARIAL FAILURE: Bokaro and Bhilai merged under swapped legacy code!"


def test_umbrella_corridor_packages_not_collapsed(synthetic_records):
    """Verify that parallel EPC packages sharing a legacy code in the same month stay distinct."""
    pkg1 = synthetic_records[4]  # 618881, legacy N16000001
    pkg2 = synthetic_records[5]  # 618882, legacy N16000001

    cid1, _, _, _ = assign_canonical_id(pkg1)
    cid2, _, _, _ = assign_canonical_id(pkg2)

    assert cid1 == "618881"
    assert cid2 == "618882"
    assert (
        cid1 != cid2
    ), "CRITICAL: Umbrella packages with distinct project_codes were merged under shared legacy code!"


def test_concurrency_invariant_same_month(synthetic_records):
    """Verify that no two records in the same month share a canonical_project_id."""
    feb_records = [r for r in synthetic_records if r["report_month"] == "2026-02"]
    assigned_cids = [assign_canonical_id(r)[0] for r in feb_records]

    assert len(assigned_cids) == len(
        set(assigned_cids)
    ), f"Concurrency invariant violated in 2026-02: {assigned_cids}"


def test_fallback_exception_handler():
    """Verify that if a record lacks project_code, fallback matching resolves safely."""
    # Lookup registry mapping known non-umbrella legacy codes to canonical ID
    registry = {"legacy:LEG_SAFE_01": "999001", "pmgid:PMG_SAFE_01": "999002"}

    # Record lacking project_code, with unique legacy code
    missing_code_record = {
        "project_code": None,
        "legacy_ocms_code": "LEG_SAFE_01",
        "pmgid": None,
        "project_name": "Gauge Conversion Section",
        "implementing_agency": "RVNL",
        "date_of_approval": "01/2021",
    }

    cid, conf, rule, evid = assign_canonical_id(missing_code_record, registry=registry)
    assert cid == "999001"
    assert conf == "fallback"
    assert rule == "fallback_legacy_ocms_code"
    assert "LEG_SAFE_01" in evid


def test_fallback_umbrella_code_blocked():
    """Verify that umbrella legacy codes are BLOCKED from being used for fallback matching."""
    umbrellas = {"N16000001", "N12000133"}
    registry = {"legacy:N16000001": "618881"}

    missing_code_record = {
        "project_code": None,
        "legacy_ocms_code": "N16000001",  # Umbrella code!
        "pmgid": None,
        "project_name": "Four Laning Corridor Package X",
        "implementing_agency": "NHAI",
        "date_of_approval": "01/2022",
    }

    cid, conf, rule, _ = assign_canonical_id(
        missing_code_record, registry=registry, umbrella_legacy_codes=umbrellas
    )

    # Must NOT use the umbrella legacy code to assign 618881!
    assert cid != "618881", "Umbrella legacy code incorrectly used in fallback match!"
    assert cid.startswith("FALLBACK_")
    assert rule == "fallback_new_synthetic"
