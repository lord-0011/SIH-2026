"""Pure validation rules for project records.

Governed by docs/04_DATA_SCHEMA.md §Validation rules table and ANTIGRAVITY.md.
Never silently deletes records. Distinguishes known reporting artifacts
(cost_revised_down, exp_exceeds_cost) from data errors.
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class ValidationIssue:
    flag: str  # e.g. 'progress_out_of_range', 'negative_value', 'date_inconsistency', 'cost_revised_down', 'exp_exceeds_cost'
    reason: str  # human-readable detailed explanation
    column: str | None = None
    value: Any = None


def parse_date_mmyyyy(val: Any) -> tuple[int, int] | None:
    """Parse date strings like 'MM/YYYY', '(MM/YYYY)', 'YYYY-MM' into (year, month).

    Returns None for missing/NA/placeholder strings.
    """
    if val is None or pd.isna(val):
        return None
    s = str(val).strip().strip("()-")
    if not s or s.upper() in ("NA", "N/A", "-", "N.A.", "NONE", "NULL"):
        return None

    # Try MM/YYYY
    parts = s.split("/")
    if len(parts) == 2:
        try:
            m, y = int(parts[0]), int(parts[1])
            if 1 <= m <= 12:
                return (y, m)
        except ValueError:
            return None

    # Try YYYY-MM
    parts = s.split("-")
    if len(parts) == 2:
        try:
            y, m = int(parts[0]), int(parts[1])
            if 1 <= m <= 12:
                return (y, m)
        except ValueError:
            return None

    return None


def validate_progress_range(record: dict | pd.Series) -> list[ValidationIssue]:
    """Flag physical_progress_pct outside [0.0, 100.0]."""
    issues = []
    val = record.get("physical_progress_pct")
    if val is not None and not pd.isna(val):
        try:
            num = float(val)
            if num < 0.0 or num > 100.0:
                issues.append(
                    ValidationIssue(
                        flag="progress_out_of_range",
                        reason=f"physical_progress_pct ({num}%) is outside valid range [0.0, 100.0]",
                        column="physical_progress_pct",
                        value=num,
                    )
                )
        except (ValueError, TypeError):
            issues.append(
                ValidationIssue(
                    flag="progress_out_of_range",
                    reason=f"physical_progress_pct ({val}) cannot be parsed as float",
                    column="physical_progress_pct",
                    value=val,
                )
            )
    return issues


def validate_non_negative(record: dict | pd.Series) -> list[ValidationIssue]:
    """Flag negative values in cost, expenditure, or progress."""
    issues = []
    numeric_cols = [
        "original_cost_cr",
        "revised_cost_cr",
        "cumulative_expenditure_cr",
        "physical_progress_pct",
    ]
    for col in numeric_cols:
        val = record.get(col)
        if val is not None and not pd.isna(val):
            try:
                num = float(val)
                if num < 0.0:
                    issues.append(
                        ValidationIssue(
                            flag="negative_value",
                            reason=f"{col} has negative value ({num})",
                            column=col,
                            value=num,
                        )
                    )
            except (ValueError, TypeError):
                pass
    return issues


def validate_dates(record: dict | pd.Series) -> list[ValidationIssue]:
    """Flag chronological date inconsistencies and sentinel dates."""
    issues = []
    approval_str = record.get("date_of_approval")
    start_str = record.get("start_date")
    orig_comp_str = record.get("original_completion_date")
    rev_comp_str = record.get("revised_completion_date")
    act_comp_str = record.get("actual_completion_date")

    d_app = parse_date_mmyyyy(approval_str)
    d_start = parse_date_mmyyyy(start_str)
    d_orig = parse_date_mmyyyy(orig_comp_str)
    d_rev = parse_date_mmyyyy(rev_comp_str)
    d_act = parse_date_mmyyyy(act_comp_str)

    # Check sentinel dates (e.g. year 1900 or uninitialized)
    for col, dt_tuple, raw_s in [
        ("date_of_approval", d_app, approval_str),
        ("start_date", d_start, start_str),
        ("original_completion_date", d_orig, orig_comp_str),
        ("revised_completion_date", d_rev, rev_comp_str),
        ("actual_completion_date", d_act, act_comp_str),
    ]:
        if dt_tuple is not None and dt_tuple[0] < 1970:
            issues.append(
                ValidationIssue(
                    flag="date_inconsistency",
                    reason=f"{col} has sentinel/uninitialized year ({raw_s})",
                    column=col,
                    value=raw_s,
                )
            )

    # 1. start_date before date_of_approval
    if d_start and d_app and d_start < d_app:
        issues.append(
            ValidationIssue(
                flag="date_inconsistency",
                reason=(f"start_date ({start_str}) is before date_of_approval ({approval_str})"),
                column="start_date",
                value=f"{start_str} < {approval_str}",
            )
        )

    # 2. revised_completion_date before original_completion_date
    if d_rev and d_orig and d_rev < d_orig:
        issues.append(
            ValidationIssue(
                flag="date_inconsistency",
                reason=(
                    f"revised_completion_date ({rev_comp_str}) is before "
                    f"original_completion_date ({orig_comp_str})"
                ),
                column="revised_completion_date",
                value=f"{rev_comp_str} < {orig_comp_str}",
            )
        )

    # 3. original_completion_date before start_date
    if d_orig and d_start and d_orig < d_start:
        issues.append(
            ValidationIssue(
                flag="date_inconsistency",
                reason=(
                    f"original_completion_date ({orig_comp_str}) is before start_date ({start_str})"
                ),
                column="original_completion_date",
                value=f"{orig_comp_str} < {start_str}",
            )
        )

    # 4. original_completion_date before date_of_approval
    if d_orig and d_app and d_orig < d_app:
        issues.append(
            ValidationIssue(
                flag="date_inconsistency",
                reason=(
                    f"original_completion_date ({orig_comp_str}) is before date_of_approval ({approval_str})"
                ),
                column="original_completion_date",
                value=f"{orig_comp_str} < {approval_str}",
            )
        )

    # 5. actual_completion_date before start_date
    if d_act and d_start and d_act < d_start:
        issues.append(
            ValidationIssue(
                flag="date_inconsistency",
                reason=(
                    f"actual_completion_date ({act_comp_str}) is before start_date ({start_str})"
                ),
                column="actual_completion_date",
                value=f"{act_comp_str} < {start_str}",
            )
        )

    return issues


def validate_cost_revision(record: dict | pd.Series) -> list[ValidationIssue]:
    """Flag revised_cost < original_cost.

    Note: This is a known reporting artifact (KEEP, not error), e.g. descope or tender savings.
    """
    issues = []
    orig = record.get("original_cost_cr")
    rev = record.get("revised_cost_cr")
    if orig is not None and rev is not None and not pd.isna(orig) and not pd.isna(rev):
        try:
            o_val = float(orig)
            r_val = float(rev)
            if r_val < o_val:
                issues.append(
                    ValidationIssue(
                        flag="cost_revised_down",
                        reason=(
                            f"revised_cost_cr ({r_val} Cr) < original_cost_cr ({o_val} Cr) "
                            "(known reporting artifact; keep record)"
                        ),
                        column="revised_cost_cr",
                        value=r_val,
                    )
                )
        except (ValueError, TypeError):
            pass
    return issues


def validate_expenditure_vs_cost(record: dict | pd.Series) -> list[ValidationIssue]:
    """Flag cumulative_expenditure > revised_cost.

    Note: This is a review flag; expenditure exceeds current sanctioned cost.
    """
    issues = []
    rev = record.get("revised_cost_cr")
    exp = record.get("cumulative_expenditure_cr")
    if rev is not None and exp is not None and not pd.isna(rev) and not pd.isna(exp):
        try:
            r_val = float(rev)
            e_val = float(exp)
            if e_val > r_val:
                issues.append(
                    ValidationIssue(
                        flag="exp_exceeds_cost",
                        reason=(
                            f"cumulative_expenditure_cr ({e_val} Cr) exceeds revised_cost_cr "
                            f"({r_val} Cr) by {round(e_val - r_val, 2)} Cr"
                        ),
                        column="cumulative_expenditure_cr",
                        value=e_val,
                    )
                )
        except (ValueError, TypeError):
            pass
    return issues


def validate_record(record: dict | pd.Series) -> list[ValidationIssue]:
    """Run all validation rules on a single project record."""
    issues: list[ValidationIssue] = []
    issues.extend(validate_progress_range(record))
    issues.extend(validate_non_negative(record))
    issues.extend(validate_dates(record))
    issues.extend(validate_cost_revision(record))
    issues.extend(validate_expenditure_vs_cost(record))
    return issues
