#!/usr/bin/env python

"""Tests for neighbourhood quality control checks."""

import numpy as np
import polars as pl
import pytest

from rainfallqc.checks import neighbourhood_checks
from rainfallqc.utils import data_utils

DEFAULT_RAIN_COL = "rain_mm"
DISTANCE_THRESHOLD = 50  # 50 km
OVERLAP_THRESHOLD = 365 * 3  # three years


def test_wet_neighbour_check_daily_gsdr(daily_gsdr_network):
    assert len(daily_gsdr_network) == 1825
    all_neighbour_cols = daily_gsdr_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_wet_neighbours(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        list_of_nearest_stations=all_neighbour_cols,
        time_res="daily",
        wet_threshold=0.5,
        min_n_neighbours=3,
    )
    assert len(result.columns) == 2
    assert result["wet_spell_flag_daily"].max() == 2.0
    assert len(result.filter(pl.col("wet_spell_flag_daily") == 1)) == 2


def test_wet_neighbour_check_problematic_data(daily_gsdr_network):
    assert len(daily_gsdr_network) == 1825
    daily_gsdr_network = daily_gsdr_network.with_columns(rain_mm_DE_test=0.0)
    all_neighbour_cols = daily_gsdr_network.columns[1:]  # exclude time
    result = neighbourhood_checks.check_wet_neighbours(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        list_of_nearest_stations=all_neighbour_cols,
        time_res="daily",
        wet_threshold=0.5,
        min_n_neighbours=3,
    )
    assert result["wet_spell_flag_daily"].max() == 2.0


def test_check_wet_neighbour_daily_gpcc(daily_gpcc_network):
    assert len(daily_gpcc_network) == 32142
    all_neighbour_cols = daily_gpcc_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_wet_neighbours(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        list_of_nearest_stations=all_neighbour_cols,
        time_res="daily",
        wet_threshold=0.5,
        min_n_neighbours=3,
    )
    assert len(result.columns) == 2
    assert result["wet_spell_flag_daily"].max() == 0

    result = neighbourhood_checks.check_wet_neighbours(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        list_of_nearest_stations=all_neighbour_cols,
        time_res="daily",
        wet_threshold=0.5,
        min_n_neighbours=5,
        n_neighbours_ignored=4,
    )
    assert result["wet_spell_flag_daily"].max() == 3.0

    with pytest.raises(ValueError):
        neighbourhood_checks.check_wet_neighbours(
            daily_gpcc_network,
            target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
            list_of_nearest_stations=[f"{DEFAULT_RAIN_COL}_tw_2483"],
            time_res="daily",
            wet_threshold=1.0,
            min_n_neighbours=5,
        )

    with pytest.raises(ValueError):
        neighbourhood_checks.check_wet_neighbours(
            daily_gpcc_network,
            target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
            list_of_nearest_stations=[],
            time_res="daily",
            wet_threshold=1.0,
            min_n_neighbours=5,
        )


def test_check_wet_neighbour_hourly(hourly_gsdr_network):
    assert len(hourly_gsdr_network) == 43824
    all_neighbour_cols = hourly_gsdr_network.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10
    result = neighbourhood_checks.check_wet_neighbours(
        hourly_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        list_of_nearest_stations=all_neighbour_cols,
        time_res="hourly",
        wet_threshold=0.5,
        min_n_neighbours=3,
        hour_offset=7,
    )
    assert len(result) == 43824
    assert len(result.columns) == 2
    assert result["wet_spell_flag_hourly"].max() == 2.0
    assert len(result.filter(pl.col("wet_spell_flag_hourly") == 1)) == 48


def test_dry_neighbour_check_daily_gsdr(daily_gsdr_network):
    all_neighbour_cols = daily_gsdr_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_dry_neighbours(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        list_of_nearest_stations=all_neighbour_cols,
        time_res="daily",
        min_n_neighbours=5,
        dry_period_days=15,
    )
    assert len(result.columns) == 2
    assert result["dry_spell_flag_daily"].max() == 3.0
    assert len(result.filter(pl.col("dry_spell_flag_daily") == 3)) == 149

    daily_gsdr_network = daily_gsdr_network.with_columns(nan_col=np.nan)

    neighbourhood_checks.check_dry_neighbours(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        list_of_nearest_stations=[f"{DEFAULT_RAIN_COL}_DE_02483", "nan_col", f"{DEFAULT_RAIN_COL}_DE_00310"],
        time_res="daily",
        min_n_neighbours=5,
        dry_period_days=15,
    )


def test_check_dry_neighbour_daily_gpcc(daily_gpcc_network):
    assert len(daily_gpcc_network) == 32142
    all_neighbour_cols = daily_gpcc_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_dry_neighbours(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        list_of_nearest_stations=all_neighbour_cols,
        time_res="daily",
        dry_period_days=15,
        min_n_neighbours=5,
    )
    assert len(result.columns) == 2
    assert result["dry_spell_flag_daily"].max() == 0


def test_check_dry_neighbour_hourly(hourly_gsdr_network):
    all_neighbour_cols = hourly_gsdr_network.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10
    result = neighbourhood_checks.check_dry_neighbours(
        hourly_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        list_of_nearest_stations=all_neighbour_cols,
        time_res="hourly",
        min_n_neighbours=3,
        dry_period_days=15,
        hour_offset=7,
    )
    assert result["dry_spell_flag_hourly"].max() == 3.0
    assert len(result.filter(pl.col("dry_spell_flag_hourly") == 3)) == 149 * 24


def test_check_monthly_neighbours(monthly_gsdr_network):
    all_neighbour_cols = monthly_gsdr_network.columns[1:]  # exclude time

    result = neighbourhood_checks.check_monthly_neighbours(
        monthly_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_00310",
        list_of_nearest_stations=all_neighbour_cols,
        min_n_neighbours=3,
        n_neighbours_ignored=0,
    )
    assert len(result.filter(pl.col("majority_monthly_flag") == 1)) == 1
    assert len(result.filter(pl.col("majority_monthly_flag") == 5)) == 9


def test_check_monthly_neighbours_gpcc(monthly_gpcc_network):
    all_neighbour_cols = monthly_gpcc_network.columns[1:]  # exclude time

    with pytest.raises(ValueError):
        neighbourhood_checks.check_monthly_neighbours(
            monthly_gpcc_network.with_columns(
                (pl.col(f"{DEFAULT_RAIN_COL}_mw_310") - 10).alias(f"{DEFAULT_RAIN_COL}_mw_310")
            ),  # introduce some negative values
            target_gauge_col=f"{DEFAULT_RAIN_COL}_mw_310",
            list_of_nearest_stations=all_neighbour_cols,
            min_n_neighbours=3,
            n_neighbours_ignored=1,
        )

    monthly_gpcc_network = monthly_gpcc_network.with_columns(
        pl.col(f"{DEFAULT_RAIN_COL}_mw_310").abs().alias(f"{DEFAULT_RAIN_COL}_mw_310")
    )  # ensure no nulls in target gauge

    result = neighbourhood_checks.check_monthly_neighbours(
        monthly_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_mw_310",
        list_of_nearest_stations=all_neighbour_cols,
        min_n_neighbours=3,
        n_neighbours_ignored=1,
    )
    assert len(result.filter(pl.col("majority_monthly_flag") > 0)) == 12


def test_check_timing_offset_gsdr(daily_gsdr_network):
    result = neighbourhood_checks.check_timing_offset(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
        time_res="daily",
    )
    assert result == 0

    result = neighbourhood_checks.check_timing_offset(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
        time_res="daily",
        offsets_to_check=(-5, 5),
    )
    assert result == 0


def test_check_timing_offset_gpcc(daily_gpcc_network):
    result = neighbourhood_checks.check_timing_offset(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_tw_310",
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
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_tw_310",
        time_res="daily",
    )
    assert result == 1


def test_check_nearest_neighbour_affinity_index_hourly(hourly_gsdr_network):
    result = neighbourhood_checks.check_neighbour_affinity_index(
        hourly_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
    )

    assert round(result, 2) == 0.81


def test_check_nearest_neighbour_affinity_index_daily(daily_gsdr_network, daily_gpcc_network):
    result = neighbourhood_checks.check_neighbour_affinity_index(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
    )

    assert round(result, 2) == 0.95

    result = neighbourhood_checks.check_neighbour_affinity_index(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_tw_310",
    )

    assert round(result, 2) == 0.97


def test_check_neighbour_correlation_hourly(hourly_gsdr_network):
    result = neighbourhood_checks.check_neighbour_correlation(
        hourly_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
    )

    assert round(result, 2) == 0.03


def test_check_neighbour_correlation_daily(daily_gsdr_network, daily_gpcc_network):
    result = neighbourhood_checks.check_neighbour_correlation(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
    )

    assert round(result, 2) == 0.01

    result = neighbourhood_checks.check_neighbour_correlation(
        daily_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_tw_2483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_tw_310",
    )

    assert round(result, 2) == 0.85


def test_check_daily_factor(daily_gsdr_network):
    result = neighbourhood_checks.check_daily_factor(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
        averaging_method="mean",
    )

    assert round(result, 2) == 3.69

    result = neighbourhood_checks.check_daily_factor(
        daily_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
        averaging_method="median",
    )

    assert round(result, 2) == 1.74

    with pytest.raises(ValueError):
        neighbourhood_checks.check_daily_factor(
            daily_gsdr_network,
            target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
            nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
            averaging_method="mode",
        )


def test_check_monthly_factor(monthly_gsdr_network, monthly_gpcc_network):
    result = neighbourhood_checks.check_monthly_factor(
        monthly_gsdr_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_DE_02483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_DE_00310",
    )
    assert round(result["monthly_factor_flag"].max(), 2) == 6
    assert len(result.filter(pl.col("monthly_factor_flag") > 0)) == 6

    result = neighbourhood_checks.check_monthly_factor(
        monthly_gpcc_network,
        target_gauge_col=f"{DEFAULT_RAIN_COL}_mw_2483",
        nearest_neighbour=f"{DEFAULT_RAIN_COL}_mw_310",
    )

    assert round(result["monthly_factor_flag"].max(), 2) == 3
    assert len(result.filter(pl.col("monthly_factor_flag") > 0)) == 61


def test_make_num_neighbours_online_col(hourly_gsdr_network):
    all_neighbour_cols = hourly_gsdr_network.columns[1:]
    result = neighbourhood_checks.make_num_neighbours_online_col(
        hourly_gsdr_network, list_of_nearest_stations=all_neighbour_cols
    )
    assert result["n_neighbours_online"][0] == 8
    assert result["n_neighbours_online"][-1] == 10
