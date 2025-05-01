#!/usr/bin/env python

"""Tests for time-series QC checks."""

import polars as pl

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
