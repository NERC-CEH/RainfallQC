#!/usr/bin/env python

"""Tests for time-series QC checks."""

from rainfallqc.checks import timeseries_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_dry_period_cdd_check(hourly_gdsr_data, gdsr_metadata):
    timeseries_checks.dry_period_cdd_check(
        hourly_gdsr_data, rain_col=DEFAULT_RAIN_COL, gauge_lat=gdsr_metadata["lat"], gauge_lon=gdsr_metadata["lon"]
    )
