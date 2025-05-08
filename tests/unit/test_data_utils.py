#!/usr/bin/env python

"""Tests for time-series QC checks."""

from rainfallqc.utils import data_utils

DEFAULT_RAIN_COL = "rain_mm"


def test_check_data_has_consistent_time_step(hourly_gdsr_data):
    data_utils.check_data_has_consistent_time_step(hourly_gdsr_data)


def test_get_data_time_steps(hourly_gdsr_data):
    data_utils.get_data_time_step_as_str(hourly_gdsr_data)


def test_format_timedelta_duration():
    data_utils.format_timedelta_duration()


def test_get_data_time_step_as_str(hourly_gdsr_data):
    data_utils.get_data_time_step_as_str(hourly_gdsr_data)
