import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


def download_yfinance_data(
    tickers: Iterable[str],
    date_range: Tuple[datetime, datetime],
    save_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Download stock data using Yahoo Finance API.

    Args:
        tickers: A list of stock tickers.
        date_range: Date range to download historical data for as a tuple of datatime
            objects.
        save_path: Directory to save downloaded data to.

    Returns:
        A dataframe containing additional information for each ticker.
        A dataframe containing historical price data for the selected date range.
    """
    # 1. Read tickers
    tickers_str = " ".join(tickers)

    # 2. Create ticker objects
    tickers = yf.Tickers(tickers_str)

    # 3. Extract ticker information
    logging.info(f"Downloading information for tickers ({tickers_str})")

    tickers_info = []
    for ticker_name, ticker_obg in tickers.tickers.items():
        try:
            tickers_info.append(pd.Series(ticker_obg.info).rename(ticker_name))
        except Exception as e:
            logging.warning(f"Problem retrieving information for {ticker_name}: {e}")
            continue

    if len(tickers_info) != 0:
        tickers_info = pd.concat(tickers_info, axis=1)

        if save_path is not None:
            tickers_info.to_csv(save_path.joinpath("ticker_information.csv"))

        logging.info("Tickers information downloaded successfully!")
    else:
        tickers_info = pd.DataFrame()
        logging.warning("Tickers information could not be downloaded. Continuing...")

    # 4. Download historical data
    start, end = date_range
    logging.info("Downloading historical data...")

    try:
        tickers_data = yf.download(
            tickers_str, start=start, end=end, ignore_tz=True, keepna=True
        )
        tickers_data.index = pd.to_datetime(tickers_data.index, format="YYYY-MM-DD")
        tickers_data = tickers_data.asfreq("D")

        if save_path is not None:
            tickers_data.to_csv(save_path.joinpath("ticker_data.csv"))

        logging.info("Historical data downloaded successfully!")
    except Exception as e:
        tickers_data = pd.DataFrame()
        logging.warning(f"There was a problem downloading historical price data: {e}")

    return tickers_info, tickers_data


@st.cache_data(show_spinner="Downloading financial data...")
def download_yfinance_data_st_cached(*args, **kwargs):
    return download_yfinance_data(*args, **kwargs)


def get_price_statistics(
    ticker_data: pd.DataFrame, save_filepath: Optional[Path] = None
) -> pd.DataFrame:
    """Calculate price statistics based on historic data.

    Args:
        ticker_data: Price data for a set of tickers.
        save_filepath: Path to save price statistics to.

    Returns:
        A dataframe with a few price-related statistics.
    """

    # 0. Define aggregate functions
    def abs_change(series: pd.Series) -> float:
        series = series.dropna()
        return series.iloc[-1] - series.iloc[0]

    def rel_change(series: pd.Series) -> float:
        series = series.dropna()
        return (abs_change(series) / series.iloc[0]) * 100

    def max_fall(series: pd.Series) -> float:
        series = series.dropna()
        return np.min(
            [
                (np.min(series.iloc[i:] - np.max(series.iloc[:i])))
                / np.max(series.iloc[:i])
                for i in range(1, len(series))
            ]
        )

    def max_rise(series: pd.Series) -> float:
        series = series.dropna()
        return np.max(
            [
                (np.max(series.iloc[i:] - np.min(series.iloc[:i])))
                / np.min(series.iloc[:i])
                for i in range(1, len(series))
            ]
        )

    # 1. Compute price statistics
    logging.info("Calculating historical price statistics...")

    price_stats = (
        pd.concat(
            (
                ticker_data["Adj Close"].describe(),
                ticker_data["Adj Close"].agg(
                    [abs_change, rel_change, max_fall, max_rise]
                ),
            )
        )
        .round(2)
        .transpose()
        .sort_values(by="rel_change", ascending=False)
    )

    logging.info("Historical price statistics calculated successfully!")

    # 1.1. Save to disk
    if save_filepath is not None:
        price_stats.to_csv(save_filepath)

    return price_stats


@st.cache_data(show_spinner="Computing price statistics...")
def get_price_statistics_st_cached(*args, **kwargs):
    return get_price_statistics(*args, **kwargs)
