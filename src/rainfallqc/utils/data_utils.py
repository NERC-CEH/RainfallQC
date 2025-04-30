# -*- coding: utf-8 -*-
"""
All data operations.

Classes and functions ordered alphabetically.
"""

import numpy as np
import polars as pl
import xarray as xr

SECONDS_IN_DAY = 86400.0


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
