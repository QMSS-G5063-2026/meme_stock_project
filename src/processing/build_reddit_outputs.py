"""Build Track B Reddit, text, and network outputs.

This script is robust to several common Reddit archive export shapes. It looks
for raw files in data/raw/reddit and accepts CSV, CSV.GZ, JSON, JSONL, Parquet,
and ZIP files containing CSV/JSON/JSONL files. If no raw Reddit archive is
available, it writes clearly labeled fallback outputs so the Streamlit app still
runs for demonstration.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from io import BytesIO
from itertools import combinations
from pathlib import Path
import re
import sys
import zipfile

import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.processing.build_fallback_data import (
    EVENT_WINDOWS,
    PROCESSED_DIR,
    TICKERS,
    build_edges,
    build_reddit_attention,
    build_text_summary,
)


RAW_REDDIT_DIR = PROJECT_ROOT / "data" / "raw" / "reddit"

DATE_COLUMNS = [
    "date", "datetime", "created", "created_at", "created_utc",
    "timestamp", "time", "retrieved_on",
]
TITLE_COLUMNS = ["title", "post_title", "submission_title"]
BODY_COLUMNS = [
    "selftext", "body", "text", "comment", "comment_body",
    "content", "message", "post_body",
]
TYPE_COLUMNS = ["type", "kind", "item_type", "record_type"]

STOPWORDS = {
    "about", "after", "again", "against", "all", "also", "amp", "and", "are", "because",
    "before", "being", "between", "but", "can", "com", "could", "daily", "did", "does",
    "don", "down", "for", "from", "fuck", "fucking", "going", "had", "has",
    "have", "i'm", "im", "into", "its", "get", "got", "http", "https", "just",
    "like", "may", "more", "most", "much",
    "not", "now", "only", "our", "out", "over", "redd", "redditmedia", "removed",
    "deleted", "same", "she", "should", "some", "than", "that", "today",
    "the", "their", "them", "then", "there", "these", "they", "this",
    "those", "through", "very", "was", "were", "what", "when", "where",
    "which", "while", "who", "why", "will", "with", "would", "your", "you",
    "gme", "amc", "bb", "nok", "bbby", "bbbyq", "blackberry", "nokia", "gamestop",
    "stock", "stocks", "share", "shares", "reddit", "wallstreetbets",
    "wsb", "ticker", "tickers",
}

STOCK_CONTEXT = re.compile(
    r"\b(stock|stocks|share|shares|calls?|puts?|options?|ticker|squeeze|"
    r"short|long|yolo|moon|hold|buy|bought|sell|sold|position|positions|"
    r"volume|price|market|float|gamma)\b",
    flags=re.IGNORECASE,
)

TOKEN_PATTERNS = {
    "GME": re.compile(r"(?<![A-Za-z0-9])(?:\$GME|GME|GameStop)(?![A-Za-z0-9])"),
    "AMC": re.compile(r"(?<![A-Za-z0-9])(?:\$AMC|AMC|AMC Entertainment)(?![A-Za-z0-9])"),
    "BBBY": re.compile(r"(?<![A-Za-z0-9])(?:\$BBBY|\$BBBYQ|BBBY|BBBYQ|Bed Bath)(?![A-Za-z0-9])"),
    "BB": re.compile(r"(?<![A-Za-z0-9])(?:\$BB|BlackBerry)(?![A-Za-z0-9])"),
    "NOK": re.compile(r"(?<![A-Za-z0-9])(?:\$NOK|NOK|Nokia)(?![A-Za-z0-9])"),
}


def read_frame_from_path(path: Path) -> list[pd.DataFrame]:
    suffix = "".join(path.suffixes).lower()
    try:
        if suffix.endswith(".csv") or suffix.endswith(".csv.gz"):
            return [pd.read_csv(path, low_memory=False)]
        if suffix.endswith(".jsonl"):
            return [pd.read_json(path, lines=True)]
        if suffix.endswith(".json"):
            try:
                return [pd.read_json(path, lines=True)]
            except ValueError:
                return [pd.read_json(path)]
        if suffix.endswith(".parquet"):
            return [pd.read_parquet(path)]
        if suffix.endswith(".zip"):
            frames: list[pd.DataFrame] = []
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    lower = member.lower()
                    if lower.endswith(".csv"):
                        with archive.open(member) as handle:
                            frames.append(pd.read_csv(handle, low_memory=False))
                    elif lower.endswith(".jsonl"):
                        with archive.open(member) as handle:
                            frames.append(pd.read_json(BytesIO(handle.read()), lines=True))
                    elif lower.endswith(".json"):
                        with archive.open(member) as handle:
                            blob = BytesIO(handle.read())
                            try:
                                frames.append(pd.read_json(blob, lines=True))
                            except ValueError:
                                blob.seek(0)
                                frames.append(pd.read_json(blob))
            return frames
    except Exception as exc:
        print(f"Skipping {path.name}: {type(exc).__name__}: {exc}")
    return []


def find_column(columns: list[str], candidates: list[str]) -> str | None:
    lookup = {col.lower(): col for col in columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def normalize_dates(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().mean() > 0.8:
        unit = "ms" if numeric.dropna().median() > 10_000_000_000 else "s"
        return pd.to_datetime(numeric, unit=unit, errors="coerce", utc=True).dt.tz_localize(None)
    return pd.to_datetime(series, errors="coerce", utc=True).dt.tz_localize(None)


def infer_record_kind(frame: pd.DataFrame, title_col: str | None) -> pd.Series:
    type_col = find_column(list(frame.columns), TYPE_COLUMNS)
    if type_col is not None:
        values = frame[type_col].astype(str).str.lower()
        return np.where(values.str.contains("comment"), "comment", "post")
    lower_columns = {col.lower() for col in frame.columns}
    if {"body", "parent_id", "link_id"} & lower_columns and title_col is None:
        return pd.Series(["comment"] * len(frame), index=frame.index)
    if title_col is not None:
        has_title = frame[title_col].fillna("").astype(str).str.strip().ne("")
        return np.where(has_title, "post", "comment")
    return pd.Series(["post"] * len(frame), index=frame.index)


def normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    columns = list(frame.columns)
    date_col = find_column(columns, DATE_COLUMNS)
    title_col = find_column(columns, TITLE_COLUMNS)
    body_cols = [col for col in BODY_COLUMNS if col in {c.lower(): c for c in columns}]
    body_cols = [find_column(columns, [col]) for col in BODY_COLUMNS]
    body_cols = [col for col in body_cols if col is not None]

    if date_col is None or (title_col is None and not body_cols):
        return pd.DataFrame(columns=["date", "kind", "text"])

    pieces = []
    if title_col:
        pieces.append(frame[title_col].fillna("").astype(str))
    for body_col in body_cols:
        pieces.append(frame[body_col].fillna("").astype(str))
    text = pieces[0]
    for piece in pieces[1:]:
        text = text + " " + piece

    normalized = pd.DataFrame(
        {
            "date": normalize_dates(frame[date_col]).dt.date.astype("string"),
            "kind": infer_record_kind(frame, title_col),
            "text": text.str.replace(r"\s+", " ", regex=True).str.strip(),
        }
    )
    normalized = normalized.dropna(subset=["date"])
    normalized = normalized[normalized["text"].str.len() > 0]
    return normalized


def load_raw_reddit() -> pd.DataFrame:
    files = [
        path for path in RAW_REDDIT_DIR.rglob("*")
        if path.is_file() and path.name != ".gitkeep"
    ]
    frames: list[pd.DataFrame] = []
    for path in files:
        for frame in read_frame_from_path(path):
            normalized = normalize_frame(frame)
            if not normalized.empty:
                frames.append(normalized)
    if not frames:
        return pd.DataFrame(columns=["date", "kind", "text"])
    data = pd.concat(frames, ignore_index=True)
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["date", "text"])
    data["kind"] = data["kind"].where(data["kind"].isin(["post", "comment"]), "post")
    return data


def extract_tickers(text: str) -> list[str]:
    mentions: list[str] = []
    for ticker, pattern in TOKEN_PATTERNS.items():
        if not pattern.search(text):
            continue
        if ticker == "BB" and "$BB" not in text and "BlackBerry" not in text and not STOCK_CONTEXT.search(text):
            continue
        mentions.append(ticker)
    return mentions


def label_sentiment(score: float) -> str:
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def assign_window(row_date: pd.Timestamp) -> list[str]:
    labels = []
    for label, (start, end) in EVENT_WINDOWS.items():
        if pd.Timestamp(start) <= row_date <= pd.Timestamp(end):
            labels.append(label)
    return labels


def tokenize(text: str) -> list[str]:
    clean = re.sub(r"https?://\S+|www\.\S+", " ", text.lower())
    tokens = re.findall(r"[a-z][a-z']{2,}", clean)
    return [token for token in tokens if token not in STOPWORDS and len(token) <= 24]


def build_outputs_from_raw(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    analyzer = SentimentIntensityAnalyzer()
    records = raw.copy()
    records["mentions"] = records["text"].map(extract_tickers)
    records = records[records["mentions"].map(bool)].copy()
    if records.empty:
        raise ValueError("Raw Reddit files were readable but contained no target ticker mentions.")

    records["sentiment"] = records["text"].map(lambda text: analyzer.polarity_scores(text)["compound"])
    records["windows"] = records["date"].map(assign_window)

    daily_rows = []
    for _, row in records.iterrows():
        for ticker in row["mentions"]:
            daily_rows.append(
                {
                    "date": row["date"].date().isoformat(),
                    "ticker": ticker,
                    "post_mentions": 1 if row["kind"] == "post" else 0,
                    "comment_mentions": 1 if row["kind"] == "comment" else 0,
                    "sentiment_mean": row["sentiment"],
                }
            )
    daily = pd.DataFrame(daily_rows)
    attention = (
        daily.groupby(["date", "ticker"], as_index=False)
        .agg(
            post_mentions=("post_mentions", "sum"),
            comment_mentions=("comment_mentions", "sum"),
            sentiment_mean=("sentiment_mean", "mean"),
        )
        .sort_values(["date", "ticker"])
    )
    attention["total_mentions"] = attention["post_mentions"] + attention["comment_mentions"]
    attention = attention[
        ["date", "ticker", "post_mentions", "comment_mentions", "total_mentions", "sentiment_mean"]
    ]
    attention["sentiment_mean"] = attention["sentiment_mean"].round(3)

    edge_counter: Counter[tuple[str, str, str]] = Counter()
    for _, row in records.iterrows():
        mentions = sorted(set(row["mentions"]))
        if len(mentions) < 2:
            continue
        windows = row["windows"] or ["Full range"]
        for window in windows:
            for source, target in combinations(mentions, 2):
                edge_counter[(window, source, target)] += 1
    edges = pd.DataFrame(
        [
            {"window": window, "source": source, "target": target, "weight": weight}
            for (window, source, target), weight in edge_counter.items()
        ]
    )
    if not edges.empty:
        edges = edges.sort_values(["window", "weight"], ascending=[True, False])

    term_counts: defaultdict[tuple[str, str, str], int] = defaultdict(int)
    term_sentiments: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    for _, row in records.iterrows():
        windows = [window for window in row["windows"] if window != "Full range"]
        if not windows:
            continue
        terms = Counter(tokenize(row["text"]))
        for window in windows:
            for ticker in row["mentions"]:
                for term, count in terms.items():
                    key = (window, ticker, term)
                    term_counts[key] += count
                    term_sentiments[key].append(row["sentiment"])

    text_rows = []
    for (window, ticker, term), count in term_counts.items():
        avg_sentiment = float(np.mean(term_sentiments[(window, ticker, term)]))
        text_rows.append(
            {
                "window": window,
                "ticker": ticker,
                "term": term,
                "count": count,
                "sentiment_label": label_sentiment(avg_sentiment),
            }
        )
    text_summary = pd.DataFrame(text_rows)
    if not text_summary.empty:
        text_summary = (
            text_summary.sort_values(["window", "ticker", "count"], ascending=[True, True, False])
            .groupby(["window", "ticker"], as_index=False)
            .head(10)
        )

    summary = pd.DataFrame(
        [
            {"metric": "raw_records_with_mentions", "value": len(records)},
            {"metric": "date_start", "value": records["date"].min().date().isoformat()},
            {"metric": "date_end", "value": records["date"].max().date().isoformat()},
            {"metric": "unique_tickers", "value": records["mentions"].explode().nunique()},
            {"metric": "data_status", "value": "processed raw Reddit export"},
        ]
    )
    return attention, edges, text_summary, summary


def upsert_data_dictionary(status: str, notes: str) -> None:
    path = PROCESSED_DIR / "data_dictionary.csv"
    if path.exists():
        dictionary = pd.read_csv(path)
    else:
        dictionary = pd.DataFrame(columns=["file", "status", "notes"])
    replacement = pd.DataFrame(
        [
            {"file": "reddit_daily_attention.csv", "status": status, "notes": notes},
            {"file": "ticker_comention_edges.csv", "status": status, "notes": notes},
            {"file": "reddit_text_summary.csv", "status": status, "notes": notes},
        ]
    )
    dictionary = dictionary[~dictionary["file"].isin(replacement["file"])]
    dictionary = pd.concat([dictionary, replacement], ignore_index=True)
    dictionary.sort_values("file").to_csv(path, index=False)


def write_fallback_outputs() -> None:
    build_reddit_attention().to_csv(PROCESSED_DIR / "reddit_daily_attention.csv", index=False)
    build_edges().to_csv(PROCESSED_DIR / "ticker_comention_edges.csv", index=False)
    build_text_summary().to_csv(PROCESSED_DIR / "reddit_text_summary.csv", index=False)
    pd.DataFrame(
        [
            {"metric": "data_status", "value": "fallback fixture"},
            {"metric": "reason", "value": "No raw Reddit archive files found in data/raw/reddit."},
        ]
    ).to_csv(PROCESSED_DIR / "reddit_processing_summary.csv", index=False)
    upsert_data_dictionary(
        "fallback fixture",
        "No raw Reddit archive is staged; app uses event-calibrated demo data.",
    )


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_raw_reddit()
    if raw.empty:
        write_fallback_outputs()
        print("No raw Reddit files found. Wrote labeled fallback Track B outputs.")
        return

    try:
        attention, edges, text_summary, summary = build_outputs_from_raw(raw)
    except ValueError as exc:
        write_fallback_outputs()
        print(f"{exc} Wrote labeled fallback Track B outputs.")
        return

    attention.to_csv(PROCESSED_DIR / "reddit_daily_attention.csv", index=False)
    edges.to_csv(PROCESSED_DIR / "ticker_comention_edges.csv", index=False)
    text_summary.to_csv(PROCESSED_DIR / "reddit_text_summary.csv", index=False)
    summary.to_csv(PROCESSED_DIR / "reddit_processing_summary.csv", index=False)
    upsert_data_dictionary(
        "processed raw Reddit export",
        "Generated from files staged in data/raw/reddit with ticker extraction, VADER sentiment, and co-mentions.",
    )
    print(
        "Wrote Reddit outputs: "
        f"{len(attention):,} daily rows, {len(edges):,} edges, {len(text_summary):,} text rows."
    )


if __name__ == "__main__":
    main()
