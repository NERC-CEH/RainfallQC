#!/usr/bin/env python

"""Tests for rain gauge quality control checks."""

import pytest

from rainfallqc.checks import comparison_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_R99_check(daily_gdsr_data, daily_gdsr_metadata):
    comparison_checks.check_annual_exceedance_ETCCDI_R99p(
        daily_gdsr_data,
        rain_col=DEFAULT_RAIN_COL,
        gauge_lat=daily_gdsr_metadata["latitude"],
        gauge_lon=daily_gdsr_metadata["longitude"],
    )


@pytest.mark.parametrize(
    "vals,max_ref_val,expected", [(1.5, 1, 4), (1.33, 1, 3), (1.2, 1, 2), (1.1, 1, 1), (0.9, 1, 0)]
)
def test_exceedance_check(vals, max_ref_val, expected):
    assert comparison_checks.exceedance_check(vals, max_ref_val) == expected
