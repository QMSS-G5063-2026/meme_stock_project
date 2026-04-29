from __future__ import annotations

from pathlib import Path
import textwrap

import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PRESENTATION_FIGURE = PROJECT_ROOT / "docs" / "figures" / "january_2021_market_attention_summary.png"

TICKER_ORDER = ["GME", "AMC", "BBBY", "BB", "NOK"]

EVENT_WINDOWS = {
    "Full range": ("2019-01-02", "2023-06-29"),
    "January 2021 squeeze": ("2021-01-01", "2021-02-15"),
    "AMC June 2021 run": ("2021-05-15", "2021-06-15"),
    "BBBY August 2022 squeeze": ("2022-08-01", "2022-09-15"),
    "BBBY bankruptcy": ("2023-04-01", "2023-05-15"),
}

TICKER_COLORS = {
    "GME": "#D1495B",
    "AMC": "#00798C",
    "BBBY": "#EDA93A",
    "BB": "#3E5C76",
    "NOK": "#4E937A",
}


st.set_page_config(
    page_title="Mapping Meme Stock Attention",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .block-container { padding-top: 1.6rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background: #f7f8fa;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.85rem 0.95rem;
    }
    .method-note {
        border-left: 4px solid #00798C;
        padding: 0.65rem 0.9rem;
        background: #f6fbfc;
        margin: 0.5rem 0 1rem 0;
    }
    .story-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.95rem 1rem;
        min-height: 8.5rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    .status-row {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def path_has_staged_files(path: Path) -> bool:
    if not path.exists():
        return False
    return any(item.is_file() and item.name != ".gitkeep" for item in path.rglob("*"))


@st.cache_data
def load_market_data() -> pd.DataFrame:
    path = PROCESSED_DIR / "market_daily.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    numeric_cols = [
        "open", "high", "low", "close", "adj_close", "volume",
        "daily_return", "volume_zscore", "return_zscore",
        "market_return", "abnormal_return",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["ticker"] = df["ticker"].astype(str).str.upper()
    df = df.sort_values(["ticker", "date"])
    first_price = df.groupby("ticker")["adj_close"].transform("first")
    df["indexed_price"] = df["adj_close"] / first_price * 100
    return df


@st.cache_data
def load_events() -> pd.DataFrame:
    path = PROCESSED_DIR / "event_timeline.csv"
    if not path.exists():
        return pd.DataFrame(columns=["date", "ticker", "event"])
    df = pd.read_csv(path, parse_dates=["date"])
    df["ticker"] = df["ticker"].astype(str).str.upper()
    return df.sort_values("date")


@st.cache_data
def load_optional_csv(filename: str, date_cols: tuple[str, ...] = ()) -> pd.DataFrame:
    path = PROCESSED_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=list(date_cols))


def coerce_date_range(value: object, fallback: tuple[pd.Timestamp, pd.Timestamp]) -> tuple[pd.Timestamp, pd.Timestamp]:
    if isinstance(value, tuple) and len(value) == 2:
        return pd.Timestamp(value[0]), pd.Timestamp(value[1])
    if isinstance(value, list) and len(value) == 2:
        return pd.Timestamp(value[0]), pd.Timestamp(value[1])
    return fallback


def filter_market(
    market: pd.DataFrame,
    tickers: list[str],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    return market[
        market["ticker"].isin(tickers)
        & (market["date"] >= start_date)
        & (market["date"] <= end_date)
    ].copy()


def filter_events(
    events: pd.DataFrame,
    tickers: list[str],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    return events[
        ((events["ticker"].isin(tickers)) | (events["ticker"] == "ALL"))
        & (events["date"] >= start_date)
        & (events["date"] <= end_date)
    ].copy()


def format_percent(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value * 100:.1f}%"


def visible_events(events_df: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame(columns=["date", "ticker", "event"])
    return events_df.head(limit).copy().reset_index(drop=True)


def wrap_event_label(label: object, width: int = 28) -> str:
    text = str(label)
    return "<br>".join(textwrap.wrap(text, width=width, break_long_words=False))


def add_event_lines_and_labels(
    fig: go.Figure,
    events_df: pd.DataFrame,
    *,
    label_y_start: float = 1.16,
    label_step: float = 0.055,
) -> go.Figure:
    events_to_show = visible_events(events_df)
    for idx, event in events_to_show.iterrows():
        fig.add_vline(
            x=event["date"],
            line_width=1,
            line_dash="dash",
            line_color="#5b616e",
            opacity=0.55,
        )
        fig.add_annotation(
            x=event["date"],
            y=label_y_start - label_step * (idx % 3),
            yref="paper",
            text=wrap_event_label(event["event"]),
            showarrow=False,
            textangle=-20,
            align="left",
            font=dict(size=10, color="#374151"),
            bgcolor="rgba(255,255,255,0.78)",
            bordercolor="rgba(107,114,128,0.28)",
            borderwidth=1,
            borderpad=2,
        )
    return fig


def format_signed_percent(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value * 100:+.1f}%"


def make_timeline_chart(
    market_df: pd.DataFrame,
    events_df: pd.DataFrame,
    reddit_df: pd.DataFrame,
    metric: str,
) -> go.Figure:
    metric_map = {
        "Indexed price": ("indexed_price", "Indexed price"),
        "Adjusted close": ("adj_close", "Adjusted close"),
        "Daily return": ("daily_return", "Daily return"),
        "Abnormal return": ("abnormal_return", "Abnormal return"),
    }
    y_col, y_title = metric_map[metric]
    rows = 3 if not reddit_df.empty else 2
    row_heights = [0.52, 0.28, 0.20] if rows == 3 else [0.62, 0.38]
    subplot_titles = [y_title, "Trading volume"]
    if rows == 3:
        subplot_titles.append("Reddit attention")

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=row_heights,
        subplot_titles=subplot_titles,
    )

    for ticker in [t for t in TICKER_ORDER if t in market_df["ticker"].unique()]:
        ticker_df = market_df[market_df["ticker"] == ticker]
        y_values = ticker_df[y_col]
        if y_col in {"daily_return", "abnormal_return"}:
            y_values = y_values * 100
        fig.add_trace(
            go.Scatter(
                x=ticker_df["date"],
                y=y_values,
                mode="lines",
                name=ticker,
                line=dict(color=TICKER_COLORS.get(ticker), width=2),
                hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}<extra>" + ticker + "</extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=ticker_df["date"],
                y=ticker_df["volume"],
                name=f"{ticker} volume",
                marker_color=TICKER_COLORS.get(ticker),
                opacity=0.32,
                showlegend=False,
                hovertemplate="%{x|%Y-%m-%d}<br>Volume: %{y:,.0f}<extra>" + ticker + "</extra>",
            ),
            row=2,
            col=1,
        )

    if rows == 3:
        for ticker in [t for t in TICKER_ORDER if t in reddit_df["ticker"].unique()]:
            ticker_df = reddit_df[reddit_df["ticker"] == ticker]
            fig.add_trace(
                go.Scatter(
                    x=ticker_df["date"],
                    y=ticker_df["total_mentions"],
                    mode="lines",
                    name=f"{ticker} Reddit",
                    line=dict(color=TICKER_COLORS.get(ticker), width=1.8, dash="dot"),
                    hovertemplate="%{x|%Y-%m-%d}<br>Mentions: %{y:,.0f}<extra>" + ticker + "</extra>",
                ),
                row=3,
                col=1,
            )

    add_event_lines_and_labels(fig, events_df)

    row1_title = f"{y_title}{' (%)' if y_col in {'daily_return', 'abnormal_return'} else ''}"
    fig.update_yaxes(title_text=row1_title, row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    if rows == 3:
        fig.update_yaxes(title_text="Mentions", row=3, col=1)
    fig.update_layout(
        height=760 if rows == 3 else 620,
        margin=dict(l=24, r=24, t=140, b=28),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0),
        barmode="overlay",
    )
    return fig


def make_candlestick_chart(market_df: pd.DataFrame, events_df: pd.DataFrame, focus_ticker: str) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=market_df["date"],
                open=market_df["open"],
                high=market_df["high"],
                low=market_df["low"],
                close=market_df["close"],
                name=focus_ticker,
                increasing_line_color=TICKER_COLORS.get(focus_ticker, "#00798C"),
                decreasing_line_color="#6B7280",
            )
        ]
    )
    add_event_lines_and_labels(fig, events_df, label_y_start=1.18)
    fig.update_layout(
        title=f"{focus_ticker} OHLC around selected events",
        height=520,
        margin=dict(l=20, r=20, t=140, b=30),
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
    )
    return fig


def make_cumulative_return_chart(market_df: pd.DataFrame, events_df: pd.DataFrame, focus_ticker: str) -> go.Figure:
    chart_df = market_df.copy()
    start_price = chart_df["adj_close"].dropna().iloc[0] if not chart_df["adj_close"].dropna().empty else np.nan
    if pd.notna(start_price) and start_price != 0:
        chart_df["cumulative_return"] = chart_df["adj_close"] / start_price - 1
    else:
        chart_df["cumulative_return"] = np.nan
    fig = go.Figure(
        go.Scatter(
            x=chart_df["date"],
            y=chart_df["cumulative_return"] * 100,
            mode="lines",
            name="Cumulative return",
            line=dict(color=TICKER_COLORS.get(focus_ticker, "#00798C"), width=2.4),
            hovertemplate="%{x|%Y-%m-%d}<br>Cumulative return: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#6b7280")
    add_event_lines_and_labels(fig, events_df, label_y_start=1.18)
    fig.update_layout(
        title=f"{focus_ticker} cumulative return from window start",
        height=430,
        margin=dict(l=20, r=20, t=130, b=30),
        xaxis_title="Date",
        yaxis_title="Return (%)",
        hovermode="x unified",
    )
    return fig


def make_event_return_chart(market_df: pd.DataFrame, events_df: pd.DataFrame, focus_ticker: str) -> go.Figure:
    chart_df = market_df.copy()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=chart_df["date"],
            y=chart_df["daily_return"] * 100,
            name="Daily return",
            marker_color=TICKER_COLORS.get(focus_ticker, "#00798C"),
            opacity=0.72,
            hovertemplate="%{x|%Y-%m-%d}<br>Daily return: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=chart_df["date"],
            y=chart_df["abnormal_return"] * 100,
            name="Abnormal return",
            marker_color="#D1495B",
            opacity=0.56,
            hovertemplate="%{x|%Y-%m-%d}<br>Abnormal return: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#6b7280")
    add_event_lines_and_labels(fig, events_df, label_y_start=1.18)
    fig.update_layout(
        title=f"{focus_ticker} daily vs. abnormal returns",
        height=430,
        margin=dict(l=20, r=20, t=130, b=30),
        xaxis_title="Date",
        yaxis_title="Return (%)",
        barmode="overlay",
        hovermode="x unified",
    )
    return fig


def make_volume_spike_chart(market_df: pd.DataFrame, events_df: pd.DataFrame, focus_ticker: str) -> go.Figure:
    chart_df = market_df.copy()
    volume_spike = chart_df.get("volume_spike", pd.Series(False, index=chart_df.index)).astype(bool)
    return_spike = chart_df.get("return_spike", pd.Series(False, index=chart_df.index)).astype(bool)
    spike_mask = volume_spike | return_spike
    marker_colors = np.where(spike_mask, "#D1495B", TICKER_COLORS.get(focus_ticker, "#00798C"))
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.68, 0.32],
        subplot_titles=["Trading volume", "Volume z-score"],
    )
    fig.add_trace(
        go.Bar(
            x=chart_df["date"],
            y=chart_df["volume"],
            name="Volume",
            marker_color=marker_colors,
            hovertemplate="%{x|%Y-%m-%d}<br>Volume: %{y:,.0f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=chart_df["date"],
            y=chart_df["volume_zscore"],
            mode="lines+markers",
            name="Volume z-score",
            line=dict(color="#3E5C76", width=1.8),
            marker=dict(size=np.where(spike_mask, 9, 5), color=marker_colors),
            hovertemplate="%{x|%Y-%m-%d}<br>Volume z-score: %{y:.2f}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    add_event_lines_and_labels(fig, events_df, label_y_start=1.18)
    fig.update_yaxes(title_text="Shares", row=1, col=1)
    fig.update_yaxes(title_text="Z-score", row=2, col=1)
    fig.update_layout(
        title=f"{focus_ticker} volume and flagged spike days",
        height=520,
        margin=dict(l=20, r=20, t=140, b=30),
        hovermode="x unified",
        showlegend=False,
    )
    return fig


def make_stock_summary(market_df: pd.DataFrame) -> pd.DataFrame:
    if market_df.empty:
        return pd.DataFrame()
    chart_df = market_df.sort_values("date").copy()
    priced_df = chart_df.dropna(subset=["adj_close"])
    if priced_df.empty:
        return pd.DataFrame()
    start_row = priced_df.iloc[0]
    end_row = priced_df.iloc[-1]
    peak_volume_row = chart_df.loc[chart_df["volume"].idxmax()]
    largest_gain_row = chart_df.loc[chart_df["daily_return"].idxmax()]
    largest_loss_row = chart_df.loc[chart_df["daily_return"].idxmin()]
    volume_spike = chart_df.get("volume_spike", pd.Series(False, index=chart_df.index)).astype(bool)
    return_spike = chart_df.get("return_spike", pd.Series(False, index=chart_df.index)).astype(bool)
    spike_days = int(
        (volume_spike | return_spike).sum()
    )
    summary = [
        {"metric": "Start price", "value": f"${start_row['adj_close']:.2f} on {start_row['date'].date()}"},
        {"metric": "End price", "value": f"${end_row['adj_close']:.2f} on {end_row['date'].date()}"},
        {"metric": "Cumulative return", "value": format_signed_percent(end_row["adj_close"] / start_row["adj_close"] - 1)},
        {"metric": "Peak volume", "value": f"{peak_volume_row['volume']:,.0f} on {peak_volume_row['date'].date()}"},
        {"metric": "Largest daily gain", "value": f"{format_signed_percent(largest_gain_row['daily_return'])} on {largest_gain_row['date'].date()}"},
        {"metric": "Largest daily loss", "value": f"{format_signed_percent(largest_loss_row['daily_return'])} on {largest_loss_row['date'].date()}"},
        {"metric": "Flagged spike days", "value": f"{spike_days:,}"},
    ]
    return pd.DataFrame(summary)


def make_network_chart(edges: pd.DataFrame) -> go.Figure:
    graph = nx.Graph()
    for _, row in edges.iterrows():
        graph.add_edge(row["source"], row["target"], weight=float(row["weight"]))

    if graph.number_of_nodes() == 0:
        return go.Figure()

    positions = nx.spring_layout(graph, seed=42, weight="weight", k=0.8)
    max_weight = max(nx.get_edge_attributes(graph, "weight").values())

    edge_traces = []
    for source, target, data in graph.edges(data=True):
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        width = 1.2 + 5.5 * data["weight"] / max_weight
        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=width, color="rgba(88, 96, 115, 0.45)"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    degrees = dict(graph.degree(weight="weight"))
    max_degree = max(degrees.values()) if degrees else 1
    node_x, node_y, node_size, node_text, node_color = [], [], [], [], []
    for node in graph.nodes():
        x_pos, y_pos = positions[node]
        node_x.append(x_pos)
        node_y.append(y_pos)
        node_size.append(22 + 32 * degrees[node] / max_degree)
        node_text.append(f"{node}<br>Weighted degree: {degrees[node]:,.0f}")
        node_color.append(TICKER_COLORS.get(node, "#00798C"))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=list(graph.nodes()),
        textposition="middle center",
        hovertext=node_text,
        hoverinfo="text",
        marker=dict(size=node_size, color=node_color, line=dict(width=1.5, color="white")),
        textfont=dict(color="white", size=12),
        showlegend=False,
    )

    fig = go.Figure(data=[*edge_traces, node_trace])
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="white",
    )
    return fig


def data_status_note(kind: str) -> str:
    raw_path = RAW_DIR / kind
    if path_has_staged_files(raw_path):
        return "Raw source files are staged locally."
    return "Using committed processed outputs; raw source files are not required to run the app."


def file_status(dictionary: pd.DataFrame, filename: str) -> str:
    if dictionary.empty or "file" not in dictionary.columns or "status" not in dictionary.columns:
        return "unknown"
    match = dictionary[dictionary["file"] == filename]
    if match.empty:
        return "unknown"
    return str(match.iloc[0]["status"])


def is_fallback_status(status: str) -> bool:
    return "fallback" in status.lower()


market = load_market_data()
events = load_events()
reddit_attention = load_optional_csv("reddit_daily_attention.csv", ("date",))
edges = load_optional_csv("ticker_comention_edges.csv")
text_summary = load_optional_csv("reddit_text_summary.csv")
google_trends = load_optional_csv("google_trends_state_level.csv")
data_dictionary = load_optional_csv("data_dictionary.csv")
google_summary = load_optional_csv("google_trends_collection_summary.csv")
reddit_summary = load_optional_csv("reddit_processing_summary.csv")

reddit_status = file_status(data_dictionary, "reddit_daily_attention.csv")
network_status = file_status(data_dictionary, "ticker_comention_edges.csv")
text_status = file_status(data_dictionary, "reddit_text_summary.csv")
trends_status = file_status(data_dictionary, "google_trends_state_level.csv")

available_tickers = [ticker for ticker in TICKER_ORDER if ticker in set(market["ticker"])]
market_min = market["date"].min()
market_max = market["date"].max()

with st.sidebar:
    st.header("Filters")
    selected_tickers = st.multiselect(
        "Tickers",
        available_tickers,
        default=[ticker for ticker in ["GME", "AMC", "BBBY"] if ticker in available_tickers],
    )
    if not selected_tickers:
        selected_tickers = available_tickers[:1]
        st.warning("At least one ticker is required. Showing the first available ticker.")

    selected_window = st.selectbox("Event window", list(EVENT_WINDOWS.keys()), index=1)
    default_start, default_end = EVENT_WINDOWS[selected_window]
    fallback_range = (
        max(pd.Timestamp(default_start), market_min),
        min(pd.Timestamp(default_end), market_max),
    )
    selected_dates = st.date_input(
        "Date range",
        value=(fallback_range[0].date(), fallback_range[1].date()),
        min_value=market_min.date(),
        max_value=market_max.date(),
    )
    start_date, end_date = coerce_date_range(selected_dates, fallback_range)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    market_metric = st.selectbox(
        "Timeline market metric",
        ["Indexed price", "Adjusted close", "Daily return", "Abnormal return"],
        index=0,
    )

    st.divider()
    st.caption("Processed data status")
    st.write(f"Reddit/text/network: {reddit_status}")
    st.write(f"Google Trends/map: {trends_status}")


filtered_market = filter_market(market, selected_tickers, start_date, end_date)
filtered_events = filter_events(events, selected_tickers, start_date, end_date)
filtered_reddit = pd.DataFrame()
if not reddit_attention.empty:
    filtered_reddit = reddit_attention[
        reddit_attention["ticker"].isin(selected_tickers)
        & (reddit_attention["date"] >= start_date)
        & (reddit_attention["date"] <= end_date)
    ].copy()


st.title("Mapping Meme Stock Attention")
st.markdown(
    "An interactive dashboard connecting meme-stock market behavior, Reddit attention, "
    "ticker co-mentions, and state-level Google search interest."
)

fallback_messages = []
if is_fallback_status(reddit_status) or is_fallback_status(network_status) or is_fallback_status(text_status):
    fallback_messages.append(
        "Reddit/text/network views use labeled fallback data because source exports were unavailable during processing."
    )
if is_fallback_status(trends_status):
    fallback_messages.append("The map uses labeled fallback Google Trends data.")
if fallback_messages:
    st.warning(" ".join(fallback_messages))
else:
    st.success("Market, Reddit/text/network, and Google Trends data are loaded from processed project/API outputs.")

if filtered_market.empty:
    st.error("No market rows match the selected filters. Adjust the date range or ticker selection.")
    st.stop()


tab_overview, tab_timeline, tab_text, tab_network, tab_map, tab_presentation, tab_methods = st.tabs(
    ["Overview", "Timeline", "Reddit/Text", "Network", "Map", "Presentation", "Methods"]
)


with tab_overview:
    st.subheader("Audience Takeaways")
    story_cols = st.columns(3)
    with story_cols[0]:
        st.markdown(
            """
            <div class="story-card">
            <strong>1. Attention and volatility move together.</strong><br>
            The January 2021 window gives the clearest example: price, volume,
            Reddit attention, and search interest all spike around the same event cluster.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with story_cols[1]:
        st.markdown(
            """
            <div class="story-card">
            <strong>2. Meme stocks behave like a basket.</strong><br>
            The co-mention network shows how GME, AMC, BB, NOK, and BBBY are discussed
            together rather than as isolated companies.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with story_cols[2]:
        st.markdown(
            """
            <div class="story-card">
            <strong>3. Search interest adds geography.</strong><br>
            State-level Google Trends data turns the story from a market chart into
            a map of broader public attention.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Project Snapshot")
    selected_rows = len(filtered_market)
    selected_events = len(filtered_events)
    max_abs_return = filtered_market["daily_return"].abs().max()
    peak_volume_row = filtered_market.loc[filtered_market["volume"].idxmax()]
    reddit_mentions = int(filtered_reddit["total_mentions"].sum()) if not filtered_reddit.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trading days shown", f"{filtered_market['date'].nunique():,}")
    c2.metric("Market rows", f"{selected_rows:,}")
    c3.metric("Max absolute daily return", format_percent(max_abs_return))
    c4.metric("Reddit mentions", f"{reddit_mentions:,}" if reddit_mentions else "n/a")

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown(
            """
            This MVP is organized around a simple question: when retail attention spiked,
            did prices, volume, and public search behavior move at the same time?

            Use the sidebar to select tickers and event windows. The same filters drive
            the market timeline, Reddit/text summaries, co-mention network, and map view.
            """
        )
        st.markdown(
            f"""
            <div class="method-note">
            Current window: <strong>{start_date.date()} to {end_date.date()}</strong>.
            Peak volume in this selection is <strong>{peak_volume_row['ticker']}</strong>
            on <strong>{peak_volume_row['date'].date()}</strong>
            with <strong>{peak_volume_row['volume']:,.0f}</strong> shares traded.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        if not filtered_events.empty:
            st.write("Event annotations in the selected window")
            st.dataframe(
                filtered_events.assign(date=filtered_events["date"].dt.date),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No event annotations fall inside this selection.")

    st.subheader("Data Coverage")
    coverage = (
        market.groupby("ticker")
        .agg(start=("date", "min"), end=("date", "max"), rows=("date", "count"))
        .reset_index()
    )
    coverage["start"] = coverage["start"].dt.date
    coverage["end"] = coverage["end"].dt.date
    st.dataframe(coverage, width="stretch", hide_index=True)

    st.subheader("Source Status")
    status_cols = st.columns(3)
    with status_cols[0]:
        st.markdown(
            f"""<div class="status-row"><strong>Market timeline</strong><br>{file_status(data_dictionary, "market_daily.csv")}</div>""",
            unsafe_allow_html=True,
        )
    with status_cols[1]:
        st.markdown(
            f"""<div class="status-row"><strong>Reddit/text/network</strong><br>{reddit_status}</div>""",
            unsafe_allow_html=True,
        )
    with status_cols[2]:
        st.markdown(
            f"""<div class="status-row"><strong>Google Trends map</strong><br>{trends_status}</div>""",
            unsafe_allow_html=True,
        )


with tab_timeline:
    st.subheader("Linked Market and Attention Timeline")
    default_focus = selected_tickers[0] if selected_tickers else available_tickers[0]
    focus_index = available_tickers.index(default_focus) if default_focus in available_tickers else 0
    timeline_focus_ticker = st.selectbox(
        "Timeline focus stock",
        available_tickers,
        index=focus_index,
    )

    timeline_market = filter_market(market, [timeline_focus_ticker], start_date, end_date)
    timeline_events = filter_events(events, [timeline_focus_ticker], start_date, end_date)
    timeline_reddit = pd.DataFrame()
    if not reddit_attention.empty:
        timeline_reddit = reddit_attention[
            (reddit_attention["ticker"] == timeline_focus_ticker)
            & (reddit_attention["date"] >= start_date)
            & (reddit_attention["date"] <= end_date)
        ].copy()

    if timeline_market.empty:
        st.warning("No market rows match the timeline focus stock and date range.")
    else:
        fig = make_timeline_chart(timeline_market, timeline_events, timeline_reddit, market_metric)
        st.plotly_chart(fig, width="stretch")
        if timeline_events.empty:
            st.info("No event annotations fall inside the selected timeline window.")
        st.caption(
            f"Timeline is focused on {timeline_focus_ticker}. Event labels use the original event text directly on the chart. "
            f"Market data are processed project data. Reddit attention status: {reddit_status}."
        )

        st.subheader("Event Stock View")
        summary = make_stock_summary(timeline_market)
        if not summary.empty:
            st.dataframe(summary, width="stretch", hide_index=True)

        st.plotly_chart(
            make_candlestick_chart(timeline_market, timeline_events, timeline_focus_ticker),
            width="stretch",
        )

        return_col, abnormal_col = st.columns(2)
        with return_col:
            st.plotly_chart(
                make_cumulative_return_chart(timeline_market, timeline_events, timeline_focus_ticker),
                width="stretch",
            )
        with abnormal_col:
            st.plotly_chart(
                make_event_return_chart(timeline_market, timeline_events, timeline_focus_ticker),
                width="stretch",
            )

        st.plotly_chart(
            make_volume_spike_chart(timeline_market, timeline_events, timeline_focus_ticker),
            width="stretch",
        )


with tab_text:
    st.subheader("Reddit Attention and Text Signals")
    if filtered_reddit.empty:
        st.warning("No Reddit attention table is available for the selected filters.")
    else:
        mention_by_ticker = (
            filtered_reddit.groupby("ticker", as_index=False)
            .agg(
                post_mentions=("post_mentions", "sum"),
                comment_mentions=("comment_mentions", "sum"),
                total_mentions=("total_mentions", "sum"),
                sentiment_mean=("sentiment_mean", "mean"),
            )
            .sort_values("total_mentions", ascending=False)
        )

        c1, c2 = st.columns([1.15, 1])
        with c1:
            mentions_fig = px.bar(
                mention_by_ticker,
                x="ticker",
                y=["post_mentions", "comment_mentions"],
                color_discrete_sequence=["#00798C", "#D1495B"],
                labels={"value": "Mentions", "variable": "Type", "ticker": "Ticker"},
                title="Attention by ticker",
            )
            mentions_fig.update_layout(height=390, margin=dict(l=20, r=20, t=55, b=20))
            st.plotly_chart(mentions_fig, width="stretch")
        with c2:
            sentiment_fig = px.bar(
                mention_by_ticker,
                x="ticker",
                y="sentiment_mean",
                color="ticker",
                color_discrete_map=TICKER_COLORS,
                labels={"sentiment_mean": "Mean sentiment", "ticker": "Ticker"},
                title="Simple sentiment by ticker",
            )
            sentiment_fig.add_hline(y=0, line_dash="dash", line_color="#6b7280")
            sentiment_fig.update_layout(height=390, showlegend=False, margin=dict(l=20, r=20, t=55, b=20))
            st.plotly_chart(sentiment_fig, width="stretch")

    if text_summary.empty:
        st.warning("No text summary table is available.")
    else:
        text_window_options = ["All windows", *text_summary["window"].drop_duplicates().tolist()]
        default_text_idx = text_window_options.index(selected_window) if selected_window in text_window_options else 0
        text_window = st.selectbox("Text summary window", text_window_options, index=default_text_idx)
        text_filtered = text_summary[text_summary["ticker"].isin(selected_tickers)].copy()
        if text_window != "All windows":
            text_filtered = text_filtered[text_filtered["window"] == text_window]
        if text_filtered.empty:
            st.info("No top-term rows match the selected tickers and text window.")
        else:
            top_terms = text_filtered.sort_values("count", ascending=False).head(18)
            term_fig = px.bar(
                top_terms,
                x="count",
                y="term",
                color="sentiment_label",
                facet_col="ticker" if top_terms["ticker"].nunique() > 1 else None,
                orientation="h",
                color_discrete_map={
                    "positive": "#4E937A",
                    "neutral": "#6B7280",
                    "negative": "#D1495B",
                },
                labels={"count": "Count", "term": "Term"},
                title="Top terms by event window",
            )
            term_fig.update_yaxes(categoryorder="total ascending")
            term_fig.update_layout(height=470, margin=dict(l=20, r=20, t=65, b=20))
            st.plotly_chart(term_fig, width="stretch")


with tab_network:
    st.subheader("Ticker Co-Mention Network")
    if edges.empty:
        st.warning("No co-mention edge table is available.")
    else:
        network_windows = edges["window"].drop_duplicates().tolist()
        default_network_idx = network_windows.index(selected_window) if selected_window in network_windows else 0
        controls = st.columns([1, 1, 2])
        with controls[0]:
            network_window = st.selectbox("Network window", network_windows, index=default_network_idx)
        candidate_edges = edges[edges["window"] == network_window].copy()
        candidate_edges = candidate_edges[
            candidate_edges["source"].isin(selected_tickers) | candidate_edges["target"].isin(selected_tickers)
        ]
        max_edge = int(candidate_edges["weight"].max()) if not candidate_edges.empty else 1
        with controls[1]:
            min_edge = st.slider("Minimum edge weight", 1, max(max_edge, 1), min(100, max(max_edge, 1)))
        network_edges = candidate_edges[candidate_edges["weight"] >= min_edge]

        if network_edges.empty:
            st.info("No edges survive the current ticker and weight filters.")
        else:
            edge_table = network_edges.sort_values("weight", ascending=False)
            top_edge = edge_table.iloc[0]
            connected_tickers = sorted(
                set(edge_table["source"].tolist()) | set(edge_table["target"].tolist())
            )

            summary_cols = st.columns(3)
            summary_cols[0].metric(
                "Strongest pair",
                f"{top_edge['source']} + {top_edge['target']}",
                f"{int(top_edge['weight']):,} co-mentions",
            )
            summary_cols[1].metric("Edges shown", f"{len(edge_table):,}")
            summary_cols[2].metric("Connected tickers", f"{len(connected_tickers):,}")

            st.write("Top co-mentions in this view")
            top_pairs = edge_table.head(5).copy()
            top_pairs.insert(
                0,
                "pair",
                top_pairs["source"].astype(str) + " + " + top_pairs["target"].astype(str),
            )
            st.dataframe(
                top_pairs[["pair", "window", "weight"]],
                width="stretch",
                hide_index=True,
            )
            st.plotly_chart(make_network_chart(network_edges), width="stretch")
            st.dataframe(edge_table, width="stretch", hide_index=True)

        st.caption(
            "Edges represent posts/comments where two tickers appear together in the same event window. "
            f"Current network data status: {network_status}."
        )


with tab_map:
    st.subheader("State-Level Google Trends Interest")
    if google_trends.empty:
        st.warning("No Google Trends state-level table is available.")
    else:
        map_windows = google_trends["window"].drop_duplicates().tolist()
        map_terms = google_trends["term"].drop_duplicates().tolist()
        default_map_window = map_windows.index(selected_window) if selected_window in map_windows else 0
        map_controls = st.columns([1, 1, 2])
        with map_controls[0]:
            map_window = st.selectbox("Map window", map_windows, index=default_map_window)
        with map_controls[1]:
            map_term = st.selectbox("Search term", map_terms)

        map_df = google_trends[
            (google_trends["window"] == map_window) & (google_trends["term"] == map_term)
        ].copy()
        if map_df.empty:
            st.info("No state-level rows match the selected map controls.")
        else:
            map_fig = px.choropleth(
                map_df,
                locations="state_code",
                locationmode="USA-states",
                color="interest",
                scope="usa",
                hover_name="state",
                hover_data={"state_code": False, "interest": True},
                color_continuous_scale="RdYlBu_r",
                range_color=(0, 100),
                labels={"interest": "Relative interest"},
                title=f"Relative Google Trends interest: {map_term}",
            )
            map_fig.update_layout(height=570, margin=dict(l=10, r=10, t=55, b=10))
            st.plotly_chart(map_fig, width="stretch")
            top_states = (
                map_df.sort_values(["interest", "state"], ascending=[False, True])
                .head(10)
                .reset_index(drop=True)
            )
            top_states.insert(0, "rank", np.arange(1, len(top_states) + 1))
            st.write("Top states for the selected term and window")
            st.dataframe(
                top_states[["rank", "state", "state_code", "interest"]],
                width="stretch",
                hide_index=True,
            )

        st.markdown(
            """
            <div class="method-note">
            Google Trends reports normalized relative interest, not raw search counts.
            State values should be interpreted within the selected term and export window.
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not google_summary.empty:
            st.caption(
                "Collection summary: "
                + ", ".join(
                    f"{row.metric}={row.value}"
                    for row in google_summary.itertuples(index=False)
                    if row.metric in {"data_status", "rows", "terms", "windows", "failures"}
                )
            )


with tab_presentation:
    st.subheader("Presentation Path")
    st.markdown(
        """
        Use this sequence for a short live demo:

        1. Start in **Overview** and state the guiding question: how did online attention, search interest, and market volatility line up?
        2. Move to **Timeline**, keep the January 2021 window, and point to the synchronized spike in price, volume, and attention.
        3. Move to **Network** and show the meme-stock basket relationship with GME and AMC as the most connected pair.
        4. Move to **Map** and switch between `GameStop`, `AMC stock`, and `WallStreetBets` to show geographic variation in search interest.
        5. End in **Methods** with the data-status table and limitations.
        """
    )
    if PRESENTATION_FIGURE.exists():
        st.image(str(PRESENTATION_FIGURE), caption="Static presentation figure for the January 2021 event window.")
    else:
        st.info("Run `python -m src.processing.build_static_figures` to generate the static presentation figure.")

    st.subheader("What Is Ready")
    ready_cols = st.columns(3)
    ready_cols[0].metric("Interactive views", "5")
    ready_cols[1].metric("Specialized types", "3")
    ready_cols[2].metric("Google Trends rows", f"{len(google_trends):,}" if not google_trends.empty else "0")
    st.markdown(
        """
        The site demonstrates all three specialized types from the course prompt:
        geospatial mapping, text analysis visualization, and network visualization.
        The main remaining empirical caveats are coverage and normalization:
        Reddit evidence is strongest around the local archive window, and Google
        Trends reports relative interest rather than raw search counts.
        """
    )


with tab_methods:
    st.subheader("Methods and Limitations")
    st.markdown(
        f"""
        The website is built around deploy-friendly local CSVs. The market and event
        timeline tables are processed project outputs. Google Trends is currently
        loaded as **{trends_status}**. Reddit/text/network data are currently
        **{reddit_status}**. Raw Reddit ZIP files are intentionally kept out of Git,
        but the processed tables needed by the app are committed.

        Track B uses simple, explainable text analysis:
        ticker mention counts, VADER sentiment, event-window top terms, and ticker
        co-mentions. Track C uses Plotly's built-in U.S. state choropleth rendering
        from state codes to avoid brittle shapefile joins.
        """
    )

    if not data_dictionary.empty:
        st.write("Processed data dictionary")
        st.dataframe(data_dictionary, width="stretch", hide_index=True)

    st.write("Expected processed files")
    expected = pd.DataFrame(
        [
            {"file": "market_daily.csv", "required": "yes", "view": "Timeline"},
            {"file": "event_timeline.csv", "required": "yes", "view": "Timeline annotations"},
            {"file": "reddit_daily_attention.csv", "required": "optional", "view": "Timeline, Reddit/Text"},
            {"file": "ticker_comention_edges.csv", "required": "optional", "view": "Network"},
            {"file": "reddit_text_summary.csv", "required": "optional", "view": "Reddit/Text"},
            {"file": "google_trends_state_level.csv", "required": "optional", "view": "Map"},
        ]
    )
    expected["present"] = expected["file"].map(lambda filename: (PROCESSED_DIR / filename).exists())
    st.dataframe(expected, width="stretch", hide_index=True)

    with st.expander("Run locally"):
        st.code("python -m streamlit run app/streamlit_app.py", language="bash")

    with st.expander("Rebuild Track B/C outputs"):
        st.code("python -m src.processing.build_all_track_b_c", language="bash")
