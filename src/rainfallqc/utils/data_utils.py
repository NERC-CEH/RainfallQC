# -*- coding: utf-8 -*-
"""
All data operations for polars including datetime and calendar functionality.

Classes and functions ordered alphabetically.
"""

import calendar
import datetime
from collections.abc import Sequence

import numpy as np
import polars as pl
import xarray as xr

SECONDS_IN_DAY = 86400.0
TEMPORAL_CONVERSIONS = {"hourly": "1h", "daily": "1d", "monthly": "1mo"}


def check_data_has_consistent_time_step(data: pl.DataFrame) -> None:
    """
    Check data has a consistent time step i.e. '1h'.

    Parameters
    ----------
    data :
        Data with time column

    Raises
    ------
    ValueError :
        If data has more than one time steps

    """
    unique_timesteps = get_data_timesteps(data)
    if unique_timesteps.len() != 1:
        timestep_strings = [format_timedelta_duration(td) for td in unique_timesteps]
        raise ValueError(f"Data has a inconsistent time step. Data has following time steps: {timestep_strings}")


def check_data_is_specific_time_res(data: pl.DataFrame, time_res: str | list) -> None:
    """
    Check data has a hourly or daily time step.

    Parameters
    ----------
    data :
        Data with time column.
    time_res :
        Time resolutions either a single string or list of strings

    Raises
    ------
    ValueError :
        If data is not hourly or daily.

    """
    # Normalize to list
    if isinstance(time_res, str):
        allowed_res = [time_res]
    elif isinstance(time_res, Sequence):
        allowed_res = list(time_res)
    else:
        raise TypeError("time_res must be a string or list of strings")

    # add terms like 'hourly', 'daily' or 'monthly'
    for time_conv in TEMPORAL_CONVERSIONS:
        if time_res == time_conv:
            allowed_res.append(TEMPORAL_CONVERSIONS[time_res])

    # Get actual time step as a string like "1h"
    time_step = get_data_timestep_as_str(data)
    if time_step not in allowed_res:
        raise ValueError(f"Invalid time step. Expected one of {allowed_res}, but got: {time_step}")


def convert_datarray_seconds_to_days(series_seconds: xr.DataArray) -> np.ndarray:
    """
    Convert xarray series from seconds to days. For some reason the CDD data from ETCCDI is in seconds.

    Parameters
    ----------
    series_seconds :
        Data in series to convert to days.

    Returns
    -------
    series_days :
        Data array converted to days.

    """
    return series_seconds.values.astype("timedelta64[s]").astype("float32") / SECONDS_IN_DAY


def convert_daily_data_to_monthly(
    daily_data: pl.DataFrame, rain_col: str, perc_for_valid_month: int | float = 95
) -> pl.DataFrame:
    """
    Convert daily data to monthly whilst setting month to NaN if less than a given percentage of days is missing.

    Parameters
    ----------
    daily_data :
        Daily data to convert to monthly
    rain_col :
        Column with rainfall data
    perc_for_valid_month :
        Percentage of month needed to be classed as a valid month for the monthly group by

    Returns
    -------
    monthly_data :
        Monthly data

    """
    check_data_is_specific_time_res(daily_data, "daily")

    # 1. Make month and year column
    daily_data = make_month_and_year_col(daily_data)

    # 2. Calculate expected days in month
    daily_data = get_expected_days_in_month(daily_data)

    # 3. Group data into monthly
    monthly_data = (
        daily_data.group_by_dynamic("time", every="1mo", closed="right")
        .agg(
            [
                pl.len().alias("n_days"),
                pl.col(rain_col).sum().alias(rain_col),
                pl.col("expected_days_in_month").first(),
            ]
        )
        .filter(
            pl.col("n_days")
            >= (
                pl.col("expected_days_in_month") * perc_for_valid_month / 100
            )  # TODO: Ensure at least n% values for month are available
        )
        .drop("n_days", "expected_days_in_month")
    )

    return monthly_data


def format_timedelta_duration(td: datetime.timedelta) -> str:
    """
    Convert timedelta to custom strings.

    Parameters
    ----------
    td :
        Time delta to convert.

    Returns
    -------
    td :
        Human-readable timedelta string using largest unit (d, h, m, s).

    """
    total_seconds = int(td.total_seconds())

    if total_seconds % 86400 == 0:  # 86400 seconds in a day
        return f"{total_seconds // 86400}d"
    elif total_seconds % 3600 == 0:
        return f"{total_seconds // 3600}h"
    elif total_seconds % 60 == 0:
        return f"{total_seconds // 60}m"
    else:
        return f"{total_seconds}s"


def get_data_timestep_as_str(data: pl.DataFrame) -> str:
    """
    Get time step of data.

    Parameters
    ----------
    data :
        Data with time column

    Returns
    -------
    time_step :
        Time step of data i.e. '1h', '1d', '15mi'.

    """
    check_data_has_consistent_time_step(data)
    unique_timestep = get_data_timesteps(data)
    return format_timedelta_duration(unique_timestep[0])


def get_data_timesteps(data: pl.DataFrame) -> pl.Series:
    """
    Get data timesteps. Ideally the data should have 1.

    Parameters
    ----------
    data :
        Data with time column.

    Returns
    -------
    unique_timesteps :
        All unique time steps in data (timedelta).

    """
    data_timesteps = data.with_columns([pl.col("time").diff().alias("time_step")])
    unique_timesteps = data_timesteps["time_step"].drop_nulls().unique()
    return unique_timesteps


def get_dry_spells(data: pl.DataFrame, rain_col: str) -> pl.DataFrame:
    """
    Get dry spell column.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data

    Returns
    -------
    data_w_dry_spells :
        Data with is_dry binary column

    """
    return data.with_columns(
        (pl.col(rain_col) == 0).cast(pl.Int8()).alias("is_dry"),
    )


def get_expected_days_in_month(data: pl.DataFrame) -> pl.DataFrame:
    """
    Get expected number of days in a months within the data.

    Parameters
    ----------
    data :
        Data with 'year' and 'month' columns

    Returns
    -------
    data:
        Data with 'expected_days_in_month" column

    """
    # Use map_elements + calendar.monthrange to compute days in each month
    return data.with_columns(
        [
            pl.struct(["year", "month"])
            .map_elements(
                lambda x: calendar.monthrange(x["year"], x["month"])[1],
                return_dtype=pl.Int64,
            )
            .alias("expected_days_in_month")
        ]
    )


def get_normalised_diff(data: pl.DataFrame, target_col: str, other_col: str, diff_col_name: str) -> pl.DataFrame:
    """
    Ger normalised difference between two columns in data.

    Parameters
    ----------
    data :
        Data with columns
    target_col :
        Target column
    other_col :
        Other column.
    diff_col_name :
        New column name for difference column

    Returns
    -------
    data_w_norm_diff :
        Data with normalised diff

    """
    return data.with_columns(
        (normalise_data(pl.col(target_col)) - normalise_data(pl.col(other_col))).alias(diff_col_name)
    )


def make_month_and_year_col(data: pl.DataFrame) -> pl.DataFrame:
    """
    Make year and month columns for polars dataframe.

    Parameters
    ----------
    data :
        Data with time column

    Returns
    -------
    data :
        Data with year and month columns

    """
    return data.with_columns(
        [
            pl.col("time").dt.year().alias("year"),
            pl.col("time").dt.month().alias("month"),
        ]
    )


def normalise_data(data: pl.Series | pl.expr.Expr) -> pl.Series:
    """
    Normalise data to [0, 1].

    Parameters
    ----------
    data :
        Data with time column.

    Returns
    -------
    norm_data :
        Normalised data.

    """
    return (data - data.min()) / (data.max() - data.min())


def replace_missing_vals_with_nan(
    data: pl.DataFrame,
    rain_col: str,
    missing_val: int = None,
) -> pl.DataFrame:
    """
    Replace no data value with numpy.nan.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column of rainfall
    missing_val :
        Missing value identifier

    Returns
    -------
    gdsr_data
        GDSR data with missing values replaced

    """
    if missing_val is None:
        return data.with_columns(
            pl.when(pl.col(rain_col).is_null()).then(np.nan).otherwise(pl.col(rain_col)).alias(rain_col)
        )
    else:
        return data.with_columns(
            pl.when((pl.col(rain_col).is_null()) | (pl.col(rain_col) == missing_val))
            .then(np.nan)
            .otherwise(pl.col(rain_col))
            .alias(rain_col)
        )
