# -*- coding: utf-8 -*-
"""
Quality control checks based on suspicious time-series artefacts.

Time-series checks are defined as QC checks that: "detect abnormalities in patterns of the data record."

Classes and functions ordered by appearance in IntenseQC framework.
"""

import numpy as np
import polars as pl
import xarray as xr

from rainfallqc.utils import data_readers, data_utils, neighbourhood_utils, spatial_utils, stats

DAILY_DIVIDING_FACTOR = {"hourly": 24, "daily": 1}


def dry_period_cdd_check(
    data: pl.DataFrame, rain_col: str, time_res: str, gauge_lat: int | float, gauge_lon: int | float
) -> pl.DataFrame:
    """
    Identify suspiciously long dry periods in time-series using the ETCCDI Consecutive Dry Days (CDD) index.

    This is QC12 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    time_res :
        Temporal resolution of the time series either 'daily' or 'hourly'
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge

    Returns
    -------
    data_w_dry_spell_flags :
        Data with dry spell flags

    """
    # 1. Load CDD data
    etccdi_cdd = data_readers.load_etccdi_data(etccdi_var="CDD")

    # 2. Make dry spell days column from ETCCDI data
    etccdi_cdd_days = compute_dry_spell_days(etccdi_cdd)

    # 3. Get nearest local CDD value to the gauge coordinates
    nearby_etccdi_cdd_days = neighbourhood_utils.get_nearest_etccdi_val_to_gauge(etccdi_cdd_days, gauge_lat, gauge_lon)

    # 4. Get local maximum CDD_days value
    max_etccdi_cdd_days = np.max(nearby_etccdi_cdd_days["CDD_days"])

    # 5. Get dry spell durations (with start and end dates)
    gauge_dry_spell_lengths = get_dry_spell_duration(data, rain_col)

    # 6. Flag dry spells
    gauge_dry_spell_lengths_flags = flag_dry_spell_duration(gauge_dry_spell_lengths, max_etccdi_cdd_days, time_res)

    # 7. Join data back to main data and flag
    data_w_dry_spell_flags = join_dry_spell_data_back_to_original(data, gauge_dry_spell_lengths_flags)

    return data_w_dry_spell_flags


def daily_accumulations(
    data: pl.DataFrame, rain_col: str, time_res: str, gauge_lat: int | float, gauge_lon: int | float
) -> pl.DataFrame:
    """
    Identify suspicious periods when rainfall is proceeded by 23 hours with no rain.

    Uses a simple precipitation intensity index (SDII) from ETCCDI.

    This is QC13 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    time_res :
        Temporal resolution of the time series either 'daily' or 'hourly'
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge

    Returns
    -------
    data_w_dry_spell_flags :
        Data with dry spell flags

    """
    if time_res != "daily" and time_res != "hourly":
        raise ValueError("time_res must be 'daily' or 'hourly'")
    # 1. Load SDII data
    etccdi_sdii = data_readers.load_etccdi_data(etccdi_var="SDII")

    # 2. Compute spatial mean
    etccdi_sdii = spatial_utils.compute_spatial_mean_xr(etccdi_sdii, var_name="SDII")

    # 3. Get nearest local CDD value to the gauge coordinates
    nearby_etccdi_sdii = neighbourhood_utils.get_nearest_etccdi_val_to_gauge(etccdi_sdii, gauge_lat, gauge_lon)

    # 4. Get local maximum CDD_days value
    max_etccdi_sdii = np.max(nearby_etccdi_sdii["SDII_mean"])

    # 5. Get world records
    rainfall_world_records = stats.get_rainfall_world_records()

    # 6. Filter out world records
    if time_res == "hourly":
        # 6.1 Filter out hourly world records
        data_not_wr = data.with_columns(
            pl.when(pl.col(rain_col) > rainfall_world_records["hourly"])
            .then(np.nan)
            .otherwise(pl.col(rain_col))
            .alias(rain_col)
        )
        # 6.2 Group into daily resolution
        data_not_wr = data_not_wr.group_by_dynamic("time", every="1d").agg(pl.col(rain_col).sum())
    # 6.3 Filter out daily world records
    data_not_wr = data_not_wr.with_columns(
        pl.when(pl.col(rain_col) > rainfall_world_records["daily"])
        .then(np.nan)
        .otherwise(pl.col(rain_col))
        .alias(rain_col)
    )

    # 7. Calculate simple precipitation intensity index

    return data_not_wr, max_etccdi_sdii


def join_dry_spell_data_back_to_original(data: pl.DataFrame, dry_spell_lengths_flags: pl.DataFrame) -> pl.DataFrame:
    """
    Flag dry spell data using dry spell lengths.

    Parameters
    ----------
    data :
        Rainfall data
    dry_spell_lengths_flags :
        Data with dry spell flags

    Returns
    -------
    dry_spell_flag_data :
        Data with dry spell flags

    """
    # 1. Make template of new data
    dry_spell_flag_data = pl.DataFrame({"time": data["time"], "dry_spell_flag": np.zeros(data["time"].shape)})

    # 2. Get all problematic flags
    dry_spell_errors = dry_spell_lengths_flags.filter(pl.col("dry_spell_flag") > 0)

    # 3. Loop through problematic flags and label the original data based on duration of dry spell
    for errored_data_row in dry_spell_errors.iter_rows():
        # overwrite flag
        dry_spell_flag_data = dry_spell_flag_data.with_columns(
            pl.when((pl.col("time") >= errored_data_row[1]) & (pl.col("time") <= errored_data_row[2]))
            .then(errored_data_row[4])
            .otherwise(pl.col("dry_spell_flag"))
            .alias("dry_spell_flag")
        )
    return dry_spell_flag_data


def flag_dry_spell_duration(
    dry_spell_lengths: pl.DataFrame, ref_dry_spell_length: int | float, time_res: str
) -> pl.DataFrame:
    """
    Flag the dry spell duration using reference local dry spell length.

    Parameters
    ----------
    dry_spell_lengths :
        Data with dry spell lengths
    ref_dry_spell_length :
        Reference dry spell length
    time_res :
        Temporal resolution of the time series either 'daily' or 'hourly'

    Returns
    -------
    dry_spell_lengths_flags :
        Data with dry spell flags

    """
    # May need to rethink how this is done uniformly (as could use day check)
    dry_spell_lengths_flags = dry_spell_lengths.with_columns(
        pl.when(pl.col("dry_spell_length") / DAILY_DIVIDING_FACTOR[time_res] >= ref_dry_spell_length * 1.5)
        .then(4)
        .when(pl.col("dry_spell_length") / DAILY_DIVIDING_FACTOR[time_res] >= ref_dry_spell_length * 1.33)
        .then(3)
        .when(pl.col("dry_spell_length") / DAILY_DIVIDING_FACTOR[time_res] >= ref_dry_spell_length * 1.2)
        .then(2)
        .when(pl.col("dry_spell_length") / DAILY_DIVIDING_FACTOR[time_res] >= ref_dry_spell_length)
        .then(1)
        .otherwise(0)
        .alias("dry_spell_flag")
    )
    return dry_spell_lengths_flags


def get_dry_spell_duration(data: pl.DataFrame, rain_col: str) -> pl.DataFrame:
    """
    Get consecutive dry spell duration.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data

    Returns
    -------
    gauge_dry_spell_lengths :
        Data with dry spell start, end and duration

    """
    # 1. Get dry spells and their lengths
    gauge_dry_spells = data.with_columns(
        (pl.col(rain_col) == 0).cast(pl.Int8()).alias("is_dry"),
    )
    # 2. Get consecutive groups of dry spells
    gauge_dry_spell_groups = gauge_dry_spells.with_columns(
        ((pl.col("is_dry").diff().fill_null(0) == 1).cum_sum()).alias("dry_group_id")
    )
    # 3. Get
    gauge_dry_spell_lengths = (
        gauge_dry_spell_groups.filter(pl.col("is_dry") == 1)
        .group_by("dry_group_id")
        .agg(
            pl.first("time").alias("dry_spell_start"),
            pl.last("time").alias("dry_spell_end"),
            pl.col("is_dry").sum().alias("dry_spell_length"),
        )
        .sort("dry_group_id")
    )
    return gauge_dry_spell_lengths


def compute_dry_spell_days(dry_spell_data: xr.Dataset) -> xr.Dataset:
    """
    Compute dry spells in ddys from ETCCDI Consecutive Dry Days data.

    Parameters
    ----------
    dry_spell_data :
        ETCCDI CDD index data

    Returns
    -------
    dry_spell_days :
        ETCCDI CDD index data with `CDD_days` variable

    """
    # Convert CDD from seconds to days
    dry_spell_days = data_utils.convert_datarray_seconds_to_days(dry_spell_data["CDD"])

    # Mask out non-land data
    dry_spell_days[dry_spell_days < 0.0] = np.nan

    # Remove errors from data where more than 366 days are dry
    dry_spell_days[dry_spell_days > 366] = np.nan  # remove errors

    # Remove invalid data
    dry_spell_days = np.ma.masked_invalid(dry_spell_days)

    # Make CDD days variable
    dry_spell_data["CDD_days"] = (("lat", "lon"), np.ma.max(dry_spell_days, axis=0))

    return dry_spell_data
