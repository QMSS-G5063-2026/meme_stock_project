# Mapping Meme Stock Attention

This project explores how meme-stock attention across Reddit, Google Trends, and
market activity evolved during major retail trading events. The main output is a
Streamlit website connecting online discussion, regional search interest, ticker
co-mentions, and financial market behavior.

## Public Website

Public app URL: https://memestockproject.streamlit.app

Final submission target: May 3, 2026. The local app is submission-ready once the
public URL has been added and verified from a clean browser session.

## Run the App

```bash
python -m pip install -r requirements.txt
python -m streamlit run app/streamlit_app.py
```

The app opens at `http://localhost:8501`.

## Rebuild Track B/C Outputs

```bash
python -m src.processing.build_all_track_b_c
```

This pipeline:

- processes raw Reddit archive files from `data/raw/reddit/` when available;
- falls back to clearly labeled demo Reddit/text/network tables if no raw archive
  is staged;
- collects state-level Google Trends data with `pytrends`, or reuses cached raw
  exports when live collection is rate-limited;
- writes presentation-ready static figures under `docs/figures/`.

## Current Data Status

- Market data: processed project output in `data/processed/market_daily.csv`.
- Event timeline: processed project output in `data/processed/event_timeline.csv`.
- Reddit/text/network: processed WallStreetBets archive output covering
  802,589 ticker-mention records from 2020-12-08 through 2021-02-04. The raw
  Reddit ZIP files are intentionally ignored because they exceed normal GitHub
  file-size limits; the processed tables needed by the app are committed.
- Google Trends: cached `pytrends` API exports, collected by state, search term,
  and event window. Live collection can be rate-limited, so the rebuild script
  reuses cached raw exports when needed.

The app relies on committed processed CSVs for deployment. Raw Reddit ZIP files
stay local because they are too large for normal GitHub hosting. Google Trends
values are normalized relative interest, not raw search counts, so the map
supports within-window geographic comparison rather than absolute search volume.

## Specialized Visualizations

The website demonstrates all three specialized visualization types named in the
course prompt:

- text analysis visualization: ticker attention, top terms, and sentiment;
- network visualization: ticker co-mention graph;
- geospatial visualization: U.S. state-level Google Trends choropleth.

See `docs/methods.md`, `docs/process_book.md`, and
`docs/presentation_notes.md` for the project methods, design decisions, and demo
path.

## Final Demo Path

1. Start in **Overview** and state the guiding question.
2. Move to **Timeline**, choose a focus stock, and use the direct event labels
   and Event Stock View to explain the January 2021 spike.
3. Move to **Reddit/Text** to show attention, sentiment, and terms.
4. Move to **Network** to highlight the strongest ticker co-mentions.
5. Move to **Map** to compare state-level search interest and top states.
6. End in **Methods** with data caveats and reproducibility notes.

