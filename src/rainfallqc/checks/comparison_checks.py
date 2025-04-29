# -*- coding: utf-8 -*-
"""
Quality control checks relying on comparison with a benchmark dataset.

Classes and functions ordered alphabetically.
"""

import numpy as np
import polars as pl
import xarray as xr

from rainfallqc.utils import data_readers


def check_annual_exceedance_etccdi_r99p(
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
    # 1. Load PRCPTOT data
    etcddi_r99p = data_readers.load_ETCCDI_data(etccdi_var="R99p")

    # 2. Get nearest local PRCPTOT value to the gauge coordinates
    nearby_etcddi_r99p = get_nearest_etccdi_val_to_gauge(etcddi_r99p, gauge_lat, gauge_lon)

    # 3. Check exceedance of PRCPTOT variable
    exceedance_flags = check_annual_exceedance_of_etccdi_variable(
        data, rain_col, nearby_etccdi_data=nearby_etcddi_r99p, etccdi_var="R99p"
    )

    return exceedance_flags


def check_annual_exceedance_etccdi_prcptot(
    data: pl.DataFrame, rain_col: str, gauge_lat: int | float, gauge_lon: int | float
) -> list:
    """
    Check annual exceedance of maximum PRCPTOT from ETCCDI dataset.

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
    exceedance_flags :
        List of flags (see `exceedance_flagger` function)

    """
    # 1. Load PRCPTOT data
    etcddi_prcptot = data_readers.load_ETCCDI_data(etccdi_var="PRCPTOT")

    # 2. Get nearest local PRCPTOT value to the gauge coordinates
    nearby_etcddi_prcptot = get_nearest_etccdi_val_to_gauge(etcddi_prcptot, gauge_lat, gauge_lon)

    # 3. Check exceedance of PRCPTOT variable
    exceedance_flags = check_annual_exceedance_of_etccdi_variable(
        data, rain_col, nearby_etccdi_data=nearby_etcddi_prcptot, etccdi_var="PRCPTOT"
    )

    return exceedance_flags


def check_annual_exceedance_of_etccdi_variable(
    data: pl.DataFrame,
    rain_col: str,
    nearby_etccdi_data: xr.Dataset,
    etccdi_var: str,
) -> list:
    """
    Check annual exceedance of maximum PRCPTOT from ETCCDI dataset.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    nearby_etccdi_data :
        ETCCDI data with given variable to check
    etccdi_var :
        variable to load from ETCCDI

    Returns
    -------
    exceedance_flags :
        List of flags (see `exceedance_flagger` function)

    """
    # 1. Get local maximum ETCCDI value
    max_ref_val = np.max(nearby_etccdi_data[etccdi_var])

    # 2. Add a daily year column to the data
    data = add_daily_year_col(data)

    # 3. Calculate percentiles
    data_percentiles = data.group_by("year").agg(pl.col(rain_col).fill_nan(0.0).quantile(0.99).alias("percentile_99"))

    # 4. Join percentiles back to the main DataFrame
    data_yearly_percentiles = data.join(data_percentiles, on="year").fill_nan(0.0)

    # 5. Filter values above the 99th percentile
    data_above_annual_99_percentile = data_yearly_percentiles.filter(pl.col(rain_col) > pl.col("percentile_99"))

    # 6. Get number of values per year above 99th percentile
    data_above_annual_percentile_year_sum = data_above_annual_99_percentile.group_by_dynamic("time", every="1y").agg(
        pl.col(rain_col).sum()
    )

    # 7. Get flags. TODO: to refactor
    flag_list = [
        exceedance_flagger(val=yr, max_ref_val=max_ref_val) for yr in data_above_annual_percentile_year_sum[rain_col]
    ]
    return flag_list


def get_nearest_etccdi_val_to_gauge(
    etccdi_data: xr.Dataset, gauge_lat: int | float, gauge_lon: int | float
) -> xr.Dataset:
    """
    Get the value at the nearest ETCCDI grid cell to the gauge coordinates.

    Parameters
    ----------
    etccdi_data
        ETCCDI data with given variable to check
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge

    Returns
    -------
    nearby_etccdi_data :
        ETCCDI data at the nearest grid cell

    """
    # 1. Get local data
    nearby_etccdi_data = etccdi_data.sel(
        lon=gauge_lon,
        lat=gauge_lat,
        method="nearest",
    )
    return nearby_etccdi_data


def add_daily_year_col(data: pl.DataFrame) -> pl.DataFrame:
    """
    Make a year column for the data. This method will first upsample data so that it is every day.

    Parameters
    ----------
    data :
        Rainfall data

    Returns
    -------
    data_w_year_col :
        Rainfall data with year column

    """
    data_daily_upsample = data.upsample("time", every="1d")
    return data_daily_upsample.with_columns(pl.col("time").dt.year().alias("year"))


def exceedance_flagger(val: int | float, max_ref_val: int | float) -> int:
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
