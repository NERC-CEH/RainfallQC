# -*- coding: utf-8 -*-
"""
Quality control checks using neighbouring gauges to identify suspicious data.

Neighbourhood checks are QC checks that: "detect abnormalities in a gauges given measurements in neighbouring gauges."

Classes and functions ordered by appearance in IntenseQC framework.
"""

from typing import List

import polars as pl

from rainfallqc.utils import data_readers, data_utils, stats


def wet_neighbour_check(
    all_neighbour_data: pl.DataFrame,
    target_gauge_col: str,
    neighbouring_gauge_cols: List[str],
    time_res: str,
    wet_threshold: int | float,
) -> pl.DataFrame:
    """
    Identify suspicious large values by comparison to neighbour for hourly or daily data.

    Flags (majority voting):
    3, if normalised difference between target gauge and neighbours is above the 99.9th percentile
    2, ...if above 99th percentile
    1, ...if above 95th percentile
    0, if not in extreme exceedance of neighbours

    Parameters
    ----------
    all_neighbour_data :
        Rainfall data of all neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_cols:
        List of columns with neighbouring gauges
    time_res :
        Time resolution of data
    wet_threshold :
        Threshold for rainfall intensity in given time period

    Returns
    -------
    data_w_wet_flags :
        Target data with wet flags

    """
    data_utils.check_data_is_specific_time_res(all_neighbour_data, time_res)

    # 1. Resample to daily
    if time_res == "hourly":
        rain_cols = all_neighbour_data.columns[1:]  # get rain columns
        all_neighbour_data = data_readers.convert_gdsr_hourly_to_daily(all_neighbour_data, rain_cols=rain_cols)

    # 2. Loop through each neighbour and get wet_flags
    for neighbouring_gauge_col in neighbouring_gauge_cols:
        all_neighbour_data_wet_flags = flag_wet_day_errors_based_on_neighbours(
            all_neighbour_data, target_gauge_col, neighbouring_gauge_col, wet_threshold
        )

        # 3. Join to all data
        all_neighbour_data = all_neighbour_data.join(
            all_neighbour_data_wet_flags[["time", f"wet_flags_{neighbouring_gauge_col}"]],
            on="time",
            how="left",
        )
        print(all_neighbour_data[f"wet_flags_{neighbouring_gauge_col}"].value_counts())

    # 4. Compute online neighbours

    # 5. majority voting

    return all_neighbour_data


def flag_wet_day_errors_based_on_neighbours(
    all_neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str, wet_threshold: float
) -> pl.DataFrame:
    """
    Flag wet days with errors based on the percentile difference with neighbouring gauge.

    Parameters
    ----------
    all_neighbour_data :
        Rainfall data of all neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_col:
        Neighbouring gauge column
    wet_threshold :
        Threshold for rainfall intensity in given time period

    Returns
    -------
    all_neighbour_data_wet_flags :
        Data with wet flags

    """
    # 1. Remove nans from target and neighbour
    all_neighbour_data_clean = all_neighbour_data.drop_nans(subset=[target_gauge_col, neighbouring_gauge_col])

    # 2. Get normalised difference between target and neighbour
    all_neighbour_data_diff = normalised_diff_between_target_neighbours(
        all_neighbour_data_clean, target_gauge_col=target_gauge_col, neighbouring_gauge_col=neighbouring_gauge_col
    )
    # 3. filter wet values
    all_neighbour_data_filtered_diff = filter_data_based_on_unusual_wetness(
        all_neighbour_data_diff,
        target_gauge_col=target_gauge_col,
        neighbouring_gauge_col=neighbouring_gauge_col,
        wet_threshold=wet_threshold,
    )

    # 4. Fit exponential function of normalised diff and get q95, q99 and q999
    expon_percentiles = stats.fit_expon_and_get_percentile(
        all_neighbour_data_filtered_diff[f"diff_{neighbouring_gauge_col}"], percentiles=[0.95, 0.99, 0.999]
    )
    # 5. Assign flags
    all_neighbour_data_wet_flags = add_wet_flags_to_data(
        all_neighbour_data_diff, target_gauge_col, neighbouring_gauge_col, expon_percentiles, wet_threshold
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
        .alias(f"wet_flags_{neighbouring_gauge_col}")
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
