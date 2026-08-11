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
