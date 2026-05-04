# Project Plan: Mapping Meme Stock Attention

## 1. Project Goal

Build an interactive web app that shows how meme-stock attention moved across Reddit discussion, Google search interest, and market behavior during major retail trading events. The app should help users compare tickers, explore key event windows, and connect social attention with market volatility.

## 2. Recommended MVP

The minimum viable version should include:

- A linked time-series dashboard for 3-5 meme stocks (`GME`, `AMC`, `BBBY`, `BB`, `NOK`)
- Reddit attention metrics over time (post/comment counts and basic keyword or sentiment summaries)
- One co-mention network view showing how tickers were discussed together
- One U.S. state-level Google Trends choropleth for selected terms and event windows
- A deployed Streamlit app with clear narrative annotations for major market events

Stretch goals:

- BERTopic or more advanced topic modeling
- User-to-ticker network exploration
- Metro-level Google Trends maps
- Short-sale volume and fails-to-deliver integration

## 3. Final Deliverables

- Interactive Streamlit application
- Cleaned datasets and reproducible data-processing scripts
- Visual assets for presentation and report use
- Short written documentation explaining data sources, methods, and limitations
- Final presentation/demo materials

## 4. Project Workstreams

### A. Data Collection and Validation

Goal: confirm which sources are usable, complete, and worth keeping in scope.

Tasks:

- Finalize ticker list and event windows
- Pull historical price and trading-volume data
- Acquire historical WallStreetBets archive data
- Test Google Trends export workflow for chosen terms
- Evaluate whether short-sale volume and fails-to-deliver data are feasible for the timeline
- Create a shared data dictionary with source notes, time coverage, and known gaps

Output:

- Raw data files stored by source
- Data inventory table
- Go/no-go decision on optional datasets

### B. Data Cleaning and Integration

Goal: build one analysis-ready dataset layer for the app.

Tasks:

- Standardize dates, ticker symbols, and time zones
- Aggregate Reddit data to daily counts by ticker
- Extract co-mentions from posts/comments
- Prepare sentiment and keyword features for selected windows
- Normalize Google Trends exports for cross-window comparison where possible
- Join market, Reddit, and search-interest data at consistent daily granularity

Output:

- Clean analysis tables for:
  - market metrics by ticker and date
  - Reddit attention by ticker and date
  - co-mention edges by time window
  - state-level Google Trends intensity by term and window

### C. Analysis and Story Development

Goal: identify the strongest patterns and shape the app narrative.

Tasks:

- Mark major market events and retail-trading milestones
- Compare attention spikes against returns and volume
- Identify dominant terms, themes, and sentiment shifts
- Filter network edges to the strongest and most interpretable relationships
- Select a small number of story beats to feature in the app

Output:

- Key findings list
- Annotated event timeline
- Short narrative outline for the final app/demo

### D. Visualization and App Development

Goal: turn the cleaned data and analysis into a polished interactive experience.

Tasks:

- Build a multi-view Streamlit layout
- Create linked time-series charts with shared filters
- Add a network view for co-mentioned tickers
- Add a state-level choropleth for search interest
- Add text-analysis summaries for selected event windows
- Include explanatory annotations, legends, and method notes

Output:

- Working app with stable navigation and consistent filters

### E. QA, Documentation, and Presentation

Goal: make the project reliable, explainable, and ready to submit.

Tasks:

- Test app interactions and edge cases
- Verify charts against source data samples
- Write concise methodology and limitation notes
- Prepare screenshots and backup static figures
- Rehearse a short live demo path

Output:

- Submission-ready app and presentation assets

## 5. Proposed Execution Sequence

### Phase 1: Scope Lock and Setup

Target outcome: confirm the MVP and establish the repo structure.

Checklist:

- Confirm final ticker list
- Confirm primary date range
- Create folders for `data/raw`, `data/processed`, `src`, `app`, and `docs`
- Decide which optional sources are in or out

### Phase 2: Data Pipeline

Target outcome: generate clean daily datasets that support the MVP views.

Checklist:

- Pull and store market data
- Ingest Reddit archive data
- Create ticker mention extraction logic
- Build daily aggregates
- Export processed tables for visualization

### Phase 3: Exploratory Analysis

Target outcome: identify what is worth highlighting in the final story.

Checklist:

- Locate attention spikes
- Compare spikes with price and volume
- Build first-pass co-mention network
- Test term/sentiment summaries
- Pick 3-5 major event windows

### Phase 4: App Build

Target outcome: ship the MVP experience end to end.

Checklist:

- Build filters and shared controls
- Add time-series dashboard
- Add network view
- Add map view
- Add event annotations and explanatory text

### Phase 5: Polish and Submission

Target outcome: make the project clear, reliable, and presentation-ready.

Checklist:

- Simplify cluttered views
- Add method notes and source citations
- Test with classmates or teammates
- Prepare final presentation flow

## 6. Suggested Team Split

If the team wants parallel work, use this split:

- Person 1: market data pipeline, event timeline, linked time-series charts
- Person 2: Reddit ingestion, text analysis, co-mention network generation
- Person 3: Google Trends mapping, Streamlit integration, polish/documentation

Shared responsibility:

- Scope decisions
- App design consistency
- Final QA and presentation

## 7. Proposed Repository Structure

```text
meme_stock_project/
|-- app/
|   `-- streamlit_app.py
|-- data/
|   |-- raw/
|   `-- processed/
|-- docs/
|   |-- methods.md
|   |-- project_plan.md
|   |-- task_list.md
|   |-- meme_stock_project_proposal.pdf
|   `-- figures/
|-- notebooks/
|   |-- market_daily_processing.ipynb
|   `-- market_daily_visualization.ipynb
|-- src/
|   |-- data_collection/
|   |-- processing/
|   |-- analysis/
|   `-- visualization/
`-- README.md
```

## 8. Risks and Mitigations

### Risk: Reddit data are noisy or incomplete

Mitigation:

- Focus on the best-covered historical archive period
- Use simple, robust mention counts before advanced NLP

### Risk: Google Trends data are normalized and inconsistent across exports

Mitigation:

- Use clearly labeled relative comparisons
- Limit the number of terms and time windows
- Fall back to state-level mapping only

### Risk: Network graphs become unreadable

Mitigation:

- Filter to strongest edges
- Limit the number of tickers and windows shown at once
- Provide threshold controls in the app

### Risk: Optional market microstructure data delay the MVP

Mitigation:

- Treat short-sale volume and fails-to-deliver data as stretch goals
- Do not block the MVP on those sources

## 9. Definition of Done

The project is ready when:

- Users can compare at least three meme stocks in one app
- The app clearly links attention and market behavior over time
- The network and map views both function with real project data
- The narrative highlights a few interpretable findings instead of showing every possible chart
- Methods and limitations are documented clearly enough for class review

## 10. Immediate Next Steps

1. Lock the ticker list and main analysis window.
2. Create the repo folders and starter app structure.
3. Acquire and validate the first two datasets: market data and WallStreetBets archive.
4. Produce one clean daily table with price, volume, and Reddit mention counts.
5. Build a first-pass timeline chart before expanding into text, network, and map views.
