#!/usr/bin/env python

"""Tests for neighbourhood quality control checks."""

from rainfallqc.checks import neighbourhood_checks

DEFAULT_RAIN_COL = "rain_mm"
DISTANCE_THRESHOLD = 50  # 50 km
OVERLAP_THRESHOLD = 365 * 3  # three years


def test_wet_neighbour_check_hourly(hourly_gdsr_network):
    assert len(hourly_gdsr_network) == 43824
    all_neighbour_cols = hourly_gdsr_network.columns[1:]  # exclude time
    neighbourhood_checks.wet_neighbour_check(
        hourly_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="hourly",
        wet_threshold=1.0,
    )


def test_wet_neighbour_check_daily(daily_gpcc_network):
    assert len(daily_gpcc_network) == 32142
    neighbourhood_checks.wet_neighbour_check(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_cols=[
            f"{DEFAULT_RAIN_COL}_tw_310",
            f"{DEFAULT_RAIN_COL}_tw_480",
            f"{DEFAULT_RAIN_COL}_tw_1283",
            f"{DEFAULT_RAIN_COL}_tw_3215",
            f"{DEFAULT_RAIN_COL}_tw_5610",
            f"{DEFAULT_RAIN_COL}_tw_6303",
        ],
        time_res="daily",
        wet_threshold=1.0,
    )


def test_make_num_neighbours_online_col(hourly_gdsr_network):
    all_neighbour_cols = hourly_gdsr_network.columns[1:]
    result = neighbourhood_checks.make_num_neighbours_online_col(
        hourly_gdsr_network, neighbouring_gauge_cols=all_neighbour_cols
    )
    assert result["n_neighbours_online"][0] == 8
    assert result["n_neighbours_online"][-1] == 10
