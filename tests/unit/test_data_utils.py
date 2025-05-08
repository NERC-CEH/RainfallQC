#!/usr/bin/env python

"""Tests for time-series QC checks."""

import datetime

import pytest

from rainfallqc.utils import data_utils

DEFAULT_RAIN_COL = "rain_mm"


def test_check_data_has_consistent_time_step(hourly_gdsr_data, inconsistent_timestep_data):
    data_utils.check_data_has_consistent_time_step(hourly_gdsr_data)
    with pytest.raises(ValueError):
        data_utils.check_data_has_consistent_time_step(inconsistent_timestep_data)


def test_check_data_is_specific_time_res(hourly_gdsr_data):
    data_utils.check_data_is_specific_time_res(hourly_gdsr_data, time_res="1h")
    with pytest.raises(TypeError):
        data_utils.check_data_is_specific_time_res(hourly_gdsr_data, time_res=120)
    with pytest.raises(ValueError):
        data_utils.check_data_is_specific_time_res(hourly_gdsr_data, time_res="1d")


def test_get_data_timesteps(hourly_gdsr_data, inconsistent_timestep_data):
    result = data_utils.get_data_timesteps(hourly_gdsr_data)
    assert len(result) == 1
    assert result[0] == datetime.timedelta(seconds=3600)
    result = data_utils.get_data_timesteps(inconsistent_timestep_data)
    assert len(result) == 3
    assert result[0] == datetime.timedelta(seconds=60)


def test_format_timedelta_duration():
    result = data_utils.format_timedelta_duration(datetime.timedelta(seconds=3600))
    assert result == "1h"

    result = data_utils.format_timedelta_duration(datetime.timedelta(seconds=360))
    assert result == "6m"

    result = data_utils.format_timedelta_duration(datetime.timedelta(seconds=36))
    assert result == "36s"


def test_get_data_timestep_as_str(hourly_gdsr_data, inconsistent_timestep_data):
    result = data_utils.get_data_timestep_as_str(hourly_gdsr_data)
    assert result == "1h"
    with pytest.raises(ValueError):
        data_utils.get_data_timestep_as_str(inconsistent_timestep_data)
