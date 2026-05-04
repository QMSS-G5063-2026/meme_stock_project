# Process Book

## Project Direction

The project started from a broad proposal: connect meme-stock price movement,
Reddit discussion, Google search interest, and networked ticker attention. The
course prompt asks for an interactive website, a process book, and at least two
specialized visualization types. We chose to include three specialized views:
text, network, and map.

## Design Choices

The first design decision was to make the Streamlit app the center of the
project rather than leave results scattered across notebooks. A single app with
shared filters makes the argument easier for an audience to follow: choose an
event window, then watch the same time period flow through the market chart,
text summaries, co-mention graph, and map.

We also moved away from click-to-highlight interactions and toward an explicit
filter display in the left sidebar. This makes the active ticker selection
visible, keeps the interaction model consistent across tabs, and supports
cleaner multi-stock comparisons during a live demo.

The second decision was to keep the text analysis explainable. Instead of making
BERTopic a requirement, the Track B pipeline uses ticker extraction, daily
mention counts, VADER sentiment, top terms, and co-mentions. This is easier to
audit and less likely to fail during a live demo.

The third decision was to use Plotly's built-in U.S. state choropleth for Google
Trends. This gives a reliable geospatial visualization without introducing a
fragile shapefile join.

The final hardening pass focused on presentation clarity and event-window stock
context rather than expanding data scope. The timeline now lets the presenter
choose one focus stock, shows original event labels directly on the chart, and
adds an Event Stock View with OHLC, cumulative-return, return, and volume/spike
charts. The network view adds a top co-mentions summary before the graph, and
the map view adds a top-states table so the geographic pattern is easier to
explain during a short demo.

## Data Decisions

Market data and event annotations were already processed in the repository. For
Track C, Google Trends collection runs through `pytrends`, producing 1,020
state-level rows across 4 terms and 5 event windows. Because live collection can
be rate-limited, the project keeps cached raw Google Trends exports so the
dashboard remains reproducible during deployment.

For Track B, the local WallStreetBets archive has been processed into
app-ready Reddit attention, text-summary, and co-mention tables. The processed
outputs include 802,589 ticker-mention records from 2020-12-08 through
2021-02-04. The raw Reddit ZIP files are kept out of Git because they are too
large for normal GitHub hosting, but the committed processed tables are enough
for the Streamlit app and presentation.

## Final Demo Flow

The final app is organized to support a short presentation:

1. Overview: introduce the question and data status.
2. Timeline: choose a focus stock and connect direct event labels to stock movement.
3. Reddit/Text: explain how discussion is summarized.
4. Network: show the meme-stock basket effect and strongest co-mention pairs.
5. Map: show geographic search interest and the highest-interest states.
6. Methods: close with source notes and limitations.

## Remaining Limitation

The major limitation is coverage rather than implementation. Reddit evidence is
strongest for the archive window around the January 2021 squeeze, while the
market timeline runs through 2023-06-29. Google Trends values are normalized
relative interest values, so the map should be interpreted as a geographic
comparison within the selected export rather than raw search volume.
