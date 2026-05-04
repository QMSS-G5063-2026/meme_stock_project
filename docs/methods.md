# Methods and Limitations

This project connects market activity, Reddit attention, ticker co-mentions, and
state-level Google search interest for five meme-stock tickers: GME, AMC, BBBY,
BB, and NOK.

## Source Notes

- Market data are Yahoo Finance daily historical prices downloaded with
  `yfinance`: https://pypi.org/project/yfinance/.
- Reddit data come from a staged `r/wallstreetbets` posts/comments archive. The
  archive source used for this workflow is the Kaggle "Reddit WallStreetBets
  Posts and Comments" dataset, collected through `pmaw`/Pushshift:
  https://www.kaggle.com/datasets/mattpodolak/rwallstreetbets-posts-and-comments.
- Google Trends data are collected with `pytrends` and interpreted using
  Google's documentation on normalized Trends values:
  https://support.google.com/trends/answer/4365533.

## Current Data Layer

- `data/processed/market_daily.csv` contains daily market prices, returns,
  volume, spike flags, and abnormal returns from 2019-01-02 through 2023-06-29.
- `data/processed/event_timeline.csv` contains the major event annotations used
  in the app.
- Track C Google Trends data are collected with `pytrends` and stored in
  `data/processed/google_trends_state_level.csv`. The current processed file
  is a cached API export reused after live collection was rate-limited.
- Track B Reddit/text/network data are generated from local WallStreetBets
  Reddit archive files staged in `data/raw/reddit/`. The current processed
  output contains 802,589 ticker-mention records from 2020-12-08 through
  2021-02-04. Raw Reddit ZIP files are not committed because they are too large
  for normal GitHub hosting, but the processed app-ready tables are committed.

## Track A: Market Data

Daily stock data were processed into ticker-level returns, volume z-scores,
return z-scores, spike flags, and abnormal returns. Volume and return spikes are
flagged when the absolute ticker-level z-score is greater than 2. Abnormal
return is calculated as the stock's daily return minus the S&P 500 daily return,
using `^GSPC` as the benchmark.

## Track B: Reddit, Text, and Network

The schema uses daily ticker-level attention counts, event-window top terms,
simple sentiment labels, and ticker co-mention edges. The production workflow is:

1. Stage WallStreetBets posts/comments in `data/raw/reddit/`.
2. Run `python -m src.processing.build_reddit_outputs`.
3. Extract ticker mentions with explicit ticker-boundary rules, including a
   context guard for ambiguous `BB` mentions.
4. Aggregate post/comment mentions by date and ticker.
5. Build co-mention edges from posts/comments that mention multiple tickers.
6. Compute interpretable top terms and VADER sentiment by event window.

The app deliberately treats BERTopic as a stretch goal because the course MVP
benefits more from reliable, explainable text summaries than from a fragile topic
model.

## Track C: Google Trends and Map

The map uses state-level Google Trends interest values by term and event window.
Google Trends values are normalized relative search interest, not raw search
counts, so the choropleth should be read as a within-export comparison.

The app uses Plotly's built-in U.S. state rendering via two-letter state codes to
avoid brittle shapefile joins during the website build.

## Presentation Caveat

The market timeline, Reddit/text/network views, and Google Trends map are backed
by processed project/API outputs. The main caveats are coverage and
normalization: Reddit archive coverage is concentrated around December 2020 to
February 2021, and Google Trends reports relative interest rather than raw
search counts. Live Google Trends collection may be rate-limited, so cached raw
exports are included for deployable reproducibility.
