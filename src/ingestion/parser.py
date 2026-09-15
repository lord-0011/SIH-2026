"""Parser for MoSPI PAIMANA Flash Report PDFs.

Extracts:
- Table 6: All Ongoing Projects
- Table 3: Completed Projects During Month
- Table 4: Newly Added Projects

Handles header forward-filling (Ministry/Sector), paired visual cell splitting,
and raw project identifier parsing.
"""

import re
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber

from src.common.logging_setup import get_logger

log = get_logger("ingestion.parser")

KNOWN_MINISTRIES = {
    "Department for Promotion of Industry & Internal Trade",
    "Department of Higher Education",
    "Department of Sports",
    "Department of Telecommunications",
    "Department of Water Resources, River Development & GR",
    "Ministry of Civil Aviation",
    "Ministry of Coal",
    "Ministry of Health & Family Welfare",
    "Ministry of Housing & Urban Affairs",
    "Ministry of Labour and Employment",
    "Ministry of Mines",
    "Ministry of Petroleum & Natural Gas",
    "Ministry of Ports, Shipping and Waterways",
    "Ministry of Power",
    "Ministry of Railways",
    "Ministry of Road Transport & Highways",
    "Ministry of Steel",
}


def clean_str(val: Any) -> str | None:
    """Clean string value, stripping whitespace and returning None for empty strings."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def parse_number(val: Any) -> float | None:
    """Parse numeric values from strings, handling commas, parens, negatives and dashes."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s in ("-", "(-)", "NA", "N/A", "nil", "Nil", "--"):
        return None
    cleaned = re.sub(r"[\s,()]", "", s)
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_table6_project_cell(
    text: str,
) -> tuple[str, str | None, str | None, str | None, str | None]:
    """Parse Col 1 of Table 6.

    Layout from bottom up:
      - (Legacy OCMS Code) (PMGID)
      - (Project Code)
      - (Agency)
      - Project Name lines
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return text, None, None, None, None

    legacy_code = None
    pmgid = None
    proj_code = None
    agency = None

    # 1. Bottom line: (Legacy) (PMGID)
    if lines:
        m_legacy = re.match(r"\((.*?)\)\s*\((.*?)\)$", lines[-1])
        if m_legacy:
            leg_val = m_legacy.group(1).strip()
            pmg_val = m_legacy.group(2).strip()
            legacy_code = None if leg_val in ("-", "--", "") else leg_val
            pmgid = None if pmg_val in ("-", "--", "") else pmg_val
            lines = lines[:-1]

    # 2. Next line up: (Project Code)
    if lines:
        m_proj = re.match(r"^\((.*?)\)$", lines[-1])
        if m_proj:
            code_val = m_proj.group(1).strip()
            if code_val not in ("-", "--", ""):
                proj_code = code_val
            lines = lines[:-1]

    # 3. Next line up: (Agency)
    if lines and lines[-1].startswith("(") and lines[-1].endswith(")"):
        agency_val = lines[-1][1:-1].strip()
        agency = None if agency_val in ("-", "--", "") else agency_val
        lines = lines[:-1]

    proj_name = " ".join(lines).strip() if lines else text
    return proj_name, agency, proj_code, legacy_code, pmgid


def parse_simple_project_cell(text: str) -> tuple[str, str | None, str | None]:
    """Parse Col 1 of Table 3 or Table 4.

    Layout:
      - Project Name lines
      - (Agency)
      - (Project Code) or Project Code
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return text, None, None

    proj_code = None
    agency = None

    if lines:
        code_cand = lines[-1].strip("()")
        if code_cand.isdigit() or len(code_cand) >= 4:
            proj_code = code_cand
            lines = lines[:-1]

    if lines and lines[-1].startswith("(") and lines[-1].endswith(")"):
        agency = lines[-1][1:-1].strip()
        lines = lines[:-1]
    elif len(lines) >= 2:
        agency = lines[-1].strip("()")
        lines = lines[:-1]

    proj_name = " ".join(lines).strip() if lines else text
    return proj_name, agency, proj_code


def is_ministry_header(norm_text: str) -> bool:
    """Check if header text represents a Ministry or Department."""
    if norm_text in KNOWN_MINISTRIES:
        return True
    return norm_text.startswith(("Ministry of", "Department of", "Department for"))


def parse_table_6(doc: pdfplumber.PDF, source_month: str, source_doc: str) -> pd.DataFrame:
    """Parse Table 6 (All Ongoing Projects)."""
    rows = []
    curr_ministry = None
    curr_sector = None

    for idx, page in enumerate(doc.pages):
        txt = page.extract_text() or ""
        # Check if page is an 'All Ongoing Projects' data page
        if (
            "All Ongoing Projects" not in txt
            or ("Legacy OCMS Code" not in txt and "Sl.No" not in txt)
            or "List of Tables" in txt
            or "Appendix" in txt
            or "CONTENTS" in txt
        ):
            continue

        tables = page.extract_tables()
        if not tables:
            continue

        table = tables[0]
        for row in table:
            if not row or not any(row):
                continue

            col0 = clean_str(row[0])
            col1 = clean_str(row[1])

            # Header row check
            if col0 == "Sl.No" or (col1 and "Project Name" in col1):
                continue

            # Section header or summary row
            if not col0 or not col0.isdigit():
                if not col1:
                    continue
                if col1.lower().startswith("total"):
                    continue

                norm_col1 = " ".join(col1.split())
                if is_ministry_header(norm_col1):
                    curr_ministry = norm_col1
                    curr_sector = None
                else:
                    curr_sector = norm_col1
                continue

            # Ongoing project row
            sl_no = int(col0)
            proj_name, agency, proj_code, legacy_code, pmgid = parse_table6_project_cell(col1 or "")
            state = clean_str(row[2]) if len(row) > 2 else None

            # Approval & Start Dates (col 3)
            c3 = clean_str(row[3]) if len(row) > 3 else ""
            c3_parts = [p.strip() for p in (c3 or "").split("\n") if p.strip()]
            approval_date = c3_parts[0] if c3_parts else None
            start_date = c3_parts[1].strip("()") if len(c3_parts) > 1 else None
            if start_date in ("-", "--"):
                start_date = None

            # Original & Revised DoC (col 4)
            c4 = clean_str(row[4]) if len(row) > 4 else ""
            c4_parts = [p.strip() for p in (c4 or "").split("\n") if p.strip()]
            orig_doc = c4_parts[0] if c4_parts else None
            rev_doc = c4_parts[1].strip("()") if len(c4_parts) > 1 else None
            if rev_doc in ("-", "--"):
                rev_doc = None

            # Original & Revised Cost (col 5)
            c5 = clean_str(row[5]) if len(row) > 5 else ""
            c5_parts = [p.strip() for p in (c5 or "").split("\n") if p.strip()]
            orig_cost = parse_number(c5_parts[0]) if c5_parts else None
            rev_cost = parse_number(c5_parts[1]) if len(c5_parts) > 1 else orig_cost

            cum_exp = parse_number(row[6]) if len(row) > 6 else None
            progress = parse_number(row[7]) if len(row) > 7 else None

            rows.append(
                {
                    "sl_no": sl_no,
                    "project_name": proj_name,
                    "implementing_agency": agency,
                    "project_code": proj_code,
                    "legacy_ocms_code": legacy_code,
                    "pmgid": pmgid,
                    "ministry": curr_ministry,
                    "sector": curr_sector,
                    "state": state,
                    "date_of_approval": approval_date,
                    "start_date": start_date,
                    "original_completion_date": orig_doc,
                    "revised_completion_date": rev_doc,
                    "original_cost_cr": orig_cost,
                    "revised_cost_cr": rev_cost,
                    "cumulative_expenditure_cr": cum_exp,
                    "physical_progress_pct": progress,
                    "report_month": source_month,
                    "source_doc": source_doc,
                }
            )

    df = pd.DataFrame(rows)
    log.info("Parsed Table 6: %d rows from %s", len(df), source_doc)
    return df


def parse_table_3(doc: pdfplumber.PDF, source_month: str, source_doc: str) -> pd.DataFrame:
    """Parse Table 3 (Completed Projects During Month)."""
    rows = []
    curr_ministry = None
    curr_sector = None

    for idx, page in enumerate(doc.pages):
        txt = page.extract_text() or ""
        if (
            "Actual Date of Completion" not in txt
            or "Sl.No" not in txt
            or "List of Tables" in txt
            or "Appendix" in txt
            or "CONTENTS" in txt
        ):
            continue

        tables = page.extract_tables()
        if not tables:
            continue

        table = tables[0]
        for row in table:
            if not row or not any(row):
                continue
            col0 = clean_str(row[0])
            col1 = clean_str(row[1])

            if col0 == "Sl.No" or (col1 and "Project Name" in col1):
                continue

            if not col0 or not col0.isdigit():
                if not col1 or col1.lower().startswith("total"):
                    continue
                norm = " ".join(col1.split())
                if is_ministry_header(norm):
                    curr_ministry = norm
                    curr_sector = None
                else:
                    curr_sector = norm
                continue

            sl_no = int(col0)
            proj_name, agency, proj_code = parse_simple_project_cell(col1 or "")
            state = clean_str(row[2]) if len(row) > 2 else None

            # Col 3: Approval / Start
            c3 = clean_str(row[3]) if len(row) > 3 else ""
            c3_parts = [p.strip() for p in (c3 or "").split("\n") if p.strip()]
            approval_date = c3_parts[0] if c3_parts else None
            start_date = c3_parts[1].strip("()") if len(c3_parts) > 1 else None

            # Col 4: Actual Completion / Orig DoC / Rev DoC
            c4 = clean_str(row[4]) if len(row) > 4 else ""
            c4_parts = [p.strip() for p in (c4 or "").split("\n") if p.strip()]
            act_comp = c4_parts[0] if c4_parts else None
            orig_doc = c4_parts[1].strip("()") if len(c4_parts) > 1 else None
            rev_doc = c4_parts[2].strip("()") if len(c4_parts) > 2 else None
            if rev_doc in ("-", "--"):
                rev_doc = None

            # Col 5: Orig Cost / Rev Cost
            c5 = clean_str(row[5]) if len(row) > 5 else ""
            c5_parts = [p.strip() for p in (c5 or "").split("\n") if p.strip()]
            orig_cost = parse_number(c5_parts[0]) if c5_parts else None
            rev_cost = parse_number(c5_parts[1]) if len(c5_parts) > 1 else orig_cost

            cum_exp = parse_number(row[6]) if len(row) > 6 else None

            rows.append(
                {
                    "sl_no": sl_no,
                    "project_name": proj_name,
                    "implementing_agency": agency,
                    "project_code": proj_code,
                    "ministry": curr_ministry,
                    "sector": curr_sector,
                    "state": state,
                    "date_of_approval": approval_date,
                    "start_date": start_date,
                    "actual_completion_date": act_comp,
                    "original_completion_date": orig_doc,
                    "revised_completion_date": rev_doc,
                    "original_cost_cr": orig_cost,
                    "revised_cost_cr": rev_cost,
                    "cumulative_expenditure_cr": cum_exp,
                    "is_completed_this_month": True,
                    "report_month": source_month,
                    "source_doc": source_doc,
                }
            )

    df = pd.DataFrame(rows)
    log.info("Parsed Table 3: %d rows from %s", len(df), source_doc)
    return df


def parse_table_4(doc: pdfplumber.PDF, source_month: str, source_doc: str) -> pd.DataFrame:
    """Parse Table 4 (Newly Added Projects)."""
    rows = []
    curr_ministry = None
    curr_sector = None

    for idx, page in enumerate(doc.pages):
        txt = page.extract_text() or ""
        tables = page.extract_tables()
        if not tables or not tables[0] or not tables[0][0]:
            continue

        hdr_str = " ".join([str(c).replace("\n", " ") for c in tables[0][0] if c])
        if not (
            "Orignal Cost" in hdr_str
            and len(tables[0][0]) == 6
            and "Sl.No" in hdr_str
            and "CONTENTS" not in txt
            and "Appendix" not in txt
            and "List of Tables" not in txt
        ):
            continue

        table = tables[0]
        for row in table:
            if not row or not any(row):
                continue
            col0 = clean_str(row[0])
            col1 = clean_str(row[1])

            if col0 == "Sl.No" or (col1 and "Project Name" in col1):
                continue

            if not col0 or not col0.isdigit():
                if not col1 or col1.lower().startswith("total"):
                    continue
                norm = " ".join(col1.split())
                if is_ministry_header(norm):
                    curr_ministry = norm
                    curr_sector = None
                else:
                    curr_sector = norm
                continue

            sl_no = int(col0)
            proj_name, agency, proj_code = parse_simple_project_cell(col1 or "")
            state = clean_str(row[2]) if len(row) > 2 else None

            # Col 3: Approval / Start
            c3 = clean_str(row[3]) if len(row) > 3 else ""
            c3_parts = [p.strip() for p in (c3 or "").split("\n") if p.strip()]
            approval_date = c3_parts[0] if c3_parts else None
            start_date = c3_parts[1].strip("()") if len(c3_parts) > 1 else None

            # Col 4: Target DoC / Rev DoC
            c4 = clean_str(row[4]) if len(row) > 4 else ""
            c4_parts = [p.strip() for p in (c4 or "").split("\n") if p.strip()]
            orig_doc = c4_parts[0] if c4_parts else None
            rev_doc = c4_parts[1].strip("()") if len(c4_parts) > 1 else None
            if rev_doc in ("-", "--"):
                rev_doc = None

            # Col 5: Orig Cost / Rev Cost
            c5 = clean_str(row[5]) if len(row) > 5 else ""
            c5_parts = [p.strip() for p in (c5 or "").split("\n") if p.strip()]
            orig_cost = parse_number(c5_parts[0]) if c5_parts else None
            rev_cost = parse_number(c5_parts[1]) if len(c5_parts) > 1 else orig_cost

            rows.append(
                {
                    "sl_no": sl_no,
                    "project_name": proj_name,
                    "implementing_agency": agency,
                    "project_code": proj_code,
                    "ministry": curr_ministry,
                    "sector": curr_sector,
                    "state": state,
                    "date_of_approval": approval_date,
                    "start_date": start_date,
                    "original_completion_date": orig_doc,
                    "revised_completion_date": rev_doc,
                    "original_cost_cr": orig_cost,
                    "revised_cost_cr": rev_cost,
                    "is_newly_added_this_month": True,
                    "report_month": source_month,
                    "source_doc": source_doc,
                }
            )

    df = pd.DataFrame(rows)
    log.info("Parsed Table 4: %d rows from %s", len(df), source_doc)
    return df


def parse_flash_report(pdf_path: Path | str, source_month: str) -> dict[str, pd.DataFrame]:
    """Parse a Flash Report PDF into ongoing, completed, and newly added tables."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Flash report not found: {path}")

    log.info("Opening %s for month %s", path.name, source_month)
    with pdfplumber.open(path) as doc:
        df_ongoing = parse_table_6(doc, source_month=source_month, source_doc=path.name)
        df_completed = parse_table_3(doc, source_month=source_month, source_doc=path.name)
        df_newly_added = parse_table_4(doc, source_month=source_month, source_doc=path.name)

    return {
        "ongoing": df_ongoing,
        "completed": df_completed,
        "newly_added": df_newly_added,
    }
