# -*- coding: utf-8 -*-
"""
Quality control checks for sub-hourly data.

From Sub-hourly QC developed by Roberto Villalobos and described in Villalobos-Herrera et al. (2022).

Code adapted from https://github.com/nclwater/SubHourlyQC/tree/main (GNU GPL v3.0) authored by Roberto Villalobos.

Classes and functions ordered by appearance in SubHourlyQC framework.
"""

import datetime

import polars as pl

from rainfallqc.checks.comparison_checks import flag_exceedance_of_ref_val_as_col
from rainfallqc.checks.timeseries_checks import (
    flag_streaks_exceeding_wet_day_rainfall_threshold,
    get_streaks_of_repeated_values,
)
from rainfallqc.core.all_qc_checks import qc_check
from rainfallqc.utils import data_utils

UK_1hr_RECORD = 92  # mm
UK_24hr_RECORD = 341.4  # mm

# Monthly thresholds taken directly from paper (not code)
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
UK_MONTHLY_THRESHOLDS_1hr = dict(zip(MONTH_NAMES, [30, 30, 30, 30, 40, 40, 40, 40, 40, 40, 30, 30]))
UK_MONTHLY_THRESHOLDS_15min = dict(zip(MONTH_NAMES, [15, 15, 13, 13, 13, 18, 20, 20, 20, 20, 17, 16]))
UK_MONTHLY_THRESHOLDS_1min = dict(zip(MONTH_NAMES, [3, 3, 2, 2, 2, 4, 5, 5, 5, 5, 4, 3]))


@qc_check("check_exceedance_of_UK_1hr_record", require_non_negative=True)
def check_exceedance_of_UK_1hr_record(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Check exceedance of UK 1-hour record.

    Flags:
    0 == if doesn't exceed threshold
    Seperate flags denote when the data exceeds the 1-hour record by:
    1 == < 20%
    2 == >= 20%
    3 == >= 33%
    4 == >= 50%

    This is HQC_UK1hr from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of UK 1hr Record

    """
    return get_subhourly_exceedance_of_given_record(
        data=data,
        target_gauge_col=target_gauge_col,
        record_rainfall_amount=UK_1hr_RECORD,
        flag_col_name="UK_1hr_record_check",
    )


@qc_check("check_exceedance_of_UK_24hr_record", require_non_negative=True)
def check_exceedance_of_UK_24hr_record(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Check exceedance of UK 24-hour record.

    Flags:
    0 == if doesn't exceed threshold
    Seperate flags denote when the data exceeds the 24-hour record by:
    1 == < 20%
    2 == >= 20%
    3 == >= 33%
    4 == >= 50%

    This is HQC_UK24hr from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of UK 24hr Record

    """
    return get_subhourly_exceedance_of_given_record(
        data=data,
        target_gauge_col=target_gauge_col,
        record_rainfall_amount=UK_24hr_RECORD,
        flag_col_name="UK_24hr_record_check",
    )


@qc_check("check_daily_exceedance_of_UK_24hr_record", require_non_negative=True)
def check_daily_exceedance_of_UK_24hr_record(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Check exceedance of UK 24-hour record when aggregating to 24 hours.

    Flags:
    0 == if doesn't exceed threshold
    Seperate flags denote when the daily sums exceeds the 24-hour record by:
    1 == < 20%
    2 == >= 20%
    3 == >= 33%
    4 == >= 50%

    This is HQC_UK24hr_rolling from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of UK 24hr rolling record

    """
    # 1. Check data is sub-hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["1m", "15m"])
    time_step = data_utils.get_data_timestep_as_str(data)

    # 2. Aggregate data to daily
    original_data = data.clone()
    daily_data = data.group_by_dynamic("time", every="1d").agg(pl.col(target_gauge_col).sum())

    if time_step == "15m":
        time_step_per_day = 96  # 96x 15-min periods per day
    if time_step == "1m":
        time_step_per_day = 1440  # 1440 x 1-min periods per day

    # 3. Flag exceedance of world record value
    data_w_flags = flag_exceedance_of_ref_val_as_col(
        daily_data, target_gauge_col, ref_val=UK_24hr_RECORD, new_col_name="UK_24hr_rolling_record_check"
    )

    # 4. Disaggregate data back to original resolution
    data_w_flags_disag = data_utils.downsample_and_fill_columns(
        high_res_data=original_data,
        low_res_data=data_w_flags,
        data_cols="UK_24hr_rolling_record_check",
        fill_limit=time_step_per_day - 1,
        fill_method="backward",
    )
    return data_w_flags_disag.select(["time", "UK_24hr_rolling_record_check"])


@qc_check("check_streaks_20mm", require_non_negative=True)
def check_streaks_20mm(
    data: pl.DataFrame, target_gauge_col: str, flag_col_name: str = "streak_flag_20mm"
) -> pl.DataFrame:
    """
    Check streaks with fixed minimum hourly threshold of 20 mm.

    Flags:
    1 == when data has streak of 2 or more timesteps that are more than 20 mm

    This is HQC_streaks_20mm from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data
    flag_col_name :
        Name for flag column (default: 'streak_flag_20mm')

    Returns
    -------
    data_w_flags:
        Rainfall data with flags denotting period of repeating streak above 20mm

    """
    # 1. Check data is sub-hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["1m", "15m"])
    time_step = data_utils.get_data_timestep_as_str(data)

    # 2. Aggregate data to hourly
    original_data = data.clone()
    hourly_data = data.group_by_dynamic("time", every="1h").agg(pl.col(target_gauge_col).sum())

    if time_step == "15m":
        time_step_per_hour = 4  # 4x 15-min periods per hour
    if time_step == "1m":
        time_step_per_hour = 60  # 60 x 1-min periods per hour

    # 3. Get streaks in data
    streak_data = get_streaks_of_repeated_values(hourly_data, target_gauge_col)

    # 4. Flag streaks of 2 or more repeated large values exceeding 20 mm
    streak_data_w_flags = flag_streaks_exceeding_wet_day_rainfall_threshold(
        streak_data, target_gauge_col, min_streak_length=2, accumulation_threshold=20, flag_col_name=flag_col_name
    )

    # 5. Disaggregate data back to original resolution
    data_w_flags_disag = data_utils.downsample_and_fill_columns(
        high_res_data=original_data,
        low_res_data=streak_data_w_flags,
        data_cols=flag_col_name,
        fill_limit=time_step_per_hour - 1,
        fill_method="backward",
    )
    return data_w_flags_disag.select(["time", flag_col_name])


@qc_check("check_freq_is_subhourly", require_non_negative=True)
def check_freq_is_subhourly(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Checks frequency and resolution of data is subhourly.
    Specifically, it will check monthly periods with frequencies >= 30 minutes, or where the resolution is
    1 mm (usually an indicator of tip counts not tip amounts in the data), and replace them with NAN.

    Flags:
    1 == when month has suspect frequency or resolution

    This is freqResChecker (Function 1 of the SHQC process) from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_flags_disag :
        Rainfall data with flags denoting months where frequency or resolution is suspect

    """
    # 1. Get all unique timestep in the data
    unique_timesteps = data_utils.get_data_timesteps(data)

    # 2. If there are more than 1 time-step then apply check
    if len(unique_timesteps) > 1:
        original_data = data.clone()
        # 3. Check frequency of data; I am uncertain of this, because what if very few values in month
        data_freqs = data.with_columns([pl.col("time").diff().alias("time_step")])
        # Taking .max() if multiple freq from mode
        most_common_freq_by_mo = data_freqs.group_by_dynamic("time", every="1mo").agg(
            pl.col("time_step").mode().max().alias("most_common_freq")
        )

        # 4. Check resolution of the data (checking mode of rainfall); I am uncertain of this, because what if very few values in month.
        # Taking .max() if multiple res from mode
        most_common_res_by_mo = data.group_by_dynamic("time", every="1mo").agg(
            pl.col(target_gauge_col).mode().max().alias("most_common_res")
        )

        # 5. Combine together
        freq_and_res = most_common_freq_by_mo.join(most_common_res_by_mo, on="time")

        # 6. Flag months where freq >= 30 mins or and resolution >=1.0
        freq_and_res_w_flags = freq_and_res.with_columns(
            pl.when((pl.col("most_common_freq") >= datetime.timedelta(minutes=30)) | (pl.col("most_common_res") >= 1.0))
            .then(1)
            .otherwise(0)
            .alias("freq_res_flag")
        )

        # 7. Disaggregate data back to original resolution
        data_w_flags_disag = data_utils.downsample_monthly_data(
            sub_monthly_data=original_data,
            monthly_data=freq_and_res_w_flags,
            data_cols="freq_res_flag",
        )

    else:
        # Check data has consistent resolution that is 1-min or 15-min
        data_utils.check_data_is_specific_time_res(data, time_res=["1m", "15m"])
        data_w_flags_disag = data.with_columns(freq_res_flag=0)
    return data_w_flags_disag


@qc_check("check_subhourly_thresholds", require_non_negative=True)
def check_subhourly_thresholds(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Tests hourly, 15-min, 1-min rainfall totals agaisnt thresholds agaisnt values set for each month.

    Flags:
    1 == when data is suspect

    This is subH_checkr (Function 2 of the SHQC process) from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_flags_disag :
        Rainfall data with flags denoting

    """
    # 1. Check data is sub-hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["1m", "15m"])
    time_step = data_utils.get_data_timestep_as_str(data)

    # 2. Add month name column
    original_data = data.clone()
    data = data.with_columns(pl.col("time").dt.strftime("%b").alias("month_name"))

    if time_step == "15m":
        time_step_per_hour = 4  # 4x 15-min periods per hour
    if time_step == "1m":
        time_step_per_hour = 60  # 60 x 1-min periods per hour


    # 3. Aggregate data to hourly
    hourly_data = data.group_by_dynamic("time", every="1h").agg(
        pl.col(target_gauge_col).sum(), pl.col("month_name").first()
    )

    # 4. Flag data based on hourly threshold
    data_1hr_w_flags = flag_data_based_on_threshold(
        hourly_data, target_gauge_col, threshold_dict=UK_MONTHLY_THRESHOLDS_1hr, threshold_col_name="month_1hr_threshold"
    )
    # 4.1 Disaggregate data back to original resolution
    data_1hr_w_flags_disag = data_utils.downsample_and_fill_columns(
        high_res_data=original_data,
        low_res_data=data_1hr_w_flags,
        data_cols="month_1hr_threshold_flag",
        fill_limit=time_step_per_hour - 1,
        fill_method="backward",
    )

    # 5. Flag data based on 15min thresholds
    if time_step == "15m":
        data_15mins = data
    if time_step == "1m":
        # Aggregate data to 15 min
        data_15mins = data.group_by_dynamic("time", every="15m").agg(
            pl.col(target_gauge_col).sum(), pl.col("month_name").first()
        )
     # Flag data based on 15min threshold
    data_15min_w_flags = flag_data_based_on_threshold(
        data_15mins, target_gauge_col, threshold_dict=UK_MONTHLY_THRESHOLDS_15min, threshold_col_name="month_15min_threshold"
    ).select(["time", "month_15min_threshold_flag"])
    if time_step == "1m":
        # Disaggregate data back to original resolution
        data_15min_w_flags = data_utils.downsample_and_fill_columns(
            high_res_data=original_data,
            low_res_data=data_15min_w_flags,
            data_cols="month_15min_threshold_flag",
            fill_limit=15 - 1,
            fill_method="backward",
        )
        # 6. Flag data based on 1min threshold
        data_1min_w_flags = flag_data_based_on_threshold(
            data, target_gauge_col, threshold_dict=UK_MONTHLY_THRESHOLDS_1min, threshold_col_name="month_1min_threshold"
        ).select(["time", "month_1min_threshold_flag"])

    # 7. Join together all flag columns
    data_w_all_flags = data_1hr_w_flags_disag.join(data_15min_w_flags, on='time')
    if time_step == "1m":
        data_w_all_flags = data_w_all_flags.join(data_1min_w_flags, on='time')
    return data_w_all_flags

def get_subhourly_exceedance_of_given_record(
    data: pl.DataFrame, target_gauge_col: str, record_rainfall_amount: [int | float], flag_col_name: str
) -> pl.DataFrame:
    """
    Check sub-houlry exceedance of given record.

    Used in QCX and QCX of the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data
    record_rainfall_amount :
        given record rainfall amount
    flag_col_name :
        Name for flag column

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of given rainfall record (see `flag_exceedance_of_ref_val_as_col` function)

    """
    # 1. Check data is sub-hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["1m", "15m"])
    time_step = data_utils.get_data_timestep_as_str(data)

    # 2. Aggregate data to hourly
    original_data = data.clone()
    hourly_data = data.group_by_dynamic("time", every="1h").agg(pl.col(target_gauge_col).sum())

    if time_step == "15m":
        time_step_per_hour = 4  # 4x 15-min periods per hour
    if time_step == "1m":
        time_step_per_hour = 60  # 60 x 1-min periods per hour

    # 3. Flag exceedance of world record value
    data_w_flags = flag_exceedance_of_ref_val_as_col(
        hourly_data, target_gauge_col, ref_val=record_rainfall_amount, new_col_name=flag_col_name
    )

    # 4. Disaggregate data back to original resolution
    data_w_flags_disag = data_utils.downsample_and_fill_columns(
        high_res_data=original_data,
        low_res_data=data_w_flags,
        data_cols=flag_col_name,
        fill_limit=time_step_per_hour - 1,
        fill_method="backward",
    )
    return data_w_flags_disag.select(["time", flag_col_name])


def flag_data_based_on_threshold(
    data: pl.DataFrame, target_gauge_col: str, threshold_dict: dict, threshold_col_name: str
) -> pl.DataFrame:
    """
    Flag data based on thresholds

    Built for SubHourlyQC framework and to be used with inbuilt UK_MONTHLY_THRESHOLDS_n.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data
    threshold_dict :
        given rainfall threshold in mm for each month (e.g. Jan: 10, Feb: 10, Mar: 12)
    threshold_col_name :
        Name to use for threshold column and threshold_flag column.

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of given month rainfall threshold

    """
    if "month_name" not in data.columns:
        raise ValueError(
            f"Expecting a 'month_name' column, please create this column with: "
            f" data = data.with_columns(pl.col('time').dt.strftime('%b').alias('month_name'))"
        )

    data = data.with_columns(
        pl.col("month_name").replace(threshold_dict).cast(pl.Int32).alias(threshold_col_name)
    )
    data_w_flags = data.with_columns(
        pl.when(pl.col(target_gauge_col) > pl.col(threshold_col_name))
        .then(1)
        .otherwise(0)
        .alias(f"{threshold_col_name}_flag")
    )
    return data_w_flags
