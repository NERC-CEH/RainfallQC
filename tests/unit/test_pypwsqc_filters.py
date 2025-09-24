#!/usr/bin/env python

"""Tests all pyPWSQC converter."""

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
        nint=6,
        n_stat=5,
        global_attributes={"title": "GSDR", "year": "2025"},
    )
    print(result)
    # assert False


def test_check_high_influx_filter(hourly_gdsr_network):
    pass


def test_run_indicatior_correlation(hourly_gdsr_network):
    pass


def test_run_peak_removal(hourly_gdsr_network):
    pass


def test_check_station_outlier(hourly_gdsr_network):
    pass
