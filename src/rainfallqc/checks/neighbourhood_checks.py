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
    Run neighbour check (wet) for hourly or daily data.

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

    for neighbouring_gauge_col in neighbouring_gauge_cols:
        diff_neighbour_col = f"diff_{neighbouring_gauge_col}"

        # 2. Remove nans from target and neighbour
        all_neighbour_data_clean = all_neighbour_data.drop_nans(subset=[target_gauge_col, neighbouring_gauge_col])

        # 3. Get normalised difference between target and neighbour
        all_neighbour_data_diff = normalised_diff_between_target_neighbours(
            all_neighbour_data_clean, target_gauge_col, neighbouring_gauge_col
        )

        # 4. filter wet values values
        all_neighbour_data_filtered_diff = all_neighbour_data_diff.filter(
            (pl.col(target_gauge_col) >= wet_threshold)
            & (pl.col(target_gauge_col).is_finite())
            & (pl.col(neighbouring_gauge_col).is_finite())
            & (pl.col(diff_neighbour_col) > 0.0)
        )

        # 5. Fit exponential function of normalised diff and get q95, q99 and q999
        expon_perc = stats.fit_expon_and_get_percentile(
            all_neighbour_data_filtered_diff[diff_neighbour_col], percentiles=[0.95, 0.99, 0.999]
        )

        # 6. Assign flags
        all_neighbour_data_wet_flags = all_neighbour_data_diff.with_columns(
            pl.when((pl.col(target_gauge_col) >= wet_threshold) & (pl.col(diff_neighbour_col) <= expon_perc[0.95]))
            .then(0)
            .when(
                (pl.col(target_gauge_col) >= wet_threshold)
                & (pl.col(diff_neighbour_col) > expon_perc[0.95])
                & (pl.col(diff_neighbour_col) <= expon_perc[0.99]),
            )
            .then(1)
            .when(
                (pl.col(target_gauge_col) >= wet_threshold)
                & (pl.col(diff_neighbour_col) > expon_perc[0.99])
                & (pl.col(diff_neighbour_col) <= expon_perc[0.999]),
            )
            .then(2)
            .when((pl.col(target_gauge_col) >= wet_threshold) & (pl.col(diff_neighbour_col) > expon_perc[0.999]))
            .then(3)
            .otherwise(0)
            .alias(f"wet_flags_{neighbouring_gauge_col}")
        )

        # 6. Join to all data
        all_neighbour_data = all_neighbour_data.join(
            all_neighbour_data_wet_flags[["time", f"wet_flags_{neighbouring_gauge_col}"]],
            on="time",
            how="left",
        )
        print(all_neighbour_data[f"wet_flags_{neighbouring_gauge_col}"].value_counts())

    # 7. Compute online neighbours
    # 8. majority voting

    return all_neighbour_data


def normalised_diff_between_target_neighbours(
    all_neighbour_data: pl.DataFrame, target_gauge_col: str, neighbouring_gauge_col: str
) -> pl.DataFrame:
    """
    Normalised difference between target rain col and neighbouring rain col.

    Parameters
    ----------
    all_neighbour_data :
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
    return all_neighbour_data.with_columns(
        (
            data_utils.normalise_data(pl.col(target_gauge_col))
            - data_utils.normalise_data(pl.col(neighbouring_gauge_col))
        ).alias(f"diff_{neighbouring_gauge_col}")
    )
