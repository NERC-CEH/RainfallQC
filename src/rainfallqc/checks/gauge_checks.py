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
    # 1. Replace missing values with NaN
    data = data_utils.replace_missing_vals_with_nan(data, target_gauge_col)

    # --- Step 2: Mark missing values ---
    data = data.with_columns(pl.col(target_gauge_col).is_nan().alias("is_missing"))

    # 3. Assign group numbers to consecutive missing values
    grouped = data.with_columns(
        pl.when(pl.col("is_missing"))
        .then((~pl.col("is_missing")).cum_sum())  # Only number missing stretches
        .otherwise(None)
        .alias("group")
    )
    # 4. Count size of each missing group
    group_counts = (
        grouped.filter(pl.col("is_missing"))
        .group_by("group")
        .agg(pl.len().alias("count"))
        .filter(pl.col("count") >= no_data_threshold)
    )

    # 5. Keep only valid groups
    valid_missing_groups = group_counts["group"].to_list()
    valid_missing = grouped.filter(pl.col("group").is_in(valid_missing_groups))

    # 6. Get first and last time for each group
    first_last = (
        valid_missing.sort("time")
        .group_by("group")
        .agg([pl.first("time").alias("start_time"), pl.last("time").alias("end_time")])
    )

    # 7. Add stable row index to full sorted data
    df_sorted = data.sort("time").with_row_index("row_idx")

    # 8. Lookup row indices of group bounds
    first_last_with_idx = (
        first_last.join(df_sorted.select(["time", "row_idx"]), left_on="start_time", right_on="time")
        .rename({"row_idx": "start_idx"})
        .join(df_sorted.select(["time", "row_idx"]), left_on="end_time", right_on="time")
        .rename({"row_idx": "end_idx"})
    )

    # 9. Compute prev/next indices and fetch values
    row_lookup = df_sorted.select([pl.col("row_idx"), pl.col(target_gauge_col)])

    first_last_with_vals = (
        first_last_with_idx.with_columns(
            [(pl.col("start_idx") - 1).alias("prev_idx"), (pl.col("end_idx") + 1).alias("next_idx")]
        )
        .join(row_lookup.rename({target_gauge_col: "prev_val"}), left_on="prev_idx", right_on="row_idx")
        .join(row_lookup.rename({target_gauge_col: "next_val"}), left_on="next_idx", right_on="row_idx")
    )

    # 10. Filter to groups bounded by zero
    bounded_by_zero = first_last_with_vals.filter((pl.col("prev_val") == 0) & (pl.col("next_val") == 0))

    # 11. Extract year from each bounded group's start time
    bounded_years = bounded_by_zero.select(pl.col("start_time").dt.year().alias("year"))

    # 12. Count how many bounded groups occur per year
    year_counts = bounded_years.group_by("year").len()

    # 13. Get years exceeding threshold
    years_w_intermittency = year_counts.filter(pl.col("len") >= annual_count_threshold)["year"].to_list()

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
