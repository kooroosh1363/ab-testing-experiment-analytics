from pathlib import Path

import pandas as pd

from src.analytics import (
    assignment_balance,
    engagement_diagnostics,
    engagement_test,
    executive_summary,
    retention_analysis,
    sample_ratio_mismatch,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "cookie_cats.csv"
OUT = ROOT / "outputs"


def main() -> None:
    if not RAW.exists():
        raise FileNotFoundError("Raw data missing. Run: python -m src.download_data")
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW)

    assignment_balance(df).to_csv(OUT / "assignment_balance.csv", index=False)
    sample_ratio_mismatch(df).to_csv(OUT / "sample_ratio_mismatch.csv", index=False)
    retention_analysis(df).to_csv(OUT / "retention_inference.csv", index=False)
    engagement_diagnostics(df).to_csv(OUT / "engagement_diagnostics.csv", index=False)
    engagement_test(df).to_csv(OUT / "engagement_test.csv", index=False)
    executive_summary(df).to_csv(OUT / "executive_summary.csv", index=False)

    print("DA-10 experiment analytics completed successfully.")


if __name__ == "__main__":
    main()
