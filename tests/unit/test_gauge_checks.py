#!/usr/bin/env python

"""Tests for rain gauge quality control checks."""

import polars as pl
import pytest

from rainfallqc.checks import gauge_checks
from rainfallqc.core import data_loaders

MULTIPLYING_FACTORS = {"hourly": 24, "daily": 1}  # compared to daily reference


@pytest.fixture
def test_daily_gdsr_data():
    data_path = (
        "../test_data/GDSR/DE_02483.txt",
    )  # TODO: maybe randomise this with every call? Or use parameterise?
    # read in metadata of gauge
    gdsr_metadata = data_loaders.read_gdsr_metadata(data_path)
    rain_col = f"rain_{gdsr_metadata['original_units']}"

    # read in gauge data
    gdsr_data = pl.read_csv(
        data_path,
        skip_rows=20,
        schema_overrides={rain_col: pl.Float64},
    )

    # add datetime column to data
    data_loaders.add_datetime_to_gdsr_data(
        gdsr_data, gdsr_metadata, multiplying_factors=MULTIPLYING_FACTORS["hourly"]
    )
    return gdsr_data


def test_get_years_where_percentiles_are_zero(test_daily_gdsr_data):
    gauge_checks.get_years_where_percentiles_are_zero(test_daily_gdsr_data)
