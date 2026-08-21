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


def strong_treatment_fixture() -> pd.DataFrame:
    n = 200
    return pd.DataFrame({
        "userid": range(1, 2 * n + 1),
        "version": ["gate_30"] * n + ["gate_40"] * n,
        "sum_gamerounds": [10] * (2 * n),
        "retention_1": [True] * 100 + [False] * 100 + [True] * 150 + [False] * 50,
        "retention_7": [True] * 80 + [False] * 120 + [True] * 140 + [False] * 60,
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
    assert (out["mde_pp_80_power"] >= 0).all()


def test_holm_adjustment_matches_known_example_and_rejects_bad_input():
    raw = [0.01, 0.04, 0.20]
    adj = holm_adjust(raw)
    assert adj == pytest.approx([0.03, 0.08, 0.20])
    assert all(a >= p for a, p in zip(adj, raw))
    with pytest.raises(ValueError, match="between 0 and 1"):
        holm_adjust([0.01, 1.2])


def test_executive_summary_uses_seven_day_retention_as_decision_metric():
    out = executive_summary(fixture()).iloc[0]
    assert out["players"] == 12
    assert out["primary_decision_metric"] == "retention_7"


def test_executive_summary_can_favor_treatment_when_effect_is_positive_and_significant():
    out = executive_summary(strong_treatment_fixture()).iloc[0]
    assert out["treatment_minus_control_pp"] > 0
    assert out["holm_adjusted_p_value"] < 0.05
    assert "gate_40" in out["decision"]
