# Task List: Mapping Meme Stock Attention

This task list reflects the final-submission state of the project. The original
three-track work split is complete enough for the course MVP; remaining work is
deployment verification and presentation rehearsal.

## Status Key

- `[ ]` Not started
- `[~]` In progress
- `[x]` Done

## Final Submission Status

- [x] Final ticker list: `GME`, `AMC`, `BBBY`, `BB`, `NOK`
- [x] Main market analysis range: 2019-01-02 through 2023-06-29
- [x] Core event windows: Full range, January 2021 squeeze, AMC June 2021 run,
  BBBY August 2022 squeeze, BBBY bankruptcy
- [x] Short-sale volume and fails-to-deliver kept out of MVP scope
- [x] Deployable Streamlit app in `app/streamlit_app.py`
- [~] Public Streamlit Community Cloud URL added to `README.md`

## Track A: Market Data and Timeline

- [x] Processed market dataset exported to `data/processed/market_daily.csv`
- [x] Event timeline exported to `data/processed/event_timeline.csv`
- [x] Daily returns, market returns, abnormal returns, volume z-scores, and spike
  flags available in the processed table
- [x] Linked market timeline built with price, volume, Reddit attention, and
  shared filters
- [x] Timeline supports one focus stock at a time with direct event labels
- [x] Event Stock View adds OHLC, cumulative-return, return, and volume/spike
  charts for the focused ticker

## Track B: Reddit, Text, and Network

- [x] WallStreetBets raw archive staged locally for processing
- [x] Processed Reddit attention table exported to
  `data/processed/reddit_daily_attention.csv`
- [x] Text summary table exported to `data/processed/reddit_text_summary.csv`
- [x] Co-mention edge table exported to
  `data/processed/ticker_comention_edges.csv`
- [x] Processed output covers 802,589 ticker-mention records from 2020-12-08
  through 2021-02-04
- [x] Text view includes mention counts, comment/post split, sentiment, and top
  terms
- [x] Network view includes a graph, edge table, strongest-pair metric, and top
  co-mentions summary

## Track C: Google Trends, Map, and App Shell

- [x] Cached Google Trends API exports available in `data/raw/google_trends/`
- [x] Processed state-level Google Trends table exported to
  `data/processed/google_trends_state_level.csv`
- [x] Google Trends collection summary exported to
  `data/processed/google_trends_collection_summary.csv`
- [x] Map view uses Plotly U.S. state choropleth from state codes
- [x] Map view includes a top-states table for the selected term and event window
- [x] Sidebar filters drive the main timeline, Reddit/Text, Network, and Map views

## Documentation And Presentation

- [x] README documents local run commands, data status, specialized
  visualizations, and final demo path
- [x] Methods notes document data sources, processing choices, and caveats
- [x] Process book documents the evolution of design and data decisions
- [x] Presentation notes include a short demo script and final submission check
- [x] Static presentation figure generated under `docs/figures/`
- [~] Public app URL still needs to be added after deployment

## QA Checklist

- [x] Python modules compile with `python -m compileall -q app src`
- [x] Streamlit app runs locally with `python -m streamlit run app/streamlit_app.py`
- [x] Browser smoke test covers Overview, Timeline, Reddit/Text, Network, Map,
  Presentation, and Methods
- [x] Automated Streamlit scenario test covers default January 2021 view, Full
  range, AMC June 2021, BBBY August 2022, single-ticker selection,
  empty-ticker fallback, network threshold changes, and map term/window changes
- [ ] Verify the public deployment URL from a clean browser session
- [ ] Add the public deployment URL to `README.md`
- [ ] Rehearse final demo using the Presentation tab flow
