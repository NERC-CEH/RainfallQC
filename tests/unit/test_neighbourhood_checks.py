#!/usr/bin/env python

"""Tests for neighbourhood quality control checks."""

import polars as pl
import pytest

from rainfallqc.checks import neighbourhood_checks
from rainfallqc.utils import data_utils

DEFAULT_RAIN_COL = "rain_mm"
DISTANCE_THRESHOLD = 50  # 50 km
OVERLAP_THRESHOLD = 365 * 3  # three years


def test_wet_neighbour_check_daily_gdsr(daily_gdsr_network):
    assert len(daily_gdsr_network) == 1825
    all_neighbour_cols = daily_gdsr_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_wet_neighbours(
        daily_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="daily",
        wet_threshold=0.5,
        min_n_neighbours=3,
    )
    assert len(result.columns) == 2
    assert result["wet_spell_flag_daily"].max() == 2.0
    assert len(result.filter(pl.col("wet_spell_flag_daily") == 1)) == 1


def test_check_wet_neighbour_daily_gpcc(daily_gpcc_network):
    assert len(daily_gpcc_network) == 32142
    all_neighbour_cols = daily_gpcc_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_wet_neighbours(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="daily",
        wet_threshold=0.5,
        min_n_neighbours=3,
    )
    assert len(result.columns) == 2
    assert result["wet_spell_flag_daily"].max() == 0

    result = neighbourhood_checks.check_wet_neighbours(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="daily",
        wet_threshold=0.5,
        min_n_neighbours=5,
        n_neighbours_ignored=4,
    )
    assert result["wet_spell_flag_daily"].max() == 1

    with pytest.raises(AssertionError):
        neighbourhood_checks.check_wet_neighbours(
            daily_gpcc_network,
            target_gauge_col="wrong",
            neighbouring_gauge_cols=all_neighbour_cols,
            time_res="daily",
            wet_threshold=1.0,
            min_n_neighbours=5,
        )

    with pytest.raises(ValueError):
        neighbourhood_checks.check_wet_neighbours(
            daily_gpcc_network,
            target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
            neighbouring_gauge_cols=[f"{DEFAULT_RAIN_COL}_tw_2483"],
            time_res="daily",
            wet_threshold=1.0,
            min_n_neighbours=5,
        )

    with pytest.raises(ValueError):
        neighbourhood_checks.check_wet_neighbours(
            daily_gpcc_network,
            target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
            neighbouring_gauge_cols=[],
            time_res="daily",
            wet_threshold=1.0,
            min_n_neighbours=5,
        )


def test_check_wet_neighbour_hourly(hourly_gdsr_network):
    assert len(hourly_gdsr_network) == 43824
    all_neighbour_cols = hourly_gdsr_network.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10
    result = neighbourhood_checks.check_wet_neighbours(
        hourly_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="hourly",
        wet_threshold=0.5,
        min_n_neighbours=3,
        hour_offset=7,
    )
    assert len(result) == 43824
    assert len(result.columns) == 2
    assert result["wet_spell_flag_hourly"].max() == 2.0
    assert len(result.filter(pl.col("wet_spell_flag_hourly") == 1)) == 24


def test_dry_neighbour_check_daily_gdsr(daily_gdsr_network):
    all_neighbour_cols = daily_gdsr_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_dry_neighbours(
        daily_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="daily",
        min_n_neighbours=5,
        dry_period_days=15,
    )
    assert len(result.columns) == 2
    assert result["dry_spell_flag_daily"].max() == 3.0
    assert len(result.filter(pl.col("dry_spell_flag_daily") == 3)) == 150


def test_check_dry_neighbour_daily_gpcc(daily_gpcc_network):
    assert len(daily_gpcc_network) == 32142
    all_neighbour_cols = daily_gpcc_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_dry_neighbours(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="daily",
        dry_period_days=15,
        min_n_neighbours=5,
    )
    assert len(result.columns) == 2
    assert result["dry_spell_flag_daily"].max() == 0


def test_check_dry_neighbour_hourly(hourly_gdsr_network):
    all_neighbour_cols = hourly_gdsr_network.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10
    result = neighbourhood_checks.check_dry_neighbours(
        hourly_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_cols=all_neighbour_cols,
        time_res="hourly",
        min_n_neighbours=3,
        dry_period_days=15,
        hour_offset=7,
    )
    assert result["dry_spell_flag_hourly"].max() == 3.0
    assert len(result.filter(pl.col("dry_spell_flag_hourly") == 3)) == 150 * 24


def test_check_monthly_neighbours(monthly_gdsr_network):
    all_neighbour_cols = monthly_gdsr_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_monthly_neighbours(
        monthly_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        neighbouring_gauge_cols=all_neighbour_cols,
        min_n_neighbours=3,
        n_neighbours_ignored=0,
    )
    assert len(result.filter(pl.col("majority_monthly_flag") == 1)) == 1
    assert len(result.filter(pl.col("majority_monthly_flag") == 5)) == 9


def test_check_monthly_neighbours_gpcc(monthly_gpcc_network):
    all_neighbour_cols = monthly_gpcc_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_monthly_neighbours(
        monthly_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_mw_310",
        neighbouring_gauge_cols=all_neighbour_cols,
        min_n_neighbours=3,
        n_neighbours_ignored=1,
    )
    assert len(result.filter(pl.col("majority_monthly_flag") > 0)) == 9


def test_check_timing_offset_gdsr(daily_gdsr_network):
    result = neighbourhood_checks.check_timing_offset(
        daily_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        time_res="daily",
    )
    assert result == 0

    result = neighbourhood_checks.check_timing_offset(
        daily_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        time_res="daily",
        offsets_to_check=(-5, 5),
    )
    assert result == 0


def test_check_timing_offset_gpcc(daily_gpcc_network):
    result = neighbourhood_checks.check_timing_offset(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_tw_310",
        time_res="daily",
    )
    assert result == 0

    # offset neighbour data by one day to pick up a +1 day offset
    offset_data = data_utils.offset_data_by_time(
        daily_gpcc_network, target_col=f"{DEFAULT_RAIN_COL}_tw_310", offset_in_time=1, time_res="daily"
    )
    result = neighbourhood_checks.check_timing_offset(
        offset_data,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_tw_310",
        time_res="daily",
    )
    assert result == 1


def test_check_nearest_neighbour_affinity_index_hourly(hourly_gdsr_network):
    result = neighbourhood_checks.check_neighbour_affinity_index(
        hourly_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
    )

    assert round(result, 2) == 0.81


def test_check_nearest_neighbour_affinity_index_daily(daily_gdsr_network, daily_gpcc_network):
    result = neighbourhood_checks.check_neighbour_affinity_index(
        daily_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
    )

    assert round(result, 2) == 0.95

    result = neighbourhood_checks.check_neighbour_affinity_index(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_tw_310",
    )

    assert round(result, 2) == 0.97


def test_check_neighbour_correlation_hourly(hourly_gdsr_network):
    result = neighbourhood_checks.check_neighbour_correlation(
        hourly_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
    )

    assert round(result, 2) == 0.03


def test_check_neighbour_correlation_daily(daily_gdsr_network, daily_gpcc_network):
    result = neighbourhood_checks.check_neighbour_correlation(
        daily_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
    )

    assert round(result, 2) == 0.01

    result = neighbourhood_checks.check_neighbour_correlation(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_tw_310",
    )

    assert round(result, 2) == 0.31


def test_check_daily_factor(daily_gdsr_network):
    result = neighbourhood_checks.check_daily_factor(
        daily_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        averaging_method="mean",
    )

    assert round(result, 2) == 4.47

    result = neighbourhood_checks.check_daily_factor(
        daily_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        averaging_method="median",
    )

    assert round(result, 2) == 1.71

    with pytest.raises(ValueError):
        neighbourhood_checks.check_daily_factor(
            daily_gdsr_network,
            target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
            neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
            averaging_method="mode",
        )


def test_check_monthly_factor(monthly_gdsr_network, monthly_gpcc_network):
    result = neighbourhood_checks.check_monthly_factor(
        monthly_gdsr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
    )
    assert round(result["monthly_factor_flag"].max(), 2) == 6
    assert len(result.filter(pl.col("monthly_factor_flag") > 0)) == 6

    result = neighbourhood_checks.check_monthly_factor(
        monthly_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_mw_2483",
        neighbouring_gauge_col=f"{DEFAULT_RAIN_COL}_mw_310",
    )

    assert round(result["monthly_factor_flag"].max(), 2) == 3
    assert len(result.filter(pl.col("monthly_factor_flag") > 0)) == 61


def test_make_num_neighbours_online_col(hourly_gdsr_network):
    all_neighbour_cols = hourly_gdsr_network.columns[1:]
    result = neighbourhood_checks.make_num_neighbours_online_col(
        hourly_gdsr_network, neighbouring_gauge_cols=all_neighbour_cols
    )
    assert result["n_neighbours_online"][0] == 8
    assert result["n_neighbours_online"][-1] == 10
