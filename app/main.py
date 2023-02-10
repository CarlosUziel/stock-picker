from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dateutil.relativedelta import relativedelta

from data.plots import candlestick_daily, candlestick_yearly
from data.utils import download_yfinance_data, get_price_statistics

# 0. Setup
st.set_page_config(page_title="StockPicker", layout="wide")
st.title("StockPicker")
st.markdown(
    "**StockPicker** allows you to compare the historical market performance of "
    "multiple [securities](https://en.wikipedia.org/wiki/Security_(finance)) "
    "available through [Yahoo Finance](https://finance.yahoo.com). "
    "The feasability of forecasting future prices is also explored."
)
st.markdown("---")

# 1. Sidebar
st.sidebar.title("Setup analysis parameters")

# 1.1. Portfolio upload
st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader(
    "Upload your portfolio of tickers:", type="txt"
)
if uploaded_file is not None:
    tickers = [
        line.split(" ")[0]
        for line in StringIO(uploaded_file.getvalue().decode("utf-8"))
        .read()
        .split("\n")
    ]
    st.sidebar.markdown("**Detected tickers**:")
    st.sidebar.text(", ".join(tickers))
else:
    tickers = None
    st.markdown("**Upload your portfolio of tickers to continue.**")

# 1.2. Date range
st.sidebar.markdown("---")
date_range = st.sidebar.date_input(
    "Select the date range that will be used for the analysis:",
    (
        datetime.now() - relativedelta(years=10),
        datetime.now() - relativedelta(months=6),
    ),
)


# 2. Download data
@st.cache_data(show_spinner="Downloading financial data...")
def cached_data_download(*args, **kwargs):
    return download_yfinance_data(*args, **kwargs)


tickers_info, tickers_data = (None, None)
if tickers is not None:
    save_path = (
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("data")
        .joinpath("uploaded_portfolio")
    )
    save_path.mkdir(parents=True, exist_ok=True)
    try:
        tickers_info, tickers_data = cached_data_download(
            tickers, date_range, save_path
        )
        with st.expander("Download information"):
            st.markdown(
                f"Size of _tickers information_: `{tickers_info.shape}`. "
                f"Size of _ticker data_: `{tickers_data.shape}`"
            )
    except Exception as e:
        st.write(f"There was a problem downloading the data: {e}")

# 3. Show tickers information
if tickers_info is not None:
    st.subheader("Tickers information")
    if tickers_info.empty:
        st.write("There is no information available for these tickers.")
    else:
        st.dataframe(tickers_info)


# 3. Compute price statistics
@st.cache_data(show_spinner="Computing price statistics on historical data...")
def cached_get_price_statistics(*args, **kwargs):
    return get_price_statistics(*args, **kwargs)


if tickers_data is not None:
    st.subheader("Price statistics on historical data")
    price_stats = None
    save_filepath = (
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("data")
        .joinpath("uploaded_portfolio")
        .joinpath("price_statistics.csv")
    )
    col0, col1 = st.columns(2)
    try:
        price_stats = cached_get_price_statistics(tickers_data, save_filepath)
        col0.markdown(
            """
        The following metrics are shown across the observed date range:
        - `count`: Number of data points.
        - `mean`: Average price.
        - `std`: Standard price deviation.
        - `min`: Minimum price.
        - `25%`/`50%`/`75%`: Price quartiles.
        - `max`: Maximum price.
        - `abs_change`: Absolute change between start and end dates.
        - `rel_change`: Relative change between start and end dates.
        - `max_fall`: Maximum price fall from a high peak.
        - `max_rise`: Maximum price rise from a low peak.
        """
        )
        col1.dataframe(price_stats.style.format(formatter="{:.2f}", na_rep="."))
    except Exception as e:
        st.write(f"There was a problem calculating price statistics: {e}")

# 4. Visualizations
if tickers_data is not None:
    # TODO: cache plotting functions
    st.markdown("---")
    st.header("Data Visualization")
    st.markdown(
        "In the following plots we can get a sense of the price evolution through "
        "the years for each security in the portfolio."
    )
    col0, col1 = st.columns(2)

    # 4.1. Pice trends
    fig = px.line(tickers_data["Adj Close"], title="Price evolution")
    fig.update_layout(
        yaxis_title="Adj. Close price",
        xaxis_title="Date",
        legend_title="Security ticker",
    )
    col0.plotly_chart(fig)

    # 4.2. Relative price increases
    def rel_change(series: pd.Series):
        initial_value = series.dropna().iloc[0]
        return ((series - initial_value) / initial_value) * 100

    fig = px.line(
        tickers_data["Adj Close"].apply(rel_change, axis=0),
        title="Price evolution (in relative terms from the start date)",
    )
    fig.update_layout(
        yaxis_title="Adj. Close price chage w.r.t. the start date",
        xaxis_title="Date",
        legend_title="Security ticker",
    )
    col1.plotly_chart(fig)

    # 4.3. Candlestick plot
    st.subheader("Candlestick charts")
    st.markdown(
        "A [candlestick chart](https://en.wikipedia.org/wiki/Candlestick_chart) "
        "is a style of financial chart used to describe price "
        "movements of a security, derivative, or currency. "
        "It is similar to a bar chart in that each candlestick represents all four "
        "important pieces of information for that day: open and close in the thick "
        "body; high and low in the “candle wick”. Being densely packed with "
        "information, it tends to represent trading patterns over short periods of "
        "time, often a few days or a few trading sessions."
    )
    col0, col1 = st.columns(2)
    ticker_selected_1 = col0.selectbox(
        "Select first ticker for comparison: ", tickers, index=0
    )
    ticker_selected_2 = col1.selectbox(
        "Select second ticker for comparison: ", tickers, index=1
    )

    col0.plotly_chart(candlestick_daily(tickers_data, ticker_selected_1))
    col1.plotly_chart(candlestick_daily(tickers_data, ticker_selected_2))

    # 4.4. Price per weekday, month and year
    col0.plotly_chart(candlestick_yearly(tickers_data, ticker_selected_1))
    col1.plotly_chart(candlestick_yearly(tickers_data, ticker_selected_2))
    
    # TODO: add the monthly and weekday candlestick charts
