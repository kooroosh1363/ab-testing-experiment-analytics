# Data Dictionary

| Column | Meaning | Analytical role |
|---|---|---|
| `userid` | Player identifier | Experiment unit / uniqueness check |
| `version` | Assigned experiment arm: `gate_30` or `gate_40` | Treatment assignment |
| `sum_gamerounds` | Number of game rounds played during the observed period | Secondary engagement diagnostic |
| `retention_1` | Whether the player returned one day after installation | Primary retention endpoint |
| `retention_7` | Whether the player returned seven days after installation | Longer-term retention endpoint |

## Derived fields and metrics

- `n`: number of players in an experiment arm
- `retained`: number of players with a positive binary retention outcome
- `retention_rate`: retained / n
- `absolute_lift_pp`: treatment rate minus control rate, in percentage points
- `relative_lift_pct`: relative change versus control
- `risk_difference_ci`: confidence interval for the treatment-control retention difference
- `z_statistic`, `p_value`: two-sided two-proportion z-test statistics
- `holm_adjusted_p_value`: family-wise-error controlled p-value across the two retention endpoints
- `mde_pp_80_power`: approximate detectable absolute retention difference at 80% power and alpha 0.05 for the observed sample sizes

## Experiment orientation

The repository uses `gate_30` as **control** and `gate_40` as **treatment** because the experiment question is whether moving the gate later improves outcomes.
