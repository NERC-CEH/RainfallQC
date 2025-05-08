#!/usr/bin/env python

"""Tests for time-series QC checks."""

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
        rain_intensity_threshold=1.0,
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 120

    result = timeseries_checks.daily_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
        rain_intensity_threshold=2.0,
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 72

    result = timeseries_checks.daily_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
        accumulation_multiplying_factor=4,
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 120

    result = timeseries_checks.daily_accumulations(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
        accumulation_threshold=0.5,
    )
    assert len(result.filter(pl.col("daily_accumulation") == 1)) == 2472
