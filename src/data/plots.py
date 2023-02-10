from copy import deepcopy

import pandas as pd
import plotly.graph_objects as go


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
                        ticker_data.loc[ticker_data.index.year == year, "Open"][0],
                        ticker_data.loc[ticker_data.index.year == year, "Adj Close"][
                            -1
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


def candlestick_monthly(tickers_data: pd.DataFrame, ticker: str):
    """Produce a candlestick chart based on monthly price data.

    Args:
        tickers_data: Tickers historical price data. Columns are a multi-index where
            first level is the metric and the second level is the ticker.
        ticker: For which ticker to generate the plot for.

    Returns:
        Candlestick plotly figure.
    """


def candlestick_weekday():
    pass
