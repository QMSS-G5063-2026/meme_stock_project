# Task List: Mapping Meme Stock Attention

This task list is organized so the project can be split across three teammates with minimal overlap. It assumes a 3-person team, but the tasks can be reassigned as needed.

## Suggested Owners

- Owner A: Market data, timeline analysis, linked charts
- Owner B: Reddit data, text analysis, co-mention network
- Owner C: Google Trends, mapping, Streamlit integration, polish

## Status Key

- `[ ]` Not started
- `[~]` In progress
- `[x]` Done

## Phase 0: Shared Kickoff

- [ ] Confirm final ticker list: `GME`, `AMC`, `BBBY`, `BB`, `NOK`
- [ ] Confirm main analysis date range
- [ ] Decide whether short-sale volume and fails-to-deliver are MVP or stretch only
- [ ] Agree on file/folder structure
- [ ] Assign owners for each task below

## Track A: Market Data and Timeline

Owner: A

### Setup

- [ ] Create `data/raw/market/`
- [ ] Choose market data source and document rate limits / access notes
- [ ] Define required fields: date, open, close, adjusted close, volume, ticker

### Collection

- [ ] Download historical daily price data for each ticker
- [ ] Download historical daily trading volume for each ticker
- [ ] Store raw files in a consistent format

### Cleaning

- [ ] Standardize column names across all tickers
- [ ] Convert dates to a common format
- [ ] Combine all tickers into one market table
- [ ] Validate missing values and obvious anomalies

### Analysis

- [ ] Calculate daily returns
- [ ] Flag key event windows
- [ ] Identify major price and volume spikes

### Deliverables

- [ ] Export cleaned market dataset to `data/processed/market_daily.csv`
- [ ] Create a short event timeline summary for app annotations

## Track B: Reddit Data, Text, and Network

Owner: B

### Setup

- [ ] Create `data/raw/reddit/`
- [ ] Download or stage the WallStreetBets historical dataset
- [ ] Confirm which fields are available in the archive

### Mention Extraction

- [ ] Define ticker-matching rules for posts/comments
- [ ] Handle false positives for short tickers like `BB`
- [ ] Extract ticker mentions from titles and/or body text

### Aggregation

- [ ] Count daily post mentions by ticker
- [ ] Count daily comment mentions by ticker if available
- [ ] Build one daily Reddit attention table

### Text Analysis

- [ ] Identify top terms for major event windows
- [ ] Run a simple sentiment approach for selected windows
- [ ] Decide whether topic modeling is worth doing for the MVP

### Network

- [ ] Generate ticker co-mention pairs
- [ ] Aggregate co-mentions by event window
- [ ] Filter to strongest edges for readability

### Deliverables

- [ ] Export `data/processed/reddit_daily_attention.csv`
- [ ] Export `data/processed/ticker_comention_edges.csv`
- [ ] Export one summary table for text-analysis view

## Track C: Google Trends, Map, and App Shell

Owner: C

### Setup

- [ ] Create `data/raw/google_trends/`
- [ ] Create `data/raw/geography/`
- [ ] Download U.S. state boundary data

### Google Trends Collection

- [ ] Select search terms for each ticker
- [ ] Export Google Trends interest-over-time data for core terms
- [ ] Export state-level interest data for at least one key event window
- [ ] Document normalization limitations and export choices

### Mapping Prep

- [ ] Clean state names / abbreviations for joins
- [ ] Join Google Trends data to state geography
- [ ] Validate that map joins render correctly

### App Shell

- [ ] Create `app/streamlit_app.py`
- [ ] Create initial app layout and navigation
- [ ] Add sidebar filters for ticker and date range
- [ ] Add placeholder sections for timeline, network, map, and text views

### Deliverables

- [ ] Export `data/processed/google_trends_state_level.csv`
- [ ] Produce a working choropleth prototype
- [ ] Produce a basic Streamlit app shell

## Integration Tasks

Owners: A, B, C

These tasks should start after each track has at least one processed output.

- [ ] Define a shared date format across processed datasets
- [ ] Define shared ticker labels across datasets
- [ ] Create a simple data dictionary for all processed files
- [ ] Add processed-data loading utilities to the app
- [ ] Connect the market timeline to shared filters
- [ ] Connect the network view to shared filters
- [ ] Connect the map view to shared filters
- [ ] Add text-analysis summaries for selected event windows

## MVP Build Tasks

Owners: A, B, C

- [ ] Build linked time-series chart for price, volume, and Reddit attention
- [ ] Add annotations for major meme-stock events
- [ ] Add one readable co-mention network view
- [ ] Add one state-level Google Trends choropleth
- [ ] Add explanatory text for methods and limitations
- [ ] Make sure the app runs end to end with real data

## QA and Submission Tasks

Owners: A, B, C

- [ ] Check source-to-chart consistency on a sample of rows
- [ ] Test app filters and date-range interactions
- [ ] Check for broken joins or missing ticker labels
- [ ] Capture screenshots for presentation use
- [ ] Write short methodology notes
- [ ] Write short limitations notes
- [ ] Rehearse final demo flow

## Recommended Split By Week

### Week 1

- Owner A: market data collection and cleaning
- Owner B: Reddit ingestion and ticker mention extraction
- Owner C: Google Trends export workflow and Streamlit shell

### Week 2

- Owner A: timeline metrics and spike detection
- Owner B: text summaries and co-mention network generation
- Owner C: map prototype and app layout

### Week 3

- All owners: integrate datasets into the app
- All owners: polish visuals, annotations, and methods notes
- All owners: QA, presentation prep, and final fixes

## Minimum Handoff Rules

To keep the team unblocked, each owner should provide:

- One processed CSV with stable column names
- One short note describing assumptions and data limitations
- One short list of fields the app will need

## First Tasks To Start Immediately

If the team wants to begin right away, start here:

1. Owner A: collect and clean market data.
2. Owner B: set up Reddit data and build ticker mention extraction.
3. Owner C: collect Google Trends exports and scaffold the Streamlit app.
4. All owners: reconvene once the first processed datasets exist.
