#!/usr/bin/env python

"""Pytest config file. Contains test fixtures of rainfall data."""

import datetime

import numpy as np
import polars as pl
import pytest

from rainfallqc.utils import data_readers, data_utils

MULTIPLYING_FACTORS = {"hourly": 24, "daily": 1}  # compared to daily reference
DEFAULT_RAIN_COL = "rain_mm"
DEFAULT_GDSR_OFFSET = "7h"  # 7 hours


@pytest.fixture
def random() -> np.random.Generator:
    return np.random.default_rng(seed=list(map(ord, "𝕽𝔞𝖓𝔡𝖔𝔪")))


def get_gdsr_data() -> pl.DataFrame:
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
    gdsr_data = data_utils.replace_missing_vals_with_nan(
        gdsr_data, rain_col=DEFAULT_RAIN_COL, missing_val=int(gdsr_metadata["no_data_value"])
    )
    return gdsr_data


def get_gpcc_data(time_res: str) -> pl.DataFrame:
    # TODO: maybe randomise this with every call? Or use parameterise
    gpcc_zip_path = f"./tests/data/GPCC/{time_res}_2483.zip"
    gpcc_file_name = f"{time_res}_2483.dat"
    gpcc_data = data_readers.read_gpcc_data_from_zip(gpcc_zip_path, gpcc_file_name, rain_col=DEFAULT_RAIN_COL)
    return gpcc_data


@pytest.fixture
def hourly_gdsr_data() -> pl.DataFrame:
    return get_gdsr_data()


@pytest.fixture()
def gdsr_metadata() -> dict:
    # TODO: maybe randomise this with every call? Or use parameterise
    data_path = "./tests/data/GDSR/DE_02483.txt"
    # read in metadata of gauge
    gdsr_metadata = data_readers.read_gdsr_metadata(data_path)
    return gdsr_metadata


@pytest.fixture
def daily_gdsr_data() -> pl.DataFrame:
    gdsr_data = get_gdsr_data()
    # convert to daily
    gdsr_data_daily = data_readers.convert_gdsr_hourly_to_daily(
        gdsr_data, rain_col=DEFAULT_RAIN_COL, offset=DEFAULT_GDSR_OFFSET
    )
    return gdsr_data_daily


@pytest.fixture()
def daily_gpcc_data() -> pl.DataFrame:
    gpcc_data_daily = get_gpcc_data(time_res="tw")
    return gpcc_data_daily


@pytest.fixture()
def monthly_gpcc_data() -> pl.DataFrame:
    gpcc_data_monthly = get_gpcc_data(time_res="mw")
    return gpcc_data_monthly


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


@pytest.fixture()
def inconsistent_timestep_data():
    return pl.DataFrame(
        {
            "timestamp": [
                datetime.datetime(2023, 1, 1, 0, 0),
                datetime.datetime(2023, 1, 1, 0, 1),  # +1 min
                datetime.datetime(2023, 1, 1, 0, 4),  # +3 min
                datetime.datetime(2023, 1, 1, 0, 5),  # +1 min
                datetime.datetime(2023, 1, 1, 0, 10),  # +5 min
            ],
            DEFAULT_RAIN_COL: [0, 1.2, 1.3, 1.4, 1.6],
        }
    )


@pytest.fixture()
def daily_gdsr_data_w_breakpoint(daily_gdsr_data):
    # Modify 'values' column: add 10 to rows after index 10
    return daily_gdsr_data.with_columns(
        [
            pl.when(pl.int_range(0, daily_gdsr_data.height).alias("idx") > 200)
            .then(pl.col(DEFAULT_RAIN_COL) + 10)
            .otherwise(pl.col(DEFAULT_RAIN_COL) / pl.col(DEFAULT_RAIN_COL))
            .alias(DEFAULT_RAIN_COL)
        ]
    )


@pytest.fixture(scope="session")
def example_array() -> np.ndarray:
    return np.array([1.3, 1.7, 0.9, 1.6, 1.4, 0.2, 4.8, 4.1, 6.0, 5.7, 5.5, 4.1])
