# -*- coding: utf-8 -*-
"""
All data operations for polars including datetime and calendar functionality.

Classes and functions ordered alphabetically.
"""

import calendar
import datetime
from collections.abc import Sequence

import numpy as np
import polars as pl
import xarray as xr

SECONDS_IN_DAY = 86400.0
TEMPORAL_CONVERSIONS = {"hourly": "1h", "daily": "1d", "monthly": "1mo"}
MONTHLY_TIME_STEPS = ["28d", "29d", "30d", "31d"]


def back_propagate_daily_data_flags(data: pl.DataFrame, flag_column: str, num_days: int) -> pl.DataFrame:
    """
    Back fill-in flags a number of days.

    This will prioritise higher flag values.

    Parameters
    ----------
    data :
        Daily data with `flag_column`
    flag_column :
        column with flags
    num_days:
        Number of days to back-propagate

    Returns
    -------
    data :
        Data with flags back-propogated

    """
    data = data.clone()
    # Extract flag values
    flag_values = (flag for flag in data[flag_column].unique() if (np.isfinite(flag) & (flag > 0)))
    for flag, data_filtered in [(flag, data.filter(pl.col(flag_column) == flag)) for flag in flag_values]:
        for time_to_use in data_filtered["time"]:
            assert isinstance(time_to_use, datetime.datetime), "time_to_use must be datetime.datetime"
            start_time = time_to_use - datetime.timedelta(days=num_days)
            data = data.with_columns(
                pl.when((pl.col("time") >= start_time) & (pl.col("time") <= time_to_use))
                .then(flag)
                .otherwise(pl.col(flag_column))
                .alias(flag_column)
            )

    return data


def calculate_dry_spell_fraction(data: pl.DataFrame, target_gauge_col: str, dry_period_days: int) -> pl.Series:
    """
    Calculate dry spell fraction.

    Parameters
    ----------
    data :
        Data with time column
    target_gauge_col :
        Column with rainfall data
    dry_period_days :
        Length for of a "dry_spell"

    Returns
    -------
    rain_daily_dry_day :
        Data with dry spell fraction

    """
    if not isinstance(data, pl.DataFrame):
        data = data.to_frame()

    # 1. make dry day column
    data_dry_days = get_dry_spells(data, target_gauge_col)

    # 2. Calculate late dry spell fraction
    data_dry_days = data_dry_days.with_columns(
        dry_spell_fraction=pl.col("is_dry").rolling_sum(window_size=dry_period_days, min_samples=dry_period_days)
        / dry_period_days
    )
    return data_dry_days["dry_spell_fraction"]


def check_data_has_consistent_time_step(data: pl.DataFrame) -> None:
    """
    Check data has a consistent time step i.e. '1h'.

    Parameters
    ----------
    data :
        Data with time column

    Raises
    ------
    ValueError :
        If data has more than one time steps

    """
    unique_timesteps = get_data_timesteps(data)
    if unique_timesteps.len() != 1:
        timestep_strings = [format_timedelta_duration(td) for td in unique_timesteps]
        raise ValueError(f"Data has a inconsistent time step. Data has following time steps: {timestep_strings}")


def check_data_is_monthly(data: pl.DataFrame) -> None:
    """
    Check data is monthly.

    Parameters
    ----------
    data :
        Data with time column

    Raises
    ------
    ValueError :
        If data has a no monthly time steps

    """
    unique_timesteps = get_data_timesteps(data)
    timestep_strings = [format_timedelta_duration(td) for td in unique_timesteps]

    if not all(ts in MONTHLY_TIME_STEPS for ts in timestep_strings):
        raise ValueError(
            f"Data contains non-monthly timesteps not like '29d', '30d', etc. Timesteps found are {timestep_strings}"
        )

    if not timestep_strings:
        raise ValueError("No timesteps found in data.")


def check_data_is_specific_time_res(data: pl.DataFrame, time_res: str | list) -> None:
    """
    Check data has a hourly or daily time step.

    Does not work for monthly data, please use 'check_data_is_monthly'.

    Parameters
    ----------
    data :
        Data with time column.
    time_res :
        Time resolutions either a single string or list of strings

    Raises
    ------
    ValueError :
        If data is not hourly or daily.

    """
    # Normalize to list
    if isinstance(time_res, str):
        allowed_res = [time_res]
    elif isinstance(time_res, Sequence):
        allowed_res = list(time_res)
    else:
        raise TypeError("time_res must be a string or list of strings")

    # add terms like 'hourly', 'daily' or 'monthly'
    for time_conv in TEMPORAL_CONVERSIONS:
        if time_res == time_conv:
            allowed_res.append(TEMPORAL_CONVERSIONS[time_res])

    # Get actual time step as a string like "1h"
    time_step = get_data_timestep_as_str(data)
    if time_step not in allowed_res:
        raise ValueError(f"Invalid time step. Expected one of {allowed_res}, but data has time-step(s): {time_step}")


def convert_datarray_seconds_to_days(series_seconds: xr.DataArray) -> np.ndarray:
    """
    Convert xarray series from seconds to days. For some reason the CDD data from ETCCDI is in seconds.

    Parameters
    ----------
    series_seconds :
        Data in series to convert to days.

    Returns
    -------
    series_days :
        Data array converted to days.

    """
    return series_seconds.values.astype("timedelta64[s]").astype("float32") / SECONDS_IN_DAY


def convert_daily_data_to_monthly(
    daily_data: pl.DataFrame, rain_cols: list, perc_for_valid_month: int | float = 95
) -> pl.DataFrame:
    """
    Convert daily data to monthly whilst setting month to NaN if less than a given percentage of days is missing.

    Parameters
    ----------
    daily_data :
        Daily data to convert to monthly
    rain_cols :
        Columns with rainfall data
    perc_for_valid_month :
        Percentage of month needed to be classed as a valid month for the monthly group by

    Returns
    -------
    monthly_data :
        Monthly data

    """
    check_data_is_specific_time_res(daily_data, "daily")

    # 1. Make month and year column
    daily_data = make_month_and_year_col(daily_data)

    # 2. Calculate expected days in month
    daily_data = get_expected_days_in_month(daily_data)

    agg_expressions = [pl.len().alias("n_days"), pl.col("expected_days_in_month").first()]
    agg_expressions += [pl.col(col).sum().alias(col) for col in rain_cols]

    # 3. Group data into monthly
    monthly_data = (
        daily_data.group_by_dynamic("time", every="1mo", closed="right")
        .agg(agg_expressions)
        .filter(
            pl.col("n_days")
            >= (
                pl.col("expected_days_in_month") * perc_for_valid_month / 100
            )  # Ensure at least n% values for month are available
        )
        .drop("n_days", "expected_days_in_month")
    )

    return monthly_data


def extract_negative_values_from_data(data: pl.DataFrame, cols_to_extract_from: list) -> pl.DataFrame:
    """
    Extract negative values from data.

    Parameters
    ----------
    data :
        Rainfall data.
    cols_to_extract_from :
        Columns to extract negative values from

    Returns
    -------
    data :
        Data with only negative values or 0.

    """
    return data.select(
        [
            "time",
            *[
                pl.when(pl.col(col) <= 0).then(pl.col(col)).otherwise(None).alias(col)
                for col in cols_to_extract_from
                if col != "time"
            ],
        ]
    )


def extract_positive_values_from_data(data: pl.DataFrame, cols_to_extract_from: list) -> pl.DataFrame:
    """
    Extract positive values from data.

    Parameters
    ----------
    data :
        Rainfall data.
    cols_to_extract_from :
        Columns to extract positive values from

    Returns
    -------
    data :
        Data with only positive values or 0.

    """
    return data.select(
        [
            "time",
            *[
                pl.when(pl.col(col) >= 0).then(pl.col(col)).otherwise(None).alias(col)
                for col in cols_to_extract_from
                if col != "time"
            ],
        ]
    )


def format_timedelta_duration(td: datetime.timedelta) -> str:
    """
    Convert timedelta to custom strings.

    Parameters
    ----------
    td :
        Time delta to convert.

    Returns
    -------
    td :
        Human-readable timedelta string using largest unit (d, h, m, s).

    """
    total_seconds = int(td.total_seconds())

    if total_seconds % 86400 == 0:  # 86400 seconds in a day
        return f"{total_seconds // 86400}d"
    elif total_seconds % 3600 == 0:
        return f"{total_seconds // 3600}h"
    elif total_seconds % 60 == 0:
        return f"{total_seconds // 60}m"
    else:
        return f"{total_seconds}s"


def get_data_timestep_as_str(data: pl.DataFrame) -> str:
    """
    Get time step of data.

    Parameters
    ----------
    data :
        Data with time column

    Returns
    -------
    time_step :
        Time step of data i.e. '1h', '1d', '15mi'.

    """
    check_data_has_consistent_time_step(data)
    unique_timestep = get_data_timesteps(data)
    return format_timedelta_duration(unique_timestep[0])


def get_data_timesteps(data: pl.DataFrame) -> pl.Series:
    """
    Get data timesteps. Ideally the data should have 1.

    Parameters
    ----------
    data :
        Data with time column.

    Returns
    -------
    unique_timesteps :
        All unique time steps in data (timedelta).

    """
    data_timesteps = data.with_columns([pl.col("time").diff().alias("time_step")])
    unique_timesteps = data_timesteps["time_step"].drop_nulls().unique()
    return unique_timesteps


def get_dry_period_proportions(dry_period_days: int) -> dict:
    """
    Get dry period proportions.

    Parameters
    ----------
    dry_period_days :
        Length for of a "dry_spell" (default: 15 days)

    Returns
    -------
    fraction_dry_days :
        Dictionary with keys "1", "2", "3" with dry spell fractions

    """
    fraction_dry_days = {}
    for d in range(1, 3 + 1):
        fraction_dry_days[str(d)] = np.trunc((1.0 - (float(d) / dry_period_days)) * 10**2) / (10**2)
    return fraction_dry_days


def get_dry_spells(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Get dry spell column.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_dry_spells :
        Data with is_dry binary column

    """
    return data.with_columns(
        (pl.col(target_gauge_col) == 0).cast(pl.Int8()).alias("is_dry"),
    )


def get_expected_days_in_month(data: pl.DataFrame) -> pl.DataFrame:
    """
    Get expected number of days in a months within the data.

    Parameters
    ----------
    data :
        Data with 'year' and 'month' columns

    Returns
    -------
    data:
        Data with 'expected_days_in_month" column

    """
    # Use map_elements + calendar.monthrange to compute days in each month
    return data.with_columns(
        [
            pl.struct(["year", "month"])
            .map_elements(
                lambda x: calendar.monthrange(x["year"], x["month"])[1],
                return_dtype=pl.Int64,
            )
            .alias("expected_days_in_month")
        ]
    )


def get_normalised_diff(data: pl.DataFrame, target_col: str, other_col: str, diff_col_name: str) -> pl.DataFrame:
    """
    Ger normalised difference between two columns in data.

    Parameters
    ----------
    data :
        Data with columns
    target_col :
        Target column
    other_col :
        Other column.
    diff_col_name :
        New column name for difference column

    Returns
    -------
    data_w_norm_diff :
        Data with normalised diff

    """
    return data.with_columns(
        (normalise_data(pl.col(target_col)) - normalise_data(pl.col(other_col))).alias(diff_col_name)
    )


def make_month_and_year_col(data: pl.DataFrame) -> pl.DataFrame:
    """
    Make year and month columns for polars dataframe.

    Parameters
    ----------
    data :
        Data with time column

    Returns
    -------
    data :
        Data with year and month columns

    """
    return data.with_columns(
        [
            pl.col("time").dt.year().alias("year"),
            pl.col("time").dt.month().alias("month"),
        ]
    )


def normalise_data(data: pl.Series | pl.expr.Expr) -> pl.Series:
    """
    Normalise data to [0, 1].

    Parameters
    ----------
    data :
        Data with time column.

    Returns
    -------
    norm_data :
        Normalised data.

    """
    return (data - data.min()) / (data.max() - data.min())


def offset_data_by_time(data: pl.DataFrame, target_col: str, offset_in_time: int, time_res: str) -> pl.DataFrame:
    """
    Shift/offset data either backwards or forwards in time.

    Parameters
    ----------
    data :
        Data with column to offset in 'time'
    target_col :
        Column of data to offset
    offset_in_time :
        Amount to offset data by i.e. 1 for 1 day if time_res set to '1d'
    time_res :
        Time resolution like 'hourly', 'daily', '1h' or '1d'

    Returns
    -------
    data :
        Offset data by 'offset_in_time' amount

    """
    # 0. Check data is specific time_res
    check_data_is_specific_time_res(data, time_res=time_res)

    # 1. If time_res is like 'hourly' then get time res in a format that works with upsample i.e. '1d'
    time_res = TEMPORAL_CONVERSIONS.get(time_res, time_res)

    # 2. Upsample data to time_res to fill in gaps
    data = data.upsample("time", every=time_res)

    # 3. Shift data in time
    return data.with_columns(
        pl.col(target_col).last().over(pl.col("time").dt.truncate(time_res)).shift(offset_in_time),
    )


def replace_missing_vals_with_nan(
    data: pl.DataFrame,
    target_gauge_col: str,
    missing_val: int = None,
) -> pl.DataFrame:
    """
    Replace no data value with numpy.nan.

    Parameters
    ----------
    data :
        Rainfall data
    target_gauge_col :
        Column of rainfall
    missing_val :
        Missing value identifier

    Returns
    -------
    gdsr_data
        GDSR data with missing values replaced

    """
    if missing_val is None:
        return data.with_columns(
            pl.when(pl.col(target_gauge_col).is_null())
            .then(np.nan)
            .otherwise(pl.col(target_gauge_col))
            .alias(target_gauge_col)
        )
    else:
        return data.with_columns(
            pl.when((pl.col(target_gauge_col).is_null()) | (pl.col(target_gauge_col) == missing_val))
            .then(np.nan)
            .otherwise(pl.col(target_gauge_col))
            .alias(target_gauge_col)
        )
