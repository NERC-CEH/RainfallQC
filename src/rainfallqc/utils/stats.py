# -*- coding: utf-8 -*-
"""
Statistical tests and other indices for rainfall data quality control.

Classes and functions ordered alphabetically.

"""

import numpy as np
import polars as pl
import scipy.stats

from rainfallqc.utils import data_utils

RAINFALL_WORLD_RECORDS = {"15m": 198.0, "hourly": 401.0, "daily": 1825.0}  # mm


def affinity_index(data: pl.DataFrame, binary_col: str, return_match_and_diff: bool = False) -> tuple | float:
    """
    Calculate affinity index from binary column.

    Parameters
    ----------
    data :
        Rainfall data
    binary_col :
        Column with binary data
    return_match_and_diff :
        Whether to return count of matching and difference columns as well as affinity index.

    Returns
    -------
    affinity :
        Affinity index.

    """
    match = data[binary_col].value_counts().filter(pl.col(binary_col) == 1)["count"]
    match = match.item() if match.len() == 1 else 0
    diff = data[binary_col].value_counts().filter(pl.col(binary_col) == 0)["count"]
    diff = diff.item() if diff.len() == 1 else 0
    affinity = match / (match + diff)
    if return_match_and_diff:
        return match, diff, affinity
    return affinity


def dry_spell_fraction(rain_daily: pl.DataFrame, target_gauge_col: str, dry_period_days: int) -> pl.Series:
    """
    Make dry spell fraction column.

    Parameters
    ----------
    rain_daily :
        Single time-step of rainfall data with 'dry_day' column
    target_gauge_col :
        Column with Rainfall data
    dry_period_days :
        Dry periods window in days

    Returns
    -------
    rain_daily_w_dry_spell_fraction :
        Single row with dry spell fraction column

    """
    assert "is_dry" in rain_daily, "No dry_day column found, please run rainfallqc.utils.data_utils.get_dry_spells()"

    # 1. Get dry spells
    rain_daily_dry_day = data_utils.get_dry_spells(rain_daily, target_gauge_col)

    # 2. Get dry spell fraction
    rain_daily_dry_day = rain_daily_dry_day.with_columns(
        dry_spell_fraction=pl.col("is_dry").rolling_sum(window_size=dry_period_days, min_samples=dry_period_days)
        / dry_period_days
    )
    return rain_daily_dry_day["dry_spell_fraction"]


def factor_diff(data: pl.DataFrame, target_col: str, other_col: str) -> pl.DataFrame:
    """
    Compute factor diff for polars.

    Parameters
    ----------
    data :
        Rainfall data
    target_col :
        Target column to compute factor diff for
    other_col :
        Other column to compute factor diff for

    Returns
    -------
    data_w_factor_diff :
        Data with factor diff

    """
    return data.with_columns(
        pl.when((pl.col(target_col) > 0) & (pl.col(other_col) > 0))
        .then(pl.col(target_col) / pl.col(other_col))
        .otherwise(np.nan)
        .alias("factor_diff")
    )


def filter_out_rain_world_records(data: pl.DataFrame, target_gauge_col: str, time_res: str) -> pl.DataFrame:
    """
    Filter out rain world records based on time resolution.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
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
        pl.when(pl.col(target_gauge_col) > rainfall_world_records[time_res])
        .then(np.nan)
        .otherwise(pl.col(target_gauge_col))
        .alias(target_gauge_col)
    )

    return data_not_wr


def fit_expon_and_get_percentile(series: pl.Series, percentiles: list[float]) -> dict[float, float]:
    """
    Fit exponential to data series and then get percentile using PPF.

    Parameters
    ----------
    series :
        Data series to fit exponential distribution.
    percentiles :
        Percentiles (between 0-1) to evaluate on the fitted exponential distribution

    Returns
    -------
    expon_percentiles :
        Threshold at percentile of fitted distribution

    """
    # 1. Fit exponential distribution of normalised diff
    expon_params = scipy.stats.expon.fit(series)
    # 2. Calculate thresholds at percentiles of fitted distribution
    return {p: scipy.stats.expon.ppf(p, expon_params[0], expon_params[1]) for p in percentiles}


def gauge_correlation(data: pl.DataFrame, target_col: str, other_col: str) -> float:
    """
    Calculate correlation between rain gauge data columns.

    Parameters
    ----------
    data :
        Rainfall data
    target_col :
        Target rainfall column
    other_col :
        Other rainfall column

    Returns
    -------
    corr_coef :
        Correlation coefficient.

    """
    return np.ma.corrcoef(np.ma.masked_invalid(data[target_col]), np.ma.masked_invalid(data[other_col]))[0, 1]


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


def percentage_diff(target: pl.Expr, other: pl.Expr) -> pl.Series:
    """
    Percentage difference between target and other column.

    Parameters
    ----------
    target:
        Target data to compare other too
    other:
        Other data

    Returns
    -------
    perc_diff:
        Percentage difference

    """
    return (target - other) * 100 / other


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


def simple_precip_intensity_index(data: pl.DataFrame, target_gauge_col: str, wet_threshold: int | float) -> float:
    """
    Calculate simple precipitation intensity index.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data
    wet_threshold :
        Threshold for rainfall intensity in given time period

    Returns
    -------
    sdii_val :
        Simple precipitation intensity index

    """
    data_rain_sum = data.filter(pl.col(target_gauge_col) >= wet_threshold).fill_nan(0.0).sum()[target_gauge_col][0]
    data_wet_day_count = data.filter(pl.col(target_gauge_col) >= wet_threshold).drop_nans().count()[target_gauge_col][0]
    return data_rain_sum / float(data_wet_day_count)
