#!/usr/bin/env python

"""Tests for time-series QC checks."""

from rainfallqc.utils import data_utils

DEFAULT_RAIN_COL = "rain_mm"


def test_get_data_time_step_as_str(hourly_gdsr_data):
    data_utils.get_data_time_step_as_str(hourly_gdsr_data)
