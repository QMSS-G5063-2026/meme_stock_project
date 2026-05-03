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

WINDOW_DEFAULT_TERMS = {
    "January 2021 squeeze": "GameStop",
    "AMC June 2021 run": "AMC stock",
    "BBBY August 2022 squeeze": "BBBY stock",
    "BBBY bankruptcy": "BBBY stock",
}

TICKER_SEARCH_TERMS = {
    "GME": "GameStop",
    "AMC": "AMC stock",
    "BBBY": "BBBY stock",
}


st.set_page_config(
    page_title="Mapping Meme Stock Attention",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="auto",
)


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    h1, h2, h3 {
        letter-spacing: 0;
        overflow-wrap: anywhere;
    }
    h1 {
        font-size: 2.25rem;
        font-weight: 680;
        margin-bottom: 0.25rem;
    }
    h2, h3 {
        color: #111827;
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e8eaef;
        border-radius: 6px;
        padding: 0.75rem 0.85rem;
        box-shadow: none;
    }
    div[data-testid="stMetric"] label {
        color: #6b7280;
        font-weight: 500;
    }
    .summary-note {
        background: #ffffff;
        border-top: 1px solid #e8eaef;
        border-bottom: 1px solid #e8eaef;
        padding: 1rem 0;
        margin: 0.25rem 0 1rem 0;
        color: #374151;
        line-height: 1.55;
        overflow-wrap: anywhere;
    }
    .summary-note p {
        margin: 0 0 0.35rem 0;
    }
    .summary-note p:last-child {
        margin-bottom: 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 1px solid #eceff3;
        overflow-x: auto;
        overflow-y: hidden;
        flex-wrap: nowrap;
    }
    .stTabs [data-baseweb="tab"] {
        padding-left: 0.75rem;
        padding-right: 0.75rem;
        flex: 0 0 auto;
        white-space: nowrap;
    }
    div[data-testid="stAppViewContainer"] {
        overflow-x: hidden;
    }
    .mobile-title-break {
        display: none;
    }
    @media (max-width: 640px) {
        div[data-testid="stAppViewContainer"],
        div[data-testid="stMain"],
        main {
            max-width: 100vw !important;
            min-width: 0 !important;
            overflow-x: hidden !important;
        }
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 0.85rem;
            max-width: calc(100vw - 2rem) !important;
            min-width: 0 !important;
            width: calc(100vw - 2rem) !important;
        }
        h1 {
            font-size: 1.85rem;
            line-height: 1.15;
            max-width: calc(100vw - 3rem) !important;
            white-space: normal !important;
        }
        h1 span,
        div[data-testid="stMarkdownContainer"],
        div[data-testid="stMarkdownContainer"] p {
            max-width: calc(100vw - 3rem) !important;
            white-space: normal !important;
            overflow-wrap: anywhere;
        }
        .summary-note {
            max-width: calc(100vw - 3rem) !important;
        }
        .summary-note,
        .summary-note * {
            overflow-wrap: anywhere;
        }
        .mobile-title-break {
            display: block;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 0.55rem;
            padding-right: 0.55rem;
        }
        div[data-testid="stMetric"] {
            padding: 0.65rem 0.7rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def processed_file_fingerprint(filename: str) -> tuple[int, int]:
    path = PROCESSED_DIR / filename
    if not path.exists():
        return (0, 0)
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


@st.cache_data
def load_optional_csv(
    filename: str,
    date_cols: tuple[str, ...] = (),
    file_fingerprint: tuple[int, int] = (0, 0),
) -> pd.DataFrame:
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


def format_compact_number(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    abs_value = abs(float(value))
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs_value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def visible_events(events_df: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame(columns=["date", "ticker", "event"])
    return events_df.head(limit).copy().reset_index(drop=True)


def date_span(df: pd.DataFrame, date_col: str = "date") -> tuple[pd.Timestamp, pd.Timestamp] | None:
    if df.empty or date_col not in df.columns:
        return None
    dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
    if dates.empty:
        return None
    return pd.Timestamp(dates.min()), pd.Timestamp(dates.max())


def reddit_coverage_message(
    reddit_df: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    selected_window: str,
) -> str:
    span = date_span(reddit_df)
    if span is None:
        return ""
    reddit_start, reddit_end = span
    if start_date <= reddit_end and end_date >= reddit_start:
        return ""
    return (
        f"Reddit archive covers {reddit_start.date()} to {reddit_end.date()}, so Reddit/Text and "
        f"Network views do not represent {selected_window} ({start_date.date()} to {end_date.date()}). "
        "Market and Map views still use the selected event window."
    )


def preferred_map_term(map_terms: list[str], selected_window: str, selected_tickers: list[str]) -> str:
    candidates = [
        WINDOW_DEFAULT_TERMS.get(selected_window, ""),
        *(TICKER_SEARCH_TERMS.get(ticker, "") for ticker in selected_tickers),
        "GameStop",
    ]
    for candidate in candidates:
        if candidate and candidate in map_terms:
            return candidate
    return map_terms[0] if map_terms else ""


def wrap_event_label(label: object, width: int = 26) -> str:
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
            textangle=-18,
            align="left",
            font=dict(size=9, color="#374151"),
            bgcolor="rgba(255,255,255,0.82)",
            bordercolor="rgba(107,114,128,0.3)",
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


def padded_axis_range(values: list[float], pad_ratio: float = 0.2) -> list[float] | None:
    if not values:
        return None
    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        return [min_value - 1, max_value + 1]
    pad = (max_value - min_value) * pad_ratio
    return [min_value - pad, max_value + pad]


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
        cliponaxis=False,
        showlegend=False,
    )

    fig = go.Figure(data=[*edge_traces, node_trace])
    fig.update_layout(
        height=520,
        margin=dict(l=24, r=24, t=16, b=16),
        xaxis=dict(visible=False, range=padded_axis_range(node_x)),
        yaxis=dict(visible=False, range=padded_axis_range(node_y)),
        plot_bgcolor="white",
    )
    return fig


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
reddit_attention = load_optional_csv(
    "reddit_daily_attention.csv",
    ("date",),
    processed_file_fingerprint("reddit_daily_attention.csv"),
)
edges = load_optional_csv(
    "ticker_comention_edges.csv",
    file_fingerprint=processed_file_fingerprint("ticker_comention_edges.csv"),
)
text_summary = load_optional_csv(
    "reddit_text_summary.csv",
    file_fingerprint=processed_file_fingerprint("reddit_text_summary.csv"),
)
google_trends = load_optional_csv(
    "google_trends_state_level.csv",
    file_fingerprint=processed_file_fingerprint("google_trends_state_level.csv"),
)
data_dictionary = load_optional_csv(
    "data_dictionary.csv",
    file_fingerprint=processed_file_fingerprint("data_dictionary.csv"),
)
google_summary = load_optional_csv(
    "google_trends_collection_summary.csv",
    file_fingerprint=processed_file_fingerprint("google_trends_collection_summary.csv"),
)
reddit_summary = load_optional_csv(
    "reddit_processing_summary.csv",
    file_fingerprint=processed_file_fingerprint("reddit_processing_summary.csv"),
)

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


filtered_market = filter_market(market, selected_tickers, start_date, end_date)
filtered_events = filter_events(events, selected_tickers, start_date, end_date)
filtered_reddit = pd.DataFrame()
if not reddit_attention.empty:
    filtered_reddit = reddit_attention[
        reddit_attention["ticker"].isin(selected_tickers)
        & (reddit_attention["date"] >= start_date)
        & (reddit_attention["date"] <= end_date)
    ].copy()
reddit_gap_message = reddit_coverage_message(reddit_attention, start_date, end_date, selected_window)


st.markdown(
    '<h1>Mapping Meme<span class="mobile-title-break"></span> Stock Attention</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    "A compact view of market volatility, Reddit attention, co-mentions, and search interest."
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
if reddit_gap_message:
    st.warning(reddit_gap_message)

if filtered_market.empty:
    st.error("No market rows match the selected filters. Adjust the date range or ticker selection.")
    st.stop()


def render_methods_data_notes() -> None:
    st.markdown(
        f"""
        Daily stock price data source: We pulled data from Yahoo Finance and processed it into
        the market timeline table. Event annotations are stored as processed project outputs.
        Google Trends is currently loaded as **{trends_status}**. Reddit/text/network data are
        currently **{reddit_status}**.

        Text analysis uses ticker mention counts, VADER sentiment, event-window top terms, and
        ticker co-mentions. The map uses Plotly's built-in U.S. state choropleth rendering from
        state codes.
        """
    )
    if reddit_gap_message:
        st.info(reddit_gap_message)
    status = pd.DataFrame(
        [
            {"view": "Market timeline", "status": file_status(data_dictionary, "market_daily.csv")},
            {"view": "Reddit/Text", "status": reddit_status},
            {"view": "Network", "status": network_status},
            {"view": "Map", "status": trends_status},
        ]
    )
    st.dataframe(status, width="stretch", hide_index=True)

    if not data_dictionary.empty:
        st.write("Processed data dictionary")
        st.dataframe(data_dictionary, width="stretch", hide_index=True)

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
    st.write("Expected processed files")
    st.dataframe(expected, width="stretch", hide_index=True)


tab_overview, tab_timeline, tab_text, tab_network, tab_map, tab_methods = st.tabs(
    ["Overview", "Timeline", "Reddit/Text", "Network", "Map", "Methods"]
)


with tab_overview:
    st.subheader("Key finding")
    max_abs_return = filtered_market["daily_return"].abs().max()
    peak_volume_row = filtered_market.loc[filtered_market["volume"].idxmax()]
    reddit_mentions = int(filtered_reddit["total_mentions"].sum()) if not filtered_reddit.empty else 0
    st.markdown(
        f"""
        <div class="summary-note">
        <p>Window: <strong>{start_date.date()}</strong> to <strong>{end_date.date()}</strong>.</p>
        <p>Largest volume day:<br>
        <strong>{peak_volume_row['ticker']}</strong> on <strong>{peak_volume_row['date'].date()}</strong><br>
        <strong>{format_compact_number(peak_volume_row['volume'])}</strong> shares traded.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Trading days", f"{filtered_market['date'].nunique():,}")
    c2.metric("Max daily move", format_percent(max_abs_return))
    c3.metric("Reddit mentions", f"{reddit_mentions:,}" if reddit_mentions else "n/a")

    with st.expander("Event annotations"):
        if not filtered_events.empty:
            overview_events = visible_events(filtered_events)
            st.dataframe(
                overview_events.assign(date=overview_events["date"].dt.date)[["date", "ticker", "event"]],
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No event annotations fall inside this selection.")

    with st.expander("Methods and data notes"):
        render_methods_data_notes()


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
            f"Timeline is focused on {timeline_focus_ticker}. Event text is shown directly on the chart. "
            f"Daily stock price data source: We pulled data from Yahoo Finance and processed it for the app. "
            f"Reddit attention status: {reddit_status}."
        )
        event_rows = visible_events(timeline_events)
        if not event_rows.empty:
            st.dataframe(
                event_rows.assign(date=event_rows["date"].dt.date)[["date", "ticker", "event"]],
                width="stretch",
                hide_index=True,
            )

        with st.expander("Detailed stock view"):
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
        if reddit_gap_message:
            st.info("No Reddit attention rows fall inside this event window; see the coverage note above.")
        else:
            st.warning("No Reddit attention rows match the selected ticker and date filters.")
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

        mentions_fig = px.bar(
            mention_by_ticker,
            x="ticker",
            y="total_mentions",
            color="ticker",
            color_discrete_map=TICKER_COLORS,
            category_orders={"ticker": TICKER_ORDER},
            hover_data={
                "post_mentions": ":,",
                "comment_mentions": ":,",
                "total_mentions": ":,",
                "ticker": False,
            },
            labels={
                "total_mentions": "Mentions",
                "post_mentions": "Post mentions",
                "comment_mentions": "Comment mentions",
                "ticker": "Ticker",
            },
            title="Attention by ticker",
        )
        mentions_fig.update_layout(height=390, showlegend=False, margin=dict(l=20, r=20, t=55, b=20))
        st.plotly_chart(mentions_fig, width="stretch")

        with st.expander("Sentiment by ticker"):
            sentiment_fig = px.bar(
                mention_by_ticker,
                x="ticker",
                y="sentiment_mean",
                color="ticker",
                color_discrete_map=TICKER_COLORS,
                category_orders={"ticker": TICKER_ORDER},
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
        if selected_window not in text_window_options:
            st.info(
                f"Top-term data does not include {selected_window}; showing {text_window} from the available Reddit text windows."
            )
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
        if selected_window not in network_windows:
            st.info(
                f"Network data is available for {', '.join(network_windows)}; using {network_window} because "
                f"{selected_window} is outside the Reddit co-mention coverage."
            )
        candidate_edges = edges[edges["window"] == network_window].copy()
        candidate_edges = candidate_edges[
            candidate_edges["source"].isin(selected_tickers) | candidate_edges["target"].isin(selected_tickers)
        ]
        max_edge = int(candidate_edges["weight"].max()) if not candidate_edges.empty else 1
        with controls[1]:
            min_edge = st.slider("Minimum edge weight", 1, max(max_edge, 1), 1)
        if not candidate_edges.empty:
            st.caption(f"Available edge weights in this selection range from 1 to {max_edge:,}.")
        network_edges = candidate_edges[candidate_edges["weight"] >= min_edge]

        if network_edges.empty:
            st.info("No edges survive the current ticker and weight filters.")
        else:
            edge_table = network_edges.sort_values("weight", ascending=False)
            top_edge = edge_table.iloc[0]
            st.plotly_chart(make_network_chart(network_edges), width="stretch")
            st.caption(
                f"Strongest pair: {top_edge['source']} + {top_edge['target']} "
                f"({int(top_edge['weight']):,} co-mentions). Current network data status: {network_status}."
            )

            top_pairs = edge_table.head(5).copy()
            top_pairs.insert(
                0,
                "pair",
                top_pairs["source"].astype(str) + " + " + top_pairs["target"].astype(str),
            )
            with st.expander("Co-mention tables"):
                st.write("Top pairs")
                st.dataframe(
                    top_pairs[["pair", "window", "weight"]],
                    width="stretch",
                    hide_index=True,
                )
                st.write("All shown edges")
                st.dataframe(edge_table, width="stretch", hide_index=True)


with tab_map:
    st.subheader("State-Level Google Trends Interest")
    if google_trends.empty:
        st.warning("No Google Trends state-level table is available.")
    else:
        map_windows = google_trends["window"].drop_duplicates().tolist()
        map_terms = google_trends["term"].drop_duplicates().tolist()
        default_map_window = map_windows.index(selected_window) if selected_window in map_windows else 0
        default_map_term = preferred_map_term(map_terms, selected_window, selected_tickers)
        default_map_term_idx = map_terms.index(default_map_term) if default_map_term in map_terms else 0
        map_controls = st.columns([1, 1, 2])
        with map_controls[0]:
            map_window = st.selectbox("Map window", map_windows, index=default_map_window)
        with map_controls[1]:
            map_term = st.selectbox("Search term", map_terms, index=default_map_term_idx)

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
            st.caption(
                "Google Trends reports normalized relative interest, not population-adjusted or raw search counts. "
                "Values are scaled against total Google searches in the selected geography and export window."
            )
            top_states = (
                map_df.sort_values(["interest", "state"], ascending=[False, True])
                .head(10)
                .reset_index(drop=True)
            )
            top_states.insert(0, "rank", np.arange(1, len(top_states) + 1))
            with st.expander("Top states"):
                st.dataframe(
                    top_states[["rank", "state", "state_code", "interest"]],
                    width="stretch",
                    hide_index=True,
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


with tab_methods:
    st.subheader("Methods and Data Notes")
    render_methods_data_notes()
