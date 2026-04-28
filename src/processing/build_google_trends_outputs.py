"""Build Track C state-level Google Trends outputs.

The script tries to collect real state-level Google Trends interest with
pytrends. It writes raw per-term exports into data/raw/google_trends and the app
schema into data/processed/google_trends_state_level.csv. If collection fails,
it falls back to the labeled demo table from build_fallback_data.py.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import time

import pandas as pd
from pytrends.request import TrendReq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.processing.build_fallback_data import EVENT_WINDOWS, PROCESSED_DIR, build_google_trends


RAW_TRENDS_DIR = PROJECT_ROOT / "data" / "raw" / "google_trends"

SEARCH_TERMS = ["GameStop", "AMC stock", "WallStreetBets", "BBBY stock"]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def collect_one(pytrends: TrendReq, term: str, window: str, start: str, end: str) -> pd.DataFrame:
    timeframe = f"{start} {end}"
    pytrends.build_payload([term], cat=0, timeframe=timeframe, geo="US", gprop="")
    raw = pytrends.interest_by_region(resolution="REGION", inc_low_vol=True, inc_geo_code=True)
    if raw.empty or term not in raw.columns:
        return pd.DataFrame()
    raw = raw.reset_index().rename(columns={"geoName": "state"})
    raw["state_code"] = raw["geoCode"].astype(str).str.replace("US-", "", regex=False)
    raw["interest"] = pd.to_numeric(raw[term], errors="coerce").fillna(0).round().astype(int)
    raw["window"] = window
    raw["term"] = term
    raw_export = raw[["window", "term", "state", "state_code", "interest"]].copy()
    return raw_export


def load_cached_exports() -> pd.DataFrame:
    frames = []
    for path in RAW_TRENDS_DIR.glob("pytrends_*.csv"):
        try:
            frame = pd.read_csv(path)
        except Exception as exc:
            print(f"Skipping cached Trends file {path.name}: {type(exc).__name__}: {exc}")
            continue
        required = {"window", "term", "state", "state_code", "interest"}
        if required.issubset(frame.columns):
            frames.append(frame[list(required)])
    if not frames:
        return pd.DataFrame(columns=["window", "term", "state", "state_code", "interest"])
    cached = pd.concat(frames, ignore_index=True)
    cached["interest"] = pd.to_numeric(cached["interest"], errors="coerce").fillna(0).clip(0, 100).astype(int)
    return cached[["window", "term", "state", "state_code", "interest"]].drop_duplicates()


def upsert_data_dictionary(status: str, notes: str) -> None:
    path = PROCESSED_DIR / "data_dictionary.csv"
    if path.exists():
        dictionary = pd.read_csv(path)
    else:
        dictionary = pd.DataFrame(columns=["file", "status", "notes"])
    replacement = pd.DataFrame(
        [
            {
                "file": "google_trends_state_level.csv",
                "status": status,
                "notes": notes,
            }
        ]
    )
    dictionary = dictionary[~dictionary["file"].isin(replacement["file"])]
    dictionary = pd.concat([dictionary, replacement], ignore_index=True)
    dictionary.sort_values("file").to_csv(path, index=False)


def write_fallback(reason: str) -> None:
    cached = load_cached_exports()
    if not cached.empty:
        cached.to_csv(PROCESSED_DIR / "google_trends_state_level.csv", index=False)
        pd.DataFrame(
            [
                {"metric": "data_status", "value": "cached Google Trends API export"},
                {"metric": "rows", "value": len(cached)},
                {"metric": "terms", "value": cached["term"].nunique()},
                {"metric": "windows", "value": cached["window"].nunique()},
                {"metric": "failures", "value": "live collection failed; reused cached raw exports"},
            ]
        ).to_csv(PROCESSED_DIR / "google_trends_collection_summary.csv", index=False)
        upsert_data_dictionary(
            "cached Google Trends API export",
            "Live pytrends collection was rate-limited, so cached raw Google Trends exports were reused.",
        )
        return

    fallback = build_google_trends()
    fallback.to_csv(PROCESSED_DIR / "google_trends_state_level.csv", index=False)
    pd.DataFrame(
        [
            {"metric": "data_status", "value": "fallback fixture"},
            {"metric": "reason", "value": reason},
        ]
    ).to_csv(PROCESSED_DIR / "google_trends_collection_summary.csv", index=False)
    upsert_data_dictionary(
        "fallback fixture",
        f"Google Trends collection failed or was unavailable: {reason}",
    )


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_TRENDS_DIR.mkdir(parents=True, exist_ok=True)
    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 30), retries=2, backoff_factor=0.5)
    rows: list[pd.DataFrame] = []
    failures: list[str] = []

    for window, (start, end) in EVENT_WINDOWS.items():
        for term in SEARCH_TERMS:
            try:
                frame = collect_one(pytrends, term, window, start, end)
                if frame.empty:
                    failures.append(f"{window} / {term}: empty result")
                    continue
                raw_name = f"pytrends_{slugify(window)}_{slugify(term)}.csv"
                frame.to_csv(RAW_TRENDS_DIR / raw_name, index=False)
                rows.append(frame)
                print(f"Collected {window} / {term}: {len(frame):,} rows")
                time.sleep(0.6)
            except Exception as exc:
                failures.append(f"{window} / {term}: {type(exc).__name__}: {exc}")

    if not rows:
        write_fallback("; ".join(failures) or "No Trends rows returned.")
        print("No Google Trends rows collected. Wrote labeled fallback Track C output.")
        return

    trends = pd.concat(rows, ignore_index=True)
    trends = trends.dropna(subset=["state_code", "interest"])
    trends["interest"] = trends["interest"].clip(0, 100).astype(int)
    trends.to_csv(PROCESSED_DIR / "google_trends_state_level.csv", index=False)

    status = "Google Trends API export" if not failures else "partial Google Trends API export"
    notes = (
        "Collected with pytrends by state, term, and event window. "
        "Values are normalized relative search interest."
    )
    if failures:
        notes += f" Collection warnings: {' | '.join(failures[:5])}"
    pd.DataFrame(
        [
            {"metric": "data_status", "value": status},
            {"metric": "rows", "value": len(trends)},
            {"metric": "terms", "value": trends["term"].nunique()},
            {"metric": "windows", "value": trends["window"].nunique()},
            {"metric": "failures", "value": len(failures)},
        ]
    ).to_csv(PROCESSED_DIR / "google_trends_collection_summary.csv", index=False)
    upsert_data_dictionary(status, notes)
    print(f"Wrote Google Trends output: {len(trends):,} rows; failures: {len(failures)}")


if __name__ == "__main__":
    main()
