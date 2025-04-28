#!/usr/bin/env python

"""Tests for rain gauge quality control checks."""

from rainfallqc.checks import comparison_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_R99_check(daily_gdsr_data):
    comparison_checks.check_annual_exceedance_ETCCDI_R99p(daily_gdsr_data, rain_col=DEFAULT_RAIN_COL)
