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

    # 1. Bottom line: can be (Legacy) (PMGID) [Apr 2026+], OR (Legacy Code) / (-) [Feb-Mar 2026]
    if lines:
        m_two = re.match(r"^\((.*?)\)\s*\((.*?)\)$", lines[-1])
        if m_two:
            leg_val = m_two.group(1).strip()
            pmg_val = m_two.group(2).strip()
            legacy_code = None if leg_val in ("-", "--", "") else leg_val
            pmgid = None if pmg_val in ("-", "--", "") else pmg_val
            lines = lines[:-1]
        elif re.match(r"^\((.*?)\)$", lines[-1]):
            val = lines[-1][1:-1].strip()
            # If line above it is parenthesized with digits (Project Code), then bottom line is Legacy Code!
            if len(lines) >= 2 and re.match(r"^\(\d{4,8}\)$", lines[-2]):
                legacy_code = None if val in ("-", "--", "") else val
                lines = lines[:-1]
            elif val in ("-", "--") or re.match(r"^[A-Za-z]\d{6,}", val):
                legacy_code = None if val in ("-", "--", "") else val
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


def parse_table_1_summary(doc: pdfplumber.PDF) -> dict[str, Any]:
    """Parse Table 1 (Ministry-wise Ongoing Projects) grand totals and MoRTH count."""
    morth_count = 0
    grand_total = None
    t1_orig_cost = None
    t1_cum_exp = None
    in_table1 = False

    for p in doc.pages[:35]:
        t = p.extract_text() or ""
        if (
            ("Table 1: Ministry-wise" in t or "Ministry-wise Ongoing Projects" in t)
            and "List of Tables" not in t
            and "CONTENTS" not in t
        ):
            in_table1 = True
        if not in_table1:
            continue
        if "Table 2:" in t or "State-wise Ongoing Projects" in t:
            break
        for table in p.extract_tables():
            for r in table:
                clean_r = [str(c).strip() for c in r if c and str(c).strip()]
                if not clean_r:
                    continue
                if any("road transport" in c.lower() for c in clean_r) and len(clean_r) >= 4:
                    if clean_r[3].isdigit():
                        morth_count = int(clean_r[3])
                if clean_r[0].lower() == "total" and len(clean_r) >= 4 and clean_r[1].isdigit():
                    grand_total = int(clean_r[1])
                    t1_orig_cost = parse_number(clean_r[2])
                    t1_cum_exp = parse_number(clean_r[3])

    return {
        "table1_project_count": grand_total,
        "table1_orig_cost_cr": t1_orig_cost,
        "table1_cum_exp_cr": t1_cum_exp,
        "morth_ongoing_count": morth_count,
    }


def parse_ongoing_table(doc: pdfplumber.PDF, source_month: str, source_doc: str) -> pd.DataFrame:
    """Parse All Ongoing Projects table (layout-aware, handles early Table 4 & modern Table 6)."""
    rows = []
    curr_ministry = None
    curr_sector = None

    for idx, page in enumerate(doc.pages):
        txt = page.extract_text() or ""
        # Check if page is an 'All Ongoing Projects' data page
        if (
            "All Ongoing Projects" not in txt
            or "List of Tables" in txt
            or "Appendix" in txt
            or "CONTENTS" in txt
        ):
            continue

        tables = page.extract_tables()
        if not tables:
            continue

        for table in tables:
            for raw_row in table:
                if not raw_row or not any(raw_row):
                    continue

                # Shift row only when leading cell is None and second cell is digit/Sl.No (handles border columns)
                if (
                    raw_row[0] is None
                    and len(raw_row) > 1
                    and clean_str(raw_row[1])
                    and (
                        clean_str(raw_row[1]).isdigit()
                        or clean_str(raw_row[1]) in ("Sl.No", "Sl. No", "Sl No")
                    )
                ):
                    row = raw_row[1:]
                else:
                    row = raw_row

                if not row or len(row) < 2:
                    continue

                col0 = clean_str(row[0])
                col1 = clean_str(row[1])

                # Header row check
                if col0 in ("Sl.No", "Sl. No", "Sl No") or (col1 and "Project Name" in col1):
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
                proj_name, agency, proj_code, legacy_code, pmgid = parse_table6_project_cell(
                    col1 or ""
                )
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
    log.info("Parsed Ongoing table: %d rows from %s", len(df), source_doc)
    return df


# Backward compatibility alias
parse_table_6 = parse_ongoing_table


def parse_table_3(doc: pdfplumber.PDF, source_month: str, source_doc: str) -> pd.DataFrame:
    """Parse Table 3 (Completed Projects During Month)."""
    rows = []
    curr_ministry = None
    curr_sector = None

    for idx, page in enumerate(doc.pages):
        txt = page.extract_text() or ""
        if (
            ("Completed Projects" not in txt and "Actual Date of Completion" not in txt)
            or "List of Tables" in txt
            or "Appendix" in txt
            or "CONTENTS" in txt
        ):
            continue

        tables = page.extract_tables()
        if not tables:
            continue

        for table in tables:
            for raw_row in table:
                if not raw_row or not any(raw_row):
                    continue
                if (
                    raw_row[0] is None
                    and len(raw_row) > 1
                    and clean_str(raw_row[1])
                    and (
                        clean_str(raw_row[1]).isdigit()
                        or clean_str(raw_row[1]) in ("Sl.No", "Sl. No", "Sl No")
                    )
                ):
                    row = raw_row[1:]
                else:
                    row = raw_row

                if not row or len(row) < 2:
                    continue

                col0 = clean_str(row[0])
                col1 = clean_str(row[1])

                if col0 in ("Sl.No", "Sl. No", "Sl No") or (col1 and "Project Name" in col1):
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
    log.info("Parsed Completed table: %d rows from %s", len(df), source_doc)
    return df


def parse_table_4(doc: pdfplumber.PDF, source_month: str, source_doc: str) -> pd.DataFrame:
    """Parse Table 4 (Newly Added Projects)."""
    rows = []
    curr_ministry = None
    curr_sector = None

    for idx, page in enumerate(doc.pages):
        txt = page.extract_text() or ""
        if (
            "Newly Added Projects" not in txt
            or "List of Tables" in txt
            or "Appendix" in txt
            or "CONTENTS" in txt
        ):
            continue

        tables = page.extract_tables()
        if not tables:
            continue

        for table in tables:
            for raw_row in table:
                if not raw_row or not any(raw_row):
                    continue
                if (
                    raw_row[0] is None
                    and len(raw_row) > 1
                    and clean_str(raw_row[1])
                    and (
                        clean_str(raw_row[1]).isdigit()
                        or clean_str(raw_row[1]) in ("Sl.No", "Sl. No", "Sl No")
                    )
                ):
                    row = raw_row[1:]
                else:
                    row = raw_row

                if not row or len(row) < 2:
                    continue

                col0 = clean_str(row[0])
                col1 = clean_str(row[1])

                if col0 in ("Sl.No", "Sl. No", "Sl No") or (col1 and "Project Name" in col1):
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
    log.info("Parsed Newly Added table: %d rows from %s", len(df), source_doc)
    return df


def parse_flash_report(pdf_path: Path | str, source_month: str) -> dict[str, Any]:
    """Parse a Flash Report PDF into ongoing, completed, and newly added tables, plus Table 1 summary."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Flash report not found: {path}")

    log.info("Opening %s for month %s", path.name, source_month)
    with pdfplumber.open(path) as doc:
        t1_summary = parse_table_1_summary(doc)
        df_ongoing = parse_ongoing_table(doc, source_month=source_month, source_doc=path.name)
        df_completed = parse_table_3(doc, source_month=source_month, source_doc=path.name)
        df_newly_added = parse_table_4(doc, source_month=source_month, source_doc=path.name)

    return {
        "ongoing": df_ongoing,
        "completed": df_completed,
        "newly_added": df_newly_added,
        "table1_summary": t1_summary,
    }
