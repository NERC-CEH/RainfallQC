# -*- coding: utf-8 -*-
"""
Quality control checks examining suspicious rain gauges.

Classes and functions ordered alphabetically.
"""

import polars as pl
import scipy.stats


def get_years_where_nth_percentile_is_zero(data: pl.DataFrame, rain_col: str, quantile: float) -> list:
    """
    Return years where the n-th percentiles is zero.

    This is QC1 from the IntenseQC framework

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    quantile :
        Between 0 & 1

    Returns
    -------
    year_list :
        List of years where n-th percentile is zero.

    """
    nth_perc = data.group_by_dynamic("time", every="1y").agg(pl.quantile(rain_col, quantile))
    return nth_perc.filter(pl.col(rain_col) == 0)["time"].dt.year().to_list()


def get_years_where_annual_mean_k_top_rows_are_zero(data: pl.DataFrame, rain_col: str, k: int) -> list:
    """
    Return year list where the annual mean top-K rows are zero.

    This is QC2 from the IntenseQC framework

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    k :
        Number of top values check i.e. k==5 is top 5

    Returns
    -------
    year_list :
        List of years where k-largest are zero.

    """
    data_top_k = data.group_by_dynamic("time", every="1y").agg(pl.col(rain_col).top_k(k).min())
    return data_top_k.filter(pl.col(rain_col) == 0)["time"].dt.year().to_list()


def check_temporal_bias(
    data: pl.DataFrame,
    rain_col: str,
    time_granularity: str,
    p_threshold: float = 0.01,
) -> int:
    """
    Perform a two-sided t-test on the distribution of mean rainfall over time slices.

    This is QC3 (day of week bias) and QC4 (hour-of-day bias) from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    time_granularity :
        Temporal grouping, either 'weekday' or 'hour'
    p_threshold :
        Significance level for the test

    Returns
    -------
    flag : int
        1 if bias is detected (p < threshold), 0 otherwise

    """
    if time_granularity == "weekday":
        time_group = pl.col("time").dt.weekday()
    elif time_granularity == "hour":
        time_group = pl.col("time").dt.hour()
    else:
        raise ValueError("time_granularity must be either 'weekday' or 'hour'")
    grouped_means = data.group_by(time_group).agg(pl.col(rain_col).drop_nans().mean())[rain_col]
    overall_mean = data[rain_col].drop_nans().mean()
    _, p_val = scipy.stats.ttest_1samp(grouped_means, overall_mean)
    return int(p_val < p_threshold)
