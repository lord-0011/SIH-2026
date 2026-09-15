"""Test Flash Report April 2026 ingestion and verify sanity anchors (docs/03 §E).

Hard verification gate:
- Exactly 1,981 ongoing projects
- Exactly 17 ministries and 22 sectors
- Original Cost ≈ Rs 37.13 lakh cr (Rs 3,712,662.01 cr)
- Revised Cost ≈ Rs 42.78 lakh cr (Rs 4,278,402.37 cr)
- Cumulative Expenditure ≈ Rs 20.36 lakh cr (Rs 2,036,107.49 cr)
- Table 3: 9 completed projects
- Table 4: 55 newly added projects
"""

import pytest

from src.common.config import DATA_INTERIM, REPORTS
from src.common.io import load_dataframe
from src.ingestion.run import run


@pytest.fixture(scope="module")
def april_data():
    """Load or parse April 2026 tables."""
    pdf_path = REPORTS / "FlashReport_April2026.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Report not found at {pdf_path}")

    # Check if already parsed in data/interim/
    ongoing_path = DATA_INTERIM / "raw_ongoing_2026_04.parquet"
    completed_path = DATA_INTERIM / "raw_completed_2026_04.parquet"
    newly_added_path = DATA_INTERIM / "raw_newly_added_2026_04.parquet"

    if not (ongoing_path.exists() and completed_path.exists() and newly_added_path.exists()):
        run({"pdf_path": pdf_path, "source_month": "2026-04"})

    df_ongoing = load_dataframe(ongoing_path)
    df_completed = load_dataframe(completed_path)
    df_newly_added = load_dataframe(newly_added_path)

    return {
        "ongoing": df_ongoing,
        "completed": df_completed,
        "newly_added": df_newly_added,
    }


def test_table6_project_counts(april_data):
    df_ongoing = april_data["ongoing"]
    assert len(df_ongoing) == 1981, f"Expected 1,981 projects, got {len(df_ongoing)}"
    assert df_ongoing["sl_no"].nunique() == 1981, "Sl.No values are not unique"
    assert df_ongoing["sl_no"].min() == 1, "Sl.No does not start at 1"
    assert df_ongoing["sl_no"].max() == 1981, "Sl.No max is not 1981"


def test_table6_ministries_and_sectors(april_data):
    df_ongoing = april_data["ongoing"]
    ministries = df_ongoing["ministry"].dropna().unique()
    sectors = df_ongoing["sector"].dropna().unique()

    assert len(ministries) == 17, f"Expected 17 ministries, found {len(ministries)}: {ministries}"
    assert len(sectors) == 22, f"Expected 22 sectors, found {len(sectors)}: {sectors}"
    assert df_ongoing["ministry"].isna().sum() == 0, "Found unassigned ministry rows"
    assert df_ongoing["sector"].isna().sum() == 0, "Found unassigned sector rows"


def test_table6_cost_and_expenditure_aggregates(april_data):
    df_ongoing = april_data["ongoing"]

    orig_cost_sum = df_ongoing["original_cost_cr"].sum()
    rev_cost_sum = df_ongoing["revised_cost_cr"].sum()
    cum_exp_sum = df_ongoing["cumulative_expenditure_cr"].sum()

    # Sanity anchors per docs/03 §E:
    # Original: Rs 3,712,662.01 cr (≈ 37.13 lakh cr)
    assert (
        pytest.approx(orig_cost_sum, rel=1e-4) == 3712662.01
    ), f"Original cost mismatch: got {orig_cost_sum}"

    # Revised: Rs 4,278,402.37 cr (≈ 42.78 lakh cr)
    assert (
        pytest.approx(rev_cost_sum, rel=1e-3) == 4278402.37
    ), f"Revised cost mismatch: got {rev_cost_sum}"

    # Cum exp: Rs 2,036,107.49 cr (≈ 20.36 lakh cr)
    assert (
        pytest.approx(cum_exp_sum, rel=1e-3) == 2036107.49
    ), f"Cumulative expenditure mismatch: got {cum_exp_sum}"


def test_table6_field_integrity(april_data):
    df_ongoing = april_data["ongoing"]

    assert df_ongoing["project_name"].isna().sum() == 0, "Found empty project names"
    assert df_ongoing["project_code"].isna().sum() == 0, "Found empty project codes"
    assert df_ongoing["report_month"].unique().tolist() == ["2026-04"]
    assert df_ongoing["source_doc"].unique().tolist() == ["FlashReport_April2026.pdf"]

    # Verify split paired columns are distinct
    assert "original_cost_cr" in df_ongoing.columns
    assert "revised_cost_cr" in df_ongoing.columns
    assert "date_of_approval" in df_ongoing.columns
    assert "start_date" in df_ongoing.columns
    assert "original_completion_date" in df_ongoing.columns
    assert "revised_completion_date" in df_ongoing.columns


def test_table3_completed_projects(april_data):
    df_completed = april_data["completed"]
    assert len(df_completed) == 9, f"Expected 9 completed projects, got {len(df_completed)}"
    assert df_completed["is_completed_this_month"].all()
    assert df_completed["actual_completion_date"].notna().sum() > 0


def test_table4_newly_added_projects(april_data):
    df_newly_added = april_data["newly_added"]
    assert len(df_newly_added) == 55, f"Expected 55 newly added projects, got {len(df_newly_added)}"
    assert df_newly_added["is_newly_added_this_month"].all()
