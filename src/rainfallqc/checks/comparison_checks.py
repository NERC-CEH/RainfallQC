# -*- coding: utf-8 -*-
"""
Quality control checks relying on comparison with a benchmark dataset.

Comparison checks are defined as QC checks that: "detect abnormalities in rainfall record based on benchmarks."

Classes and functions ordered by appearance in IntenseQC framework.
"""

import numpy as np
import polars as pl
import xarray as xr

from rainfallqc.utils import data_readers, data_utils, neighbourhood_utils, stats


def check_annual_exceedance_etccdi_r99p(
    data: pl.DataFrame, target_gauge_col: str, gauge_lat: int | float, gauge_lon: int | float
) -> list:
    """
    Check annual exceedance of maximum R99p from ETCCDI dataset.

    This is QC8 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
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
    etccdi_r99p = data_readers.load_etccdi_data(etccdi_var="R99p")

    # 2. Get nearest local R99p value to the gauge coordinates
    nearby_etccdi_r99p = neighbourhood_utils.get_nearest_etccdi_val_to_gauge(etccdi_r99p, gauge_lat, gauge_lon)

    # 3. Get sum of rainfall above the 99th percentile per year
    sum_rainfall_above_99percentile_per_year = get_sum_rainfall_above_percentile_per_year(
        data, target_gauge_col, percentile=0.99
    )

    # 4. Get flags of exceedance for R99p variable where the 0.99 percentile sum is more than ETCCDI max
    exceedance_flags = flag_exceedance_of_max_etccdi_variable(
        sum_rainfall_above_99percentile_per_year, target_gauge_col, nearby_etccdi_r99p, etccdi_var="R99p"
    )

    return exceedance_flags


def check_annual_exceedance_etccdi_prcptot(
    data: pl.DataFrame, target_gauge_col: str, gauge_lat: int | float, gauge_lon: int | float
) -> list:
    """
    Check annual exceedance of maximum PRCPTOT from ETCCDI dataset.

    This is QC9 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
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
    etccdi_prcptot = data_readers.load_etccdi_data(etccdi_var="PRCPTOT")

    # 2. Get nearest local PRCPTOT value to the gauge coordinates
    nearby_etccdi_prcptot = neighbourhood_utils.get_nearest_etccdi_val_to_gauge(etccdi_prcptot, gauge_lat, gauge_lon)

    # 3. Get sum of rainfall above the 99th percentile per year
    sum_rainfall_above_99percentile_per_year = get_sum_rainfall_above_percentile_per_year(
        data, target_gauge_col, percentile=0.99
    )

    # 4. Get flags of exceedance for PRCPTOT variable where the 0.99 percentile sum is more than ETCCDI max
    exceedance_flags = flag_exceedance_of_max_etccdi_variable(
        sum_rainfall_above_99percentile_per_year, target_gauge_col, nearby_etccdi_prcptot, etccdi_var="PRCPTOT"
    )

    return exceedance_flags


def check_exceedance_of_rainfall_world_record(data: pl.DataFrame, target_gauge_col: str, time_res: str) -> pl.DataFrame:
    """
    Check exceedance of rainfall world record.

    See Also `utils/stats.py` from world record sources.

    This is QC10 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data
    time_res :
        Time resolution

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of World Record (see `flag_exceedance_of_ref_val_as_col` function)

    """
    # 1. Get rainfall world records
    rainfall_world_records = stats.get_rainfall_world_records()

    # 2. Flag exceedance of world record value
    data_w_flags = flag_exceedance_of_ref_val_as_col(
        data, target_gauge_col, ref_val=rainfall_world_records[time_res], new_col_name="world_record_check"
    )
    return data_w_flags.select(["time", "world_record_check"])


def check_hourly_exceedance_etccdi_rx1day(
    data: pl.DataFrame, target_gauge_col: str, gauge_lat: int | float, gauge_lon: int | float
) -> pl.DataFrame:
    """
    Check exceedance of hourly day rainfall 1-day record.

    This is QC11 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of Rx1day Record (see `flag_exceedance_of_ref_val_as_col` function)

    """
    # 0. Check data can be resampled to hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["15m", "1h"])

    # 1. Resample into hourly
    data_hourly = data
    time_step = data_utils.get_data_timestep_as_str(data)
    if time_step == "15m":
        data_hourly = data_hourly.group_by_dynamic("time", every="1h").agg(pl.col(target_gauge_col).sum())

    # 2. Load Rx1day data
    etccdi_rx1day = data_readers.load_etccdi_data(etccdi_var="Rx1day")

    # 3. Get nearest local Rx1day value to the gauge coordinates
    nearby_etccdi_rx1day = neighbourhood_utils.get_nearest_etccdi_val_to_gauge(etccdi_rx1day, gauge_lat, gauge_lon)

    # 4. Get local maximum ETCCDI value
    max_nearby_etccdi_rx1day = np.max(nearby_etccdi_rx1day["Rx1day"])

    # 5. Flag exceedance of max ETCCDI value
    data_w_flags = flag_exceedance_of_ref_val_as_col(
        data_hourly, target_gauge_col, ref_val=max_nearby_etccdi_rx1day, new_col_name="rx1day_check"
    )
    # 6. Return data (forward fill if 15 min resolution)
    if time_step == "15m":
        # 6.1 Join flags back to original hourly data
        data_w_flags = data.join(data_w_flags[["time", "rx1day_check"]], on="time", how="left")
        # 6.2 Forward flood-fill data to convert the flags back to 15 mins
        data_w_flags = data_w_flags.with_columns(
            pl.col("rx1day_check").forward_fill(limit=3)  # 15 min groups
        )

    return data_w_flags.select(["time", "rx1day_check"])


def get_sum_rainfall_above_percentile_per_year(
    data: pl.DataFrame,
    target_gauge_col: str,
    percentile: float,
) -> pl.DataFrame:
    """
    Check annual exceedance of maximum PRCPTOT from ETCCDI dataset.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data
    percentile :
        nth percentile to check for values above

    Returns
    -------
    exceedance_flags :
        List of flags (see `exceedance_flagger` function)

    """
    # 1. Add a daily year column to the data
    data = add_daily_year_col(data)

    # 2. Calculate percentiles
    data_percentiles = data.group_by("year").agg(
        pl.col(target_gauge_col).fill_nan(0.0).quantile(percentile).alias("percentile")
    )

    # 3. Join percentiles back to the main DataFrame
    data_yearly_percentiles = data.join(data_percentiles, on="year").fill_nan(0.0)

    # 4. Filter values above the nth percentile
    data_above_annual_percentile = data_yearly_percentiles.filter(pl.col(target_gauge_col) > pl.col("percentile"))

    # 5. Get number of values per year above nth percentile
    sum_rainfall_above_percentile = data_above_annual_percentile.group_by_dynamic("time", every="1y").agg(
        pl.col(target_gauge_col).sum()
    )

    return sum_rainfall_above_percentile


def flag_exceedance_of_max_etccdi_variable(
    annual_sum_rainfall: pl.DataFrame, target_gauge_col: str, nearby_etccdi_data: xr.Dataset, etccdi_var: str
) -> list:
    """
    Flag exceedance of maximum ETCCDI variable, comparing the maximum sums of each year.

    Parameters
    ----------
    annual_sum_rainfall :
        Rainfall data as by year sums
    target_gauge_col :
        Column with rainfall data
    nearby_etccdi_data :
        ETCCDI data with given variable to check
    etccdi_var :
        variable to load from ETCCDI

    Returns
    -------
    exceedance_flags :
        Flags of exceedances of max ETCCDI value

    """
    # 1. Get local maximum ETCCDI value
    etccdi_var_max = np.max(nearby_etccdi_data[etccdi_var])

    # 2. Get flags.
    exceedance_flags = [
        flag_exceedance_of_ref_val(val=yr, ref_val=etccdi_var_max) for yr in annual_sum_rainfall[target_gauge_col]
    ]
    return exceedance_flags


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


def flag_exceedance_of_ref_val(val: int | float, ref_val: int | float) -> int:
    """
    Exceedance flagger from intenseqc.

    Parameters
    ----------
    val :
        Value to check
    ref_val :
        Reference value to compare against

    Returns
    -------
    Flag :
        Exceedance flag

    """
    if val is None or np.isnan(val):
        return np.nan
    elif val >= ref_val * 1.5:
        return 4
    elif val >= ref_val * 1.33:
        return 3
    elif val >= ref_val * 1.2:
        return 2
    elif val >= ref_val:
        return 1
    else:
        return 0


def flag_exceedance_of_ref_val_as_col(
    data: pl.DataFrame, target_gauge_col: str, ref_val: int | float, new_col_name: str
) -> pl.DataFrame:
    """
    Flag exceedance of maximum reference value and return as column.

    Used in QC11 of the IntenseQC framework. TODO: could this be used in QC8+9?

    Parameters
    ----------
    data :
        Rainfall data.
    target_gauge_col :
        Column with rainfall data
    ref_val :
        Reference value.
    new_col_name :
        New column name.

    Returns
    -------
    data :
        Data with exceedance flags between 0-4.

    """
    return data.with_columns(
        pl.when(pl.col(target_gauge_col).is_null() | pl.col(target_gauge_col).is_nan())
        .then(np.nan)
        .when(pl.col(target_gauge_col) >= ref_val * 1.5)
        .then(4)
        .when(pl.col(target_gauge_col) >= ref_val * 1.33)
        .then(3)
        .when(pl.col(target_gauge_col) >= ref_val * 1.2)
        .then(2)
        .when(pl.col(target_gauge_col) >= ref_val)
        .then(1)
        .otherwise(0)
        .alias(new_col_name)
    )
