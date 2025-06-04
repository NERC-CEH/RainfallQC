# -*- coding: utf-8 -*-
"""
Quality control checks examining suspicious rain gauges.

Gauge checks are defined as QC checks that: "detect abnormalities in summary and descriptive statistics of rain gauges."

Classes and functions ordered by appearance in IntenseQC framework.
"""

import polars as pl
import scipy.stats

from rainfallqc.utils import data_utils, stats


def check_years_where_nth_percentile_is_zero(data: pl.DataFrame, target_gauge_col: str, quantile: float) -> list:
    """
    Return years where the n-th percentiles is zero.

    This is QC1 from the IntenseQC framework

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data
    quantile :
        Between 0 & 1

    Returns
    -------
    year_list :
        List of years where n-th percentile is zero.

    """
    nth_perc = data.group_by_dynamic("time", every="1y").agg(pl.quantile(target_gauge_col, quantile))
    return nth_perc.filter(pl.col(target_gauge_col) == 0)["time"].dt.year().to_list()


def check_years_where_annual_mean_k_top_rows_are_zero(data: pl.DataFrame, target_gauge_col: str, k: int) -> list:
    """
    Return year list where the annual mean top-K rows are zero.

    This is QC2 from the IntenseQC framework

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data
    k :
        Number of top values check i.e. k==5 is top 5

    Returns
    -------
    year_list :
        List of years where k-largest are zero.

    """
    data_top_k = data.group_by_dynamic("time", every="1y").agg(pl.col(target_gauge_col).top_k(k).min())
    return data_top_k.filter(pl.col(target_gauge_col) == 0)["time"].dt.year().to_list()


def check_temporal_bias(
    data: pl.DataFrame,
    target_gauge_col: str,
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
    target_gauge_col :
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

    # 1. Get time-average mean
    grouped_means = data.group_by(time_group).agg(pl.col(target_gauge_col).drop_nans().mean())[target_gauge_col]

    # 2. Get data mean
    overall_mean = data[target_gauge_col].drop_nans().mean()

    # 3. Compute 1-sample t-test
    _, p_val = scipy.stats.ttest_1samp(grouped_means, overall_mean)
    return int(p_val < p_threshold)


def check_intermittency(
    data: pl.DataFrame, target_gauge_col: str, no_data_threshold: int = 2, annual_count_threshold: int = 5
) -> list:
    """
    Return years where more than five periods of missing data are bounded by zeros.

    TODO: split into multiple sub-functions and write more tests!
    This is QC5 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data
    no_data_threshold :
        Number of missing values needed to be counted as a no data period (default: 2 (days))
    annual_count_threshold :
        Number of missing data periods above no_data_threshold per year (default: 5)

    Returns
    -------
    years_w_intermittency :
        List of years with intermittency issues.

    """
    # 1. Identify missing values
    data = data_utils.replace_missing_vals_with_nan(data, target_gauge_col)  # drops None by default
    missing_vals_mask = data[target_gauge_col].is_nan()
    data = data.with_columns(missing_vals_mask.alias("is_missing"))

    # 2. Identify group numbers for consecutive nulls
    gauge_data_missing_groups = data.with_columns(
        (pl.when(data["is_missing"]).then((~data["is_missing"]).cum_sum()).otherwise(None)).alias("group")
    )

    # 3. Get length of groups of missing data
    gauge_data_missing_group_counts = gauge_data_missing_groups.group_by("group").agg(
        pl.col("is_missing").sum().alias("count")
    )

    # 4. Get groups with missing values above or at the `no_data_threshold`
    no_data_period_groups = gauge_data_missing_group_counts.filter(pl.col("count") >= no_data_threshold)["group"]

    # 5. Select rows belonging to 'no data periods'
    gauge_data_no_data_periods = gauge_data_missing_groups.filter(
        pl.col("group").is_in(no_data_period_groups.to_list())
    )

    # 6. Get annual counts of no data periods
    gauge_data_year_counts = gauge_data_no_data_periods.select(pl.col("time").dt.year()).to_series().value_counts()

    # 7. Filter out years above or at the threshold of `annual_count_threshold`
    years_w_intermittency = gauge_data_year_counts.filter(pl.col("count") >= annual_count_threshold)["time"].to_list()
    return years_w_intermittency


def check_breakpoints(
    data: pl.DataFrame,
    target_gauge_col: str,
    p_threshold: float = 0.01,
) -> int:
    """
    Use a Pettitt test rainfall data to check for breakpoints.

    This is QC6 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data.
    target_gauge_col :
        Column with rainfall data.
    p_threshold :
        Significance level for the test.

    Returns
    -------
    flag : int
        1 if breakpoint is detected (p < p_threshold), 0 otherwise

    """
    # 1. Upsample data to daily
    data_upsampled = data.upsample("time", every="1d")

    # 2. Compute Pettitt test for breakpoints
    _, p_val = stats.pettitt_test(data_upsampled[target_gauge_col].fill_nan(0.0))
    if p_val < p_threshold:
        return 1
    else:
        return 0


def check_min_val_change(data: pl.DataFrame, target_gauge_col: str, expected_min_val: float) -> list:
    """
    Return years when the minimum recorded value changes.

    Used to determine whether there are possible changes to the measuring equipment.
    This is QC7 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data.
    expected_min_val :
        Expected value of rainfall i.e. basically the resolution of data.

    Returns
    -------
    yr_list :
        List of years with minimum value changes.

    """
    # 1. Filter out non-zero years
    data_non_zero = data.filter(pl.col(target_gauge_col) > 0)

    # 2. Get minimum value each year
    data_min_by_year = data_non_zero.group_by_dynamic(pl.col("time"), every="1y").agg(pl.col(target_gauge_col).min())

    non_res_years = data_min_by_year.filter(pl.col(target_gauge_col) != expected_min_val)
    return non_res_years["time"].dt.year().to_list()
