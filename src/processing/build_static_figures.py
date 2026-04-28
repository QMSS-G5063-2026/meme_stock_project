"""Build presentation-ready static figures for the process book and demo."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURE_DIR = PROJECT_ROOT / "docs" / "figures"

TICKERS = ["GME", "AMC", "BBBY", "BB", "NOK"]
COLORS = {
    "GME": "#D1495B",
    "AMC": "#00798C",
    "BBBY": "#EDA93A",
    "BB": "#3E5C76",
    "NOK": "#4E937A",
}


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    market = pd.read_csv(PROCESSED_DIR / "market_daily.csv", parse_dates=["date"])
    reddit = pd.read_csv(PROCESSED_DIR / "reddit_daily_attention.csv", parse_dates=["date"])
    window_start = pd.Timestamp("2021-01-01")
    window_end = pd.Timestamp("2021-02-15")
    market = market[(market["date"] >= window_start) & (market["date"] <= window_end)].copy()
    reddit = reddit[(reddit["date"] >= window_start) & (reddit["date"] <= window_end)].copy()
    market["indexed_price"] = market["adj_close"] / market.groupby("ticker")["adj_close"].transform("first") * 100

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for ticker in TICKERS:
        m = market[market["ticker"] == ticker]
        r = reddit[reddit["ticker"] == ticker]
        if not m.empty:
            axes[0].plot(m["date"], m["indexed_price"], label=ticker, color=COLORS[ticker], linewidth=2)
        if not r.empty:
            axes[1].plot(r["date"], r["total_mentions"], label=ticker, color=COLORS[ticker], linewidth=2)

    axes[0].set_title("January 2021 meme-stock price moves, indexed to Jan. 1 window")
    axes[0].set_ylabel("Indexed price")
    axes[1].set_title("Reddit attention over the same event window")
    axes[1].set_ylabel("Mentions")
    axes[1].set_xlabel("Date")
    for axis in axes:
        axis.grid(True, alpha=0.25)
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].legend(ncol=5, frameon=False, loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "january_2021_market_attention_summary.png", dpi=180)
    plt.close(fig)
    print(f"Wrote {FIGURE_DIR / 'january_2021_market_attention_summary.png'}")


if __name__ == "__main__":
    main()
