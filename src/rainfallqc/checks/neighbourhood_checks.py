# -*- coding: utf-8 -*-
"""
Quality control checks using neighbouring gauges to identify suspicious data.

Neighbourhood checks are QC checks that: "detect abnormalities in a gauges given measurements in neighbouring gauges."

Classes and functions ordered by appearance in IntenseQC framework.
"""

from typing import Iterable, List

import numpy as np
import polars as pl

from rainfallqc.utils import data_readers, data_utils, neighbourhood_utils, stats


def check_wet_neighbours(
    neighbour_data: pl.DataFrame,
    target_gauge_col: str,
    neighbouring_gauge_cols: List[str],
    time_res: str,
    wet_threshold: int | float,
    min_n_neighbours: int,
    n_neighbours_ignored: int = 0,
    hour_offset: int = 0,
) -> pl.DataFrame:
    """
    Identify suspicious large values by comparison to neighbour for hourly or daily data.

    Flags (majority voting where flag is the highest value across all neighbours):
    3, if normalised difference between target gauge and neighbours is above the 99.9th percentile
    2, ...if above 99th percentile
    1, ...if above 95th percentile
    0, if not in extreme exceedance of neighbours

    This is QC16 & QC17 from the IntenseQC framework.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_cols:
        List of columns with neighbouring gauges
    time_res :
        Time resolution of data
    wet_threshold :
        Threshold for rainfall intensity in given time period
    min_n_neighbours :
        Minimum number of neighbours needed to be checked for flag
    n_neighbours_ignored :
        Number of zero flags allowed for majority voting (default: 0)
    hour_offset :
        Time offset of hourly data in hours (i.e. if 7am-7am, then set this to 7) (default: 0)

    Returns
    -------
    data_w_wet_flags :
        Target data with wet flags

    """
    # 0. Initial checks
    data_utils.check_data_is_specific_time_res(neighbour_data, time_res)
    neighbouring_gauge_cols_new = neighbouring_gauge_cols.copy()  # make copy
    if target_gauge_col in neighbouring_gauge_cols_new:
        # Remove target col from list so it is not included as a neighbour of itself.
        neighbouring_gauge_cols_new.remove(target_gauge_col)
    check_neighbouring_gauge_columns(neighbour_data, target_gauge_col, neighbouring_gauge_cols_new)

    # 1. Resample to daily
    if time_res == "hourly":
        rain_cols = neighbour_data.columns[1:]  # get rain columns
        original_hourly_neighbour_data = neighbour_data.clone()
        neighbour_data = data_readers.convert_data_hourly_to_daily(
            neighbour_data, rain_cols=rain_cols, hour_offset=hour_offset
        )

    # 2. Loop through each neighbour and get wet_flags
    for neighbouring_gauge_col in neighbouring_gauge_cols_new:
        # 2.1 Flag data based on comparison of wet values in neighbours
        one_neighbour_data_wet_flags = flag_wet_day_errors_based_on_neighbours(
            neighbour_data, target_gauge_col, neighbouring_gauge_col, wet_threshold
        )

        # 2.2 Join to all data
        neighbour_data = neighbour_data.join(
            one_neighbour_data_wet_flags[["time", f"wet_flag_{neighbouring_gauge_col}"]],
            on="time",
            how="left",
        )

    # 3. Get number of neighbours 'online' for each time step
    neighbour_data = make_num_neighbours_online_col(neighbour_data, neighbouring_gauge_cols_new)

    # 4. Neighbour majority voting where the flag is the highest flag in all neighbours
    neighbour_data_w_wet_flags = get_majority_voting_flag(
        neighbour_data,
        neighbouring_gauge_cols_new,
        min_n_neighbours,
        n_zeros_allowed=n_neighbours_ignored,
        flag_col_prefix="wet_flag_",
        new_flag_col_name="majority_wet_flag",
        aggregation="min",
    )

    # 5. Clean up data for return
    neighbour_data_w_wet_flags = neighbour_data_w_wet_flags.select(["time", "majority_wet_flag"])

    # 6. If hourly data join back and forward flood fill
    if time_res == "hourly":
        # 6.1 Join flags back to original hourly data
        hourly_neighbour_data_w_wet_flags = original_hourly_neighbour_data.join(
            neighbour_data_w_wet_flags[["time", "majority_wet_flag"]], on="time", how="left"
        )
        # 6.2 Forward flood-fill data to convert the flags back to hourly
        hourly_neighbour_data_w_wet_flags = hourly_neighbour_data_w_wet_flags.with_columns(
            pl.col("majority_wet_flag").forward_fill(limit=23)  # hours
        )
        hourly_neighbour_data_w_wet_flags = hourly_neighbour_data_w_wet_flags.rename(
            {"majority_wet_flag": f"wet_spell_flag_{time_res}"}
        )
        return hourly_neighbour_data_w_wet_flags.select(["time", f"wet_spell_flag_{time_res}"])
    else:
        neighbour_data_w_wet_flags = neighbour_data_w_wet_flags.rename(
            {"majority_wet_flag": f"wet_spell_flag_{time_res}"}
        )
        return neighbour_data_w_wet_flags


def check_dry_neighbours(
    neighbour_data: pl.DataFrame,
    target_gauge_col: str,
    neighbouring_gauge_cols: List[str],
    time_res: str,
    min_n_neighbours: int,
    dry_period_days: int = 15,
    n_neighbours_ignored: int = 0,
    hour_offset: int = 0,
) -> pl.DataFrame:
    """
    Identify suspicious dry periods by comparison to neighbour for hourly or daily data.

    Flags (majority voting where flag is the highest value across all neighbours):
    3, if >= 3 average number of wet days in neighbours during a dry period in target.
    2, ...if 2 days
    1, ...if 1 day
    0, if not neighbours on average dry during dry target gauge period.

    This is QC18 & QC19 from the IntenseQC framework.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_cols:
        List of columns with neighbouring gauges
    time_res :
        Time resolution of data
    min_n_neighbours :
        Minimum number of neighbours needed to be checked for flag
    dry_period_days :
        Length for of a "dry_spell" (default: 15 days)
    n_neighbours_ignored :
        Number of zero flags allowed for majority voting (default: 0)
    hour_offset :
        Time offset of hourly data in hours (i.e. if 7am-7am, then set this to 7) (default: 0)

    Returns
    -------
    data_w_dry_flags :
        Target data with dry flags

    """
    # 0. Initial checks
    data_utils.check_data_is_specific_time_res(neighbour_data, time_res)
    neighbouring_gauge_cols_new = neighbouring_gauge_cols.copy()  # make copy
    if target_gauge_col in neighbouring_gauge_cols_new:
        # Remove target col from list so it is not included as a neighbour of itself.
        neighbouring_gauge_cols_new.remove(target_gauge_col)
    check_neighbouring_gauge_columns(neighbour_data, target_gauge_col, neighbouring_gauge_cols_new)

    # 1. Get proportions of dry period required to be flagged 1, 2, or 3
    dry_period_proportions = data_utils.get_dry_period_proportions(dry_period_days)

    # 2. Resample to daily
    if time_res == "hourly":
        rain_cols = neighbour_data.columns[1:]  # get rain columns
        original_hourly_neighbour_data = neighbour_data.clone()
        neighbour_data = data_readers.convert_data_hourly_to_daily(
            neighbour_data, rain_cols=rain_cols, hour_offset=hour_offset
        )

    # 3. Loop through each neighbour and get wet_flags
    for neighbouring_gauge_col in neighbouring_gauge_cols_new:
        # 3.1 Convert to dry spell fraction
        one_neighbour_data = get_dry_spell_fraction_col(
            neighbour_data,
            target_gauge_col=target_gauge_col,
            dry_period_days=dry_period_days,
            neighbouring_gauge_col=neighbouring_gauge_col,
        )

        # 3.2 Flag dry spell fractions
        one_neighbour_data_dry_flags = flag_dry_spell_fractions(
            one_neighbour_data,
            target_gauge_col=target_gauge_col,
            neighbouring_gauge_col=neighbouring_gauge_col,
            proportion_of_dry_day_for_flags=dry_period_proportions,
        )

        # 3.3 Join to all data
        neighbour_data = neighbour_data.join(
            one_neighbour_data_dry_flags[["time", f"dry_flag_{neighbouring_gauge_col}"]],
            on="time",
            how="left",
        )

    # 4. Get number of neighbours 'online' for each time step
    neighbour_data = make_num_neighbours_online_col(neighbour_data, neighbouring_gauge_cols_new)

    # 5. Neighbour majority voting where the flag is the highest flag in all neighbours
    neighbour_data_w_dry_flags = get_majority_voting_flag(
        neighbour_data,
        neighbouring_gauge_cols_new,
        min_n_neighbours,
        n_zeros_allowed=n_neighbours_ignored,
        flag_col_prefix="dry_flag_",
        new_flag_col_name="majority_dry_flag",
        aggregation="min",
    )

    # 6. Clean up data for return
    neighbour_data_w_dry_flags = neighbour_data_w_dry_flags.select(["time", "majority_dry_flag"])
    # 7. Backwards propagate dry flags into dry period
    neighbour_data_w_dry_flags = data_utils.back_propagate_daily_data_flags(
        neighbour_data_w_dry_flags, flag_column="majority_dry_flag", num_days=(dry_period_days - 1)
    )

    # 8. If hourly data join back and forward flood fill
    if time_res == "hourly":
        # 8.1 Join flags back to original hourly data
        hourly_neighbour_data_w_dry_flags = original_hourly_neighbour_data.join(
            neighbour_data_w_dry_flags[["time", "majority_dry_flag"]], on="time", how="left"
        )
        # 8.2 Forward flood-fill data to convert the flags back to hourly
        hourly_neighbour_data_w_dry_flags = hourly_neighbour_data_w_dry_flags.with_columns(
            pl.col("majority_dry_flag").forward_fill(limit=23)  # hours
        )
        hourly_neighbour_data_w_dry_flags = hourly_neighbour_data_w_dry_flags.rename(
            {"majority_dry_flag": f"dry_spell_flag_{time_res}"}
        )
        return hourly_neighbour_data_w_dry_flags.select(["time", f"dry_spell_flag_{time_res}"])
    else:
        neighbour_data_w_dry_flags = neighbour_data_w_dry_flags.rename(
            {"majority_dry_flag": f"dry_spell_flag_{time_res}"}
        )
        return neighbour_data_w_dry_flags


def check_monthly_neighbours(
    monthly_neighbour_data: pl.DataFrame,
    target_gauge_col: str,
    neighbouring_gauge_cols: List[str],
    min_n_neighbours: int,
    n_neighbours_ignored: int = 0,
) -> pl.DataFrame:
    """
    Identify suspicious monthly totals by comparison to neighbouring monthly gauges.

    Flags (majority voting where flag is the highest value across all neighbours):
    Flags -3 to 3 based on percentage difference:
    -3, -100% (i.e. gauge dry but neighbours not)
    -2, <= 50%
    -1, <= 25%
    1, >= 25%
    2, >= 50%
    3, >= 100%
    Flags equal to 3 may be upgraded to:
    4, >=1.25 x record maximum for all neighbours
    5, >=2 x record maximum for all neighbours
    Or:
    0, if not in extreme exceedance of neighbours

    This is QC20 from the IntenseQC framework.

    Parameters
    ----------
    monthly_neighbour_data :
        Monthly rainfall data of neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_cols:
        List of columns with neighbouring gauges
    min_n_neighbours :
        Minimum number of neighbours needed to be checked for flag
    n_neighbours_ignored :
        Number of zero flags allowed for majority voting (default: 0)

    Returns
    -------
    data_w_monthly_flags :
        Target data with monthly flags

    """
    # 0. Initial checks
    data_utils.check_data_is_monthly(monthly_neighbour_data)
    neighbouring_gauge_cols_new = neighbouring_gauge_cols.copy()  # make copy
    if target_gauge_col in neighbouring_gauge_cols_new:
        # Remove target col from list so it is not included as a neighbour of itself.
        neighbouring_gauge_cols_new.remove(target_gauge_col)
    check_neighbouring_gauge_columns(monthly_neighbour_data, target_gauge_col, neighbouring_gauge_cols_new)

    # 2. Loop through each neighbour and get percentage diff flags
    for neighbouring_gauge_col in neighbouring_gauge_cols_new:
        # 2.1. Calculate percentage difference between target and neighbour
        one_neighbour_data_perc_diff = monthly_neighbour_data.select(
            ["time", stats.percentage_diff(pl.col(target_gauge_col), pl.col(neighbouring_gauge_col)).alias("perc_diff")]
        )

        # 2.2 Flag percentage difference
        one_neighbour_data_monthly_flags = flag_percentage_diff_of_neighbour(
            one_neighbour_data_perc_diff, neighbouring_gauge_col=neighbouring_gauge_col
        )

        # 2.3 Join to all data
        monthly_neighbour_data = monthly_neighbour_data.join(
            one_neighbour_data_monthly_flags[["time", f"perc_diff_flag_{neighbouring_gauge_col}"]],
            on="time",
            how="left",
        )

    # 3. Get majority-voted flag for positive and negative flags
    # i.e. get minimum positive flag, when positive, and maximum negative flag when negative
    monthly_neighbour_data_w_flags = get_majority_positive_or_negative_flags(
        monthly_neighbour_data,
        neighbouring_gauge_cols=neighbouring_gauge_cols_new,
        min_n_neighbours=min_n_neighbours,
        n_neighbours_ignored=n_neighbours_ignored,
    )

    # 4. Calculate neighbour monthly max column
    monthly_neighbour_data_w_flags = make_neighbour_monthly_max_climatology(
        monthly_neighbour_data_w_flags, neighbouring_gauge_cols_new
    )

    # 5. Upgrade extreme wet flags to 4 or 5 based on excess of neighbour monthly max climatology
    monthly_neighbour_data_w_flags = upgrade_monthly_flag_using_neighbour_max_climatology(
        monthly_neighbour_data_w_flags, target_gauge_col, min_n_neighbours
    )

    return monthly_neighbour_data_w_flags.select(["time", "majority_monthly_flag"])


def check_timing_offset(
    neighbour_data: pl.DataFrame,
    target_gauge_col: str,
    neighbouring_gauge_col: str,
    time_res: str,
    offsets_to_check: Iterable[int] = (-1, 0, 1),
) -> int:
    """
    Identify suspicious data offset using Affinity Index and correlation (r^2) between target and nearest neighbour.

    Flags:
    -1, -1 day offset
    0, no offset
    1, +1 day offset

    This is QC21 from the IntenseQC framework.

    Parameters
    ----------
    neighbour_data :
        Rainfall data with target and neighbouring gauge and time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col :
        Neighbouring gauge column
    time_res :
        Time resolution of data
    offsets_to_check :
        Offset values to check (default: -1, 0, 1)

    Returns
    -------
    offset_flag :
        e.g. -1, 0 or 1

    """
    # 0. Initial checks
    assert all(column in neighbour_data.columns for column in [target_gauge_col, neighbouring_gauge_col]), (
        f"Not all of {[target_gauge_col, neighbouring_gauge_col]} found in input data columns"
    )
    # Add 0 (i.e. no lag) to offsets to check if not included
    if 0 not in offsets_to_check:
        offsets_to_check = list(offsets_to_check)
        offsets_to_check.append(0)

    # 1. create dictionaries to store affinity index and correlation at different offsets/lags
    neighbour_affinities = {}
    neighbour_correlation = {}

    # 2. Loop through offsets and calculate affinity index and correlation
    for offset in offsets_to_check:
        # 2.1. Offset neighbour data by offset amount
        offset_neighbour_data = data_utils.offset_data_by_time(
            neighbour_data, target_col=target_gauge_col, offset_in_time=offset, time_res=time_res
        )

        # 2.2 get non-zero minima column
        offset_neighbour_data = neighbourhood_utils.get_rain_not_minima_column(
            offset_neighbour_data, target_col=target_gauge_col, other_col=neighbouring_gauge_col
        )

        # 2.3 Calculate affinity index
        neighbour_affinities[offset] = stats.affinity_index(offset_neighbour_data, binary_col="rain_not_minima")

        # 2.4 Calculate neighbour pearson correlation
        neighbour_correlation[offset] = stats.gauge_correlation(
            offset_neighbour_data,
            target_col=target_gauge_col,
            other_col=neighbouring_gauge_col,
        )

    # Get flag
    offset_flag = 0
    if max(neighbour_affinities, key=neighbour_affinities.get) == max(
        neighbour_correlation, key=neighbour_correlation.get
    ):
        offset_flag = max(neighbour_affinities, key=neighbour_affinities.get)

    return offset_flag


def check_neighbour_affinity_index(
    neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str
) -> float:
    """
    Pre-QC Affinity index calculated between target and nearest neighbouring gauge.

    Flag:
    Between 0-1 for affinity index

    This is QC22 from the IntenseQC framework.

    Parameters
    ----------
    neighbour_data :
        Rainfall data with target and neighbouring gauge and time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col :
        Neighbouring gauge column

    Returns
    -------
    affinity_index :
        Between 0 and 1

    """
    # 1. get non-zero minima column
    neighbour_data = neighbourhood_utils.get_rain_not_minima_column(
        neighbour_data, target_col=target_gauge_col, other_col=neighbouring_gauge_col
    )

    # 2. Calculate affinity index
    return stats.affinity_index(neighbour_data, binary_col="rain_not_minima")


def check_neighbour_correlation(
    neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str
) -> float:
    """
    Pre-QC pearson correlation calculated between target and neighbouring gauge.

    Flag:
    Between -1 to +1 for pearson correlation coefficient

    This is QC23 from the IntenseQC framework.

    Parameters
    ----------
    neighbour_data :
        Rainfall data with target and neighbouring gauge and time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col :
        Neighbouring gauge column

    Returns
    -------
    r_squared :
        Between -1 to 1

    """
    # 1. Calculate pearson correlation
    return stats.gauge_correlation(neighbour_data, target_col=target_gauge_col, other_col=neighbouring_gauge_col)


def check_daily_factor(
    neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str, averaging_method: str = "mean"
) -> float:
    """
    Daily factor difference between target and neighbouring gauge.

    Flag:
    Scalar factor difference.

    This is QC24 from the IntenseQC framework.

    Parameters
    ----------
    neighbour_data :
        Daily rainfall data with target and neighbouring gauge and time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col :
        Neighbouring gauge column
    averaging_method :
        Method to use to get average i.e. mean or median (default mean)

    Returns
    -------
    daily_factor :
        Average factor diff between target and neighbour

    Raises
    ------
    ValueError :
        If averaging method not 'mean' or 'median'

    """
    # 0. Initial checks
    data_utils.check_data_is_specific_time_res(neighbour_data, "daily")

    # 1. Daily factor difference
    daily_factor = stats.factor_diff(neighbour_data, target_col=target_gauge_col, other_col=neighbouring_gauge_col)

    # 2. Get mean daily factor difference
    daily_factor_positive_vals = daily_factor.drop_nans().filter(
        (pl.col(target_gauge_col) > 0) & (pl.col(neighbouring_gauge_col) > 0)
    )

    if averaging_method == "mean":
        return daily_factor_positive_vals["factor_diff"].mean()
    elif averaging_method == "median":
        return daily_factor_positive_vals["factor_diff"].median()
    else:
        raise ValueError(f"{averaging_method} not recognised, please use 'mean' or 'median'")


def check_monthly_factor(
    neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str
) -> pl.DataFrame:
    """
    Monthly factor difference between target and neighbouring gauge.

    Flags:
    1, when ~10 x greater than neighbour monthly total
    2, when ~25.4 x greater ...
    3, when ~2.54 x greater ...
    4, when ~10 x smaller than neighbour monthly total
    5, when ~25.4 x smaller ...
    6, when ~2.54 x smaller ...
    else, 0

    This is QC25 from the IntenseQC framework.

    Parameters
    ----------
    neighbour_data :
        Daily rainfall data with target and neighbouring gauge and time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col :
        Neighbouring gauge column

    Returns
    -------
    monthly_factor_flag :
        Factor diff flags between target and neighbour

    """
    # 0. Initial checks
    data_utils.check_data_is_monthly(neighbour_data)

    # 1. Calculate monthly factor difference
    monthly_factor = stats.factor_diff(neighbour_data, target_col=target_gauge_col, other_col=neighbouring_gauge_col)

    # 2. Flag factor difference
    monthly_factor_flags = flag_monthly_factor_differences(monthly_factor, target_gauge_col=neighbouring_gauge_col)
    return monthly_factor_flags.select(["time", "monthly_factor_flag"])


def flag_monthly_factor_differences(monthly_factor: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Flag monthly difference flag after IntenseQC framework for QC25.

    Flags:
    1, when ~10 x greater than neighbour monthly total
    2, when ~25.4 x greater ...
    3, when ~2.54 x greater ...
    4, when ~10 x smaller than neighbour monthly total
    5, when ~25.4 x smaller ...
    6, when ~2.54 x smaller ...
    else, 0


    Parameters
    ----------
    monthly_factor :
        Rainfall data with 'factor_diff' and gauge_col
    target_gauge_col :
        Rain column

    Returns
    -------
    monthly_factor_w_flag :
        Rainfall data with flags based on monthly factor difference

    """
    return monthly_factor.with_columns(
        pl.when((pl.col("factor_diff") < 11) & (pl.col("factor_diff") > 9))
        .then(1)
        .when((pl.col("factor_diff") < 26) & (pl.col("factor_diff") > 24))
        .then(2)
        .when((pl.col("factor_diff") < 3) & (pl.col("factor_diff") > 2))
        .then(3)
        .when((pl.col("factor_diff") > 1 / 11) & (pl.col("factor_diff") < 1 / 9))
        .then(4)
        .when((pl.col("factor_diff") > 1 / 26) & (pl.col("factor_diff") < 1 / 24))
        .then(5)
        .when((pl.col("factor_diff") > 1 / 3) & (pl.col("factor_diff") < 1 / 2))
        .then(6)
        .otherwise(0)
        .alias("monthly_factor_flag")
    )


def make_neighbour_monthly_max_climatology(
    monthly_neighbour_data: pl.DataFrame, neighbouring_gauge_cols: list
) -> pl.DataFrame:
    """
    Make neighbourhood monthly max climatology.

    Parameters
    ----------
    monthly_neighbour_data :
        Monthly rainfall data of neighbouring gauges with time col
    neighbouring_gauge_cols:
        List of columns with neighbouring gauges

    Returns
    -------
    data_w_monthly_flags :
        Target data with monthly flags

    """
    # 1. Make number of neighbours online column
    monthly_neighbour_data = make_num_neighbours_online_col(monthly_neighbour_data, neighbouring_gauge_cols)

    # 2. Make month and year column
    monthly_neighbour_data = data_utils.make_month_and_year_col(monthly_neighbour_data)

    # 3. Calculate neighbour max monthly climatology
    monthly_neighbour_data_max = monthly_neighbour_data.group_by("month").agg(
        pl.max_horizontal([pl.col(col).max() for col in neighbouring_gauge_cols]).alias("neighbour_max")
    )

    # 4. Join neighbour max climatology back to data
    monthly_neighbour_data = monthly_neighbour_data.join(monthly_neighbour_data_max, on="month")
    return monthly_neighbour_data


def upgrade_monthly_flag_using_neighbour_max_climatology(
    monthly_neighbour_data_w_flags: pl.DataFrame, target_gauge_col: str, min_n_neighbours: int
) -> pl.DataFrame:
    """
    Upgrade flags to 4 and 5 flags for monthly neighbours in excess of neighbourhood monthly climatological max.

    Parameters
    ----------
    monthly_neighbour_data_w_flags :
        Monthly rainfall data of neighbouring gauges with time col and 'majority_monthly_flag'
    target_gauge_col :
        Target gauge column
    min_n_neighbours :
        Minimum number of neighbours needed to be checked for flag

    Returns
    -------
    data_w_monthly_flags :
        Target data with monthly flags

    """
    return monthly_neighbour_data_w_flags.with_columns(
        pl.when(
            (pl.col("majority_monthly_flag") == 3)
            & (pl.col("n_neighbours_online") >= min_n_neighbours)
            & (pl.col(target_gauge_col) > (1.25 * pl.col("neighbour_max")))
            & (pl.col(target_gauge_col) < (2 * pl.col("neighbour_max")))
        )
        .then(4)
        .when(
            (pl.col("majority_monthly_flag") == 3)
            & (pl.col("n_neighbours_online") >= min_n_neighbours)
            & (pl.col(target_gauge_col) > (2 * pl.col("neighbour_max")))
        )
        .then(5)
        .otherwise(pl.col("majority_monthly_flag"))
        .alias("majority_monthly_flag")
    )


def get_majority_positive_or_negative_flags(
    monthly_neighbour_data: pl.DataFrame,
    neighbouring_gauge_cols: list,
    min_n_neighbours: int,
    n_neighbours_ignored: int,
) -> pl.DataFrame:
    """
    Get majority voted positive or negative flags i.e. get minimum positive flag, or maximum negative flag.

    Parameters
    ----------
    monthly_neighbour_data :
        Monthly rainfall data of neighbouring gauges with time col
    neighbouring_gauge_cols:
        List of columns with neighbouring gauges
    min_n_neighbours :
        Minimum number of neighbours needed to be checked for flag
    n_neighbours_ignored :
        Number of zero flags allowed for majority voting

    Returns
    -------
    data_w_monthly_flag :
        Data with majority_monthly_flag

    """
    # 1. Get negative and positive only data for flagging
    all_flag_cols = [f"perc_diff_flag_{col}" for col in neighbouring_gauge_cols]
    data_positive = data_utils.extract_positive_values_from_data(
        monthly_neighbour_data, cols_to_extract_from=all_flag_cols
    )
    data_negative = data_utils.extract_negative_values_from_data(
        monthly_neighbour_data, cols_to_extract_from=all_flag_cols
    )

    # 2. Get number of neighbours 'online' at each time step for positive and negative data
    data_positive = make_num_neighbours_online_col(data_positive, all_flag_cols)
    data_negative = make_num_neighbours_online_col(data_negative, all_flag_cols)

    # 3. Neighbour majority voting where the flag is the highest flag in all neighbours
    data_positive_flags = get_majority_voting_flag(
        data_positive,
        neighbouring_gauge_cols,
        min_n_neighbours,
        n_zeros_allowed=n_neighbours_ignored,
        flag_col_prefix="perc_diff_flag_",
        new_flag_col_name="majority_monthly_flag",
        aggregation="min",
    )
    data_negative_flags = get_majority_voting_flag(
        data_negative,
        neighbouring_gauge_cols,
        min_n_neighbours,
        n_zeros_allowed=n_neighbours_ignored,
        flag_col_prefix="perc_diff_flag_",
        new_flag_col_name="majority_monthly_flag",
        aggregation="max",
    )

    # 4. Merge flags together
    monthly_neighbour_data_w_flags = data_positive_flags.select(["time", "majority_monthly_flag"]).join(
        data_negative_flags.select(["time", "majority_monthly_flag"]), on="time", how="full"
    )
    monthly_neighbour_data_w_flags = monthly_neighbour_data_w_flags.with_columns(
        [
            pl.when((pl.col("majority_monthly_flag") != 0) & pl.col("majority_monthly_flag").is_not_nan())
            .then(pl.col("majority_monthly_flag"))
            .when((pl.col("majority_monthly_flag_right") != 0) & pl.col("majority_monthly_flag_right").is_not_nan())
            .then(pl.col("majority_monthly_flag_right"))
            .when(
                (pl.col("majority_monthly_flag") == 0) & pl.col("majority_monthly_flag_right").is_nan()
                | (pl.col("majority_monthly_flag_right") == 0) & pl.col("majority_monthly_flag").is_nan()
                | (pl.col("majority_monthly_flag") == 0) & (pl.col("majority_monthly_flag_right") == 0)
            )
            .then(0)
            .otherwise(np.nan)
            .alias("majority_monthly_flag")
        ]
    )

    # 5. Join back to original data
    return monthly_neighbour_data.join(monthly_neighbour_data_w_flags, on="time", how="left")


def get_dry_spell_fraction_col(
    neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str, dry_period_days: int
) -> pl.DataFrame:
    """
    Get dry spell fraction column.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col:
        Neighbouring gauge column
    dry_period_days :
        Length for of a "dry_spell" (default: 15 days)

    Returns
    -------
    data_w_dry_spell_fraction :
        Target data with dry spell fractions

    """
    return neighbour_data.with_columns(
        pl.col(target_gauge_col)
        .map_batches(
            lambda row: data_utils.calculate_dry_spell_fraction(
                row, target_gauge_col=target_gauge_col, dry_period_days=dry_period_days
            )
        )
        .alias(f"dry_spell_fraction_{target_gauge_col}"),
        pl.col(neighbouring_gauge_col)
        .map_batches(
            lambda row: data_utils.calculate_dry_spell_fraction(
                row, target_gauge_col=neighbouring_gauge_col, dry_period_days=dry_period_days
            )
        )
        .alias(f"dry_spell_fraction_{neighbouring_gauge_col}"),
    )


def flag_dry_spell_fractions(
    one_neighbour_data: pl.DataFrame,
    target_gauge_col: str,
    neighbouring_gauge_col: str,
    proportion_of_dry_day_for_flags: dict,
) -> pl.DataFrame:
    """
    Flag dry spell fractions.

    Parameters
    ----------
    one_neighbour_data :
        Rainfall data of one neighbouring gauge with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col :
        Neighbouring gauge column
    proportion_of_dry_day_for_flags :
        Proportion of dry days needed to be flagged 1, 2, or 3

    Returns
    -------
    data_w_dry_spell_fraction :
        Target data with dry spell fractions

    """
    return one_neighbour_data.with_columns(
        pl.when(
            (pl.col(f"dry_spell_fraction_{target_gauge_col}") == 1.0)
            & (pl.col(f"dry_spell_fraction_{neighbouring_gauge_col}") == 1.0)
        )
        .then(0)
        .when(
            (pl.col(f"dry_spell_fraction_{target_gauge_col}") == 1.0)
            & (pl.col(f"dry_spell_fraction_{neighbouring_gauge_col}") < 1.0)
            & (pl.col(f"dry_spell_fraction_{neighbouring_gauge_col}") >= proportion_of_dry_day_for_flags["1"]),
        )
        .then(1)
        .when(
            (pl.col(f"dry_spell_fraction_{target_gauge_col}") == 1.0)
            & (pl.col(f"dry_spell_fraction_{neighbouring_gauge_col}") < proportion_of_dry_day_for_flags["1"])
            & (pl.col(f"dry_spell_fraction_{neighbouring_gauge_col}") >= proportion_of_dry_day_for_flags["2"]),
        )
        .then(2)
        .when(
            (pl.col(f"dry_spell_fraction_{target_gauge_col}") == 1.0)
            & (pl.col(f"dry_spell_fraction_{neighbouring_gauge_col}") < proportion_of_dry_day_for_flags["2"])
        )
        .then(3)
        .otherwise(0)
        .alias(f"dry_flag_{neighbouring_gauge_col}")
    )


def flag_percentage_diff_of_neighbour(neighbour_data: pl.DataFrame, neighbouring_gauge_col: str) -> pl.DataFrame:
    """
    Flag percentage difference between target gauge and neighbouring gauge.

    Flags -3 to 3 based on percentage difference:
    -3, -100% (i.e. gauge dry but neighbours not)
    -2, <= 50%
    -1, <= 25%
    1, >= 25%
    2, >= 50%
    3, >= 100%

    Parameters
    ----------
    neighbour_data :
        Rainfall data of all neighbouring gauges with time col
    neighbouring_gauge_col:
        Neighbouring gauge column

    Returns
    -------
    neighbour_data_w_flags :
        Data with perc_diff flags

    """
    return neighbour_data.with_columns(
        pl.when((pl.col("perc_diff") <= -100.0))
        .then(-3)
        .when((pl.col("perc_diff") <= -50.0) & (pl.col("perc_diff") > -100.0))
        .then(-2)
        .when((pl.col("perc_diff") <= -25.0) & (pl.col("perc_diff") > -50.0))
        .then(-1)
        .when((pl.col("perc_diff") <= 25.0) & (pl.col("perc_diff") > -25.0))
        .then(0)
        .when((pl.col("perc_diff") >= 25.0) & (pl.col("perc_diff") < 50.0))
        .then(1)
        .when((pl.col("perc_diff") >= 50.0) & (pl.col("perc_diff") < 100.0))
        .then(2)
        .when((pl.col("perc_diff") >= 100.0))
        .then(3)
        .otherwise(0)
        .alias(f"perc_diff_flag_{neighbouring_gauge_col}")
    )


def get_majority_voting_flag(
    neighbour_data: pl.DataFrame,
    neighbouring_gauge_cols: list[str],
    min_n_neighbours: int,
    n_zeros_allowed: int,
    flag_col_prefix: str,
    new_flag_col_name: str,
    aggregation: str,
) -> pl.DataFrame:
    """
    Get the highest flag that is in all neighbours.

    For this function, we introduce the 'n_zeros_allowed' parameter to allow for some leeway for problematic neighbours
    This stops a problematic neighbour that is similar to problematic target from stopping flagging.


    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col
    neighbouring_gauge_cols:
        List of columns with neighbouring gauges
    min_n_neighbours :
        Minimum number of neighbours online that will be considered
    n_zeros_allowed :
        Number of zero flags allowed (default: 0)
    flag_col_prefix :
        Prefix for flag column e.g. "wet_flag_"
    new_flag_col_name :
        New flag column name
    aggregation :
        "min" or "max"

    Returns
    -------
    neighbour_data_w_majority_wet_flag :
        Data with majority wet flag

    """
    # Added because if flags are negative then we want to use 'max_horizontal' else use 'min_horizontal'
    aggregate_func = pl.min_horizontal if aggregation == "min" else pl.max_horizontal
    return neighbour_data.with_columns(
        pl.when(pl.col("n_neighbours_online") < min_n_neighbours)
        .then(np.nan)
        .otherwise(
            # Check if there is less than or equal to the number of allowed zeros. Zeros mean no flag, thus no error.
            pl.when(
                pl.sum_horizontal(
                    [
                        (pl.col(f"{flag_col_prefix}{neighbour_col}") == 0).cast(pl.Int8)
                        for neighbour_col in neighbouring_gauge_cols
                    ]
                )
                <= n_zeros_allowed
            )
            .then(
                # ignore zeros in calculation of min
                aggregate_func(
                    [
                        pl.when(pl.col(f"{flag_col_prefix}{neighbour_col}") == 0)
                        .then(None)
                        .otherwise(pl.col(f"{flag_col_prefix}{neighbour_col}"))
                        for neighbour_col in neighbouring_gauge_cols
                    ]
                )
            )
            .otherwise(
                aggregate_func(
                    [pl.col(f"{flag_col_prefix}{neighbour_col}") for neighbour_col in neighbouring_gauge_cols]
                )
            )
        )
        .alias(new_flag_col_name)
    )


def make_num_neighbours_online_col(neighbour_data: pl.DataFrame, neighbouring_gauge_cols: list[str]) -> pl.DataFrame:
    """
    Get number of neighbours online column.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col
    neighbouring_gauge_cols :
        Columns to check if not null

    Returns
    -------
    neighbour_data_online_neighbours :
        Data with column for number of online neighbours

    """
    return neighbour_data.with_columns(
        (
            len(neighbouring_gauge_cols)
            - pl.sum_horizontal([pl.col(c).is_null().cast(pl.Int32) for c in neighbouring_gauge_cols])
        ).alias("n_neighbours_online")
    )


def flag_wet_day_errors_based_on_neighbours(
    neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str, wet_threshold: float
) -> pl.DataFrame:
    """
    Flag wet days with errors based on the percentile difference with neighbouring gauge.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of all neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col:
        Neighbouring gauge column
    wet_threshold :
        Threshold for rainfall intensity in given time period

    Returns
    -------
    neighbour_data_wet_flags :
        Data with wet flags

    """
    # 1. Remove nans from target and neighbour
    neighbour_data_clean = neighbour_data.drop_nans(subset=[target_gauge_col, neighbouring_gauge_col])

    # 2. Get normalised difference between target and neighbour
    neighbour_data_diff = normalised_diff_between_target_neighbours(
        neighbour_data_clean, target_gauge_col=target_gauge_col, neighbouring_gauge_col=neighbouring_gauge_col
    )
    # 3. filter wet values
    neighbour_data_filtered_diff = filter_data_based_on_unusual_wetness(
        neighbour_data_diff,
        target_gauge_col=target_gauge_col,
        neighbouring_gauge_col=neighbouring_gauge_col,
        wet_threshold=wet_threshold,
    )

    # 4. Fit exponential function of normalised diff and get q95, q99 and q999
    expon_percentiles = stats.fit_expon_and_get_percentile(
        neighbour_data_filtered_diff[f"diff_{neighbouring_gauge_col}"], percentiles=[0.95, 0.99, 0.999]
    )
    # 5. Assign flags
    all_neighbour_data_wet_flags = add_wet_flags_to_data(
        neighbour_data_diff, target_gauge_col, neighbouring_gauge_col, expon_percentiles, wet_threshold
    )
    return all_neighbour_data_wet_flags


def add_wet_flags_to_data(
    neighbour_data_diff: pl.DataFrame,
    target_gauge_col: str,
    neighbouring_gauge_col: str,
    expon_percentiles: dict,
    wet_threshold: float,
) -> pl.DataFrame:
    """
    Add flags to data based on when target gauge is wetter than neighbour above certain exponential thresholds.

    Parameters
    ----------
    neighbour_data_diff :
        Data with normalised diff to neighbour

    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col :
        Neighbouring gauge column
    expon_percentiles :
        Thresholds at percentile of fitted distribution (needs 0.95, 0.99 & 0.999)
    wet_threshold :
        Threshold for rainfall intensity in given time period

    Returns
    -------
    neighbour_data_wet_flags :
        Data with wet flags applied

    """
    return neighbour_data_diff.with_columns(
        pl.when(
            (pl.col(target_gauge_col) >= wet_threshold)
            & (pl.col(f"diff_{neighbouring_gauge_col}") <= expon_percentiles[0.95])
        )
        .then(0)
        .when(
            (pl.col(target_gauge_col) >= wet_threshold)
            & (pl.col(f"diff_{neighbouring_gauge_col}") > expon_percentiles[0.95])
            & (pl.col(f"diff_{neighbouring_gauge_col}") <= expon_percentiles[0.99]),
        )
        .then(1)
        .when(
            (pl.col(target_gauge_col) >= wet_threshold)
            & (pl.col(f"diff_{neighbouring_gauge_col}") > expon_percentiles[0.99])
            & (pl.col(f"diff_{neighbouring_gauge_col}") <= expon_percentiles[0.999]),
        )
        .then(2)
        .when(
            (pl.col(target_gauge_col) >= wet_threshold)
            & (pl.col(f"diff_{neighbouring_gauge_col}") > expon_percentiles[0.999])
        )
        .then(3)
        .otherwise(0)
        .alias(f"wet_flag_{neighbouring_gauge_col}")
    )


def filter_data_based_on_unusual_wetness(
    neighbour_data_diff: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str, wet_threshold: float
) -> pl.DataFrame:
    """
    Filter data based on wet threshold.

    Parameters
    ----------
    neighbour_data_diff :
        Data with normalised diff to neighbour
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col :
        Neighbouring gauge column
    wet_threshold :
        Threshold for rainfall intensity in given time period

    Returns
    -------
    filtered_diff :
        Data filtered to wet threshold and where diff is positive (thus more wet)

    """
    return neighbour_data_diff.filter(
        (pl.col(target_gauge_col) >= wet_threshold)
        & (pl.col(target_gauge_col).is_finite())
        & (pl.col(neighbouring_gauge_col).is_finite())
        & (pl.col(f"diff_{neighbouring_gauge_col}") > 0.0)
    )


def normalised_diff_between_target_neighbours(
    neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str
) -> pl.DataFrame:
    """
    Normalised difference between target rain col and neighbouring rain col.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of all neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col :
        Neighbouring gauge column

    Returns
    -------
    neighbour_data_w_diff :
        Data with normalised diff to each neighbour

    """
    return neighbour_data.with_columns(
        (
            data_utils.normalise_data(pl.col(target_gauge_col))
            - data_utils.normalise_data(pl.col(neighbouring_gauge_col))
        ).alias(f"diff_{neighbouring_gauge_col}")
    )


def check_neighbouring_gauge_columns(
    neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_cols: list
) -> None:
    """
    Run checks of neighbouring gauge columns to check if there are any columns and if the target gauge is there.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of all neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_cols:
        List of columns with neighbouring gauges

    Raises
    ------
    ValueError :
        If there are no neighbouring gauges in the 'neighbouring_gauge_cols' list
    AssertionError :
        If 'target_gauge_col' not in neighbour_data

    """
    if len(neighbouring_gauge_cols) == 0:
        raise ValueError("No neighbouring gauge columns found, please make sure that there is at least 1.")
    assert target_gauge_col in neighbour_data.columns, (
        f"Target column: '{target_gauge_col}' needs to column be in data."
    )
