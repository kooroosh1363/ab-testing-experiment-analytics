import pandas as pd
import pytest

from src.analytics import (
    assignment_balance,
    clean_experiment_data,
    executive_summary,
    holm_adjust,
    retention_analysis,
)


def fixture() -> pd.DataFrame:
    return pd.DataFrame({
        "userid": range(1, 13),
        "version": ["gate_30"] * 6 + ["gate_40"] * 6,
        "sum_gamerounds": [10, 20, 5, 40, 12, 8, 11, 19, 4, 28, 9, 7],
        "retention_1": [True, True, False, True, False, True, True, False, False, True, False, False],
        "retention_7": [True, False, False, True, False, True, False, False, False, True, False, False],
    })


def test_clean_data_preserves_experiment_unit_grain():
    out = clean_experiment_data(fixture())
    assert len(out) == 12
    assert out["userid"].is_unique
    assert set(out["version"]) == {"gate_30", "gate_40"}


def test_duplicate_user_is_rejected():
    df = fixture()
    df.loc[11, "userid"] = 1
    with pytest.raises(ValueError, match="unique"):
        clean_experiment_data(df)


def test_assignment_balance_reconciles_population():
    out = assignment_balance(fixture())
    assert out["players"].sum() == 12
    assert round(out["allocation_pct"].sum(), 8) == 100


def test_retention_analysis_preserves_direction_and_ci_fields():
    out = retention_analysis(fixture()).set_index("metric")
    assert set(out.index) == {"retention_1", "retention_7"}
    assert out.loc["retention_7", "absolute_lift_pp"] < 0
    assert out["p_value"].between(0, 1).all()
    assert out["holm_adjusted_p_value"].between(0, 1).all()
    assert (out["ci_low_pp"] <= out["ci_high_pp"]).all()


def test_holm_adjustment_is_monotone_and_not_smaller_than_raw():
    raw = [0.01, 0.04, 0.20]
    adj = holm_adjust(raw)
    assert all(a >= p for a, p in zip(adj, raw))
    assert all(0 <= a <= 1 for a in adj)


def test_executive_summary_uses_seven_day_retention_as_decision_metric():
    out = executive_summary(fixture()).iloc[0]
    assert out["players"] == 12
    assert out["primary_decision_metric"] == "retention_7"
