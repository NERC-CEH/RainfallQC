#!/usr/bin/env python

"""Tests for time-series QC checks."""

import datetime

import polars as pl
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


def test_convert_daily_data_to_monthly(daily_gdsr_data, daily_gpcc_data, hourly_gdsr_data):
    result = data_utils.convert_daily_data_to_monthly(daily_gdsr_data, rain_cols=[DEFAULT_RAIN_COL])
    assert result[DEFAULT_RAIN_COL].max() == 208.2
    assert len(result.filter(pl.col(DEFAULT_RAIN_COL).is_nan())) == 17
    data_time_steps = data_utils.get_data_timesteps(result)
    data_time_steps_str = [data_utils.format_timedelta_duration(td) for td in data_time_steps]
    assert data_time_steps_str == ["28d", "29d", "30d", "31d"]

    result = data_utils.convert_daily_data_to_monthly(
        daily_gpcc_data, rain_cols=[DEFAULT_RAIN_COL], perc_for_valid_month=99
    )
    assert len(result.filter(pl.col(DEFAULT_RAIN_COL).is_nan())) == 0
    assert round(result[DEFAULT_RAIN_COL].max(), 1) == 413.1
    data_time_steps = data_utils.get_data_timesteps(result)
    data_time_steps_str = [data_utils.format_timedelta_duration(td) for td in data_time_steps]
    assert data_time_steps_str == ["28d", "29d", "30d", "31d"]

    with pytest.raises(ValueError):
        data_utils.convert_daily_data_to_monthly(hourly_gdsr_data, rain_cols=[DEFAULT_RAIN_COL])


def test_check_data_is_monthly(hourly_gdsr_data, monthly_gdsr_network, monthly_gpcc_data):
    data_utils.check_data_is_monthly(monthly_gpcc_data)
    data_utils.check_data_is_monthly(monthly_gdsr_network)
    with pytest.raises(ValueError):
        data_utils.check_data_is_monthly(hourly_gdsr_data)


def test_get_dry_spells(hourly_gdsr_data):
    result = data_utils.get_dry_spells(hourly_gdsr_data, rain_col=DEFAULT_RAIN_COL)
    assert "is_dry" in result


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


def test_normalise_data(hourly_gdsr_data):
    result = data_utils.normalise_data(hourly_gdsr_data[DEFAULT_RAIN_COL])
    assert round((result.drop_nans().mean() * 100), 2) == 0.06


def test_get_normalised_diff(gauge_comparison_data):
    result = data_utils.get_normalised_diff(
        gauge_comparison_data, target_col="gauge1", other_col="gauge2", diff_col_name="diff"
    )
    assert round(result["diff"].drop_nans().mean(), 2) == 0.03
