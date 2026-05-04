# Mapping Meme Stock Attention

Interactive Streamlit dashboard for exploring meme-stock activity across market
prices, Reddit attention, ticker co-mentions, and state-level Google Trends.

Live website: https://memestockproject.streamlit.app

## What This Project Shows

The project focuses on GME, AMC, BBBY, BB, and NOK. Its main finding is that the
January 2021 meme-stock squeeze is the clearest moment where market volatility,
Reddit discussion, and public search interest moved together. The dashboard also
shows that meme stocks were often discussed as a connected group, not only as
individual companies.

## Run Locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app/streamlit_app.py
```

The app opens at http://localhost:8501.

## Main Files

- `app/streamlit_app.py` - Streamlit dashboard
- `data/processed/` - committed CSV files used by the app
- `src/processing/` - scripts for rebuilding Reddit, Google Trends, and figures
- `notebooks/` - earlier market-data notebooks
- `docs/final_report_process_book.pdf` - final PDF process book
- `docs/` - methods, process notes, presentation notes, and project planning

## Data Sources

- Yahoo Finance daily prices, accessed with `yfinance`
- Kaggle WallStreetBets posts/comments archive
- Google Trends state-level search interest, collected with `pytrends`
- Curated meme-stock event timeline in `data/processed/event_timeline.csv`

Raw Reddit ZIP files are not committed because they are too large for GitHub.
The app uses the committed processed CSVs.

## Rebuild Processed Outputs

```bash
python -m src.processing.build_all_track_b_c
```

This rebuilds Reddit/text/network outputs when raw Reddit files are available
and refreshes Google Trends outputs from cached exports when live collection is
rate-limited.

## Notes

Google Trends values are normalized relative interest, not raw or
population-adjusted search counts. Reddit mentions are a proxy for attention,
not proof of trading behavior. Daily market data do not capture intraday trading
halts or order-flow dynamics.
