#!/usr/bin/env python

"""Tests for time-series QC checks."""

from rainfallqc.checks import timeseries_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_dry_period_cdd_check_hourly(hourly_gdsr_data, gdsr_metadata):
    timeseries_checks.dry_period_cdd_check(
        hourly_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        time_res="hourly",
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
    )


def test_dry_period_cdd_check_daily(daily_gdsr_data, gdsr_metadata):
    timeseries_checks.dry_period_cdd_check(
        daily_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        time_res="daily",
        gauge_lat=gdsr_metadata["latitude"],
        gauge_lon=gdsr_metadata["longitude"],
    )
