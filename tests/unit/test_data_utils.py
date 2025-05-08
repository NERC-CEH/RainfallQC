#!/usr/bin/env python

"""Tests for time-series QC checks."""

import datetime

import pytest

from rainfallqc.utils import data_utils

DEFAULT_RAIN_COL = "rain_mm"


def test_check_data_has_consistent_time_step(hourly_gdsr_data, inconsistent_timestep_data):
    data_utils.check_data_has_consistent_time_step(hourly_gdsr_data)
    with pytest.raises(ValueError):
        data_utils.check_data_has_consistent_time_step(
            data_utils.check_data_has_consistent_time_step(inconsistent_timestep_data)
        )


def test_get_data_timesteps(hourly_gdsr_data, inconsistent_timestep_data):
    data_utils.get_data_timesteps(hourly_gdsr_data)


def test_format_timedelta_duration():
    result = data_utils.format_timedelta_duration(datetime.timedelta(seconds=3600))
    assert result == "1h"

    result = data_utils.format_timedelta_duration(datetime.timedelta(seconds=360))
    assert result == "6m"

    result = data_utils.format_timedelta_duration(datetime.timedelta(seconds=36))
    assert result == "36s"


def test_get_data_timestep_as_str(hourly_gdsr_data, inconsistent_timestep_data):
    data_utils.get_data_timestep_as_str(hourly_gdsr_data)
