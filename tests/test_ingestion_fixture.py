"""Deterministic, code-coupled fixture tests for PDF ingestion and parser logic.

Runs entirely on a committed synthetic/sample 1-page PDF fixture and crafted text strings.
Provides authoritative parser regression coverage in CI without requiring heavy DVC datasets.
"""

from pathlib import Path

import pandas as pd
import pdfplumber

from src.ingestion.parser import (
    clean_str,
    is_ministry_header,
    parse_number,
    parse_ongoing_table,
    parse_simple_project_cell,
    parse_table6_project_cell,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SAMPLE_PDF = FIXTURE_DIR / "sample_table6_page.pdf"


def test_fixture_pdf_table6_extraction():
    """Verify end-to-end table extraction and project code resolution on committed PDF fixture.

    Exercises the Feb/Mar 2026 table layout containing projects with legacy codes (N04000106)
    and projects with dash placeholders (-). Ensures no project codes are swallowed as NaN.
    """
    assert SAMPLE_PDF.exists(), f"Committed sample PDF missing at {SAMPLE_PDF}"

    with pdfplumber.open(SAMPLE_PDF) as doc:
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
