#!/usr/bin/env python

"""Tests for rain gauge quality control checks."""

from rainfallqc.checks import gauge_checks


def test_get_years_where_percentiles_are_zero(daily_gdsr_data):
    gauge_checks.get_years_where_percentiles_are_zero(daily_gdsr_data)
