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
    if time_res != "daily" and time_res != "hourly":
        raise ValueError("time_res must be 'daily' or 'hourly'")

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
    data: pl.DataFrame,
    rain_col: str,
    gauge_lat: int | float,
    gauge_lon: int | float,
    rain_intensity_threshold: int | float = 1.0,
    accumulation_multiplying_factor: int | float = 2.0,
    accumulation_threshold: float = None,
) -> pl.DataFrame:
    """
    Identify suspicious periods where an hour of rainfall is preceded by 23 hours with no rain.

    Uses a simple precipitation intensity index (SDII) from ETCCDI.

    This is QC13 from the IntenseQC framework.

    Please see 'Notes' below for any additional information about the implementation of this method.

    Parameters
    ----------
    data :
        Hourly rainfall data
    rain_col :
        Column with rainfall data
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge
    rain_intensity_threshold :
        Threshold for rainfall intensity in one day (default is 1 mm)
    accumulation_multiplying_factor :
        Factor to multiply SDII value for to identify an accumulation of rain recordings
    accumulation_threshold :
        Rain accumulation for detecting possible daily accumulations

    Returns
    -------
    data_w_daily_accumulation_flags :
        Data with daily accumulation flags

    Notes
    -----
    This method returns only 0 and 1 flags. This differs from the description of the daily accumulation check from
    IntenseQC. This decision was taken as the IntenseQC python package only returns 0 and 1 flags.

    """
    # 1. Get local mean ETCCDI SDII value (this is the default for SDII in this method)
    etccdi_sdii = get_local_etccdi_sdii_mean(gauge_lat, gauge_lon)

    # 2. Filter out world records
    daily_data_non_wr = get_daily_non_wr_data(data, rain_col)

    # 3. Calculate simple precipitation intensity index from daily data
    gauge_sdii = stats.calculate_simple_precip_intensity_index(daily_data_non_wr, rain_col, rain_intensity_threshold)

    # 4. Get rain gauge accumulation threshold
    if not accumulation_threshold:
        accumulation_threshold = get_accumulation_threshold(accumulation_multiplying_factor, etccdi_sdii, gauge_sdii)

    # 5. Flag monthly accumulations in hourly data based on SDII threshold
    da_flags = flag_daily_accumulations(data, rain_col, accumulation_threshold)

    return data.with_columns(daily_accumulation=pl.Series(da_flags))


def monthly_accumulations(
    data: pl.DataFrame,
    rain_col: str,
    gauge_lat: int | float,
    gauge_lon: int | float,
    rain_intensity_threshold: int | float = 1.0,
    accumulation_multiplying_factor: int | float = 2.0,
    accumulation_threshold: float = None,
) -> pl.DataFrame:
    """
    Identify suspicious periods when an hour of rainfall is preceded by 1 month with no rain.

    Flags two different types of accumulations:
    1) dry, when the isolated high value
    2) wet, when the isolated value is followed by a few more wet values

    Uses a simple precipitation intensity index (SDII) from ETCCDI.

    This is QC14 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Hourly rainfall data
    rain_col :
        Column with rainfall data
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge
    rain_intensity_threshold :
        Threshold for rainfall intensity in one day (default is 1 mm)
    accumulation_multiplying_factor :
        Factor to multiply SDII value for to identify an accumulation of rain recordings
    accumulation_threshold :
        Rain accumulation for detecting possible monthly accumulations

    Returns
    -------
    data_w_monthly_accumulation_flags :
        Data with monthly accumulation flags

    """
    # 1. Get local mean ETCCDI SDII value (this is the default for SDII in this method)
    etccdi_sdii = get_local_etccdi_sdii_mean(gauge_lat, gauge_lon)

    # 2. Filter out world records
    daily_data_non_wr = get_daily_non_wr_data(data, rain_col)

    # 3. Calculate simple precipitation intensity index from daily data
    gauge_sdii = stats.calculate_simple_precip_intensity_index(daily_data_non_wr, rain_col, rain_intensity_threshold)

    # 4. Get rain gauge accumulation threshold
    if not accumulation_threshold:
        accumulation_threshold = get_accumulation_threshold(accumulation_multiplying_factor, etccdi_sdii, gauge_sdii)

    # 5. Get dry spell durations (with start and end dates)
    gauge_dry_spell_lengths = get_dry_spell_duration(data, rain_col)

    # 6. Get first wet value after consecutive dry spell
    gauge_dry_spell_info = get_first_wet_after_dry_spell(gauge_dry_spell_lengths, rain_col)

    return gauge_dry_spell_info


def get_daily_non_wr_data(data: pl.DataFrame, rain_col: str) -> pl.DataFrame:
    """
    Get daily non-world record data.

    Parameters
    ----------
    data :
        Hourly rainfall data
    rain_col :
        Column with rainfall data

    Returns
    -------
    daily_data_not_wr :
        Daily rainfall data with world records filtered out

    """
    # 1. Filter out hourly world records
    data_not_wr = stats.filter_out_rain_world_records(data, rain_col, time_res="hourly")
    # 2. Group into daily resolution
    daily_data = data_not_wr.group_by_dynamic("time", every="1d").agg(pl.col(rain_col).sum())
    # 3. Filter out daily world records
    daily_data_not_wr = stats.filter_out_rain_world_records(daily_data, rain_col, time_res="daily")
    return daily_data_not_wr


def get_local_etccdi_sdii_mean(gauge_lat: int | float, gauge_lon: int | float) -> float:
    """
    Get the nearby ETCCDI Standard Precipitation Index mean SDII.

    Parameters
    ----------
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge

    Returns
    -------
    nearby_etccdi_sdii_mean :
        Local mean SDII value

    """
    # 1. Load SDII data
    etccdi_sdii = data_readers.load_etccdi_data(etccdi_var="SDII")
    # 2. Compute spatial mean
    etccdi_sdii = spatial_utils.compute_spatial_mean_xr(etccdi_sdii, var_name="SDII")
    # 3. Get nearest local CDD value to the gauge coordinates
    nearby_etccdi_sdii = neighbourhood_utils.get_nearest_etccdi_val_to_gauge(etccdi_sdii, gauge_lat, gauge_lon)
    # 4. Get local maximum CDD_days value
    nearby_etccdi_sdii_mean = np.max(nearby_etccdi_sdii["SDII_mean"])
    return nearby_etccdi_sdii_mean


def flag_daily_accumulations(data: pl.DataFrame, rain_col: str, accumulation_threshold: float) -> np.ndarray:
    """
    Flag daily accumulation of hourly data.

    Parameters
    ----------
    data :
        Hourly rainfall data
    rain_col :
        Column with rainfall data
    accumulation_threshold :
        Rain accumulation for detecting possible daily accumulations

    Returns
    -------
    da_flags :
        Daily accumulation flags

    """
    # Note uses 24-hour moving window
    rain_vals = data[rain_col]
    da_flags = np.zeros_like(rain_vals)
    for i in range(len(rain_vals) - 24):
        day_rain_vals = rain_vals[i : i + 24]
        da_flag = flag_one_daily_accumulation_based_on_threshold(day_rain_vals, accumulation_threshold)
        if da_flag > max(da_flags[i : i + 24]):
            da_flags[i : i + 24] = np.full(24, da_flag)
    return da_flags


def flag_one_daily_accumulation_based_on_threshold(day_rain_vals: pl.Series, accumulation_threshold: float) -> int:
    """
    Flag one day as accumulation if a value is preceded by 23 hourly recordings of 0.

    Parameters
    ----------
    day_rain_vals :
        One day of rain values
    accumulation_threshold :
        Reference SDII threshold

    Returns
    -------
    flag :
        1 if daily accumulation, otherwise 0

    """
    flag = 0
    if day_rain_vals[23] > 0:
        dry_hours = 0
        for h in range(23):
            if day_rain_vals[h] <= 0:
                dry_hours += 1
        if dry_hours == 23:
            if day_rain_vals[23] > accumulation_threshold:
                flag = 1
    return flag


def get_accumulation_threshold(
    etccdi_sdii: float, gauge_sdii: float, accumulation_multiplying_factor: int | float
) -> float:
    """
    Get rainfall accumulation threshold based on ETCCDI or rain gauge Standard Precipitation Intensity Index (index).

    Parameters
    ----------
    etccdi_sdii :
        SDII value from ETCCDI
    gauge_sdii :
        SDII value from rain gauge
    accumulation_multiplying_factor :
        Factor to multiply to SDII value for to identify an accumulation of rain recordings

    Returns
    -------
    accumulation_threshold :
        Reference SDII threshold

    """
    if np.isnan(etccdi_sdii):
        accumulation_threshold = etccdi_sdii * accumulation_multiplying_factor
    else:
        accumulation_threshold = gauge_sdii * accumulation_multiplying_factor
    return accumulation_threshold


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

    # 2. Get all non-0 flags (i.e. suspicious dry spells)
    dry_spell_non_zero = dry_spell_lengths_flags.filter(pl.col("dry_spell_flag") > 0)

    # 3. Loop through problematic flags and label the original data based on duration of dry spell
    for non_zero_data_row in dry_spell_non_zero.iter_rows():
        # overwrite flag
        dry_spell_flag_data = dry_spell_flag_data.with_columns(
            pl.when((pl.col("time") >= non_zero_data_row[1]) & (pl.col("time") <= non_zero_data_row[2]))
            .then(non_zero_data_row[4])
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
    # 1. Get dry spells
    gauge_dry_spells = get_dry_spells(data, rain_col)

    # 2. Get consecutive groups of dry spells
    gauge_dry_spell_groups = get_consecutive_dry_days(gauge_dry_spells)

    # 3. Get dry spell lengths
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


def get_first_wet_after_dry_spell(data: pl.DataFrame, rain_col: str) -> pl.DataFrame:
    """
    Get first non-zero rainfall value after dry spell.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data

    Returns
    -------
    data_w_first_wet :
        Data with binary column denoting first wet after dry spell

    """
    # 1. Get dry spells
    gauge_dry_spells = get_dry_spells(data, rain_col)

    # 2. Get consecutive groups of dry spells
    gauge_dry_spell_groups = get_consecutive_dry_days(gauge_dry_spells)

    return gauge_dry_spell_groups.with_columns(
        pl.when((pl.col("is_dry") == 0) & (pl.col("dry_group_id").diff().fill_null(0) == 1))
        .then(pl.col("time"))
        .otherwise(None)
        .alias("first_wet_after_dry")
    )


def get_consecutive_dry_days(gauge_dry_spells: pl.DataFrame) -> pl.DataFrame:
    """
    Get consecutive groups of 0 rainfall days.

    Parameters
    ----------
    gauge_dry_spells :
        Data with 'is_dry' column

    Returns
    -------
    gauge_dry_spell_groups :
        Data with group ids for consecutive dry days

    """
    return gauge_dry_spells.with_columns(((pl.col("is_dry").diff().fill_null(0) == 1).cum_sum()).alias("dry_group_id"))


def get_dry_spells(data: pl.DataFrame, rain_col: str) -> pl.DataFrame:
    """
    Get dry spell column.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data

    Returns
    -------
    data_w_dry_spells :
        Data with is_dry binary column

    """
    return data.with_columns(
        (pl.col(rain_col) == 0).cast(pl.Int8()).alias("is_dry"),
    )


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
