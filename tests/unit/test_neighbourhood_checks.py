#!/usr/bin/env python

"""Tests for neighbourhood quality control checks."""

from rainfallqc.checks import neighbourhood_checks

DEFAULT_RAIN_COL = "rain_mm"
DISTANCE_THRESHOLD = 50  # 50 km
OVERLAP_THRESHOLD = 365 * 3  # three years


def test_wet_neighbour_check_daily(daily_gpcc_network):
    assert len(daily_gpcc_network) == 32142
    neighbourhood_checks.wet_neighbour_check(
        daily_gpcc_network, target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_{310}", time_res="daily"
    )


#
# def test_wet_neighbour_check_daily(daily_gdsr_data, daily_gpcc_data):
#     neighbourhood_checks.wet_neighbour_check(daily_gdsr_data, time_res="daily")
#     neighbourhood_checks.wet_neighbour_check(daily_gpcc_data, time_res="daily")
