# -*- coding: utf-8 -*-
"""
Statistical tests.

Classes and functions ordered alphabetically.

"""

import numpy as np
import polars as pl

RAINFALL_WORLD_RECORDS = {"hourly": 401.0, "daily": 1825.0}  # mm


def filter_out_rain_world_records(data: pl.DataFrame, rain_col: str, time_res: str) -> pl.DataFrame:
    """
    Filter out rain world records based on time resolution.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    time_res :
        Temporal resolution of the time series either 'daily' or 'hourly'

    Returns
    -------
    data_not_wr :
        Data without rain world records

    """
    # 1. Get world records
    rainfall_world_records = get_rainfall_world_records()
    # 2. Filter out world records
    data_not_wr = data.with_columns(
        pl.when(pl.col(rain_col) > rainfall_world_records[time_res])
        .then(np.nan)
        .otherwise(pl.col(rain_col))
        .alias(rain_col)
    )

    return data_not_wr


def get_rainfall_world_records() -> dict[str, float]:
    """
    Return rainfall world record as of 29/04/25.

    See:
    - http://www.nws.noaa.gov/oh/hdsc/record_precip/record_precip_world.html
    - http://www.bom.gov.au/water/designRainfalls/rainfallEvents/worldRecRainfall.shtml
    - https://wmo.asu.edu/content/world-meteorological-organization-global-weather-climate-extremes-archive

    Returns
    -------
    rwr :
        rainfall world records set in stats.py

    """
    return RAINFALL_WORLD_RECORDS


def pettitt_test(arr: pl.Series | np.ndarray) -> (int | float, int | float):
    """
    Pettitt test for detecting a change point in a time series.

    Calculated following Pettitt (1979): https://www.jstor.org/stable/2346729?seq=4#metadata_info_tab_contents.

    TAKEN FROM: https://stackoverflow.com/questions/58537876/how-to-run-standard-normal-homogeneity-test-for-a-time-series-data.

    Parameters
    ----------
    arr : pl.Series or np.ndarray
        The input time series data.

    Returns
    -------
    tau : int
        Index of the change point (first point of the second segment).
    p : float
        p-value for the test statistic.

    """
    if isinstance(arr, pl.Series):
        arr = arr.to_numpy()

    n = len(arr)
    K = np.zeros(n)

    # Compute rank matrix difference in a vectorized way
    for t in range(n):
        left = arr[:t]
        right = arr[t:]
        if left.size > 0 and right.size > 0:
            K[t] = np.sum(np.sign(left[:, None] - right[None, :]))

    tau = int(np.argmax(np.abs(K)))
    U = np.max(np.abs(K))
    p = 2 * np.exp((-6 * U**2) / (n**3 + n**2))
    return tau, p


def calculate_simple_precip_intensity_index(data: pl.DataFrame, rain_col: str, wet_day_threshold: int | float) -> float:
    """
    Calculate simple precipitation intensity index.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    wet_day_threshold :
        Threshold for rainfall intensity in given time period

    Returns
    -------
    sdii_val :
        Simple precipitation intensity index

    """
    data_rain_sum = data.filter(pl.col(rain_col) >= wet_day_threshold).fill_nan(0.0).sum()[rain_col][0]
    data_wet_day_count = data.filter(pl.col(rain_col) >= wet_day_threshold).drop_nans().count()[rain_col][0]
    return data_rain_sum / float(data_wet_day_count)
