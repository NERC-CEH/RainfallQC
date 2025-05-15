#!/usr/bin/env python

"""Tests for neighbourhood quality control checks."""

from rainfallqc.checks import neighbourhood_checks
from rainfallqc.utils import data_readers

DEFAULT_RAIN_COL = "rain_mm"
DISTANCE_THRESHOLD = 50  # 50 km
OVERLAP_THRESHOLD = 365 * 3  # three years


def test_wet_neighbour_check(hourly_gdsr_data):
    # Load network
    data_readers.GDSRNetworkReader(target_gauge_id="DE_00310", path_to_gdsr_dir="./tests/data/GDSR/")
    neighbourhood_checks.wet_neighbour_check(
        hourly_gdsr_data, rain_col=DEFAULT_RAIN_COL, target_gauge_id="DE_00310", time_res="hourly"
    )


#
# def test_wet_neighbour_check_daily(daily_gdsr_data, daily_gpcc_data):
#     neighbourhood_checks.wet_neighbour_check(daily_gdsr_data, time_res="daily")
#     neighbourhood_checks.wet_neighbour_check(daily_gpcc_data, time_res="daily")
