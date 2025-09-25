#!/usr/bin/env python

"""Tests all pyPWSQC converter."""

import numpy as np
import polars as pl
import xarray as xr

from rainfallqc.checks import pypwsqc_filters

DEFAULT_RAIN_COL = "rain_mm"


def test_run_bias_correction(hourly_gdsr_network):
    pass


def test_run_event_based_filter(hourly_gdsr_network):
    pass


def test_check_faulty_zeros(hourly_gdsr_network_no_prefix, gdsr_gauge_network):
    all_neighbour_cols = hourly_gdsr_network_no_prefix.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10

    result = pypwsqc_filters.check_faulty_zeros(
        hourly_gdsr_network_no_prefix,
        gdsr_gauge_network,
        neighbouring_gauge_ids=all_neighbour_cols,
        neighbour_metadata_gauge_id_col="station_id",
        time_res="1h",
        projection="EPSG:25832",
        nint=24,
        n_stat=5,
        max_distance_for_neighbours=50000,
        global_attributes={"title": "GSDR", "year": "2025"},
    )

    _, counts = np.unique(result["fz_flag"], return_counts=True)
    assert all([a == b for a, b in zip(counts, [19208, 418223, 809], strict=False)])


def test_check_high_influx_filter(hourly_gdsr_network):
    pass


def test_run_indicator_correlation(hourly_gdsr_network):
    pass


def test_run_peak_removal(hourly_gdsr_network):
    pass


def test_check_station_outlier(hourly_gdsr_network_no_prefix, gdsr_gauge_network):
    all_neighbour_cols = hourly_gdsr_network_no_prefix.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10

    result = pypwsqc_filters.check_station_outlier(
        hourly_gdsr_network_no_prefix,
        gdsr_gauge_network,
        neighbouring_gauge_ids=all_neighbour_cols,
        neighbour_metadata_gauge_id_col="station_id",
        time_res="1h",
        projection="EPSG:25832",
        evaluation_period=8064,
        mmatch=200,
        gamma=0.15,
        n_stat=5,
        max_distance_for_neighbours=50000,
        global_attributes={"title": "GSDR", "year": "2025"},
    )
    print(result)
    assert "so_flag" in result
    assert "gamma" in result
    _, counts = np.unique(result["so_flag"], return_counts=True)
    assert all([a == b for a, b in zip(counts, [98112, 329181, 10947], strict=False)])


def test_convert_neighbour_data_to_xarray(hourly_gdsr_network_no_prefix, gdsr_gauge_network):
    all_neighbour_cols = hourly_gdsr_network_no_prefix.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10

    neighbour_metadata = gdsr_gauge_network.filter(pl.col("station_id").is_in(all_neighbour_cols))

    result = pypwsqc_filters.convert_neighbour_data_to_xarray(
        hourly_gdsr_network_no_prefix,
        neighbour_metadata,
        projection="EPSG:25832",
        global_attributes={"title": "GSDR", "year": "2025"},
    )
    assert isinstance(result, xr.Dataset)
