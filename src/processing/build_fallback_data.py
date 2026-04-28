"""Generate clearly labeled fallback processed data for Tracks B and C.

The app reads these CSV schemas directly. Replace the generated outputs with
real Reddit/Kaggle and Google Trends exports once those sources are staged.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MARKET_PATH = PROCESSED_DIR / "market_daily.csv"

TICKERS = ["GME", "AMC", "BBBY", "BB", "NOK"]

EVENT_WINDOWS = {
    "Full range": ("2019-01-02", "2023-06-29"),
    "January 2021 squeeze": ("2021-01-01", "2021-02-15"),
    "AMC June 2021 run": ("2021-05-15", "2021-06-15"),
    "BBBY August 2022 squeeze": ("2022-08-01", "2022-09-15"),
    "BBBY bankruptcy": ("2023-04-01", "2023-05-15"),
}

STATE_ROWS = [
    ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"),
    ("AR", "Arkansas"), ("CA", "California"), ("CO", "Colorado"),
    ("CT", "Connecticut"), ("DE", "Delaware"), ("FL", "Florida"),
    ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"),
    ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"),
    ("KS", "Kansas"), ("KY", "Kentucky"), ("LA", "Louisiana"),
    ("ME", "Maine"), ("MD", "Maryland"), ("MA", "Massachusetts"),
    ("MI", "Michigan"), ("MN", "Minnesota"), ("MS", "Mississippi"),
    ("MO", "Missouri"), ("MT", "Montana"), ("NE", "Nebraska"),
    ("NV", "Nevada"), ("NH", "New Hampshire"), ("NJ", "New Jersey"),
    ("NM", "New Mexico"), ("NY", "New York"), ("NC", "North Carolina"),
    ("ND", "North Dakota"), ("OH", "Ohio"), ("OK", "Oklahoma"),
    ("OR", "Oregon"), ("PA", "Pennsylvania"), ("RI", "Rhode Island"),
    ("SC", "South Carolina"), ("SD", "South Dakota"), ("TN", "Tennessee"),
    ("TX", "Texas"), ("UT", "Utah"), ("VT", "Vermont"),
    ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"),
    ("WI", "Wisconsin"), ("WY", "Wyoming"),
]


def gaussian_day(dates: pd.Series, center: str, width: float, amplitude: float) -> np.ndarray:
    offsets = (dates - pd.Timestamp(center)).dt.days.to_numpy()
    return amplitude * np.exp(-(offsets**2) / (2 * width**2))


def build_reddit_attention() -> pd.DataFrame:
    if MARKET_PATH.exists():
        dates = (
            pd.read_csv(MARKET_PATH, usecols=["date"])["date"]
            .drop_duplicates()
            .pipe(pd.to_datetime)
            .sort_values()
            .reset_index(drop=True)
        )
    else:
        dates = pd.Series(pd.date_range("2019-01-02", "2023-06-29", freq="B"))

    rows = []
    for ticker in TICKERS:
        post_base = {"GME": 28, "AMC": 21, "BBBY": 8, "BB": 9, "NOK": 7}[ticker]
        comment_base = {"GME": 120, "AMC": 95, "BBBY": 36, "BB": 42, "NOK": 34}[ticker]
        post_mentions = np.full(len(dates), post_base, dtype=float)
        comment_mentions = np.full(len(dates), comment_base, dtype=float)
        sentiment = np.full(len(dates), 0.08, dtype=float)

        if ticker == "GME":
            post_mentions += gaussian_day(dates, "2021-01-27", 4.5, 5200)
            comment_mentions += gaussian_day(dates, "2021-01-27", 4.5, 28500)
            sentiment += gaussian_day(dates, "2021-01-27", 8, 0.33)
        if ticker == "AMC":
            post_mentions += gaussian_day(dates, "2021-01-28", 5, 2200)
            comment_mentions += gaussian_day(dates, "2021-01-28", 5, 11800)
            post_mentions += gaussian_day(dates, "2021-06-02", 5, 3400)
            comment_mentions += gaussian_day(dates, "2021-06-02", 5, 16000)
            sentiment += gaussian_day(dates, "2021-06-02", 8, 0.26)
        if ticker == "BBBY":
            post_mentions += gaussian_day(dates, "2022-08-17", 5, 1900)
            comment_mentions += gaussian_day(dates, "2022-08-17", 5, 7900)
            post_mentions += gaussian_day(dates, "2023-04-23", 8, 420)
            comment_mentions += gaussian_day(dates, "2023-04-23", 8, 1800)
            sentiment += gaussian_day(dates, "2022-08-17", 7, 0.18)
            sentiment -= gaussian_day(dates, "2023-04-23", 10, 0.32)
        if ticker == "BB":
            post_mentions += gaussian_day(dates, "2021-01-28", 5, 1150)
            comment_mentions += gaussian_day(dates, "2021-01-28", 5, 5600)
            sentiment += gaussian_day(dates, "2021-01-28", 8, 0.18)
        if ticker == "NOK":
            post_mentions += gaussian_day(dates, "2021-01-28", 5, 980)
            comment_mentions += gaussian_day(dates, "2021-01-28", 5, 5100)
            sentiment += gaussian_day(dates, "2021-01-28", 8, 0.16)

        for date, posts, comments, sent in zip(dates, post_mentions, comment_mentions, sentiment):
            rows.append(
                {
                    "date": date.date().isoformat(),
                    "ticker": ticker,
                    "post_mentions": int(round(posts)),
                    "comment_mentions": int(round(comments)),
                    "total_mentions": int(round(posts + comments)),
                    "sentiment_mean": round(float(np.clip(sent, -0.55, 0.7)), 3),
                }
            )
    return pd.DataFrame(rows)


def build_edges() -> pd.DataFrame:
    window_weights = {
        "Full range": {
            ("GME", "AMC"): 4200, ("GME", "BB"): 1800, ("GME", "NOK"): 1600,
            ("AMC", "BB"): 1300, ("AMC", "NOK"): 1200, ("BB", "NOK"): 900,
            ("GME", "BBBY"): 850, ("AMC", "BBBY"): 620, ("BBBY", "BB"): 260,
        },
        "January 2021 squeeze": {
            ("GME", "AMC"): 1500, ("GME", "BB"): 880, ("GME", "NOK"): 760,
            ("AMC", "BB"): 520, ("AMC", "NOK"): 470, ("BB", "NOK"): 340,
            ("GME", "BBBY"): 90,
        },
        "AMC June 2021 run": {
            ("GME", "AMC"): 980, ("AMC", "BB"): 260, ("AMC", "NOK"): 230,
            ("GME", "BB"): 180, ("GME", "NOK"): 150, ("AMC", "BBBY"): 110,
        },
        "BBBY August 2022 squeeze": {
            ("GME", "BBBY"): 760, ("AMC", "BBBY"): 430, ("BBBY", "BB"): 180,
            ("BBBY", "NOK"): 120, ("GME", "AMC"): 360,
        },
        "BBBY bankruptcy": {
            ("GME", "BBBY"): 280, ("AMC", "BBBY"): 210, ("BBBY", "BB"): 95,
            ("BBBY", "NOK"): 70, ("GME", "AMC"): 160,
        },
    }
    rows = []
    for window, weights in window_weights.items():
        for source, target in combinations(TICKERS, 2):
            weight = weights.get((source, target), weights.get((target, source), 0))
            if weight > 0:
                rows.append({"window": window, "source": source, "target": target, "weight": weight})
    return pd.DataFrame(rows)


def build_text_summary() -> pd.DataFrame:
    terms = {
        "January 2021 squeeze": {
            "GME": [("short squeeze", 980, "positive"), ("hold", 870, "positive"), ("gamma", 540, "neutral"),
                    ("Robinhood", 510, "negative"), ("diamond hands", 470, "positive")],
            "AMC": [("movie theaters", 410, "neutral"), ("squeeze", 390, "positive"), ("halt", 260, "negative")],
            "BB": [("BlackBerry", 260, "neutral"), ("undervalued", 220, "positive"), ("calls", 180, "positive")],
            "NOK": [("Nokia", 230, "neutral"), ("volume", 190, "neutral"), ("calls", 160, "positive")],
        },
        "AMC June 2021 run": {
            "AMC": [("apes", 720, "positive"), ("short interest", 610, "neutral"), ("hold", 590, "positive"),
                    ("dilution", 280, "negative"), ("gamma squeeze", 250, "positive")],
            "GME": [("sympathy trade", 210, "neutral"), ("meme basket", 190, "neutral")],
        },
        "BBBY August 2022 squeeze": {
            "BBBY": [("Ryan Cohen", 620, "neutral"), ("squeeze", 580, "positive"), ("options", 440, "neutral"),
                     ("selloff", 330, "negative"), ("bankruptcy risk", 190, "negative")],
            "GME": [("chairman", 210, "neutral"), ("basket", 180, "neutral")],
            "AMC": [("sympathy", 170, "neutral"), ("retail", 150, "neutral")],
        },
        "BBBY bankruptcy": {
            "BBBY": [("Chapter 11", 520, "negative"), ("delisting", 360, "negative"),
                     ("risk", 290, "negative"), ("turnaround", 150, "positive")],
            "GME": [("lessons", 120, "neutral"), ("risk management", 95, "neutral")],
        },
    }
    rows = []
    for window, by_ticker in terms.items():
        for ticker, values in by_ticker.items():
            for term, count, label in values:
                rows.append(
                    {
                        "window": window,
                        "ticker": ticker,
                        "term": term,
                        "count": count,
                        "sentiment_label": label,
                    }
                )
    return pd.DataFrame(rows)


def build_google_trends() -> pd.DataFrame:
    rng = np.random.default_rng(28)
    term_window_strength = {
        ("GameStop", "January 2021 squeeze"): 92,
        ("AMC stock", "January 2021 squeeze"): 68,
        ("WallStreetBets", "January 2021 squeeze"): 84,
        ("BBBY stock", "January 2021 squeeze"): 18,
        ("GameStop", "AMC June 2021 run"): 42,
        ("AMC stock", "AMC June 2021 run"): 91,
        ("WallStreetBets", "AMC June 2021 run"): 58,
        ("BBBY stock", "AMC June 2021 run"): 16,
        ("GameStop", "BBBY August 2022 squeeze"): 34,
        ("AMC stock", "BBBY August 2022 squeeze"): 38,
        ("WallStreetBets", "BBBY August 2022 squeeze"): 57,
        ("BBBY stock", "BBBY August 2022 squeeze"): 86,
        ("GameStop", "BBBY bankruptcy"): 25,
        ("AMC stock", "BBBY bankruptcy"): 22,
        ("WallStreetBets", "BBBY bankruptcy"): 35,
        ("BBBY stock", "BBBY bankruptcy"): 78,
    }
    finance_states = {"CA", "NY", "NJ", "TX", "FL", "MA", "IL", "WA", "NV", "CO"}
    rows = []
    for (term, window), base_strength in term_window_strength.items():
        values = []
        for code, state in STATE_ROWS:
            boost = 12 if code in finance_states else 0
            regional_noise = rng.normal(0, 8)
            value = np.clip(base_strength + boost + regional_noise, 2, 100)
            values.append((code, state, value))
        max_value = max(value for _, _, value in values)
        for code, state, value in values:
            interest = int(round(value / max_value * 100))
            rows.append(
                {
                    "window": window,
                    "term": term,
                    "state": state,
                    "state_code": code,
                    "interest": interest,
                }
            )
    return pd.DataFrame(rows)


def build_data_dictionary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "file": "market_daily.csv",
                "status": "existing project data",
                "notes": "Daily price, volume, return, spike, and abnormal-return fields.",
            },
            {
                "file": "event_timeline.csv",
                "status": "existing project data",
                "notes": "Major meme-stock milestones used for app annotations.",
            },
            {
                "file": "reddit_daily_attention.csv",
                "status": "fallback fixture",
                "notes": "Replace with WallStreetBets aggregates before final empirical claims.",
            },
            {
                "file": "ticker_comention_edges.csv",
                "status": "fallback fixture",
                "notes": "Replace with co-mentions extracted from Reddit posts/comments.",
            },
            {
                "file": "reddit_text_summary.csv",
                "status": "fallback fixture",
                "notes": "Replace with top terms and sentiment from real Reddit text.",
            },
            {
                "file": "google_trends_state_level.csv",
                "status": "fallback fixture",
                "notes": "Replace with Google Trends state-level exports.",
            },
        ]
    )


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "reddit_daily_attention.csv": build_reddit_attention(),
        "ticker_comention_edges.csv": build_edges(),
        "reddit_text_summary.csv": build_text_summary(),
        "google_trends_state_level.csv": build_google_trends(),
        "data_dictionary.csv": build_data_dictionary(),
    }
    for filename, frame in outputs.items():
        frame.to_csv(PROCESSED_DIR / filename, index=False)
        print(f"Wrote {filename}: {len(frame):,} rows")


if __name__ == "__main__":
    main()
