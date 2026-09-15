"""Unit and integration tests for data validation (STEP_02).

Tests each validation rule with crafted rows, verifies multi-flag aggregation,
and tests the validation pipeline runner on real interim parquet data.
"""

from pathlib import Path

import pandas as pd

from src.validation.rules import (
    parse_date_mmyyyy,
    validate_cost_revision,
    validate_dates,
    validate_expenditure_vs_cost,
    validate_non_negative,
    validate_progress_range,
    validate_record,
)
from src.validation.run import run, validate_dataframe


def test_parse_date_mmyyyy():
    """Verify robust parsing of various date formats and handling of NA/placeholders."""
    assert parse_date_mmyyyy("03/2023") == (2023, 3)
    assert parse_date_mmyyyy("(01/2024)") == (2024, 1)
    assert parse_date_mmyyyy("2025-07") == (2025, 7)
    assert parse_date_mmyyyy("NA") is None
    assert parse_date_mmyyyy("-") is None
    assert parse_date_mmyyyy("N.A.") is None
    assert parse_date_mmyyyy("") is None
    assert parse_date_mmyyyy(None) is None
    assert parse_date_mmyyyy(float("nan")) is None


def test_validate_progress_range():
    """Verify physical progress is flagged only when strictly outside [0, 100]."""
    assert len(validate_progress_range({"physical_progress_pct": 0.0})) == 0
    assert len(validate_progress_range({"physical_progress_pct": 50.5})) == 0
    assert len(validate_progress_range({"physical_progress_pct": 100.0})) == 0

    under = validate_progress_range({"physical_progress_pct": -0.1})
    assert len(under) == 1
    assert under[0].flag == "progress_out_of_range"

    over = validate_progress_range({"physical_progress_pct": 100.1})
    assert len(over) == 1
    assert over[0].flag == "progress_out_of_range"


def test_validate_non_negative():
    """Verify negative cost, expenditure, and progress are caught."""
    clean_row = {
        "original_cost_cr": 100.0,
        "revised_cost_cr": 120.0,
        "cumulative_expenditure_cr": 50.0,
        "physical_progress_pct": 40.0,
    }
    assert len(validate_non_negative(clean_row)) == 0

    bad_row = {
        "original_cost_cr": -10.0,
        "revised_cost_cr": 120.0,
        "cumulative_expenditure_cr": -5.0,
        "physical_progress_pct": 40.0,
    }
    issues = validate_non_negative(bad_row)
    assert len(issues) == 2
    assert all(i.flag == "negative_value" for i in issues)
    assert {i.column for i in issues} == {"original_cost_cr", "cumulative_expenditure_cr"}


def test_validate_dates():
    """Verify chronological sequence checks and sentinel year detection."""
    clean_dates = {
        "date_of_approval": "01/2020",
        "start_date": "06/2020",
        "original_completion_date": "06/2023",
        "revised_completion_date": "12/2024",
    }
    assert len(validate_dates(clean_dates)) == 0

    # start before approval
    issues1 = validate_dates({"start_date": "01/2019", "date_of_approval": "06/2020"})
    assert any("before date_of_approval" in i.reason for i in issues1)

    # revised completion before original completion
    issues2 = validate_dates(
        {
            "original_completion_date": "12/2024",
            "revised_completion_date": "06/2024",
        }
    )
    assert any("before original_completion_date" in i.reason for i in issues2)

    # original completion before start
    issues3 = validate_dates({"start_date": "06/2023", "original_completion_date": "01/2023"})
    assert any("before start_date" in i.reason for i in issues3)

    # sentinel year 1900
    issues4 = validate_dates({"start_date": "01/1900"})
    assert any("sentinel/uninitialized" in i.reason for i in issues4)


def test_validate_cost_revision():
    """Verify revised < original flags cost_revised_down (known artifact)."""
    assert len(validate_cost_revision({"original_cost_cr": 100, "revised_cost_cr": 120})) == 0
    assert len(validate_cost_revision({"original_cost_cr": 100, "revised_cost_cr": 100})) == 0

    issues = validate_cost_revision({"original_cost_cr": 100, "revised_cost_cr": 90})
    assert len(issues) == 1
    assert issues[0].flag == "cost_revised_down"
    assert "known reporting artifact" in issues[0].reason


def test_validate_expenditure_vs_cost():
    """Verify expenditure exceeding revised cost is flagged for review."""
    assert (
        len(validate_expenditure_vs_cost({"revised_cost_cr": 100, "cumulative_expenditure_cr": 80}))
        == 0
    )
    assert (
        len(
            validate_expenditure_vs_cost({"revised_cost_cr": 100, "cumulative_expenditure_cr": 100})
        )
        == 0
    )

    issues = validate_expenditure_vs_cost(
        {"revised_cost_cr": 100, "cumulative_expenditure_cr": 110}
    )
    assert len(issues) == 1
    assert issues[0].flag == "exp_exceeds_cost"
    assert "exceeds revised_cost_cr" in issues[0].reason


def test_validate_record_combined():
    """Verify multi-flag aggregation on single record."""
    bad_record = {
        "project_name": "Test Anomaly Project",
        "date_of_approval": "06/2020",
        "start_date": "01/2019",  # date_inconsistency
        "original_cost_cr": 100.0,
        "revised_cost_cr": 80.0,  # cost_revised_down
        "cumulative_expenditure_cr": 95.0,  # exp_exceeds_cost
        "physical_progress_pct": -5.0,  # progress_out_of_range AND negative_value
    }
    issues = validate_record(bad_record)
    flags = {i.flag for i in issues}
    assert flags == {
        "date_inconsistency",
        "cost_revised_down",
        "exp_exceeds_cost",
        "progress_out_of_range",
        "negative_value",
    }


def test_validate_dataframe():
    """Verify dataframe validation attaches data_quality_flag column and keeps rows intact."""
    df = pd.DataFrame(
        [
            {
                "project_code": "P1",
                "project_name": "Clean Project",
                "original_cost_cr": 100.0,
                "revised_cost_cr": 100.0,
                "cumulative_expenditure_cr": 50.0,
                "physical_progress_pct": 50.0,
            },
            {
                "project_code": "P2",
                "project_name": "Cost Down Project",
                "original_cost_cr": 100.0,
                "revised_cost_cr": 90.0,
                "cumulative_expenditure_cr": 50.0,
                "physical_progress_pct": 50.0,
            },
        ]
    )
    val_df, audits = validate_dataframe(df, table_type="ongoing", report_month="2026-04")
    assert len(val_df) == 2
    assert pd.isna(val_df["data_quality_flag"].iloc[0])
    assert val_df["data_quality_flag"].iloc[1] == "cost_revised_down"
    assert len(audits) == 1
    assert audits[0]["project_code"] == "P2"
    assert audits[0]["flag"] == "cost_revised_down"


def test_pipeline_integration_real_data():
    """Verify validation pipeline runs cleanly on actual interim parquets."""
    res = run()
    assert res["files_processed"] >= 35
    assert res["total_records"] == 19596
    assert res["total_flagged_records"] > 0
    assert Path(res["audit_log_path"]).exists()
    assert Path(res["report_path"]).exists()

    # Verify Jan 2026 negative values are detected
    df_log = pd.read_parquet("data/interim/validation_log.parquet")
    neg_issues = df_log[df_log["flag"] == "negative_value"]
    assert len(neg_issues) == 4
    assert (neg_issues["report_month"] == "2026-01").all()
