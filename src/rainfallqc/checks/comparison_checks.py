# -*- coding: utf-8 -*-
"""
Quality control checks relying on comparison with a benchmark dataset.

Classes and functions ordered alphabetically.
"""

import numpy as np
import polars as pl

from rainfallqc.utils import data_readers


def check_annual_exceedance_ETCCDI_R99p(
    data: pl.DataFrame, rain_col: str, gauge_lat: int | float, gauge_lon: int | float
) -> list:
    """
    Check annual exceedance of maximum R99p from ETCCDI dataset.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge

    Returns
    -------
    flag_list :
        List of flags

    """
    # 1. Load R99p data
    etcddi_r99p = data_readers.load_ETCCDI_data(etccdi_var="R99p")

    # 2. Get local R99p data
    one_gauge_r99p = etcddi_r99p.sel(
        lon=gauge_lon,
        lat=gauge_lat,
        method="nearest",
    )

    # 3. Get local maximum R99p value
    max_r99p = np.max(one_gauge_r99p["R99p"])

    # 4. Upsample data to every day
    data_daily_upsample = data.upsample("time", every="1d")
    data_daily_upsample = data_daily_upsample.with_columns(pl.col("time").dt.year().alias("year"))

    # 5. Calculate percentiles
    data_percentiles = data_daily_upsample.group_by("year").agg(
        pl.col(rain_col).fill_nan(0.0).quantile(0.99).alias("percentile_99")
    )

    # 6. Join percentiles back to the main DataFrame
    data_yearly_percentiles = data_daily_upsample.join(data_percentiles, on="year").fill_nan(0.0)

    # 7. Filter values above the 99th percentile
    data_above_annual_r99p = data_yearly_percentiles.filter(pl.col(rain_col) > pl.col("percentile_99"))

    # 8. Get number of values per year above 99th percentile
    data_above_annual_r99_year_sum = data_above_annual_r99p.group_by_dynamic("time", every="1y").agg(
        pl.col(rain_col).sum()
    )

    # 9. Get flags. TODO: to refactor
    flag_list = [day_check(val=yr, max_ref_val=max_r99p) for yr in data_above_annual_r99_year_sum[rain_col]]

    return flag_list


def day_check(val: int | float, max_ref_val: int | float) -> int:
    """
    From intenseqc.

    TODO: TO REFACTOR as messy. Do we need this many flags?
    """
    if val >= max_ref_val * 1.5:
        return 4
    elif val >= max_ref_val * 1.33:
        return 3
    elif val >= max_ref_val * 1.2:
        return 2
    elif val >= max_ref_val:
        return 1
    else:
        return 0
