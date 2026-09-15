"""Multi-month ingestion test suite across all 13 Flash Reports (July 2025 - July 2026).

Verifies:
1. Non-circular ground truth: All Ongoing row count == Table 1 Ministry-wise grand total.
2. Independent cross-check against published report figures.
3. Cost and expenditure aggregate fidelity.
4. Independent format vs coverage axes (layout_type vs morth_ongoing_count).
5. Availability of both revised cost and revised completion date across all 13 months.
6. Field integrity across all parquet datasets.
"""

import pandas as pd
import pytest

from src.common.config import DATA_INTERIM
from src.common.io import load_dataframe

# Published ground-truth reference figures (independent secondary cross-check)
PUBLISHED_GROUND_TRUTH = {
    "2025-07": {
        "ongoing_count": 791,
        "orig_cost": 2386335.28,
        "layout": "Early",
        "morth": 0,
        "completed": 0,
        "newly_added": 0,
    },
    "2025-08": {
        "ongoing_count": 800,
        "orig_cost": 2375332.37,
        "layout": "Early",
        "morth": 0,
        "completed": 0,
        "newly_added": 0,
    },
    "2025-09": {
        "ongoing_count": 794,
        "orig_cost": 2533121.98,
        "layout": "Modern",
        "morth": 0,
        "completed": 6,
        "newly_added": 34,
    },
    "2025-10": {
        "ongoing_count": 820,
        "orig_cost": 2552631.73,
        "layout": "Modern",
        "morth": 0,
        "completed": 6,
        "newly_added": 35,
    },
    "2025-11": {
        "ongoing_count": 823,
        "orig_cost": 2418198.30,
        "layout": "Modern",
        "morth": 0,
        "completed": 13,
        "newly_added": 21,
    },
    "2025-12": {
        "ongoing_count": 1392,
        "orig_cost": 2968247.55,
        "layout": "Modern",
        "morth": 584,
        "completed": 17,
        "newly_added": 20,
    },
    "2026-01": {
        "ongoing_count": 1702,
        "orig_cost": 3371816.32,
        "layout": "Modern",
        "morth": 863,
        "completed": 3,
        "newly_added": 203,
    },
    "2026-02": {
        "ongoing_count": 1948,
        "orig_cost": 3632088.32,
        "layout": "Modern",
        "morth": 1108,
        "completed": 9,
        "newly_added": 268,
    },
    "2026-03": {
        "ongoing_count": 1941,
        "orig_cost": 3588861.17,
        "layout": "Modern",
        "morth": 1120,
        "completed": 25,
        "newly_added": 12,
    },
    "2026-04": {
        "ongoing_count": 1981,
        "orig_cost": 3712662.01,
        "layout": "Modern",
        "morth": 1137,
        "completed": 9,
        "newly_added": 55,
    },
    "2026-05": {
        "ongoing_count": 1987,
        "orig_cost": 3709724.65,
        "layout": "Modern",
        "morth": 1149,
        "completed": 16,
        "newly_added": 35,
    },
    "2026-06": {
        "ongoing_count": 1847,
        "orig_cost": 3561721.07,
        "layout": "Modern",
        "morth": 1022,
        "completed": 130,
        "newly_added": 17,
    },
    "2026-07": {
        "ongoing_count": 1775,
        "orig_cost": 3370138.22,
        "layout": "Modern",
        "morth": 993,
        "completed": 25,
        "newly_added": 36,
    },
}


@pytest.fixture(scope="module")
def summary_df():
    summary_file = DATA_INTERIM / "ingestion_summary.csv"
    needs_ingestion = False
    if not summary_file.exists():
        needs_ingestion = True
    else:
        df_check = pd.read_csv(summary_file)
        if len(df_check) < 13:
            needs_ingestion = True

    if not needs_ingestion:
        for m in PUBLISHED_GROUND_TRUTH.keys():
            clean_m = m.replace("-", "_")
            if not (DATA_INTERIM / f"raw_ongoing_{clean_m}.parquet").exists():
                needs_ingestion = True
                break

    if needs_ingestion:
        from src.ingestion.run import run

        run()

    assert summary_file.exists(), f"Ingestion summary not found at {summary_file}"
    return pd.read_csv(summary_file)


def test_all_13_months_present(summary_df):
    assert len(summary_df) == 13, f"Expected 13 months, found {len(summary_df)}"
    months = summary_df["report_month"].tolist()
    expected = list(PUBLISHED_GROUND_TRUTH.keys())
    assert months == expected, f"Month list mismatch: {months} vs {expected}"


def test_non_circular_table1_match(summary_df):
    """Authoritative check: assert extracted ongoing row count == Table 1 grand total from PDF."""
    for _, row in summary_df.iterrows():
        month = row["report_month"]
        t1_count = row["table1_project_count"]
        ongoing_count = row["ongoing_row_count"]
        assert (
            ongoing_count == t1_count
        ), f"[{month}] Authoritative Table 1 mismatch: extracted {ongoing_count} vs Table 1 {t1_count}"
        assert row["count_match"] is True or row["count_match"] == 1


def test_independent_ground_truth_crosscheck(summary_df):
    """Secondary cross-check: assert extracted counts match published reference constants."""
    for _, row in summary_df.iterrows():
        month = row["report_month"]
        ref = PUBLISHED_GROUND_TRUTH[month]
        assert (
            row["ongoing_row_count"] == ref["ongoing_count"]
        ), f"[{month}] Project count mismatch vs reference"
        assert row["layout_type"] == ref["layout"], f"[{month}] Layout type mismatch"
        assert row["morth_ongoing_count"] == ref["morth"], f"[{month}] MoRTH count mismatch"
        assert row["completed_row_count"] == ref["completed"], f"[{month}] Completed count mismatch"
        assert (
            row["newly_added_row_count"] == ref["newly_added"]
        ), f"[{month}] Newly added count mismatch"


def test_cost_aggregates_match_table1(summary_df):
    """Assert extracted ongoing original cost equals Table 1 original cost sum."""
    for _, row in summary_df.iterrows():
        month = row["report_month"]
        t1_cost = float(row["table1_orig_cost_cr"])
        ongoing_cost = float(row["ongoing_orig_cost_cr"])
        assert (
            pytest.approx(ongoing_cost, rel=1e-4) == t1_cost
        ), f"[{month}] Cost sum mismatch: extracted {ongoing_cost} vs Table 1 {t1_cost}"


def test_revised_fields_available_all_months(summary_df):
    """Assert both revised cost and revised completion date are available across all 13 months."""
    for _, row in summary_df.iterrows():
        month = row["report_month"]
        assert (
            row["has_revised_cost"] is True or row["has_revised_cost"] == 1
        ), f"[{month}] Missing revised cost"
        assert (
            row["has_revised_doc"] is True or row["has_revised_doc"] == 1
        ), f"[{month}] Missing revised DoC"


def test_parquet_file_integrity(summary_df):
    """Verify all 13 ongoing parquet files exist with valid columns and non-null identifiers."""
    for month in PUBLISHED_GROUND_TRUTH.keys():
        clean_month = month.replace("-", "_")
        parquet_file = DATA_INTERIM / f"raw_ongoing_{clean_month}.parquet"
        assert parquet_file.exists(), f"Parquet file missing: {parquet_file}"

        df = load_dataframe(parquet_file)
        assert len(df) == PUBLISHED_GROUND_TRUTH[month]["ongoing_count"]
        assert df["sl_no"].nunique() == len(df), f"[{month}] Non-unique sl_no"
        assert df["sl_no"].min() == 1, f"[{month}] Sl.No does not start at 1"
        assert df["project_name"].notna().all(), f"[{month}] Missing project name"
        assert df["original_cost_cr"].notna().all(), f"[{month}] Missing original cost"
        assert (df["report_month"] == month).all(), f"[{month}] Incorrect report_month tag"
        assert (
            df["project_code"].notna().all()
        ), f"[{month}] Missing project_code on {df['project_code'].isna().sum()} rows"


def test_project_code_completeness_all_months(summary_df):
    """Regression test: assert project_code missing rate is 0.0% across all 13 months.

    Guards against the Feb/Mar parser bug where single-paren legacy codes swallowed
    project codes.
    """
    for month in PUBLISHED_GROUND_TRUTH.keys():
        clean_month = month.replace("-", "_")
        parquet_file = DATA_INTERIM / f"raw_ongoing_{clean_month}.parquet"
        df = load_dataframe(parquet_file)
        null_count = df["project_code"].isna().sum()
        null_rate = null_count / len(df)
        assert (
            null_rate == 0.0
        ), f"[{month}] project_code missing on {null_count}/{len(df)} rows ({null_rate:.2%})"

