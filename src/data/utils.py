from datetime import datetime
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import yfinance as yf


def download_data(
    portfolio_filepath: Path, date_range: Tuple[datetime, datetime], save_path: Path
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Download stock data using Yahoo Finance API.

    Args:
        portfolio_filepath: Path to file representing a portfolio of stocks. Each line
            in the file must be a valid stock ticker.
        date_range: Date range to download historical data for as a tuple of datatime
            objects.
        save_path: Directory to save downloaded data to.

    Returns:
        A dataframe containing additional information for each ticker.
        A dataframe containing historical price data for the selected date range.
    """
    # 1. Read tickers
    tickers_str = " ".join(portfolio_filepath.read_text().split("\n"))

    # 2. Create ticker objects
    tickers = yf.Tickers(tickers_str)

    # 3. Extract ticker information
    ticker_info = pd.concat(
        [
            pd.Series(ticker_obg.info).rename(ticker_name)
            for ticker_name, ticker_obg in tickers.tickers.items()
        ],
        axis=1,
    )

    # 3.1. Save ticker information
    ticker_info.to_csv(save_path.joinpath("ticker_information.csv"))

    # 4. Download historical data
    start, end = date_range
    ticker_data = yf.download(
        tickers_str, start=start, end=end, ignore_tz=True, keepna=True
    )

    # 4.1. Save ticker data
    ticker_data.to_csv(save_path.joinpath("ticker_data.csv"))

    return ticker_info, ticker_data


def get_price_statistics(
    ticker_data: pd.DataFrame, save_filepath: Path
) -> pd.DataFrame:
    """Calculate price statistics based on historic data.

    Args:
        ticker_data: Price data for a set of tickers.
        save_filepath: Path to save price statistics to.

    Returns:
        A dataframe with a few price-related statistics.
    """

    # 0. Define aggregate functions
    def abs_start_end_change(series: pd.Series) -> float:
        return series.iloc[-1] - series.iloc[0]

    def rel_start_end_change(series: pd.Series) -> float:
        return (abs_start_end_change(series) / series.iloc[0]) * 100

    def max_fall(series: pd.Series) -> float:
        return np.min(
            [
                (np.min(series.iloc[i:] - np.max(series.iloc[:i])))
                / np.max(series.iloc[:i])
                for i in range(1, len(series))
            ]
        )

    def max_rise(series: pd.Series) -> float:
        return np.max(
            [
                (np.max(series.iloc[i:] - np.min(series.iloc[:i])))
                / np.min(series.iloc[:i])
                for i in range(1, len(series))
            ]
        )

    # 1. Compute price statistics
    price_stats = (
        pd.concat(
            (
                ticker_data.describe(),
                ticker_data.agg(
                    [abs_start_end_change, rel_start_end_change, max_fall, max_rise]
                ),
            )
        )
        .round(2)
        .transpose()
        .sort_values(by="rel_start_end_change", ascending=False)
    )

    # 1.1. Save to disk
    price_stats.to_csv(save_filepath)

    return price_stats
