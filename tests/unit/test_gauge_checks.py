#!/usr/bin/env python

"""Tests for rain gauge quality control checks."""

import numpy.testing
import pytest

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
    years_k_top_2000 = gauge_checks.get_years_where_annual_mean_k_top_rows_are_zero(
        daily_gdsr_data, rain_col=DEFAULT_RAIN_COL, k=2000
    )
    assert len(years_k_top_5) == 0
    numpy.testing.assert_array_equal(years_k_top_2000, [2006, 2007, 2008, 2009])


def test_check_day_of_week_bias(daily_gdsr_data):
    week_bias_true = gauge_checks.check_temporal_bias(
        daily_gdsr_data, rain_col=DEFAULT_RAIN_COL, time_granularity="weekday"
    )
    assert week_bias_true == 0
    # week_bias_false = gauge_checks.check_day_of_week_bias(other_daily_gdsr_data, rain_col=DEFAULT_RAIN_COL)


def test_check_hour_of_day_bias(daily_gdsr_data):
    hour_bias_true = gauge_checks.check_temporal_bias(
        daily_gdsr_data, rain_col=DEFAULT_RAIN_COL, time_granularity="hour"
    )
    assert hour_bias_true == 0


def test_check_wrong_time_gran(daily_gdsr_data):
    with pytest.raises(ValueError):
        gauge_checks.check_temporal_bias(daily_gdsr_data, rain_col=DEFAULT_RAIN_COL, time_granularity="wrong")


def test_intermittency_check(daily_gdsr_data, gappy_daily_data):
    yr_list = gauge_checks.intermittency_check(daily_gdsr_data, rain_col=DEFAULT_RAIN_COL)
    numpy.testing.assert_array_equal(sorted(yr_list), [2006, 2010])

    yr_list = gauge_checks.intermittency_check(gappy_daily_data, rain_col=DEFAULT_RAIN_COL, no_data_threshold=2)
    numpy.testing.assert_array_equal(yr_list, 2006)


def test_breakpoints(daily_gdsr_data, gappy_daily_data):
    flag = gauge_checks.breakpoints_check(daily_gdsr_data, rain_col=DEFAULT_RAIN_COL)
    assert flag == 1

    flag = gauge_checks.breakpoints_check(gappy_daily_data, rain_col=DEFAULT_RAIN_COL)
    assert flag == 0
