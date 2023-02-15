from datetime import datetime
from io import StringIO

import pandas as pd
import plotly.express as px
import streamlit as st
from dateutil.relativedelta import relativedelta

from data.plots import (
    candlestick_daily_st_cached,
    candlestick_yearly_st_cached,
    violin_month_day_st_cached,
    violin_monthly_st_cached,
    violin_weekday_st_cached,
)
from data.utils import download_yfinance_data_st_cached, get_price_statistics_st_cached
from models.plots import plot_data_predictions_st_cached, plot_data_split_st_cached
from models.utils import (
    fit_forecaster_st_cached,
    preprocess_data_st_cached,
    split_time_data_st_cached,
)

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
    st.header("Data Download")
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
    value=(
        datetime.now() - relativedelta(years=5),
        datetime.now(),
    ),
    max_value=datetime.now(),
    min_value=datetime.now() - relativedelta(years=100),
)


# 2. Download data
tickers_info, tickers_data = (None, None)
if tickers is not None:
    try:
        tickers_info, tickers_data = download_yfinance_data_st_cached(
            tickers, date_range
        )
        with st.expander("Download information"):
            st.markdown(f"Size of _tickers information_: `{tickers_info.shape}`")
            st.markdown(f"Size of _ticker data_: `{tickers_data.shape}`")
    except Exception as e:
        st.write(f"There was a problem downloading the data: {e}")

# 3. Show tickers information
if tickers_info is not None:
    st.subheader("Tickers information")
    if tickers_info.empty:
        st.write("There is no information available for these tickers.")
    else:
        st.dataframe(tickers_info.dropna(how="all").transpose())


# 3. Compute price statistics
if tickers_data is not None:
    st.subheader("Price statistics on historical data")
    price_stats = None
    col0, col1 = st.columns(2)
    try:
        price_stats = get_price_statistics_st_cached(tickers_data)
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
        "Select first ticker for comparison: ", tickers, index=0, key="candlestick_1"
    )
    ticker_selected_2 = col1.selectbox(
        "Select second ticker for comparison: ", tickers, index=1, key="candlestick_2"
    )

    col0.plotly_chart(
        candlestick_daily_st_cached(tickers_data, ticker_selected_1),
        use_container_width=True,
    )
    col1.plotly_chart(
        candlestick_daily_st_cached(tickers_data, ticker_selected_2),
        use_container_width=True,
    )
    col0.plotly_chart(
        candlestick_yearly_st_cached(tickers_data, ticker_selected_1),
        use_container_width=True,
    )
    col1.plotly_chart(
        candlestick_yearly_st_cached(tickers_data, ticker_selected_2),
        use_container_width=True,
    )

    # 4.4. Price seasonality
    st.subheader("Seasonality")
    st.markdown(
        """
    [Seasonality](https://www.investopedia.com/terms/s/seasonality.asp) is a 
    characteristic of a time series in which the data experiences regular and 
    predictable changes that recur every calendar year. Any predictable fluctuation 
    or pattern that recurs or repeats over a one-year period is said to be seasonal.
    """
    )
    col0, col1 = st.columns(2)
    ticker_selected_1 = col0.selectbox(
        "Select first ticker for comparison: ", tickers, index=0, key="sesonality_1"
    )
    ticker_selected_2 = col1.selectbox(
        "Select second ticker for comparison: ", tickers, index=1, key="sesonality_2"
    )

    # monthly
    col0.plotly_chart(
        violin_monthly_st_cached(tickers_data, ticker_selected_1),
        use_container_width=True,
    )
    col1.plotly_chart(
        violin_monthly_st_cached(tickers_data, ticker_selected_2),
        use_container_width=True,
    )

    # day of the month
    col0.plotly_chart(
        violin_month_day_st_cached(tickers_data, ticker_selected_1),
        use_container_width=True,
    )
    col1.plotly_chart(
        violin_month_day_st_cached(tickers_data, ticker_selected_2),
        use_container_width=True,
    )

    # day of the week
    col0.plotly_chart(
        violin_weekday_st_cached(tickers_data, ticker_selected_1),
        use_container_width=True,
    )
    col1.plotly_chart(
        violin_weekday_st_cached(tickers_data, ticker_selected_2),
        use_container_width=True,
    )

# 5. Forecasting
if tickers_data is not None:
    st.markdown("---")
    st.header("Forecasting")
    st.markdown(
        "Next, we will try to predict the future price of our tickers using machine "
        "learning for forecasting."
    )
    ticker_selected = st.selectbox(
        "Select ticker to forecast: ", tickers, index=0, key="forecast_1"
    )

    # 5.1. Get and plot train and test data
    st.subheader("Split data into training and testing sets")
    st.markdown(
        "Data is split into training and testing sets for model fitting and evaluation, "
        "respectively."
    )
    train_data, test_data = split_time_data_st_cached(
        preprocess_data_st_cached(
            tickers_data.reorder_levels(order=[1, 0], axis=1)[ticker_selected]
        )
    )
    st.plotly_chart(
        plot_data_split_st_cached(train_data, test_data), use_container_width=True
    )

    # 5.2. Model selection and hyper-parameter tuning
    st.subheader("Model selection and hyper-parameter tuning")
    st.markdown(
        "By default, a random forest autoregressor is trained to make predictions into"
        " the future. Its hyper-parameters are tuned using a special case of Grid "
        "Search with backtesting."
    )

    _, results_grid, pred, error_mse = fit_forecaster_st_cached(
        train_data, test_data, exog_cols=["day", "month"]
    )

    st.markdown("### Grid Search results")
    st.dataframe(results_grid)

    st.markdown("### Prediction results")
    st.plotly_chart(
        plot_data_predictions_st_cached(train_data, test_data, pred),
        use_container_width=True,
    )
    st.markdown(f"Test mean squared error (MSE): {error_mse:.2f}")
