#!/usr/bin/env python

"""Tests for neighbourhood quality control checks."""

import pytest

from rainfallqc.checks import neighbourhood_checks

DEFAULT_RAIN_COL = "rain_mm"
DISTANCE_THRESHOLD = 50  # 50 km
OVERLAP_THRESHOLD = 365 * 3  # three years


def test_wet_neighbour_check_hourly(hourly_gdsr_network):
    assert len(hourly_gdsr_network) == 43824
    all_neighbour_cols = hourly_gdsr_network.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10
    result = neighbourhood_checks.wet_neighbour_check(
        hourly_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="hourly",
        wet_threshold=1.0,
        min_n_neighbours=5,
    )
    assert len(result.columns) == 12
    assert result["majority_wet_flag"].max() == 2
    assert result["majority_wet_flag"][357] == 2


def test_wet_neighbour_check_daily(daily_gpcc_network):
    assert len(daily_gpcc_network) == 32142
    all_neighbour_cols = daily_gpcc_network.columns[1:]  # exclude time

    result = neighbourhood_checks.wet_neighbour_check(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="daily",
        wet_threshold=1.0,
        min_n_neighbours=5,
    )
    assert len(result.columns) == 12
    assert result["majority_wet_flag"].max() == 0

    result = neighbourhood_checks.wet_neighbour_check(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="daily",
        wet_threshold=1.0,
        min_n_neighbours=5,
        n_neighbours_ignored=3,
    )
    assert result["majority_wet_flag"].max() == 1

    with pytest.raises(AssertionError):
        neighbourhood_checks.wet_neighbour_check(
            daily_gpcc_network,
            target_gauge_col="wrong",
            neighbouring_gauge_cols=all_neighbour_cols,
            time_res="daily",
            wet_threshold=1.0,
            min_n_neighbours=5,
        )


def test_make_num_neighbours_online_col(hourly_gdsr_network):
    all_neighbour_cols = hourly_gdsr_network.columns[1:]
    result = neighbourhood_checks.make_num_neighbours_online_col(
        hourly_gdsr_network, neighbouring_gauge_cols=all_neighbour_cols
    )
    assert result["n_neighbours_online"][0] == 8
    assert result["n_neighbours_online"][-1] == 10
