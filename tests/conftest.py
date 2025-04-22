#!/usr/bin/env python

"""Pytest config file. Contains test fixtures of rainfall data."""

import datetime

import numpy as np
import polars as pl
import pytest

from rainfallqc.utils import data_readers, data_utils

MULTIPLYING_FACTORS = {"hourly": 24, "daily": 1}  # compared to daily reference
DEFAULT_RAIN_COL = "rain_mm"


@pytest.fixture
def random() -> np.random.Generator:
    return np.random.default_rng(seed=list(map(ord, "𝕽𝔞𝖓𝔡𝖔𝔪")))


@pytest.fixture
def daily_gdsr_data() -> pl.DataFrame:
    # TODO: maybe randomise this with every call? Or use parameterise
    data_path = "./tests/data/GDSR/DE_02483.txt"
    # read in metadata of gauge
    gdsr_metadata = data_readers.read_gdsr_metadata(data_path)
    rain_col = f"rain_{gdsr_metadata['original_units']}"

    # read in gauge data
    gdsr_data = pl.read_csv(
        data_path,
        skip_rows=20,
        schema_overrides={rain_col: pl.Float64},
    )

    # add datetime column to data
    gdsr_data = data_readers.add_datetime_to_gdsr_data(
        gdsr_data, gdsr_metadata, multiplying_factor=MULTIPLYING_FACTORS["hourly"]
    )
    gdsr_data = data_utils.replace_missing_vals_with_nan_gdsr_data(
        gdsr_data, rain_col=DEFAULT_RAIN_COL, missing_val=int(gdsr_metadata["no_data_value"])
    )
    return gdsr_data


@pytest.fixture
def gappy_daily_data() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "time": pl.date_range(
                datetime.date(year=2006, month=1, day=1), datetime.date(year=2006, month=1, day=17), eager=True
            ),
            DEFAULT_RAIN_COL: [
                np.nan,
                np.nan,
                1,
                None,
                None,
                4,
                None,
                None,
                None,
                8,
                None,
                9,
                None,
                None,
                12,
                None,
                None,
            ],
        }
    )
