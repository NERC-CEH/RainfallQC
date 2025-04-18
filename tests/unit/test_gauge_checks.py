#!/usr/bin/env python

"""Tests for rain gauge quality control checks."""

import numpy.testing

from rainfallqc.checks import gauge_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_get_years_where_nth_percentile_is_zero(daily_gdsr_data):
    years_95th = gauge_checks.get_years_where_nth_percentile_is_zero(
        daily_gdsr_data, rain_col=DEFAULT_RAIN_COL, quantile=0.95
    )
    years_50th = gauge_checks.get_years_where_nth_percentile_is_zero(
        daily_gdsr_data, rain_col=DEFAULT_RAIN_COL, quantile=0.5
    )

    assert len(years_95th) == 0
    numpy.testing.assert_array_equal(years_50th, [2006, 2007, 2008, 2009, 2010])


def test_get_years_where_annual_mean_k_top_rows_are_zero(daily_gdsr_data):
    years_k_top_5 = gauge_checks.get_years_where_annual_mean_k_top_rows_are_zero(
        daily_gdsr_data, rain_col=DEFAULT_RAIN_COL, k=5
    )
    years_k_top_1600 = gauge_checks.get_years_where_annual_mean_k_top_rows_are_zero(
        daily_gdsr_data, rain_col=DEFAULT_RAIN_COL, k=1600
    )
    assert len(years_k_top_5) == 0
    numpy.testing.assert_array_equal(years_k_top_1600, [2006, 2008, 2010])
