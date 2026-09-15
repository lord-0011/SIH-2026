"""Deterministic, code-coupled fixture tests for PDF ingestion and parser logic.

Runs in every CI environment (GitHub Actions, clean runners) WITHOUT requiring
external data, DVC pull, or Google Drive credentials.
Uses committed fixtures in tests/fixtures/:
  1. sample_flash_report.pdf (multi-page synthetic report covering Tables 1, 3, 4, 6)
  2. sample_table6_page.pdf (real 1-page Table 6 page covering Feb/Mar 2026 layout)
"""

from pathlib import Path

import pandas as pd
import pdfplumber
import pytest

from src.ingestion.parser import (
    clean_str,
    is_ministry_header,
    parse_flash_report,
    parse_number,
    parse_ongoing_table,
    parse_simple_project_cell,
    parse_table6_project_cell,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SYNTHETIC_PDF = FIXTURE_DIR / "sample_flash_report.pdf"
SAMPLE_PAGE_PDF = FIXTURE_DIR / "sample_table6_page.pdf"


# ---------------------------------------------------------------------------
# Tests against synthetic multi-page flash report fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fixture_data():
    """Parse the committed synthetic PDF fixture.

    Fails immediately if fixture is missing — NEVER calls pytest.skip().
    """
    assert (
        SYNTHETIC_PDF.exists()
    ), f"Required test fixture missing: {SYNTHETIC_PDF}. Run tests/fixtures/generate_fixture.py"
    return parse_flash_report(SYNTHETIC_PDF, source_month="2026-04")


def test_fixture_file_exists():
    """Verify that the committed PDF fixtures are physically present in the repository."""
    assert SYNTHETIC_PDF.exists(), f"Fixture file not found at {SYNTHETIC_PDF}"
    assert SYNTHETIC_PDF.stat().st_size > 0, f"Fixture file {SYNTHETIC_PDF} is empty"
    assert SAMPLE_PAGE_PDF.exists(), f"Fixture file not found at {SAMPLE_PAGE_PDF}"
    assert SAMPLE_PAGE_PDF.stat().st_size > 0, f"Fixture file {SAMPLE_PAGE_PDF} is empty"


def test_table1_summary_extraction(fixture_data):
    """Verify Table 1 summary extraction against the fixture's printed summary page.

    Source values measured from Page 1 of tests/fixtures/sample_flash_report.pdf:
    - Printed 'Total' row: 1,981 projects, Rs 3,712,662.01 cr original, Rs 2,036,107.69 cr expenditure
    - Printed 'Ministry of Road Transport & Highways' row: 1,137 projects
    """
    t1 = fixture_data["table1_summary"]

    # Grand total project count printed in Table 1 Total row
    assert t1["table1_project_count"] == 1981, f"Expected 1981, got {t1['table1_project_count']}"

    # Cost and expenditure totals printed in Table 1 Total row
    assert (
        t1["table1_orig_cost_cr"] == 3712662.01
    ), f"Expected 3712662.01, got {t1['table1_orig_cost_cr']}"
    assert (
        t1["table1_cum_exp_cr"] == 2036107.69
    ), f"Expected 2036107.69, got {t1['table1_cum_exp_cr']}"

    # MoRTH count printed in Table 1 Road Transport row
    assert t1["morth_ongoing_count"] == 1137, f"Expected 1137, got {t1['morth_ongoing_count']}"


def test_ongoing_table_row_count_and_columns(fixture_data):
    """Verify Table 6 ongoing table row count and schema.

    Expected row count is exactly 3 (the measured number of ongoing project rows
    synthesized on Page 2 of tests/fixtures/sample_flash_report.pdf).
    """
    df = fixture_data["ongoing"]
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3, f"Expected 3 rows in synthetic fixture, got {len(df)}"

    expected_cols = {
        "sl_no",
        "project_name",
        "implementing_agency",
        "project_code",
        "legacy_ocms_code",
        "pmgid",
        "ministry",
        "sector",
        "state",
        "date_of_approval",
        "start_date",
        "original_completion_date",
        "revised_completion_date",
        "original_cost_cr",
        "revised_cost_cr",
        "cumulative_expenditure_cr",
        "physical_progress_pct",
        "report_month",
        "source_doc",
    }
    assert expected_cols.issubset(
        set(df.columns)
    ), f"Missing columns: {expected_cols - set(df.columns)}"


def test_adversarial_paired_cost_splitting(fixture_data):
    """ADVERSARIAL ASSERTION: paired cost cells must split into distinct numeric columns.

    Source on Page 2 Row 1: '265.91\\n(280.50)'
    Must split into original_cost_cr=265.91 and revised_cost_cr=280.5.
    Must NOT remain merged as a string, nor contain parentheses.
    """
    df = fixture_data["ongoing"]
    row0 = df[df["sl_no"] == 1].iloc[0]

    # Values must be numeric floats
    assert isinstance(row0["original_cost_cr"], float)
    assert isinstance(row0["revised_cost_cr"], float)

    # Values measured from fixture
    assert row0["original_cost_cr"] == 265.91
    assert row0["revised_cost_cr"] == 280.50

    # Ensure they did not get conflated or merged
    assert row0["original_cost_cr"] != row0["revised_cost_cr"]

    # Fallback test: Page 2 Row 3 has only original cost '500.00' (no revised cost in source)
    row2 = df[df["sl_no"] == 3].iloc[0]
    assert row2["original_cost_cr"] == 500.00
    assert row2["revised_cost_cr"] == 500.00


def test_adversarial_null_token_normalization(fixture_data):
    """ADVERSARIAL ASSERTION: '-' and '(-)' placeholder tokens must parse to None/null.

    They must NEVER be preserved as literal string '-' or '(-)', which would corrupt
    downstream joins and key lookups.
    """
    df = fixture_data["ongoing"]
    row1 = df[df["sl_no"] == 2].iloc[0]

    assert pd.isna(
        row1["legacy_ocms_code"]
    ), f"Expected null/NaN, got {repr(row1['legacy_ocms_code'])}"
    assert pd.isna(row1["pmgid"]), f"Expected null/NaN, got {repr(row1['pmgid'])}"
    assert row1["legacy_ocms_code"] != "-"
    assert row1["pmgid"] != "-"

    row2 = df[df["sl_no"] == 3].iloc[0]
    assert pd.isna(row2["start_date"]), f"Expected null/NaN, got {repr(row2['start_date'])}"
    assert pd.isna(
        row2["revised_completion_date"]
    ), f"Expected null/NaN, got {repr(row2['revised_completion_date'])}"
    assert row2["start_date"] != "-"
    assert row2["revised_completion_date"] != "-"


def test_garbage_cost_faithful_ingestion(fixture_data):
    """Verify that anomalous source values (revised_cost=0.1) are carried through faithfully."""
    df = fixture_data["ongoing"]
    row1 = df[df["sl_no"] == 2].iloc[0]

    assert row1["project_code"] == "618886"
    assert row1["original_cost_cr"] == 238.66
    assert row1["revised_cost_cr"] == 0.1


def test_paired_dates_and_multiline_project_name(fixture_data):
    """Verify paired date splitting and multi-line project name cleanup."""
    df = fixture_data["ongoing"]
    row0 = df[df["sl_no"] == 1].iloc[0]

    expected_name = "Construction of New Domestic Terminal Building and miscellaneous airside works"
    assert row0["project_name"] == expected_name
    assert row0["implementing_agency"] == "AAI"
    assert row0["project_code"] == "612786"
    assert row0["legacy_ocms_code"] == "N04000106"
    assert row0["pmgid"] == "PMG12345"

    assert row0["date_of_approval"] == "03/2023"
    assert row0["start_date"] == "01/2024"
    assert row0["original_completion_date"] == "01/2026"
    assert row0["revised_completion_date"] == "07/2026"


def test_ministry_and_sector_forward_filling(fixture_data):
    """Verify that Ministry and Sector headers forward-fill onto all ongoing rows."""
    df = fixture_data["ongoing"]
    assert (df["ministry"] == "Ministry of Civil Aviation").all()
    assert (df["sector"] == "Civil Aviation").all()


def test_completed_and_newly_added_tables_extracted(fixture_data):
    """Verify that Table 3 (Completed) and Table 4 (Newly Added) are extracted from the fixture."""
    df_comp = fixture_data["completed"]
    df_new = fixture_data["newly_added"]

    assert len(df_comp) == 1, f"Expected 1 completed project, got {len(df_comp)}"
    row_comp = df_comp.iloc[0]
    assert row_comp["project_code"] == "701001"
    assert row_comp["actual_completion_date"] == "04/2026"
    assert row_comp["original_cost_cr"] == 150.0
    assert row_comp["revised_cost_cr"] == 165.0
    assert bool(row_comp["is_completed_this_month"]) is True

    assert len(df_new) == 1, f"Expected 1 newly added project, got {len(df_new)}"
    row_new = df_new.iloc[0]
    assert row_new["project_code"] == "801001"
    assert row_new["original_cost_cr"] == 85.0
    assert bool(row_new["is_newly_added_this_month"]) is True


# ---------------------------------------------------------------------------
# Tests against real 1-page sample Table 6 fixture (Feb 2026 layout)
# ---------------------------------------------------------------------------


def test_fixture_pdf_table6_extraction():
    """Verify end-to-end table extraction and project code resolution on committed PDF fixture.

    Exercises the Feb/Mar 2026 table layout containing projects with legacy codes (N04000106)
    and projects with dash placeholders (-). Ensures no project codes are swallowed as NaN.
    """
    assert SAMPLE_PAGE_PDF.exists(), f"Committed sample PDF missing at {SAMPLE_PAGE_PDF}"

    with pdfplumber.open(SAMPLE_PAGE_PDF) as doc:
        df = parse_ongoing_table(doc, source_month="2026-02", source_doc="sample_table6_page.pdf")

    assert len(df) == 20, f"Expected 20 projects in sample page, got {len(df)}"
    assert df["sl_no"].tolist() == list(range(1, 21))

    # Strict assertion: ZERO missing project codes across all extracted rows
    assert df["project_code"].notna().all(), "project_code is missing on some rows"
    assert (df["project_code"] != "").all(), "project_code is empty on some rows"

    # Row 1: Kadapa Airport -> has both Project Code and Legacy OCMS Code
    p1 = df[df["sl_no"] == 1].iloc[0]
    assert p1["project_code"] == "612786"
    assert p1["legacy_ocms_code"] == "N04000106"
    assert "Kadapa Airport" in p1["project_name"]
    assert p1["implementing_agency"] == "Airport Authority of India [AAI]"

    # Row 5: Bihta Airport -> regression check for Feb/Mar 2026 '(-)' legacy code layout
    p5 = df[df["sl_no"] == 5].iloc[0]
    assert p5["project_code"] == "612183", f"Expected project_code 612183, got {p5['project_code']}"
    assert pd.isna(p5["legacy_ocms_code"]) or p5["legacy_ocms_code"] is None
    assert "Bihta" in p5["project_name"]
    assert p5["implementing_agency"] == "Airport Authority of India [AAI]"

    # Row 9: Keshod Airport -> regression check for NA approval date and '(-)' legacy code
    p9 = df[df["sl_no"] == 9].iloc[0]
    assert p9["project_code"] == "619054"
    assert pd.isna(p9["legacy_ocms_code"]) or p9["legacy_ocms_code"] is None


# ---------------------------------------------------------------------------
# Unit tests for project cell parser regular expressions & edge cases
# ---------------------------------------------------------------------------


def test_parse_table6_project_cell_pattern_a_legacy_code():
    """Verify Pattern A: Agency + Project Code + Legacy OCMS Code (Feb-Mar 2026)."""
    cell_text = (
        "Construction of New Domestic Terminal Building\n"
        "(Airport Authority of India [AAI])\n"
        "(612786)\n"
        "(N04000106)"
    )
    name, agency, code, leg, pmg = parse_table6_project_cell(cell_text)
    assert name == "Construction of New Domestic Terminal Building"
    assert agency == "Airport Authority of India [AAI]"
    assert code == "612786"
    assert leg == "N04000106"
    assert pmg is None


def test_parse_table6_project_cell_pattern_a_dash_legacy():
    """Regression test: verify '(-)' legacy code does NOT swallow project code (Feb/Mar bug)."""
    cell_text = (
        "Development of New Civil Enclave at Bihta\n"
        "(Airport Authority of India [AAI])\n"
        "(612183)\n"
        "(-)"
    )
    name, agency, code, leg, pmg = parse_table6_project_cell(cell_text)
    assert name == "Development of New Civil Enclave at Bihta"
    assert agency == "Airport Authority of India [AAI]"
    assert code == "612183", f"Project code was swallowed: got {code}"
    assert leg is None
    assert pmg is None


def test_parse_table6_project_cell_pattern_b_early_layout():
    """Verify Pattern B: Agency + Project Code only (Jul 2025 - Jan 2026)."""
    cell_text = "4-Laning of NH Section\n" "(NHIDCL)\n" "(618384)"
    name, agency, code, leg, pmg = parse_table6_project_cell(cell_text)
    assert name == "4-Laning of NH Section"
    assert agency == "NHIDCL"
    assert code == "618384"
    assert leg is None
    assert pmg is None


def test_parse_table6_project_cell_pattern_c_four_identifiers():
    """Verify Pattern C: Agency + Project Code + Legacy Code + PMGID (Apr-May 2026)."""
    cell_text = (
        "Singrauli Super Thermal Power Project\n" "(NTPC)\n" "(612142)\n" "(N18000382) (4353)"
    )
    name, agency, code, leg, pmg = parse_table6_project_cell(cell_text)
    assert name == "Singrauli Super Thermal Power Project"
    assert agency == "NTPC"
    assert code == "612142"
    assert leg == "N18000382"
    assert pmg == "4353"


def test_parse_table6_project_cell_pattern_c_dash_identifiers():
    """Verify Pattern C with dashes: '(-) (-)' (Jun-Jul 2026)."""
    cell_text = (
        "Kadapa Airport AICMC\n" "(Airport Authority of India [AAI])\n" "(612786)\n" "(-) (-)"
    )
    name, agency, code, leg, pmg = parse_table6_project_cell(cell_text)
    assert name == "Kadapa Airport AICMC"
    assert agency == "Airport Authority of India [AAI]"
    assert code == "612786"
    assert leg is None
    assert pmg is None


def test_parse_simple_project_cell():
    """Verify Table 3 & 4 simple project cell parsing."""
    cell_text = "Gauge Conversion Project\n" "(Railway Board [RB])\n" "(701234)"
    name, agency, code = parse_simple_project_cell(cell_text)
    assert name == "Gauge Conversion Project"
    assert agency == "Railway Board [RB]"
    assert code == "701234"


def test_clean_str_and_parse_number():
    """Verify string cleaning and number parsing."""
    assert clean_str("  1,234.56  ") == "1,234.56"
    assert parse_number("1,234.56") == 1234.56
    assert parse_number("(500.00)") == 500.0
    assert parse_number("-") is None
    assert parse_number("") is None
    assert parse_number(None) is None


def test_is_ministry_header():
    """Verify ministry header identification."""
    assert is_ministry_header("Ministry of Civil Aviation") is True
    assert is_ministry_header("Department of Telecommunications") is True
    assert is_ministry_header("Department for Promotion of Industry and Internal Trade") is True
    assert is_ministry_header("Aviation & Aviation Infrastructure") is False
    assert is_ministry_header("Total") is False
