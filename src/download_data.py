from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SOURCE_URL = "https://raw.githubusercontent.com/yufung/ab-testing-cookie-cats/master/data/cookie_cats.csv"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    request = Request(SOURCE_URL, headers={"User-Agent": "DA-10-experiment-analytics/1.0"})
    with urlopen(request, timeout=60) as response:
        content = response.read()
    out = RAW / "cookie_cats.csv"
    out.write_bytes(content)
    print(f"Saved {len(content):,} bytes to {out}")


if __name__ == "__main__":
    main()
