#!/usr/bin/env python

"""Tests for time-series QC checks."""

import numpy as np
import polars as pl
import pytest

from rainfallqc.checks import timeseries_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_dry_period_cdd_check_hourly(hourly_gsdr_data, gsdr_metadata):
    result = timeseries_checks.check_dry_period_cdd(
        hourly_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        time_res="hourly",
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("dry_spell_flag") == 4)) == 2200

    with pytest.raises(ValueError):
        timeseries_checks.check_dry_period_cdd(
            hourly_gsdr_data,
            target_gauge_col=DEFAULT_RAIN_COL,
            time_res="decadal",
            gauge_lat=gsdr_metadata["latitude"],
            gauge_lon=gsdr_metadata["longitude"],
        )


def test_dry_period_cdd_check_daily_gpcc(daily_gpcc_data, gsdr_metadata):
    result = timeseries_checks.check_dry_period_cdd(
        daily_gpcc_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        time_res="daily",
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("dry_spell_flag") > 0)) == 0


def test_dry_period_cdd_check_daily_gsdr(daily_gsdr_data, gsdr_metadata):
    result = timeseries_checks.check_dry_period_cdd(
        daily_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        time_res="daily",
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("dry_spell_flag") == 4)) == 91


def test_daily_accumulations(hourly_gsdr_data, gsdr_metadata):
    result = timeseries_checks.check_daily_accumulations(
        hourly_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 432

    result = timeseries_checks.check_daily_accumulations(
        hourly_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
        accumulation_multiplying_factor=4.0,
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 312

    result = timeseries_checks.check_daily_accumulations(
        hourly_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
        accumulation_threshold=0.5,
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 2472


def test_get_accumulation_threshold():
    result = timeseries_checks.get_accumulation_threshold(2, 1, 1)
    assert result == 2
    result = timeseries_checks.get_accumulation_threshold(np.nan, 1, 1)
    assert result == 1
    result = timeseries_checks.get_accumulation_threshold(2, np.nan, 1)
    assert result == 2


def test_monthly_accumulations(hourly_gsdr_data, gsdr_metadata):
    result = timeseries_checks.check_monthly_accumulations(
        hourly_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("monthly_accumulation") == 2)) == 22
    result = timeseries_checks.check_monthly_accumulations(
        hourly_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
        accumulation_threshold=5.0,
    )
    assert len(result.filter(pl.col("monthly_accumulation") == 2)) == 55

    result = timeseries_checks.check_monthly_accumulations(
        hourly_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
        wet_day_threshold=12.0,
        accumulation_threshold=11,
    )
    assert len(result.filter(pl.col("monthly_accumulation") == 2)) == 23


def test_monthly_accumulations_daily_data(daily_gsdr_data, gsdr_metadata):
    result = timeseries_checks.check_monthly_accumulations(
        daily_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("monthly_accumulation") > 0)) == 36


def test_streaks_check(hourly_gsdr_data, gsdr_metadata):
    result = timeseries_checks.check_streaks(
        hourly_gsdr_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        gauge_lat=gsdr_metadata["latitude"],
        gauge_lon=gsdr_metadata["longitude"],
        data_resolution=gsdr_metadata["resolution"],
    )
    assert len(result.filter(pl.col("streak_flag1") == 1)) == 33
    assert len(result.filter(pl.col("streak_flag3") == 3)) == 455
    assert len(result.filter(pl.col("streak_flag4") == 4)) == 432
    assert len(result.filter(pl.col("streak_flag5") == 5)) == 120


def test_get_streaks_of_repeated_values(hourly_gsdr_data):
    result = timeseries_checks.get_streaks_of_repeated_values(
        hourly_gsdr_data,
        data_col=DEFAULT_RAIN_COL,
    )
    assert result["streak_id"].unique().len() == 8775


def test_flag_streaks_exceeding_data_resolution(hourly_gsdr_data, gsdr_metadata):
    streak_data = timeseries_checks.get_streaks_of_repeated_values(hourly_gsdr_data, DEFAULT_RAIN_COL)
    result = timeseries_checks.flag_streaks_exceeding_data_resolution(
        streak_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        streak_length=12,
        data_resolution=gsdr_metadata["resolution"],
    )
    assert len(result.filter(pl.col("streak_flag3") > 0)) == 455

    result = timeseries_checks.flag_streaks_exceeding_data_resolution(
        streak_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        streak_length=36,
        data_resolution=gsdr_metadata["resolution"],
    )
    assert len(result.filter(pl.col("streak_flag3") > 0)) == 288


def test_flag_streaks_exceeding_wet_day_rainfall_threshold(hourly_gsdr_data, gsdr_metadata):
    streak_data = timeseries_checks.get_streaks_of_repeated_values(hourly_gsdr_data, DEFAULT_RAIN_COL)
    result = timeseries_checks.flag_streaks_exceeding_wet_day_rainfall_threshold(
        streak_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        streak_length=12,
        accumulation_threshold=11,
    )
    assert len(result.filter(pl.col("streak_flag1") > 0)) == 23

    result = timeseries_checks.flag_streaks_exceeding_wet_day_rainfall_threshold(
        streak_data,
        target_gauge_col=DEFAULT_RAIN_COL,
        streak_length=6,
        accumulation_threshold=6,
    )
    assert len(result.filter(pl.col("streak_flag1") > 0)) == 71


def test_flag_n_hours_accumulation_based_on_threshold(hourly_gsdr_data):
    test_data = pl.Series([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 200])
    result = timeseries_checks.flag_n_hours_accumulation_based_on_threshold(
        period_rain_vals=test_data, accumulation_threshold=11.0, n_hours=24
    )
    assert result == 1

    none_data = pl.Series([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 200])
    result = timeseries_checks.flag_n_hours_accumulation_based_on_threshold(
        period_rain_vals=none_data, accumulation_threshold=11.0, n_hours=24
    )
    assert result == 0
