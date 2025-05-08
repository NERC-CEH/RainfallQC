# -*- coding: utf-8 -*-
"""
All data operations.

Classes and functions ordered alphabetically.
"""

import datetime

import numpy as np
import polars as pl
import xarray as xr

SECONDS_IN_DAY = 86400.0


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
        human readable timedelta string.

    """
    total_seconds = int(td.total_seconds())

    if total_seconds % 3600 == 0:
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
