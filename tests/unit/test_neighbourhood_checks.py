#!/usr/bin/env python

"""Tests for neighbourhood quality control checks."""

from rainfallqc.checks import neighbourhood_checks

DEFAULT_RAIN_COL = "rain_mm"
DISTANCE_THRESHOLD = 50  # 50 km
OVERLAP_THRESHOLD = 365 * 3  # three years


def test_wet_neighbour_check_hourly(hourly_gdsr_network):
    assert len(hourly_gdsr_network) == 43824
    neighbourhood_checks.wet_neighbour_check(
        hourly_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        neighbouring_gauge_cols=[f"{DEFAULT_RAIN_COL}_DE_00390", f"{DEFAULT_RAIN_COL}_DE_06303"],
        time_res="hourly",
    )


def test_wet_neighbour_check_daily(daily_gpcc_network):
    assert len(daily_gpcc_network) == 32142
    neighbourhood_checks.wet_neighbour_check(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_310",
        neighbouring_gauge_cols=[f"{DEFAULT_RAIN_COL}_tw_480", f"{DEFAULT_RAIN_COL}_tw_1283"],
        time_res="daily",
    )


#
# def test_wet_neighbour_check_daily(daily_gdsr_data, daily_gpcc_data):
#     neighbourhood_checks.wet_neighbour_check(daily_gdsr_data, time_res="daily")
#     neighbourhood_checks.wet_neighbour_check(daily_gpcc_data, time_res="daily")
