# -*- coding: utf-8 -*-
"""
Quality control checks examining suspicious rain gauges.

Classes and functions ordered alphabetically.
"""

import polars as pl


def get_years_where_nth_percentile_is_zero(data: pl.DataFrame, rain_col: str, quantile: float) -> list:
    """
    Return years where the n-th percentiles is zero.

    This QC1 from the IntenseQC framework

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
