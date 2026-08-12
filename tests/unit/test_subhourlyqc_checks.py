#!/usr/bin/env python

"""Tests for subhourlyQC checks from Villalobos-Herrera et al. (2022)."""

import numpy.testing
import pytest

import polars as pl
from rainfallqc.checks import subhourlyqc_checks

DEFAULT_RAIN_COL = "rain_mm"


def test_check_exceedance_of_UK_1hr_record(min15_gsdr_data):
    result = subhourlyqc_checks.check_exceedance_of_UK_1hr_record(min15_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result) == 175293
    assert len(result.filter(pl.col("UK_1hr_record_check") == 4)) == 160
    assert len(result.filter(pl.col("UK_1hr_record_check") == 3)) == 8
    assert len(result.filter(pl.col("UK_1hr_record_check") == 0)) == 170797


def test_check_exceedance_of_UK_1h_record_1min_data(min1_gsdr_data):
    result = subhourlyqc_checks.check_exceedance_of_UK_1hr_record(min1_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result) == 2629381
    assert len(result.filter(pl.col("UK_1hr_record_check") == 4)) == 62460
    assert len(result.filter(pl.col("UK_1hr_record_check") == 3)) == 9480
    assert len(result.filter(pl.col("UK_1hr_record_check") == 0)) == 2466001



def test_check_exceedance_of_UK_24hr_record(min15_gsdr_data):
    result = subhourlyqc_checks.check_exceedance_of_UK_24hr_record(min15_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("UK_24hr_record_check") == 4)) == 116
    assert len(result.filter(pl.col("UK_24hr_record_check") == 3)) == 0
    assert len(result.filter(pl.col("UK_24hr_record_check") == 0)) == 170873


def test_check_daily_exceedance_of_UK_24hr_record(min15_gsdr_data):
    result = subhourlyqc_checks.check_daily_exceedance_of_UK_24hr_record(min15_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("UK_24hr_rolling_record_check") == 4)) == 768
    assert len(result.filter(pl.col("UK_24hr_rolling_record_check") == 3)) == 96
    assert len(result.filter(pl.col("UK_24hr_rolling_record_check") == 0)) == 167425


def test_check_daily_exceedance_of_UK_24hr_record_1min_data(min1_gsdr_data):
    result = subhourlyqc_checks.check_daily_exceedance_of_UK_24hr_record(min1_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("UK_24hr_rolling_record_check") == 4)) == 483840
    assert len(result.filter(pl.col("UK_24hr_rolling_record_check") == 3)) == 54720
    assert len(result.filter(pl.col("UK_24hr_rolling_record_check") == 0)) == 1882081


def test_check_streaks_20mm(min15_gsdr_data):
    result = subhourlyqc_checks.check_streaks_20mm(min15_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("streak_flag_20mm") == 0)) == 174801
    assert len(result.filter(pl.col("streak_flag_20mm") == 1)) == 492

def test_check_streaks_20mm_1min_data(min1_gsdr_data):
    result = subhourlyqc_checks.check_streaks_20mm(min1_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("streak_flag_20mm") == 0)) == 2603281
    assert len(result.filter(pl.col("streak_flag_20mm") == 1)) == 26100

def test_check_freq_is_subhourly(min15_gsdr_data):
    result = subhourlyqc_checks.check_freq_is_subhourly(min15_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("freq_res_flag") == 0)) == 175293
    assert len(result.filter(pl.col("freq_res_flag") == 1)) == 0
    min15_gsdr_data_sample = min15_gsdr_data.sample(17500, seed=24)
    min15_gsdr_data_sample = min15_gsdr_data_sample.sort(by='time')
    result = subhourlyqc_checks.check_freq_is_subhourly(min15_gsdr_data_sample, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("freq_res_flag") == 0)) == 8194
    assert len(result.filter(pl.col("freq_res_flag") == 1)) == 9306

def test_check_freq_is_subhourly_1min_data(min1_gsdr_data):
    min1_gsdr_data_sample = min1_gsdr_data.sample(15400, seed=32)
    min1_gsdr_data_sample = min1_gsdr_data_sample.sort(by='time')
    result = subhourlyqc_checks.check_freq_is_subhourly(min1_gsdr_data_sample, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("freq_res_flag") == 1)) == 10936


def test_check_subhourly_thresholds(min15_gsdr_data):
    result = subhourlyqc_checks.check_subhourly_thresholds(min15_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("month_1hr_threshold_flag") == 0)) == 170393
    assert len(result.filter(pl.col("month_1hr_threshold_flag") == 1)) == 4900
    assert len(result.filter(pl.col("month_15min_threshold_flag") == 0)) == 170893
    assert len(result.filter(pl.col("month_15min_threshold_flag") == 1)) == 4400

def test_check_subhourly_thresholds_1min_data(min1_gsdr_data):
    result = subhourlyqc_checks.check_subhourly_thresholds(min1_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL)
    assert len(result.filter(pl.col("month_1hr_threshold_flag") == 1)) == 303540
    assert len(result.filter(pl.col("month_15min_threshold_flag") == 1)) == 213210
    assert len(result.filter(pl.col("month_1min_threshold_flag") == 1)) == 102541



def test_flag_data_based_on_threshold(min15_gsdr_data):
    data = min15_gsdr_data.with_columns(pl.col("time").dt.strftime("%b").alias("month_name"))
    hourly_data = data.group_by_dynamic("time", every="1h").agg(
        pl.col(DEFAULT_RAIN_COL).sum(), pl.col("month_name").first()
    )
    result = subhourlyqc_checks.flag_data_based_on_threshold(data, target_gauge_col=DEFAULT_RAIN_COL, threshold_dict=subhourlyqc_checks.UK_MONTHLY_THRESHOLDS_15min, threshold_col_name="monthly_15min_threshold")
    assert len(result.filter(pl.col("monthly_15min_threshold_flag") == 1)) == 4400
    assert len(result.filter(pl.col("monthly_15min_threshold_flag") == 0)) == 170893

    with pytest.raises(ValueError):
        subhourlyqc_checks.flag_data_based_on_threshold(min15_gsdr_data, target_gauge_col=DEFAULT_RAIN_COL, threshold_dict=subhourlyqc_checks.UK_MONTHLY_THRESHOLDS_15min, threshold_col_name="monthly_15min_threshold")
