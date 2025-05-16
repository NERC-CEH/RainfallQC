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

    # 2. Get normalised difference between target and neighbour
    # TODO: get all all_neighbour_data.columns that are not target and not time
    # all_neighbour_data_norm_diff = all_neighbour_data.with_columns(
    #     data_utils.normalise_data(pl.col(target_gauge_col))
    #     - data_utils.normalise_data(pl.col(f"{rain_col}_GPCC_{gpcc_id_name}"))
    # )
    #
    # all_neighbour_data_norm_diff

    return all_neighbour_data[target_gauge_col]
