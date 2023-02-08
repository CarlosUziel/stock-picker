import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple

import typer

from data.utils import download_data, get_price_statistics

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def main(
    portfolio_filepath: Path = typer.Argument(
        Path(__file__)
        .resolve()
        .parents[2]
        .joinpath("data")
        .joinpath("portfolios")
        .joinpath("big_tech.txt"),
        help="Path to file containing tickers in a portfolio, one per line.",
    ),
    date_range: Tuple[datetime, datetime] = typer.Argument(
        (datetime(2008, 1, 1), datetime(2023, 1, 1)),
        help="date_range: Date range to download historical data for as a tuple of datatime objects.",
    ),
    save_root_path: Path = typer.Argument(
        Path(__file__).resolve().parents[2].joinpath("data"),
        help="Directory to save downloaded and processed data to.",
    ),
):
    """ETL pipeline for Yahoo Finance data."""

    # 0. Setup
    save_path = save_root_path.joinpath(portfolio_filepath.stem)
    save_path.mkdir(exist_ok=True, parents=True)

    # 1. Download data
    _, ticker_data = download_data(portfolio_filepath, date_range, save_path)

    # 2. Generate price statistics
    _ = get_price_statistics(ticker_data, save_path)


if __name__ == "__main__":
    typer.run(main)
