#!/usr/bin/env python

"""Tests all pyPWSQC converter."""

from rainfallqc.checks import pypwsqc_filters

DEFAULT_RAIN_COL = "rain_mm"


def test_run_bias_correction(hourly_gdsr_network):
    pass


def test_run_event_based_filter(hourly_gdsr_network):
    pass


def test_check_faulty_zeros(hourly_gdsr_network, gdsr_gauge_network):
    all_neighbour_cols = hourly_gdsr_network.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10
    result = pypwsqc_filters.check_faulty_zeros(hourly_gdsr_network)
    assert result


def test_check_high_influx_filter(hourly_gdsr_network):
    pass


def test_run_indicatior_correlation(hourly_gdsr_network):
    pass


def test_run_peak_removal(hourly_gdsr_network):
    pass


def test_check_station_outlier(hourly_gdsr_network):
    pass
