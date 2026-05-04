# Project Documentation

## Project Topic

This project examines meme-stock market behavior, Reddit attention, ticker
co-mentions, and state-level Google search interest. The main question is how
retail-trading attention moved across financial markets, online discussion, and
regional public search behavior during major meme-stock events.

The dashboard focuses on GME, AMC, BBBY, BB, and NOK. These tickers capture the
January 2021 meme-stock cluster, the AMC follow-on rally in June 2021, and later
BBBY events through the 2023 bankruptcy filing.

## Data Sources

- Daily stock prices: Yahoo Finance historical market data, downloaded with the
  `yfinance` Python package and stored in
  `data/processed/market_daily.csv`. `yfinance` describes itself as a Python
  interface for fetching financial and market data from Yahoo Finance:
  https://pypi.org/project/yfinance/.
- Reddit mentions: local `r/wallstreetbets` posts/comments archive files staged
  in `data/raw/reddit/`, processed into daily ticker mention counts, text
  summaries, and co-mention edges. The archive source used for this workflow is
  the Kaggle "Reddit WallStreetBets Posts and Comments" dataset, which contains
  posts and comments from early December 2020 to early February 2021 and was
  collected through `pmaw`/Pushshift:
  https://www.kaggle.com/datasets/mattpodolak/rwallstreetbets-posts-and-comments.
  The raw Reddit files are not committed because they are too large for normal
  GitHub hosting; the committed processed outputs cover 802,589 target-ticker
  mention records from 2020-12-08 through 2021-02-04.
- Google search interest: Google Trends state-level search interest, collected
  with `pytrends` and cached in `data/raw/google_trends/`. The processed app
  table is `data/processed/google_trends_state_level.csv`. Google explains that
  Trends values are anonymized, aggregated, and normalized relative search
  interest values rather than raw search counts:
  https://support.google.com/trends/answer/4365533. The `pytrends`
  `interest_by_region` interface supports region-level queries:
  https://pypi.org/project/pytrends/.
- Event annotations: major meme-stock milestones were curated from news and
  filing sources and stored in `data/processed/event_timeline.csv`. Most events
  cluster around January 2021, with later AMC and BBBY events included to extend
  the story through 2023.

## Visualization Choices

The left filter bar allows users to dynamically select stocks, event windows,
date ranges, and market metrics. Keeping these controls in one place makes the
dashboard behave consistently across the timeline, Reddit/text, network, and map
views.

We changed the stock-comparison interaction from click highlighting to an
explicit filter display. This makes the selected stocks visible at all times,
supports multi-stock comparison, and avoids hidden interaction states that can
be confusing during a short presentation. The filter approach is also cleaner in
Streamlit because the same selection can drive every tab after each app rerun,
rather than requiring users to remember which chart elements they clicked.

The timeline view combines market performance, event labels, volume/return spike
flags, and Reddit attention. This makes it possible to compare financial and
attention signals within the same date window.

The Reddit/text view separates post mentions, comment mentions, sentiment, and
top terms. This keeps the text analysis explainable and audit-friendly.

The network view uses ticker co-mentions to show which stocks were discussed
together in the same posts or comments. Edge weights represent co-mention counts
within the selected event window.

The map view uses a U.S. state choropleth to show where selected Google search
terms had relatively higher interest during key event windows. It adds a
geographic layer to a topic that is often visualized only as a price timeline.

## Data Analysis Choices and Limitations

### Daily Stock Price

Key events were identified by consulting multiple news, financial, and filing
sources. Because many of the largest meme-stock events occurred in January 2021,
and because Bed Bath & Beyond filed for bankruptcy in April 2023, the main
visualization window emphasizes 2021 through 2023.

Daily stock data were downloaded from Yahoo Finance for the target tickers.
Daily returns were calculated from adjusted close prices. Statistically abnormal
volume and price days were flagged using ticker-level z-scores for volume and
daily return, with absolute z-scores greater than 2 treated as volume or return
spikes.

Abnormal returns were calculated by comparing each stock's daily return with the
S&P 500 daily return, using `^GSPC` as the market benchmark:

`abnormal_return = stock_daily_return - market_daily_return`

Limitations: daily data miss intraday trading freezes, volatility, and order-flow
dynamics. Event annotations are curated rather than exhaustive, and z-score
spikes identify unusual days but do not prove that a specific event caused the
price or volume movement.

### Reddit Mentions

Reddit attention was measured by scanning `r/wallstreetbets` post and comment
text for target ticker mentions. The processing pipeline uses explicit ticker
boundary rules for GME, AMC, BBBY/BBBYQ, BB/BlackBerry, and NOK/Nokia. Because
`BB` can also appear in non-stock contexts, the extractor requires either `$BB`,
`BlackBerry`, or nearby stock-market context words before counting it.

Mentions are aggregated by date, ticker, and record type, producing separate
post mention counts, comment mention counts, total mentions, and mean VADER
sentiment. Co-mention edges are created when two or more target tickers appear in
the same post or comment, then aggregated by event window.

Limitations: the Reddit archive is concentrated around 2020-12-08 to
2021-02-04, so Reddit evidence is strongest for the January 2021 squeeze and
weaker for later 2021-2023 events. A ticker mention is a proxy for attention,
not a measure of investment behavior or endorsement. Ticker extraction can miss
slang, sarcasm, images, and deleted/removed content, and sentiment scores are
only a rough summary of noisy social-media language.

### Geospatial Mapping

State-level Google Trends values were collected for selected search terms and
event windows, including `GameStop`, `AMC stock`, `WallStreetBets`, and
`BBBY stock`. The pipeline uses `pytrends` with U.S. region-level results and
stores cached exports so the app can be rebuilt even when live Google Trends
collection is rate-limited.

The map uses Plotly's U.S. state choropleth with two-letter state codes. Each
state's value is a normalized Google Trends interest score from 0 to 100 for the
selected term and window.

Limitations: Google Trends reports relative search interest, not raw search
volume. Values are best interpreted within the same selected term and event
window; they should not be treated as exact search counts or directly compared
as absolute search volume across unrelated exports. Search terms also capture
public curiosity, which may include news attention, entertainment interest, or
confusion, not only trading intent.

## Next Steps

- Fix the date range UI, which is partially cropped in the current sidebar.
- Add a short caption below each visualization explaining the chart's specific
  function and how to read it.
- Add the final public Streamlit Community Cloud URL to the README after
  deployment.
- If time allows, expand Reddit coverage beyond the January 2021 archive window
  so later AMC and BBBY events have stronger social-media evidence.
