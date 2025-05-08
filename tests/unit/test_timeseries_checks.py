#!/usr/bin/env python

"""Tests for time-series QC checks."""

import numpy as np
import polars as pl
import pytest

from rainfallqc.checks import timeseries_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_dry_period_cdd_check_hourly(hourly_gdsr_data, gdsr_metadata):
    result = timeseries_checks.dry_period_cdd_check(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        time_res="hourly",
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("dry_spell_flag") == 4)) == 2200

    with pytest.raises(ValueError):
        timeseries_checks.dry_period_cdd_check(
            hourly_gdsr_data,
            rain_col=DEFAULT_RAIN_COL,
            time_res="decadal",
            gauge_lat=gdsr_metadata["latitude"],
            gauge_lon=gdsr_metadata["longitude"],
        )


def test_dry_period_cdd_check_daily_gpcc(daily_gpcc_data, gdsr_metadata):
    result = timeseries_checks.dry_period_cdd_check(
        daily_gpcc_data,
        rain_col=DEFAULT_RAIN_COL,
        time_res="daily",
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("dry_spell_flag") > 0)) == 0


def test_dry_period_cdd_check_daily_gdsr(daily_gdsr_data, gdsr_metadata):
    result = timeseries_checks.dry_period_cdd_check(
        daily_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        time_res="daily",
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("dry_spell_flag") == 4)) == 91


def test_daily_accumulations(hourly_gdsr_data, gdsr_metadata):
    result = timeseries_checks.daily_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
        wet_day_threshold=1.0,
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 432

    result = timeseries_checks.daily_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
        accumulation_multiplying_factor=4,
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 168

    result = timeseries_checks.daily_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
        accumulation_multiplying_factor=4,
        wet_day_threshold=10,
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 10

    result = timeseries_checks.daily_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
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


def test_monthly_accumulations(hourly_gdsr_data, gdsr_metadata):
    result = timeseries_checks.monthly_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("monthly_accumulation") == 2)) == 22
    result = timeseries_checks.monthly_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
        accumulation_threshold=5.0,
    )
    assert len(result.filter(pl.col("monthly_accumulation") == 2)) == 55

    result = timeseries_checks.monthly_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
        wet_day_threshold=12.0,
        accumulation_threshold=11,
    )
    assert len(result.filter(pl.col("monthly_accumulation") == 2)) == 23


def test_monthly_accumulations_daily_data(daily_gdsr_data, gdsr_metadata):
    result = timeseries_checks.monthly_accumulations(
        daily_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
    )
    assert len(result.filter(pl.col("monthly_accumulation") > 0)) == 2


def test_streaks_check(hourly_gdsr_data, gdsr_metadata):
    timeseries_checks.streaks_check(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
    )


def test_get_streaks_of_repeated_values(hourly_gdsr_data):
    result = timeseries_checks.get_streaks_of_repeated_values(
        hourly_gdsr_data,
        data_col=DEFAULT_RAIN_COL,
    )
    assert result["streak_id"].unique().len() == 8775
