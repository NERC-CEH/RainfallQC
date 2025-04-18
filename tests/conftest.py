#!/usr/bin/env python

"""Pytest config file. Contains test fixtures of rainfall data."""

import numpy as np
import polars as pl
import pytest

from rainfallqc.utils import data_loaders

MULTIPLYING_FACTORS = {"hourly": 24, "daily": 1}  # compared to daily reference


@pytest.fixture
def random() -> np.random.Generator:
    return np.random.default_rng(seed=list(map(ord, "𝕽𝔞𝖓𝔡𝖔𝔪")))


@pytest.fixture
def daily_gdsr_data() -> pl.DataFrame:
    # TODO: maybe randomise this with every call? Or use parameterise
    data_path = "./tests/data/GDSR/DE_02483.txt"
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
    gdsr_data = data_loaders.add_datetime_to_gdsr_data(
        gdsr_data, gdsr_metadata, multiplying_factor=MULTIPLYING_FACTORS["hourly"]
    )
    return gdsr_data
