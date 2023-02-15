from copy import deepcopy
from datetime import datetime
from typing import Iterable, Optional, Tuple, Union

import pandas as pd
import streamlit as st
from dateutil.relativedelta import relativedelta
from skforecast.ForecasterAutoreg import ForecasterAutoreg
from skforecast.model_selection import grid_search_forecaster
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error


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
    ticker_data: pd.DataFrame,
    start_train_date: Optional[datetime] = None,
    test_steps: int = 28,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split time-series data into train and test sets. Train test data will always be
    older than test data.

    Args:
        tickers_data: Ticker historical price data. Columns are "Adj Close", "Close",
            "High", "Low" and "Open".
        start_train_date: Date from which training data is selected.
        test_steps: Number of time points to be used for testing in days. This number of
            newest data is used to build the test set.

    Returns:
        A dataframe with training data.
        A dataframe with testing data.
    """
    return (
        ticker_data.loc[
            start_train_date : (
                ticker_data.index.max() - relativedelta(days=test_steps)
            )
        ],
        ticker_data.iloc[-test_steps:, :],
    )


@st.cache_data(show_spinner="Splitting data into train and test sets...")
def split_time_data_st_cached(*args, **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame]:
    return split_time_data(*args, **kwargs)


def fit_forecaster(
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
    exog_cols: Union[str, Iterable[str]],
    pred_col: str = "Adj Close",
    test_steps: int = 28,
    random_seed: int = 8080,
) -> Tuple[ForecasterAutoreg, pd.DataFrame, pd.Series, float]:
    """
    Fit a forecaster model.

    Args:
        train_data: Training data.
        test_data: Testing data.
        exog_col: Columns of exogenous variables to include during data modeling.
        pred_col: Column to use as predictor, such as adjusted closing price.
        test_steps: Number of time points to be used for testing.
        random_seed: Seed to initialize random state with.

    Returns:
        A ForecasterAutoreg object refit with the optimal hyper-parameters.
        A DataFrame with GridSearch results.
        A Series with predictions on the test data.
        The MSE of the test predictions.
    """

    # 1. Define forecaster model
    forecaster = ForecasterAutoreg(
        regressor=RandomForestRegressor(random_state=random_seed),
        lags=14,
    )

    # 2. Define hyper-parameter grids to configure
    lags_grid = [1, 2, 3, 7]
    param_grid = {"n_estimators": [50, 100, 200], "max_depth": [None, 3, 7, 11]}

    # 3. Tune hyper-parameters using grid search
    results_grid = grid_search_forecaster(
        forecaster=forecaster,
        y=train_data[pred_col],
        exog=train_data[exog_cols],
        param_grid=param_grid,
        lags_grid=lags_grid,
        steps=test_steps,
        refit=True,
        metric="mean_squared_error",
        initial_train_size=int(len(train_data) * 0.5),
        return_best=True,
        verbose=False,
    )

    # 4. Make predictions
    pred = forecaster.predict(steps=test_steps, exog=test_data[exog_cols])

    # 5. Get test error
    error_mse = mean_squared_error(y_true=test_data[pred_col], y_pred=pred)

    return forecaster, results_grid, pred, error_mse


@st.cache_data(show_spinner="Fiting forecaster model (this will take a while)...")
def fit_forecaster_st_cached(
    *args, **kwargs
) -> Tuple[ForecasterAutoreg, pd.DataFrame, pd.Series, float]:
    return fit_forecaster(*args, **kwargs)
