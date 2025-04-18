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


def check_day_of_week_bias(data: pl.DataFrame, rain_col: str) -> list:
    """
    Perform a two-sided t-test on the distribution of mean rainfall over the days of the week.

    This is QC3 from the IntenseQC framework

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data

    Returns
    -------
    year_list :
        List of years where k-largest are zero.

    """
    data_weekday_mean = data.group_by(pl.col("time").dt.weekday()).agg(pl.col(rain_col).drop_nans().mean())[rain_col]
    data_mean = data[rain_col].drop_nans().mean()
    print(data_mean, data_weekday_mean)
    _, p_val = scipy.stats.ttest_1samp(data_weekday_mean, data_mean)
    p_val = 1
    if p_val < 0.01:
        return 1
    return 0
