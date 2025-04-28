#!/usr/bin/env python

"""Tests for rain gauge quality control checks."""

from rainfallqc.checks import comparison_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_R99_check():
    comparison_checks.check_annual_exceedance_ETCCDI_R99p()
