"""Deterministic fixture-based tests for data validation rules (STEP_02).

Exercises split date rules (date_impossible, start_before_approval, schedule_advanced)
and cost revision categories (implausible_cost_revision vs cost_revised_down)
on committed test fixtures to guard against silent regressions in CI.
"""

from src.validation.rules import (
    validate_cost_revision,
    validate_dates,
    validate_non_negative,
    validate_record,
)

FIXTURE_PROJECTS = {
    # 1. Clean compliant project
    "clean_baseline": {
        "project_code": "P_CLEAN",
        "project_name": "Compliant Bridge Construction",
        "date_of_approval": "01/2021",
        "start_date": "06/2021",
        "original_completion_date": "12/2024",
        "revised_completion_date": "12/2025",
        "original_cost_cr": 500.0,
        "revised_cost_cr": 550.0,
        "cumulative_expenditure_cr": 250.0,
        "physical_progress_pct": 50.0,
    },
    # 2. Schedule acceleration (revised completion earlier than original) -> signal
    "schedule_acceleration": {
        "project_code": "P_ACCEL",
        "project_name": "Rapid Expressway Package",
        "date_of_approval": "01/2020",
        "start_date": "03/2020",
        "original_completion_date": "12/2024",
        "revised_completion_date": "06/2024",  # 6 months early
        "original_cost_cr": 1000.0,
        "revised_cost_cr": 1000.0,
        "cumulative_expenditure_cr": 800.0,
        "physical_progress_pct": 90.0,
    },
    # 3. Administrative convention (work started before formal approval)
    "start_before_approval": {
        "project_code": "P_EARLY_START",
        "project_name": "Emergency Flood Restoration Rail",
        "date_of_approval": "06/2021",  # formal sanction after work start
        "start_date": "01/2021",
        "original_completion_date": "12/2023",
        "revised_completion_date": "12/2023",
        "original_cost_cr": 150.0,
        "revised_cost_cr": 150.0,
        "cumulative_expenditure_cr": 100.0,
        "physical_progress_pct": 75.0,
    },
    # 4. Physically impossible chronology (completion before start)
    "impossible_date_completion_before_start": {
        "project_code": "P_IMP_1",
        "project_name": "Time Machine Tunnel",
        "date_of_approval": "01/2020",
        "start_date": "06/2023",
        "original_completion_date": "01/2022",  # impossible
        "revised_completion_date": None,
        "original_cost_cr": 200.0,
        "revised_cost_cr": 200.0,
        "cumulative_expenditure_cr": 10.0,
        "physical_progress_pct": 5.0,
    },
    # 5. Sentinel year 1900 (uninitialized Excel epoch)
    "sentinel_date_1900": {
        "project_code": "P_SENTINEL",
        "project_name": "Establishment of new GMC Saran",
        "date_of_approval": "03/2019",
        "start_date": "01/1900",  # sentinel
        "original_completion_date": "01/1900",
        "revised_completion_date": None,
        "original_cost_cr": 300.0,
        "revised_cost_cr": 300.0,
        "cumulative_expenditure_cr": 50.0,
        "physical_progress_pct": 10.0,
    },
    # 6. Extreme downward revision (>90% drop, e.g. project 618886)
    "implausible_crash_revision": {
        "project_code": "618886",
        "project_name": "Road Safety Improvement of Critical Junctions",
        "date_of_approval": "02/2022",
        "start_date": "08/2022",
        "original_completion_date": "08/2024",
        "revised_completion_date": "10/2026",
        "original_cost_cr": 238.66,
        "revised_cost_cr": 0.10,  # 99.96% drop artifact
        "cumulative_expenditure_cr": 42.08,
        "physical_progress_pct": 80.0,
    },
    # 7. Legitimate descoping (e.g. 5% reduction)
    "legitimate_descope": {
        "project_code": "P_DESCOPE",
        "project_name": "Port Wharf Facility (Descoped Crane Bay)",
        "date_of_approval": "04/2020",
        "start_date": "10/2020",
        "original_completion_date": "10/2023",
        "revised_completion_date": "10/2023",
        "original_cost_cr": 500.0,
        "revised_cost_cr": 475.0,  # 5% downward revision
        "cumulative_expenditure_cr": 400.0,
        "physical_progress_pct": 95.0,
    },
    # 8. Negative expenditure anomaly (e.g. Jan 2026 MoRTH project 619065)
    "negative_expenditure": {
        "project_code": "619065",
        "project_name": "4L Expressway from Km 26.400 to km 53.500 of Malur",
        "date_of_approval": "01/2021",
        "start_date": "05/2021",
        "original_completion_date": "05/2024",
        "revised_completion_date": "12/2025",
        "original_cost_cr": 1200.0,
        "revised_cost_cr": 1200.0,
        "cumulative_expenditure_cr": -54.57,  # negative expenditure anomaly
        "physical_progress_pct": 60.0,
    },
}


def test_clean_baseline_fixture():
    """Verify clean project generates zero flags."""
    issues = validate_record(FIXTURE_PROJECTS["clean_baseline"])
    assert len(issues) == 0


def test_schedule_acceleration_is_signal_not_defect():
    """Verify revised < original completion generates schedule_advanced and NOT date_impossible."""
    issues = validate_dates(FIXTURE_PROJECTS["schedule_acceleration"])
    flags = [i.flag for i in issues]
    assert flags == ["schedule_advanced"]
    assert "date_impossible" not in flags
    assert "date_inconsistency" not in flags


def test_start_before_approval_is_distinct_convention():
    """Verify start < approval generates start_before_approval and NOT date_impossible."""
    issues = validate_dates(FIXTURE_PROJECTS["start_before_approval"])
    flags = [i.flag for i in issues]
    assert flags == ["start_before_approval"]
    assert "date_impossible" not in flags


def test_impossible_dates_flag_date_impossible():
    """Verify chronological impossibilities and sentinel dates generate date_impossible."""
    issues1 = validate_dates(FIXTURE_PROJECTS["impossible_date_completion_before_start"])
    assert any(i.flag == "date_impossible" for i in issues1)

    issues2 = validate_dates(FIXTURE_PROJECTS["sentinel_date_1900"])
    assert any(i.flag == "date_impossible" and "sentinel" in i.reason for i in issues2)


def test_implausible_cost_revision_vs_standard_descope():
    """Verify >90% drop triggers implausible_cost_revision while 5% drop triggers cost_revised_down."""
    # Extreme drop (238.66 -> 0.10)
    crash_issues = validate_cost_revision(FIXTURE_PROJECTS["implausible_crash_revision"])
    crash_flags = [i.flag for i in crash_issues]
    assert crash_flags == ["implausible_cost_revision"]
    assert "cost_revised_down" not in crash_flags

    # Legitimate descope (500 -> 475)
    descope_issues = validate_cost_revision(FIXTURE_PROJECTS["legitimate_descope"])
    descope_flags = [i.flag for i in descope_issues]
    assert descope_flags == ["cost_revised_down"]
    assert "implausible_cost_revision" not in descope_flags


def test_negative_expenditure_fixture():
    """Verify negative expenditure triggers negative_value."""
    issues = validate_non_negative(FIXTURE_PROJECTS["negative_expenditure"])
    flags = [i.flag for i in issues]
    assert "negative_value" in flags
    assert any(i.column == "cumulative_expenditure_cr" and i.value == -54.57 for i in issues)


def test_project_618886_combined_flags():
    """Verify project 618886 triggers both implausible_cost_revision and exp_exceeds_cost."""
    issues = validate_record(FIXTURE_PROJECTS["implausible_crash_revision"])
    flags = {i.flag for i in issues}
    assert flags == {"implausible_cost_revision", "exp_exceeds_cost"}
