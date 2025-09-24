#!/usr/bin/env python

"""Tests all pyPWSQC converter."""

from rainfallqc.checks import pypwsqc_filters


def test_run_bias_correction(hourly_gdsr_network):
    pass


def test_run_event_based_filter(hourly_gdsr_network):
    pass


def test_check_faulty_zeros(hourly_gdsr_network):
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
