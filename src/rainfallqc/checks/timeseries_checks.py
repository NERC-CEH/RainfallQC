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

DAILY_DIVIDING_FACTOR = {"15m": 96, "hourly": 24, "daily": 1}


def check_dry_period_cdd(
    data: pl.DataFrame, target_gauge_col: str, time_res: str, gauge_lat: int | float, gauge_lon: int | float
) -> pl.DataFrame:
    """
    Identify suspiciously long dry periods in time-series using the ETCCDI Consecutive Dry Days (CDD) index.

    This is QC12 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data
    time_res :
        Temporal resolution of the time series either '15m', 'daily' or 'hourly'
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge

    Returns
    -------
    data_w_dry_spell_flags :
        Data with dry spell flags

    """
    if time_res != "15m" and time_res != "daily" and time_res != "hourly":
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
    gauge_dry_spell_lengths = get_dry_spell_duration(data, target_gauge_col)

    # 6. Flag dry spells
    gauge_dry_spell_lengths_flags = flag_dry_spell_duration(gauge_dry_spell_lengths, max_etccdi_cdd_days, time_res)

    # 7. Join data back to main data and flag
    data_w_dry_spell_flags = join_dry_spell_data_back_to_original(data, gauge_dry_spell_lengths_flags)

    # 8. Join rain col back
    data_w_dry_spell_flags = data_w_dry_spell_flags.with_columns(pl.lit(data[target_gauge_col]).alias(target_gauge_col))

    # 9. Remove unnecessary columns
    return data_w_dry_spell_flags.select(["time", "dry_spell_flag"])


def check_daily_accumulations(
    data: pl.DataFrame,
    target_gauge_col: str,
    gauge_lat: int | float,
    gauge_lon: int | float,
    wet_day_threshold: int | float = 1.0,
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
    target_gauge_col :
        Column with rainfall data
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge
    wet_day_threshold :
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
    # 0. Check data is hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["1h"])

    # 1. Get accumulation threshold from ETCCDI SDII value, if not given
    if not accumulation_threshold:
        accumulation_threshold = get_accumulation_threshold_from_etccdi(
            data, target_gauge_col, gauge_lat, gauge_lon, wet_day_threshold, accumulation_multiplying_factor
        )

    # 2. Flag daily (24 hour) accumulations in hourly data based on SDII threshold
    da_flags = flag_accumulation_periods(
        data, target_gauge_col, accumulation_threshold=accumulation_threshold, accumulation_period_in_hours=24
    )

    # 3. Add daily_accumulation column
    data = data.with_columns(daily_accumulation=pl.Series(da_flags))

    # 4. Remove unnecessary columns
    return data.select(["time", "daily_accumulation"])


def check_monthly_accumulations(
    data: pl.DataFrame,
    target_gauge_col: str,
    gauge_lat: int | float,
    gauge_lon: int | float,
    wet_day_threshold: int | float = 1.0,
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
        Daily or Hourly or 15 min rainfall data
    target_gauge_col :
        Column with rainfall data
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge
    wet_day_threshold :
        Threshold for rainfall intensity in one day (default is 1 mm)
    accumulation_multiplying_factor :
        Factor to multiply SDII value for to identify an accumulation of rain recordings (default is 2)
    accumulation_threshold :
        Rain accumulation for detecting possible monthly accumulations

    Returns
    -------
    data_w_monthly_accumulation_flags :
        Data with monthly accumulation flags

    Notes
    -----
    The original method filters out dry spells less than

    """
    # 0. Check time step of data
    data_utils.check_data_is_specific_time_res(data, time_res=["15m", "1h", "1d"])
    time_step = data_utils.get_data_timestep_as_str(data)
    if time_step == "15m":
        min_dry_spell_duration = 2880  # roughly 2880 15-minutes in month
    elif time_step == "1h":
        min_dry_spell_duration = 720  # roughly 720 hours in month
    else:
        min_dry_spell_duration = 30  # roughly 30 days in month

    # 1. Get accumulation threshold from ETCCDI SDII value, if not given
    if not accumulation_threshold:
        accumulation_threshold = get_accumulation_threshold_from_etccdi(
            data, target_gauge_col, gauge_lat, gauge_lon, wet_day_threshold, accumulation_multiplying_factor
        )

    # 2. Get info about dry spells in rainfall record
    gauge_dry_spell_info = get_dry_spell_info(data, target_gauge_col)

    # 3. Get possible accumulations
    gauge_data_possible_accumulations = get_possible_accumulations(
        gauge_dry_spell_info, target_gauge_col, accumulation_threshold
    )

    # 4. Flag monthly (720 h) accumulations
    gauge_data_monthly_accumulations = flag_accumulation_based_on_next_dry_spell_duration(
        gauge_data_possible_accumulations,
        min_dry_spell_duration=min_dry_spell_duration,
        accumulation_col_name="monthly_accumulation",
    )

    # 5. Remove unnecessary columns
    return gauge_data_monthly_accumulations.select(["time", "monthly_accumulation"])


def check_streaks(
    data: pl.DataFrame,
    target_gauge_col: str,
    gauge_lat: int | float,
    gauge_lon: int | float,
    data_resolution: float,
    accumulation_threshold: float = None,
) -> pl.DataFrame:
    """
    Check for suspected repeated values.

    Flags (TODO: change numbers as original includes unuseful 2):
    1, if streaks of 2 or more repeated values exceeding 2* mean wet day rainfall
    3, if streaks of 12 or more greater than data resolution
    4, if streaks of 24 or more greater than zero
    5, if period of zeros bounded by streaks of >= 24

    This is QC15 from the IntenseQC framework.

    Parameters
    ----------
    data :
        Hourly data with rainfall.
    target_gauge_col :
        Column with rainfall data.
    gauge_lat :
        latitude of the rain gauge.
    gauge_lon :
        longitude of the rain gauge.
    data_resolution :
        Resolution of rainfall data (i.e. minimum rainfall recording).
    accumulation_threshold :
        Rain accumulation for detecting possible monthly accumulations

    Returns
    -------
    data_w_streak_flags :
        Data with streak flags.

    """
    # 0. Check data is hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["1h"])

    # 1. Get accumulation threshold from ETCCDI SDII value, if not given
    if not accumulation_threshold:
        accumulation_threshold = get_accumulation_threshold_from_etccdi(
            data, target_gauge_col, gauge_lat, gauge_lon, wet_day_threshold=1.0, accumulation_multiplying_factor=2.0
        )

    # 2. Get streaks of repeated values
    streak_data = get_streaks_of_repeated_values(data, target_gauge_col)

    # 3. Flag streaks of 2 or more repeated large values exceeding 2 * mean wet day rainfall (from ETCCDI SDII)
    streak_flag1 = flag_streaks_exceeding_wet_day_rainfall_threshold(
        streak_data, target_gauge_col, streak_length=2, accumulation_threshold=accumulation_threshold
    )

    # 4. Flag streaks of 12 or more greater than data resolution
    streak_flag3 = flag_streaks_exceeding_data_resolution(
        streak_data, target_gauge_col, streak_length=12, data_resolution=data_resolution
    )

    # 5. Flag streaks of 24 or more greater than zero
    streak_flag4 = flag_streaks_exceeding_zero(streak_data, target_gauge_col, streak_length=24)

    # 6. Flag periods of zeros bounded by streaks of multiples of 24
    streak_flag5 = flag_streaks_of_zero_bounded_by_days(streak_data, target_gauge_col)

    # 7. Join flags together
    data_w_streak_flags = data.with_columns(
        streak_flag1=streak_flag1["streak_flag1"],
        streak_flag3=streak_flag3["streak_flag3"],
        streak_flag4=streak_flag4["streak_flag4"],
        streak_flag5=streak_flag5["streak_flag5"],
    )
    return data_w_streak_flags.select(["time", "streak_flag1", "streak_flag3", "streak_flag4", "streak_flag5"])


def flag_streaks_of_zero_bounded_by_days(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Flag streak of zeros bounded by record that are a multiple of 24 hours.

    TODO: make work for daily using: DAILY_DIVIDING_FACTOR

    Parameters
    ----------
    data :
        Hourly data with rainfall.
    target_gauge_col :
        Column with rainfall data.

    Returns
    -------
    streaks_w_flag5 :
        Data with streak flag 5.

    """
    # 1. group of streaks
    data_streak_groups = (
        data.group_by("streak_id")
        .agg(streak_len=pl.len(), rain_amount=pl.col(target_gauge_col).first())
        .sort(by="streak_id")
    )

    # 2. get dry spells
    streak_w_dry_spells = data_utils.get_dry_spells(data_streak_groups, target_gauge_col="rain_amount")

    # 3. Flag streaks of multiples of 1 day
    streaks_w_flag5 = streak_w_dry_spells.with_columns(
        (
            pl.when((pl.col("is_dry") == 1) & (pl.col("streak_len") % 24 == 0) & (pl.col("streak_len").shift(-1) >= 24))
            .then(1)
            .otherwise(0)
            .alias("streak_flag5_next")
        ),
        (
            pl.when((pl.col("is_dry") == 1) & (pl.col("streak_len") % 24 == 0) & (pl.col("streak_len").shift(1) >= 24))
            .then(1)
            .otherwise(0)
            .alias("streak_flag5_prev")
        ),
    )

    # 4. Filter out only streaks where next or previous are multiples of 24
    streaks_w_flag5 = streaks_w_flag5.filter((pl.col("streak_flag5_next") == 1) | (pl.col("streak_flag5_prev") == 1))

    # 2. Label original data
    data_w_flags = data.with_columns(
        pl.when(pl.col("streak_id").is_in(streaks_w_flag5["streak_id"].unique().to_list()))
        .then(5)
        .otherwise(0)
        .alias("streak_flag5")
    )
    return data_w_flags


def flag_streaks_exceeding_zero(data: pl.DataFrame, target_gauge_col: str, streak_length: int) -> pl.DataFrame:
    """
    Flag values exceeding wet day rainfall accumulation threshold.

    Parameters
    ----------
    data :
        Rainfall data with streak_id.
    target_gauge_col :
        Column with rainfall data.
    streak_length :
        Only streaks longer than this will be considered.

    Returns
    -------
    data_w_flags :
        Data with streak flag 4

    """
    # 1. Get streak above length and exceeding zero
    streaks_exceeding_zero = get_streaks_above_threshold(data, target_gauge_col, streak_length, 0.0)

    # 2. Label original data
    data_w_flags = data.with_columns(
        pl.when(pl.col("streak_id").is_in(streaks_exceeding_zero["streak_id"].unique().to_list()))
        .then(4)
        .otherwise(0)
        .alias("streak_flag4")
    )
    return data_w_flags


def flag_streaks_exceeding_data_resolution(
    data: pl.DataFrame, target_gauge_col: str, streak_length: int, data_resolution: float
) -> pl.DataFrame:
    """
    Flag streaks exceeding data resolution.

    Parameters
    ----------
    data:
        Rainfall data with streak_id..
    target_gauge_col:
        Column with rainfall data.
    streak_length :
        Only streaks longer than this will be considered
    data_resolution:
        Resolution of rainfall data (i.e. minimum rainfall recording).

    Returns
    -------
    data_w_flags :
        Data with streak flag 3

    """
    # 1. Get streak above length and data resolution
    streaks_above_data_resolution = get_streaks_above_threshold(data, target_gauge_col, streak_length, data_resolution)

    # 2. Label original data
    data_w_flags = data.with_columns(
        pl.when(pl.col("streak_id").is_in(streaks_above_data_resolution["streak_id"].unique().to_list()))
        .then(3)
        .otherwise(0)
        .alias("streak_flag3")
    )
    return data_w_flags


def flag_streaks_exceeding_wet_day_rainfall_threshold(
    data: pl.DataFrame, target_gauge_col: str, streak_length: int, accumulation_threshold: float
) -> pl.DataFrame:
    """
    Flag values exceeding wet day rainfall accumulation threshold.

    Parameters
    ----------
    data :
        Rainfall data with streak_id..
    target_gauge_col :
        Column with rainfall data.
    streak_length :
        Only streaks longer than this will be considered
    accumulation_threshold :
        Threshold for rain accumulation.

    Returns
    -------
    data_w_flags :
        Data with streak flag 1

    """
    # 1. Get streak above length and accumulation threshold
    streaks_above_accumulation = get_streaks_above_threshold(
        data, target_gauge_col, streak_length, accumulation_threshold
    )

    # 2. Label original data
    data_w_flags = data.with_columns(
        pl.when(pl.col("streak_id").is_in(streaks_above_accumulation["streak_id"].unique().to_list()))
        .then(1)
        .otherwise(0)
        .alias("streak_flag1")
    )
    return data_w_flags


def get_streaks_above_threshold(
    data: pl.DataFrame, target_gauge_col: str, streak_length: int, value_threshold: int | float
) -> pl.DataFrame:
    """
        Get streak groups above given threshold.

    Parameters
    ----------
    data :
        Rainfall data with streak_id..
    target_gauge_col :
        Column with rainfall data.
    streak_length :
        Minimum length of streaks.
    value_threshold :
        Threshold to check .

    Returns
    -------
    streaks_above_accumulation :
        Get all streaks above given value

    """
    # 0. Cast threshold to float
    value_threshold = float(value_threshold)

    # 1. group of streaks
    data_streak_groups = (
        data.group_by("streak_id")
        .agg(streak_len=pl.len(), rain_amount=pl.col(target_gauge_col).first())
        .sort(by="streak_id")
    )
    # 2. Get streaks above streak length and threshold
    streaks_above_accumulation = data_streak_groups.drop_nans().filter(
        (pl.col("streak_len") >= streak_length) & (pl.col("rain_amount") > value_threshold)
    )
    return streaks_above_accumulation


def get_streaks_of_repeated_values(data: pl.DataFrame, data_col: str) -> pl.DataFrame:
    """
    Get streaks of repeated values in time series.

    Parameters
    ----------
    data :
        Data with time column.
    data_col :
        Column with values to check streaks in.

    Returns
    -------
    streak_data :
        Data with streak column.

    """
    # Step 1. get streaks columns
    streak_data = data.with_columns(
        (pl.when(pl.col(data_col) == pl.col(data_col).shift(1)).then(1).otherwise(0).alias("same_as_prev"))
    )

    # Step 2. Label groups of streaks
    return streak_data.with_columns(
        streak_id=(1 - pl.col("same_as_prev")).cum_sum(),
    )


def flag_accumulation_based_on_next_dry_spell_duration(
    data: pl.DataFrame, min_dry_spell_duration: int | float, accumulation_col_name: str
) -> pl.DataFrame:
    """
    Flag possible accumulation based on subsequent minimum dry spell duration.

    Flags:
    2, if dry spell followed with high value then wet period (wet)
    1, if dry spell followed with high value then no rain for next 23 hours (dry)
    0, if neither

    Parameters
    ----------
    data :
        Rainfall data with dry spell info and possible accumulation label
    min_dry_spell_duration :
        Minimum dry spell duration
    accumulation_col_name :
        Name for accumulation column

    Returns
    -------
    data_w_flag :
        Data with accumulation flag

    """
    return data.with_columns(
        pl.when(
            (pl.col("possible_accumulation") == 1)
            & (pl.col("dry_spell_length").fill_null(0.0) <= min_dry_spell_duration)
            & (pl.col("next_dry_spell").is_not_null())
        )
        .then(2)
        .when(
            (pl.col("possible_accumulation") == 1)
            & (pl.col("dry_spell_length").fill_null(0.0) <= min_dry_spell_duration)
        )
        .then(1)
        .otherwise(0)
        .alias(accumulation_col_name)
    )


def get_surrounding_dry_spell_lengths(data: pl.DataFrame) -> pl.DataFrame:
    """
    Make prev_dry_spell and next_dry_spell columns from dry_spell_lengths.

    Parameters
    ----------
    data :
        Data with dry_spell_lengths

    Returns
    -------
    data :
        Data with columns of previous and next dry spell durations

    """
    return data.with_columns(
        prev_dry_spell=pl.col("dry_spell_length").shift(1),
        next_dry_spell=pl.col("dry_spell_length").shift(-1),
    )


def get_possible_accumulations(
    gauge_dry_spell_info: pl.DataFrame, target_gauge_col: str, accumulation_threshold: float
) -> pl.DataFrame:
    """
    Get possible accumulations as 0 or 1 based on dry spell info.

    Parameters
    ----------
    gauge_dry_spell_info :
        Rainfall data with columns with dry spell info (durations, first_wet_after_dry, etc.)
    target_gauge_col :
        Column with rainfall data
    accumulation_threshold :
        Threshold of rainfall intensity

    Returns
    -------
    gauge_data_possible_accumulations :
        Data with 1 is possible accumulation, otherwise 0.

    """
    # 1. Get values above daily accumulation threshold in one hour
    gauge_data_possible_accumulations = gauge_dry_spell_info.with_columns(
        pl.when(pl.col("dry_spell_end") == pl.col("time"))
        .then(pl.col(target_gauge_col).shift(-1).fill_nan(0.0) > accumulation_threshold)
        .otherwise(np.nan)
        .alias("possible_accumulation")
    )

    # 2. Shift the value along
    gauge_data_possible_accumulations = gauge_data_possible_accumulations.with_columns(
        possible_accumulation=pl.col("possible_accumulation").shift(1)
    )

    return gauge_data_possible_accumulations


def get_daily_non_wr_data(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Get daily non-world record data.

    Parameters
    ----------
    data :
        Hourly rainfall data
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    daily_data_not_wr :
        Daily rainfall data with world records filtered out

    """
    # 1. Filter out hourly world records
    data_not_wr = stats.filter_out_rain_world_records(data, target_gauge_col, time_res="hourly")
    # 2. Group into daily resolution
    daily_data = data_not_wr.group_by_dynamic("time", every="1d").agg(pl.col(target_gauge_col).sum())
    # 3. Filter out daily world records
    daily_data_not_wr = stats.filter_out_rain_world_records(daily_data, target_gauge_col, time_res="daily")
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


def flag_accumulation_periods(
    data: pl.DataFrame, target_gauge_col: str, accumulation_threshold: float, accumulation_period_in_hours: int
) -> np.ndarray:
    """
    Flag accumulation in a given period of hourly data.

    TODO: make work for daily using: DAILY_DIVIDING_FACTOR

    Parameters
    ----------
    data :
        Hourly rainfall data
    target_gauge_col :
        Column with rainfall data
    accumulation_threshold :
        Rain accumulation for detecting possible period accumulations
    accumulation_period_in_hours :
        Accumulation period in hours

    Returns
    -------
    pa_flags :
        Accumulation flags

    """
    # Note uses n-hour moving window
    rain_vals = data[target_gauge_col]
    pa_flags = np.zeros_like(rain_vals)
    for i in range(len(rain_vals) - accumulation_period_in_hours):
        period_rain_vals = rain_vals[i : i + accumulation_period_in_hours]
        pa_flag = flag_n_hours_accumulation_based_on_threshold(
            period_rain_vals, accumulation_threshold, n_hours=accumulation_period_in_hours
        )
        if pa_flag > max(pa_flags[i : i + accumulation_period_in_hours]):
            pa_flags[i : i + accumulation_period_in_hours] = np.full(accumulation_period_in_hours, pa_flag)
    return pa_flags


def flag_n_hours_accumulation_based_on_threshold(
    period_rain_vals: pl.Series, accumulation_threshold: float, n_hours: int
) -> int | float:
    """
    Flag a period as accumulation if a value is preceded by n hourly recordings of 0.

    Parameters
    ----------
    period_rain_vals :
        One period of rain values
    accumulation_threshold :
        Reference SDII threshold
    n_hours :
        Number of hours in reference period

    Returns
    -------
    flag :
        1 if period accumulation, otherwise 0

    """
    flag = 0
    if period_rain_vals.is_nan().all():
        return np.nan
    elif period_rain_vals[n_hours - 1]:
        if period_rain_vals[n_hours - 1] > 0:
            dry_hours = 0
            for h in range(n_hours - 1):
                if period_rain_vals[h] is None:
                    continue
                elif period_rain_vals[h] <= 0:
                    dry_hours += 1
            if dry_hours == n_hours - 1:
                if period_rain_vals[n_hours - 1] > accumulation_threshold:
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
        accumulation_threshold = gauge_sdii * accumulation_multiplying_factor
    else:
        accumulation_threshold = etccdi_sdii * accumulation_multiplying_factor
    return accumulation_threshold


def get_accumulation_threshold_from_etccdi(
    data: pl.DataFrame,
    target_gauge_col: str,
    gauge_lat: int | float,
    gauge_lon: int | float,
    wet_day_threshold: float,
    accumulation_multiplying_factor: float,
) -> float:
    """
    Get rain accumulation threshold from ETCCDI data.

    Parameters
    ----------
    data :
        Rainfall data.
    target_gauge_col :
        Column with rainfall data.
    gauge_lat :
        latitude of the rain gauge.
    gauge_lon :
        longitude of the rain gauge.
    wet_day_threshold :
        Threshold for rainfall intensity in one day (whether it is a wet day or not)
    accumulation_multiplying_factor :
        Factor to multiply SDII value for to identify an accumulation of rain recordings

    Returns
    -------
    accumulation_threshold :
        Rain accumulation threshold that is e.g.  2*standard precipitation intensity threshold

    """
    # 1. Get local mean ETCCDI SDII value (this is the default for SDII in this method)
    etccdi_sdii = get_local_etccdi_sdii_mean(gauge_lat, gauge_lon)
    # 2. Filter out world records
    daily_data_non_wr = get_daily_non_wr_data(data, target_gauge_col)
    # 3. Calculate simple precipitation intensity index from daily data
    gauge_sdii = stats.simple_precip_intensity_index(daily_data_non_wr, target_gauge_col, wet_day_threshold)
    # 4. Get rain gauge accumulation threshold
    return get_accumulation_threshold(etccdi_sdii, gauge_sdii, accumulation_multiplying_factor)


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


def get_dry_spell_duration(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Get consecutive dry spell duration.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    gauge_dry_spell_lengths :
        Data with dry spell start, end and duration

    """
    # 1. Get dry spells
    gauge_dry_spells = data_utils.get_dry_spells(data, target_gauge_col)

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


def get_first_wet_after_dry_spell(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Get first non-zero rainfall value after dry spell.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_first_wet :
        Data with binary column denoting first wet after dry spell

    """
    # 1. Get dry spells
    gauge_dry_spells = data_utils.get_dry_spells(data, target_gauge_col)

    # 2. Get consecutive groups of dry spells
    gauge_dry_spell_groups = get_consecutive_dry_days(gauge_dry_spells)

    return gauge_dry_spell_groups.with_columns(
        pl.when((pl.col("is_dry") == 0) & (pl.col("dry_group_id").diff().fill_null(0) == 1))
        .then(pl.col("time"))
        .otherwise(None)
        .alias("first_wet_after_dry")
    )


def get_dry_spell_info(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Get summary of dry spells (i.e. duration and first wet value after dry and previous and next dry spells duration).

    Parameters
    ----------
    data :
        Hourly rainfall data
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    gauge_dry_spell_info :
        Data with dry spell information

    """
    # 1. Get dry spell durations (with start and end dates)
    gauge_dry_spell_lengths = get_dry_spell_duration(data, target_gauge_col)

    # 2. Get first wet value after consecutive dry spell
    gauge_first_wet_after_dry = get_first_wet_after_dry_spell(data, target_gauge_col)

    # 3. Join data together
    gauge_dry_spell_info = gauge_first_wet_after_dry.join(gauge_dry_spell_lengths, on="dry_group_id", how="left")

    # 4. Get previous and next dry spell durations for flagging
    return get_surrounding_dry_spell_lengths(gauge_dry_spell_info)


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


def compute_dry_spell_days(dry_spell_data: xr.Dataset) -> xr.Dataset:
    """
    Compute dry spells in days from ETCCDI Consecutive Dry Days data.

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
