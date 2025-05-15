# -*- coding: utf-8 -*-
"""
Quality control checks using neighbouring gauges to identify suspicious data.

Neighbourhood checks are QC checks that: "detect abnormalities in a gauges given measurements in neighbouring gauges."

Classes and functions ordered by appearance in IntenseQC framework.
"""

import polars as pl

from rainfallqc.utils import data_utils


def wet_neighbour_check(
    all_neighbour_data: pl.DataFrame, rain_col: str, target_gauge_id: str, time_res: str
) -> pl.DataFrame:
    """
    Run neighbour check (wet) for hourly or daily data.

    Parameters
    ----------
    all_neighbour_data :
        Data of all neighbouring gauges
    rain_col :
        Column with rainfall data
    target_gauge_id :
        Target gauge id
    time_res :
        Time resolution of data

    Returns
    -------
    data_w_wet_flags :
        Target data with wet flags

    """
    data_utils.check_data_is_specific_time_res(all_neighbour_data, time_res)
    return all_neighbour_data[rain_col]
