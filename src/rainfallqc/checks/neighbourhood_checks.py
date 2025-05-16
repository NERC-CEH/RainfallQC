# -*- coding: utf-8 -*-
"""
Quality control checks using neighbouring gauges to identify suspicious data.

Neighbourhood checks are QC checks that: "detect abnormalities in a gauges given measurements in neighbouring gauges."

Classes and functions ordered by appearance in IntenseQC framework.
"""

import polars as pl

from rainfallqc.utils import data_readers, data_utils


def wet_neighbour_check(all_neighbour_data: pl.DataFrame, target_gauge_col: str, time_res: str) -> pl.DataFrame:
    """
    Run neighbour check (wet) for hourly or daily data.

    Parameters
    ----------
    all_neighbour_data :
        Rainfall data of all neighbouring gauges with time col
    target_gauge_col :
        Target gauge column
    time_res :
        Time resolution of data

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

    # TODO: get all all_neighbour_data.columns that are not target and not time
    # TODO: loop through other_rain_cols

    # 2. Get normalised difference between target and neighbour
    # all_neighbour_data_norm_diff = all_neighbour_data.with_columns(
    #     data_utils.normalise_data(pl.col(target_gauge_col))
    #     - data_utils.normalise_data(pl.col(f"{rain_col}_GPCC_{gpcc_id_name}"))
    # )

    # TODO: add wet_threshold to func description
    # 3. filter wet values values
    # all_neighbour_data_norm_diff_filtered = (
    #     all_neighbour_data_norm_diff.filter(
    #         (pl.col(target_gauge_col) >= wet_threshold)
    #         & (pl.col(target_gauge_col).is_finite())
    #         & (pl.col(other_rain_col).is_finite())
    #         & (pl.col(f"{target_gauge_col}_normalised_diff") > 0.0)
    #     )

    # TODO: move to stats
    # 4. Fit exponential function of normalised diff and get q95, q99 and q999
    # expon_params = scipy.stats.expon.fit(
    #     all_neighbour_data_norm_diff_filtered[f"{target_gauge_col}_normalised_diff"]
    # )
    # # 8. Calculate thresholds at key percentiles of fitted distribution
    # q95 = scipy.stats.expon.ppf(0.95, expon_params[0], expon_params[1])
    # q99 = scipy.stats.expon.ppf(0.99, expon_params[0], expon_params[1])
    # q999 = scipy.stats.expon.ppf(0.999, expon_params[0], expon_params[1])

    # 5. Assign flags
    # all_neighbour_data_wet_flags = (
    #     all_neighbour_data_norm_diff.with_columns(
    #         pl.when(
    #             (pl.col(target_gauge_col) >= 1.0)
    #             & (pl.col(f"{target_gauge_col}_normalised_diff") <= q95)
    #         )
    #         .then(0)
    #         .when(
    #             (pl.col(target_gauge_col) >= 1.0)
    #             & (pl.col(f"{target_gauge_col}_normalised_diff") > q95)
    #             & (pl.col(f"{target_gauge_col}_normalised_diff") <= q99),
    #         )
    #         .then(1)
    #         .when(
    #             (pl.col(target_gauge_col) >= 1.0)
    #             & (pl.col(f"{target_gauge_col}_normalised_diff") > q99)
    #             & (pl.col(f"{target_gauge_col}_normalised_diff") <= q999),
    #         )
    #         .then(2)
    #         .when(
    #             (pl.col(target_gauge_col) >= 1.0)
    #             & (pl.col(f"{target_gauge_col}_normalised_diff") > q95)
    #         )
    #         .then(3)
    #         .otherwise(0)
    #         .alias(f"wet_flags_{other_rain_col}")
    #     )
    # )

    # 6. Join to all data
    #     all_data = all_data.join(
    #         all_neighbour_data_wet_flags[["time", f"wet_flags_{other_rain_col}"]],
    #         on="time",
    #         how="left",
    #     )

    # 7. Compute online neighbours
    # 8. majority voting

    return all_neighbour_data[target_gauge_col]
