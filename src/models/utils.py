from copy import deepcopy
from typing import Tuple

import pandas as pd
import streamlit as st


def preprocess_data(ticker_data: pd.DataFrame) -> pd.DataFrame:
    """Prepare Yahoo Finance data before modelling for forecasting.

    Args:
        ticker_data: Ticker historical price data. Columns are "Adj Close", "Close",
            "High", "Low" and "Open".

    Returns:
        A dataframe with the right format for time-series forecasting.
    """
    # 0. Setup
    ticker_data = deepcopy(ticker_data)

    # 1. Ensure index is datetime with the right frequency
    ticker_data.index = pd.to_datetime(ticker_data.index, format="YYYY-MM-DD")
    ticker_data = ticker_data.asfreq("D").sort_index()

    # 2. Discard missing values at the beginning and end of the time period
    ticker_data = ticker_data.loc[
        ticker_data.first_valid_index() : ticker_data.last_valid_index()
    ]

    # 3. Forward fill missing values
    ticker_data = ticker_data.fillna(method="ffill")

    # 4. Add date-based exogenous variables
    for date_part in ("day", "weekday", "month", "year"):
        ticker_data[date_part] = getattr(ticker_data.index, date_part)

    return ticker_data


@st.cache_data(show_spinner="Pre-processing data...")
def preprocess_data_st_cached(*args, **kwargs) -> pd.DataFrame:
    return preprocess_data(*args, **kwargs)


def split_time_data(
    ticker_data: pd.DataFrame, test_size: int = 30
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split time-series data into train and test sets. Train test data will always be
    older than test data.

    Args:
        tickers_data: Ticker historical price data. Columns are "Adj Close", "Close",
            "High", "Low" and "Open".
        test_size: Number of time points to be used for testing. This number of newest
            data is used to build the test set.

    Returns:
        A dataframe with training data.
        A dataframe with testing data.
    """
    return ticker_data.iloc[:-test_size, :], ticker_data.iloc[-test_size:, :]


@st.cache_data(show_spinner="Splitting data into train and test sets...")
def split_time_data_st_cached(*args, **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame]:
    return split_time_data(*args, **kwargs)
