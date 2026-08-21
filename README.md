# DA-10 — A/B Testing & Experiment Analytics

Portfolio-grade experimentation analytics using the public **Cookie Cats** A/B test dataset.

## Business question

Should the in-game gate remain at level 30 or move to level 40 if the decision is based on observed player retention rather than a single unadjusted p-value?

DA-10 treats `gate_30` as control and `gate_40` as treatment and focuses on defensible experiment interpretation.

## What the project analyzes

- experiment-unit uniqueness and assignment balance
- 1-day and 7-day retention rates
- absolute lift in percentage points
- relative lift versus control
- 95% confidence intervals for the risk difference
- two-sided two-proportion z-tests
- Holm correction across the two retention endpoints
- approximate realized-sample 80%-power sensitivity / MDE diagnostic
- `sum_gamerounds` distribution diagnostics
- Mann-Whitney U as a secondary exploratory distribution test
- executive recommendation tied to 7-day retention

## Data

The public file contains **90,189 players** with player-level assignment and outcomes:

- `userid`
- `version`: `gate_30` / `gate_40`
- `sum_gamerounds`
- `retention_1`
- `retention_7`

See [DATA_SOURCE.md](DATA_SOURCE.md) for provenance limitations and [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for metric definitions.

Raw data is downloaded at runtime and excluded from version control:

```bash
python -m src.download_data
```

## Run locally

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.download_data
python -m src.run_analysis
```

## Outputs

- `assignment_balance.csv`
- `retention_inference.csv`
- `engagement_diagnostics.csv`
- `engagement_test.csv`
- `executive_summary.csv`

## Statistical design

For each retention endpoint, the pipeline estimates the treatment-control risk difference and its 95% confidence interval. The null hypothesis is tested with a pooled two-proportion z-test.

Because both `retention_1` and `retention_7` are examined, raw p-values are also corrected using the Holm procedure to control family-wise error. The executive decision uses 7-day retention as the primary business outcome rather than cherry-picking whichever endpoint produces the smallest p-value.

The project reports an approximate absolute MDE / sensitivity diagnostic at 80% power for the **realized sample size** under a large-sample normal approximation. This is useful context for interpreting a null result, but it is explicitly **not** presented as a substitute for a pre-experiment power and sample-size plan.

## Engagement diagnostic

`sum_gamerounds` is highly skewed, so the project reports mean, median, p95, and maximum by arm and uses a Mann-Whitney U test as a **secondary exploratory distribution test**. The test can detect distributional differences, but it should not be described as a direct test of the mean or median treatment effect. It is not treated as a revenue metric and does not override the retention decision rule.

## Decision rule

The executive layer is directional and symmetric:

- significant positive `gate_40 - gate_30` effect on 7-day retention → evidence favors `gate_40`
- significant negative effect → evidence favors keeping `gate_30`
- otherwise → no statistically robust evidence to prefer either gate under the Holm-adjusted rule

This avoids a one-sided implementation bug in which only a significant negative treatment effect could generate a positive recommendation for the control.

## Analytical boundaries

This public educational dataset does not independently prove production randomization quality, exposure logging, instrumentation correctness, or generalizability to future game populations. The repository therefore avoids claims about revenue, LTV, churn causality, or arbitrary exploratory subgroup effects.

## Engineering quality

GitHub Actions:

1. installs pinned dependencies,
2. runs unit tests,
3. downloads the public Cookie Cats CSV,
4. runs the complete experiment pipeline,
5. validates the expected **90,189 experiment units** and all deliverables.

Tests cover experiment-unit uniqueness, assignment reconciliation, inference direction, confidence interval fields, Holm correction against a known example, invalid p-value rejection, the 7-day-retention decision rule, and both directions of statistically significant recommendations.

## Portfolio signal

DA-10 demonstrates experiment analysis as a decision system rather than a p-value exercise: data integrity, treatment orientation, uncertainty, multiplicity, practical sensitivity, skewed secondary metrics, reproducible acquisition, and CI-backed validation.
