from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm, mannwhitneyu

CONTROL = "gate_30"
TREATMENT = "gate_40"
EXPECTED_COLUMNS = {"userid", "version", "sum_gamerounds", "retention_1", "retention_7"}


@dataclass(frozen=True)
class ProportionResult:
    metric: str
    control_n: int
    treatment_n: int
    control_rate: float
    treatment_rate: float
    absolute_lift_pp: float
    relative_lift_pct: float
    ci_low_pp: float
    ci_high_pp: float
    z_statistic: float
    p_value: float
    mde_pp_80_power: float


def clean_experiment_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    missing = sorted(EXPECTED_COLUMNS.difference(out.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if out["userid"].isna().any():
        raise ValueError("userid contains missing values")
    if out["userid"].duplicated().any():
        raise ValueError("userid must be unique at experiment-unit grain")

    versions = set(out["version"].dropna().unique())
    if versions != {CONTROL, TREATMENT}:
        raise ValueError(f"Expected exactly {CONTROL} and {TREATMENT}; got {sorted(versions)}")

    for col in ["retention_1", "retention_7"]:
        if out[col].dtype != bool:
            normalized = out[col].astype(str).str.strip().str.lower().map({"true": True, "false": False, "1": True, "0": False})
            if normalized.isna().any():
                raise ValueError(f"{col} contains non-binary values")
            out[col] = normalized.astype(bool)

    out["sum_gamerounds"] = pd.to_numeric(out["sum_gamerounds"], errors="coerce")
    if out["sum_gamerounds"].isna().any() or (out["sum_gamerounds"] < 0).any():
        raise ValueError("sum_gamerounds must be non-negative numeric data")
    return out


def assignment_balance(df: pd.DataFrame) -> pd.DataFrame:
    x = clean_experiment_data(df)
    counts = x["version"].value_counts().reindex([CONTROL, TREATMENT])
    total = counts.sum()
    return pd.DataFrame({
        "version": counts.index,
        "players": counts.values,
        "allocation_pct": 100 * counts.values / total,
    })


def _two_proportion_result(df: pd.DataFrame, metric: str) -> ProportionResult:
    x = clean_experiment_data(df)
    control = x.loc[x["version"] == CONTROL, metric].astype(int)
    treatment = x.loc[x["version"] == TREATMENT, metric].astype(int)
    n_c, n_t = len(control), len(treatment)
    c_success, t_success = int(control.sum()), int(treatment.sum())
    p_c, p_t = c_success / n_c, t_success / n_t
    diff = p_t - p_c

    # Unpooled Wald CI for the risk difference.
    se_diff = math.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    z975 = norm.ppf(0.975)
    ci_low = diff - z975 * se_diff
    ci_high = diff + z975 * se_diff

    # Pooled standard error for the null H0: p_t == p_c.
    pooled = (c_success + t_success) / (n_c + n_t)
    se_null = math.sqrt(pooled * (1 - pooled) * (1 / n_c + 1 / n_t))
    z_stat = diff / se_null if se_null > 0 else 0.0
    p_value = 2 * norm.sf(abs(z_stat))

    relative = 100 * diff / p_c if p_c > 0 else np.nan

    # Approximate absolute MDE for 80% power, two-sided alpha=.05 around pooled baseline.
    z_alpha = norm.ppf(1 - 0.05 / 2)
    z_beta = norm.ppf(0.80)
    mde = (z_alpha + z_beta) * math.sqrt(pooled * (1 - pooled) * (1 / n_c + 1 / n_t))

    return ProportionResult(
        metric=metric,
        control_n=n_c,
        treatment_n=n_t,
        control_rate=p_c,
        treatment_rate=p_t,
        absolute_lift_pp=100 * diff,
        relative_lift_pct=relative,
        ci_low_pp=100 * ci_low,
        ci_high_pp=100 * ci_high,
        z_statistic=z_stat,
        p_value=p_value,
        mde_pp_80_power=100 * mde,
    )


def holm_adjust(p_values: list[float]) -> list[float]:
    m = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(m, dtype=float)
    running_max = 0.0
    for rank, idx in enumerate(order):
        value = min(1.0, (m - rank) * p_values[idx])
        running_max = max(running_max, value)
        adjusted[idx] = running_max
    return adjusted.tolist()


def retention_analysis(df: pd.DataFrame) -> pd.DataFrame:
    results = [_two_proportion_result(df, "retention_1"), _two_proportion_result(df, "retention_7")]
    adjusted = holm_adjust([r.p_value for r in results])
    rows = []
    for r, p_adj in zip(results, adjusted):
        rows.append({
            "metric": r.metric,
            "control_n": r.control_n,
            "treatment_n": r.treatment_n,
            "control_rate_pct": 100 * r.control_rate,
            "treatment_rate_pct": 100 * r.treatment_rate,
            "absolute_lift_pp": r.absolute_lift_pp,
            "relative_lift_pct": r.relative_lift_pct,
            "ci_low_pp": r.ci_low_pp,
            "ci_high_pp": r.ci_high_pp,
            "z_statistic": r.z_statistic,
            "p_value": r.p_value,
            "holm_adjusted_p_value": p_adj,
            "mde_pp_80_power": r.mde_pp_80_power,
            "significant_05_after_holm": p_adj < 0.05,
        })
    return pd.DataFrame(rows)


def engagement_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    x = clean_experiment_data(df)
    rows = []
    for arm in [CONTROL, TREATMENT]:
        s = x.loc[x["version"] == arm, "sum_gamerounds"]
        rows.append({
            "version": arm,
            "players": len(s),
            "mean_gamerounds": float(s.mean()),
            "median_gamerounds": float(s.median()),
            "p95_gamerounds": float(s.quantile(0.95)),
            "max_gamerounds": float(s.max()),
        })
    return pd.DataFrame(rows)


def engagement_test(df: pd.DataFrame) -> pd.DataFrame:
    x = clean_experiment_data(df)
    c = x.loc[x["version"] == CONTROL, "sum_gamerounds"]
    t = x.loc[x["version"] == TREATMENT, "sum_gamerounds"]
    stat, p = mannwhitneyu(t, c, alternative="two-sided")
    return pd.DataFrame([{
        "metric": "sum_gamerounds",
        "test": "Mann-Whitney U",
        "u_statistic": float(stat),
        "p_value": float(p),
        "note": "Secondary exploratory diagnostic; distribution is highly skewed and this is not a revenue metric.",
    }])


def executive_summary(df: pd.DataFrame) -> pd.DataFrame:
    ret = retention_analysis(df)
    r7 = ret.loc[ret["metric"] == "retention_7"].iloc[0]
    recommendation = (
        "Evidence favors keeping gate_30 for 7-day retention."
        if r7["absolute_lift_pp"] < 0 and r7["holm_adjusted_p_value"] < 0.05
        else "No statistically robust evidence to prefer gate_40 on 7-day retention."
    )
    return pd.DataFrame([{
        "players": len(clean_experiment_data(df)),
        "primary_decision_metric": "retention_7",
        "treatment_minus_control_pp": r7["absolute_lift_pp"],
        "holm_adjusted_p_value": r7["holm_adjusted_p_value"],
        "decision": recommendation,
    }])
