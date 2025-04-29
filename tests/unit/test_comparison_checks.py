#!/usr/bin/env python

"""Tests for rain gauge quality control checks."""

import polars as pl
import pytest

from rainfallqc.checks import comparison_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_check_annual_exceedance_etccdi_r99p(daily_gdsr_data, daily_gdsr_metadata):
    comparison_checks.check_annual_exceedance_etccdi_r99p(
        daily_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=daily_gdsr_metadata["latitude"],
        gauge_lon=daily_gdsr_metadata["longitude"],
    )


def test_check_annual_exceedance_etccdi_prcptot(daily_gdsr_data, daily_gdsr_metadata):
    comparison_checks.check_annual_exceedance_etccdi_prcptot(
        daily_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=daily_gdsr_metadata["latitude"],
        gauge_lon=daily_gdsr_metadata["longitude"],
    )


def test_check_daily_exceedance_of_rainfall_world_record(daily_gdsr_data):
    result = comparison_checks.check_exceedance_of_rainfall_world_record(
        daily_gdsr_data, rain_col=DEFAULT_RAIN_COL, time_res="daily"
    )
    assert len(result.filter(pl.col("world_record_check") == 4)) == 66


def test_check_hourly_exceedance_of_rainfall_world_record(hourly_gdsr_data):
    result = comparison_checks.check_exceedance_of_rainfall_world_record(
        hourly_gdsr_data, rain_col=DEFAULT_RAIN_COL, time_res="hourly"
    )
    assert len(result.filter(pl.col("world_record_check") == 4)) == 1051


def test_check_daily_exceedance_etccdi_rx1day(hourly_gdsr_data):
    result = comparison_checks.check_exceedance_of_rainfall_world_record(
        hourly_gdsr_data, rain_col=DEFAULT_RAIN_COL, time_res="hourly"
    )
    assert len(result.filter(pl.col("world_record_check") == 4)) == 1051


@pytest.mark.parametrize(
    "vals,max_ref_val,expected", [(1.5, 1, 4), (1.33, 1, 3), (1.2, 1, 2), (1.1, 1, 1), (0.9, 1, 0)]
)
def test_flag_exceedance_of_ref_val(vals, max_ref_val, expected):
    assert comparison_checks.flag_exceedance_of_ref_val(vals, max_ref_val) == expected
