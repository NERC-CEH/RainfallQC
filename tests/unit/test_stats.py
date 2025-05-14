#!/usr/bin/env python

"""Test statistics."""

import polars as pl

from rainfallqc.utils import stats

DEFAULT_RAIN_COL = "rain_mm"


def test_pettitt_test(example_array):
    tau, p = stats.pettitt_test(example_array)
    assert tau == 6
    assert round(p, 2) == 0.03


def test_pettitt_test_pl(example_array):
    example_series = pl.Series(example_array)
    tau, p = stats.pettitt_test(example_series)
    assert tau == 6
    assert round(p, 2) == 0.03


def test_simple_precip_intensity_index(hourly_gdsr_data):
    result = stats.simple_precip_intensity_index(hourly_gdsr_data, rain_col=DEFAULT_RAIN_COL, wet_day_threshold=1.0)
    assert round(result, 1) == 8.5
    result = stats.simple_precip_intensity_index(hourly_gdsr_data, rain_col=DEFAULT_RAIN_COL, wet_day_threshold=5.0)
    assert round(result, 1) == 50.4
    result = stats.simple_precip_intensity_index(hourly_gdsr_data, rain_col=DEFAULT_RAIN_COL, wet_day_threshold=0.5)
    assert round(result, 1) == 5.6


def test_affinity_index(test_binary_data):
    result = stats.affinity_index(test_binary_data, binary_col="col1")
    assert round(result, 2) == 0.53


def test_gauge_correlation(gauge_comparison_data):
    result = stats.gauge_correlation(gauge_comparison_data, target_col="gauge1", other_col="gauge2")
    assert round(result, 2) == 0.72


def test_factor_diff(gauge_comparison_data):
    result = stats.factor_diff(gauge_comparison_data, target_col="gauge1", other_col="gauge2")
    assert round(result["factor_diff"][5], 2) == 1.90
