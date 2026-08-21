# Data Source & Provenance

## Dataset

DA-10 uses the public **Cookie Cats A/B test** dataset, a widely used educational experiment dataset originating from the DataCamp Cookie Cats project and mirrored publicly on GitHub.

- Experiment unit: one player (`userid`)
- Treatment assignment: `version` (`gate_30` vs `gate_40`)
- Engagement measure: `sum_gamerounds`
- Binary outcomes: `retention_1`, `retention_7`
- Public mirror used for reproducible acquisition: `yufung/ab-testing-cookie-cats`

The raw CSV is downloaded at runtime and is not committed to this repository.

## Experiment context

Cookie Cats is a mobile puzzle game. The experiment compares moving an in-game gate from level 30 to level 40. The dataset exposes player-level randomized assignment and downstream engagement/retention outcomes.

## Claim boundaries

This repository treats the file as a **public experiment dataset**, but it does not independently verify the original production instrumentation, randomization implementation, traffic allocation system, exposure logging, or dataset license beyond its public educational distribution.

Therefore the project can defensibly analyze:

- observed group sizes and assignment balance
- 1-day and 7-day retention differences
- absolute and relative lift
- confidence intervals and hypothesis tests
- multiplicity-adjusted inference across the two retention endpoints
- practical significance and approximate minimum detectable effect
- `sum_gamerounds` as a secondary engagement diagnostic

It does **not** claim:

- that the experiment is currently live
- that assignment was perfectly randomized beyond what can be checked from the file
- causal effects on revenue, LTV, monetization, or churn
- generalization to all players, geographies, or future game versions without further evidence
- that exploratory segment slicing would be causal without pre-registration

## Reproducible acquisition

Run:

```bash
python -m src.download_data
```

The script downloads the public CSV mirror into `data/raw/cookie_cats.csv`.
