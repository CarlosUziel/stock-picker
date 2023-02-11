from copy import deepcopy

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def candlestick_daily(tickers_data: pd.DataFrame, ticker: str):
    """Produce a candlestick chart based on daily price data.

    Args:
        tickers_data: Tickers historical price data. Columns are a multi-index where
            first level is the metric and the second level is the ticker.
        ticker: For which ticker to generate the plot for.

    Returns:
        Candlestick plotly figure.
    """
    # 0. Reorder index
    tickers_data = deepcopy(tickers_data)
    tickers_data.columns = tickers_data.columns.reorder_levels(order=[1, 0])
    ticker_data = tickers_data[ticker]

    # 1. Create figure
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=tickers_data.index,
                open=ticker_data["Open"],
                close=ticker_data["Adj Close"],
                low=ticker_data["Low"],
                high=ticker_data["High"],
            )
        ]
    )
    # 2. Adjust figure's layout
    fig.update_layout(
        title=f"Candlestick daily chart ({ticker})",
        yaxis_title="Price (USD)",
        xaxis_title="Date",
        xaxis_rangeslider_visible=False,
    )

    return fig


@st.cache_data(show_spinner="Plotting daily candlestick chart...")
def candlestick_daily_st_cached(*args, **kwargs):
    return candlestick_daily(*args, **kwargs)


def candlestick_yearly(tickers_data: pd.DataFrame, ticker: str):
    """Produce a candlestick chart based on yearly price data.

    Args:
        tickers_data: Tickers historical price data. Columns are a multi-index where
            first level is the metric and the second level is the ticker.
        ticker: For which ticker to generate the plot for.

    Returns:
        Candlestick plotly figure.
    """
    # 0. Reorder index
    tickers_data = deepcopy(tickers_data)
    tickers_data.columns = tickers_data.columns.reorder_levels(order=[1, 0])
    ticker_data = tickers_data[ticker]

    # 1. Compute yearly metrics
    ticker_data_yearly = (
        pd.concat(
            [
                pd.Series(
                    [
                        ticker_data.loc[
                            ticker_data.loc[
                                ticker_data.index.year == year
                            ].first_valid_index(),
                            "Open",
                        ],
                        ticker_data.loc[
                            ticker_data.loc[
                                ticker_data.index.year == year
                            ].last_valid_index(),
                            "Adj Close",
                        ],
                        ticker_data.loc[ticker_data.index.year == year, "Low"].min(),
                        ticker_data.loc[ticker_data.index.year == year, "High"].max(),
                    ]
                ).rename(year)
                for year in ticker_data.index.year.unique()
            ],
            axis=1,
        )
        .transpose()
        .set_index(pd.to_datetime(ticker_data.index.year.unique(), format="%Y"))
        .set_axis(["open", "close", "low", "high"], axis=1)
    )

    # 1.1. Compute change between open and closing prices
    ticker_data_yearly["open_close_change"] = (
        (ticker_data_yearly["close"] - ticker_data_yearly["open"])
        / ticker_data_yearly["open"]
    ) * 100

    # 2. Create plot annotations
    high_max = ticker_data_yearly["high"].max()
    annotations = [
        dict(
            x=year,
            y=(
                ticker_data_yearly.loc[ticker_data_yearly.index == year, "high"].values[
                    0
                ]
                / high_max
                + 0.05
            ),
            xref="x",
            yref="paper",
            showarrow=False,
            xanchor="center",
            text="{:.1f}%".format(
                ticker_data_yearly.loc[
                    ticker_data_yearly.index == year, "open_close_change"
                ].values[0]
            ),
        )
        for year in ticker_data_yearly.index
    ]

    # 3. Create figure
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=ticker_data_yearly.index,
                open=ticker_data_yearly["open"],
                close=ticker_data_yearly["close"],
                low=ticker_data_yearly["low"],
                high=ticker_data_yearly["high"],
            )
        ]
    )
    # 4. Adjust figure's layout
    fig.update_layout(
        title=f"Candlestick yearly chart ({ticker})",
        yaxis_title="Price (USD)",
        xaxis_title="Year",
        xaxis_rangeslider_visible=False,
        annotations=annotations,
    )

    return fig


@st.cache_data(show_spinner="Plotting yearly candlestick chart...")
def candlestick_yearly_st_cached(*args, **kwargs):
    return candlestick_yearly(*args, **kwargs)


def violin_monthly(tickers_data: pd.DataFrame, ticker: str):
    """Produce a violin plot chart based on monthly price data to evaluate seasonality.

    Args:
        tickers_data: Tickers historical price data. Columns are a multi-index where
            first level is the metric and the second level is the ticker.
        ticker: For which ticker to generate the plot for.

    Returns:
        Violin plotly figure.
    """
    # 0. Setup
    ticker_close = deepcopy(tickers_data["Adj Close"][[ticker]])
    ticker_close["month"] = ticker_close.index.month
    ticker_close.sort_values(by=["month"])

    # 1. Produce figure
    fig = px.violin(ticker_close, x="month", y=ticker, box=True, points="all")
    fig.update_layout(
        title=f"Monthly seasonality ({ticker})",
        yaxis_title="Closing price (USD)",
        xaxis_title="Month",
    )

    return fig


@st.cache_data(show_spinner="Plotting monthly seasonality...")
def violin_monthly_st_cached(*args, **kwargs):
    return violin_monthly(*args, **kwargs)


def violin_month_day(tickers_data: pd.DataFrame, ticker: str):
    """Produce a violin plot chart based on day of the month price data to evaluate
        seasonality.

    Args:
        tickers_data: Tickers historical price data. Columns are a multi-index where
            first level is the metric and the second level is the ticker.
        ticker: For which ticker to generate the plot for.

    Returns:
        Violin plotly figure.
    """
    # 0. Setup
    ticker_close = deepcopy(tickers_data["Adj Close"][[ticker]])
    ticker_close["day"] = ticker_close.index.day
    ticker_close.sort_values(by=["day"])

    # 1. Produce figure
    fig = px.violin(ticker_close, x="day", y=ticker, box=True, points="all")
    fig.update_layout(
        title=f"Day of the month seasonality ({ticker})",
        yaxis_title="Closing price (USD)",
        xaxis_title="Day",
    )

    return fig


@st.cache_data(show_spinner="Plotting day of the month seasonality...")
def violin_month_day_st_cached(*args, **kwargs):
    return violin_month_day(*args, **kwargs)


def violin_weekday(tickers_data: pd.DataFrame, ticker: str):
    """Produce a violin plot chart based on weekday price data to evaluate seasonality.

    Args:
        tickers_data: Tickers historical price data. Columns are a multi-index where
            first level is the metric and the second level is the ticker.
        ticker: For which ticker to generate the plot for.

    Returns:
        Violin plotly figure.
    """
    # 0. Setup
    ticker_close = deepcopy(tickers_data["Adj Close"][[ticker]])
    ticker_close["weekday"] = ticker_close.index.weekday
    ticker_close.sort_values(by=["weekday"])

    # 1. Produce figure
    fig = px.violin(ticker_close, x="weekday", y=ticker, box=True, points="all")
    fig.update_layout(
        title=f"Day of the week seasonality ({ticker})",
        yaxis_title="Closing price (USD)",
        xaxis_title="Weekday",
    )

    return fig


@st.cache_data(show_spinner="Plotting day of the week seasonality...")
def violin_weekday_st_cached(*args, **kwargs):
    return violin_weekday(*args, **kwargs)
