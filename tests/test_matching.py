"""Full 13-Month Real Data Verification Suite for Entity Matching (STEP_03).

Runs locally and in pre-merge verification when data is pulled via DVC.
Skips cleanly in clean CI runners where raw DVC parquets are absent.
"""

import pandas as pd
import pytest

from src.common.config import DATA_INTERIM
from src.common.io import load_dataframe
from src.matching.run import run


@pytest.fixture(scope="module")
def matched_corpus():
    """Load or produce matched datasets across all 13 months."""
    raw_files = sorted(DATA_INTERIM.glob("raw_ongoing_*.parquet"))
    if not raw_files:
        pytest.skip(
            "Raw ongoing parquets not found in data/interim — run 'dvc pull' to fetch data from Google Drive"
        )

    matched_files = sorted(DATA_INTERIM.glob("matched_ongoing_*.parquet"))
    if len(matched_files) < 13:
        run()
        matched_files = sorted(DATA_INTERIM.glob("matched_ongoing_*.parquet"))

    if len(matched_files) < 13:
        pytest.skip("Matched ongoing datasets incomplete — run 'dvc pull'")

    dfs = [load_dataframe(f) for f in matched_files]
    corpus = pd.concat(dfs, ignore_index=True)
    registry = load_dataframe(DATA_INTERIM / "canonical_projects.parquet")
    audit = pd.read_csv(DATA_INTERIM / "matching_audit.csv")

    return {"corpus": corpus, "registry": registry, "audit": audit, "month_dfs": dfs}


def test_exact_code_match_rate_100pct(matched_corpus):
    """Verify that post-fix, 100% of ongoing records receive exact_code canonical IDs."""
    corpus = matched_corpus["corpus"]
    assert len(corpus) == 18601, f"Expected 18,601 ongoing records, got {len(corpus)}"
    assert (
        corpus["match_confidence"] == "exact_code"
    ).all(), "Found non-exact_code matches in ongoing data"
    assert corpus["canonical_project_id"].notna().all(), "Found null canonical_project_ids"
    assert (corpus["canonical_project_id"] != "").all(), "Found empty canonical_project_ids"


def test_corpus_canonical_project_count(matched_corpus):
    """Verify headline count of exactly 2,243 distinct canonical projects."""
    registry = matched_corpus["registry"]
    corpus = matched_corpus["corpus"]
    assert len(registry) == 2243, f"Expected 2,243 canonical projects, got {len(registry)}"
    assert corpus["canonical_project_id"].nunique() == 2243


def test_concurrency_invariant_all_13_months(matched_corpus):
    """Verify concurrency invariant: within the same month, no duplicate canonical_project_ids."""
    for df in matched_corpus["month_dfs"]:
        month = df["report_month"].iloc[0]
        assert len(df) == df["canonical_project_id"].nunique(), (
            f"Concurrency invariant violated in month {month}: {len(df)} records but "
            f"{df['canonical_project_id'].nunique()} unique IDs"
        )


def test_no_merge_of_distinct_project_codes(matched_corpus):
    """Verify no-merge invariant: distinct project_codes never share a canonical_project_id."""
    corpus = matched_corpus["corpus"]
    assert corpus["canonical_project_id"].nunique() == corpus["project_code"].nunique()


def test_zero_cross_month_renames(matched_corpus):
    """Verify zero cross-month renames: (legacy_ocms_code, project_name) -> 1 project_code."""
    corpus = matched_corpus["corpus"]
    valid = corpus[
        corpus["legacy_ocms_code"].notna()
        & (corpus["legacy_ocms_code"] != "")
        & (corpus["legacy_ocms_code"] != "-")
    ].copy()
    valid["norm_name"] = valid["project_name"].str.strip().str.lower()
    mapping = valid.groupby(["legacy_ocms_code", "norm_name"])["project_code"].nunique()
    multi_leg_name = mapping[mapping > 1]
    assert len(multi_leg_name) == 0, f"Cross-month renames found: {multi_leg_name.to_dict()}"


def test_umbrella_legacy_code_counts_reconciled(matched_corpus):
    """Verify reconciliation of 26 single-month vs 30 corpus-wide umbrella legacy codes."""
    corpus = matched_corpus["corpus"]

    # 1. Single-month concurrency: exactly 26
    single_month_umbrellas = set()
    for _, group in corpus.groupby("report_month"):
        valid = group[group["legacy_ocms_code"].notna() & (group["legacy_ocms_code"] != "")]
        counts = valid.groupby("legacy_ocms_code")["project_code"].nunique()
        single_month_umbrellas.update(counts[counts > 1].index)
    assert (
        len(single_month_umbrellas) == 26
    ), f"Expected 26 single-month umbrellas, got {len(single_month_umbrellas)}"

    # 2. Corpus-wide pooled 13 months: exactly 30
    valid_all = corpus[corpus["legacy_ocms_code"].notna() & (corpus["legacy_ocms_code"] != "")]
    corpus_counts = valid_all.groupby("legacy_ocms_code")["project_code"].nunique()
    corpus_umbrellas = set(corpus_counts[corpus_counts > 1].index)
    assert (
        len(corpus_umbrellas) == 30
    ), f"Expected 30 corpus-wide umbrellas, got {len(corpus_umbrellas)}"

    # 3. The 4 swap codes
    swap_diff = corpus_umbrellas - single_month_umbrellas
    expected_swaps = {"N12000133", "N12000134", "N12000135", "N22000602"}
    assert swap_diff == expected_swaps, f"Expected swap codes {expected_swaps}, got {swap_diff}"


def test_mid_window_arrivals_and_trajectory_anchoring(matched_corpus):
    """Verify all 1,341 mid-window arrivals (1,187 MoRTH + 154 other) have trajectory anchor dates."""
    registry = matched_corpus["registry"]

    mid_window = registry[registry["is_mid_window_arrival"]]
    assert len(mid_window) == 1341, f"Expected 1,341 mid-window arrivals, got {len(mid_window)}"

    morth_mid = registry[registry["is_morth_onboarded_mid_window"]]
    assert len(morth_mid) == 1187, f"Expected 1,187 MoRTH mid-window arrivals, got {len(morth_mid)}"

    non_morth_mid = registry[
        registry["is_mid_window_arrival"] & ~registry["is_morth_onboarded_mid_window"]
    ]
    assert (
        len(non_morth_mid) == 154
    ), f"Expected 154 non-MoRTH mid-window arrivals, got {len(non_morth_mid)}"

    # Trajectory anchor dates must be populated for ALL 1,341 mid-window arrivals
    assert (
        mid_window["trajectory_anchor_date"].notna().all()
    ), "Found missing trajectory_anchor_date among mid-window arrivals!"
    assert (mid_window["trajectory_anchor_date"] != "").all(), "Found empty trajectory_anchor_date"
    assert (mid_window["trajectory_anchor_date"] != "-").all(), "Found '-' trajectory_anchor_date"
