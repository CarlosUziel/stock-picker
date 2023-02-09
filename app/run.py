from datetime import datetime
from io import StringIO
from pathlib import Path

import streamlit as st
from dateutil.relativedelta import relativedelta

from data.utils import download_yfinance_data, get_price_statistics

# 0. Setup
st.set_page_config(page_title="StockPicker", layout="wide")
st.sidebar.title("Portfolio Upload")
st.title("StockPicker")
st.markdown(
    "**StockPicker** allows you to compare the market performance of multiple tickers, "
    "as accepted by [Yahoo Finance](https://finance.yahoo.com), from historical and "
    "forecast price data."
)

# 1. Portfolio file upload
uploaded_file = st.sidebar.file_uploader(
    "Upload your portfolio of tickers:", type="txt"
)
tickers = None

# 1.1. Detect tickers
if uploaded_file is not None:
    st.subheader("Portfolio uploaded successfully!")

    tickers = [
        line.split(" ")[0]
        for line in StringIO(uploaded_file.getvalue().decode("utf-8"))
        .read()
        .split("\n")
    ]
    st.markdown(f"Here is the list of tickers detected: {', '.join(tickers)}")
    st.markdown("---")
else:
    st.markdown(
        "**Upload your portfolio of tickers to continue. "
        "You can find this functionality on the left-hand sidebar.**"
    )


# 2. Download data
tickers_info, tickers_data = (None, None)
if tickers is not None:
    # 2.1. Select date range
    st.header("Comparison analysis")
    date_range = st.date_input(
        "Select the date range that will be used for the analysis:",
        (
            datetime.now() - relativedelta(years=10),
            datetime.now() - relativedelta(months=6),
        ),
    )

    if st.button("Start analysis"):
        save_path = (
            Path(__file__)
            .resolve()
            .parents[1]
            .joinpath("data")
            .joinpath("uploaded_portfolio")
        )
        save_path.mkdir(parents=True, exist_ok=True)
        with st.spinner("Downloading financial data..."):
            try:
                tickers_info, tickers_data = download_yfinance_data(
                    tickers, date_range, save_path
                )
                st.write("Data finished downloading!")
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
    with st.spinner("Computing price statistics on historical data..."):
        try:
            price_stats = get_price_statistics(tickers_data, save_filepath)
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
