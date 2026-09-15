"""Leakage discipline is enforced by tests (ANTIGRAVITY.md §2, docs/05 §Leakage).

Every feature/label function MUST get a test here asserting it reads no report_month
later than the prediction cutoff T. This placeholder documents the contract; replace
with real tests as features/labels are implemented (STEP_06, STEP_07)."""

import pytest


@pytest.mark.skip(reason="Replace with real leakage tests at STEP_06/07")
def test_feature_reads_no_future_month():
    # given a panel with months up to T and beyond, a feature computed at T
    # must be identical whether or not months > T are present in the input.
    ...
