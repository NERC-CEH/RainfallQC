#!/usr/bin/env python

"""Pytest config file. Contains test fixtures of rainfall data."""

import datetime

import numpy as np
import polars as pl
import pytest

from rainfallqc.utils import data_readers, data_utils

DEFAULT_RAIN_COL = "rain_mm"
DEFAULT_GDSR_OFFSET = 7  # 7 hours
GPCC_TIME_RES_CONVERSION = {"tw": "daily", "mw": "monthly"}


@pytest.fixture
def random() -> np.random.Generator:
    return np.random.default_rng(seed=list(map(ord, "𝕽𝔞𝖓𝔡𝖔𝔪")))


def get_gpcc_data(time_res: str, gauge_id: str = "2483") -> pl.DataFrame:
    # TODO: maybe randomise this with every call? Or use parameterise
    gpcc_zip_path = f"./tests/data/GPCC/{time_res}_{gauge_id}.zip"
    gpcc_file_name = f"{time_res}_{gauge_id}.dat"
    gpcc_data = data_readers.read_gpcc_data_from_zip(
        gpcc_zip_path, gpcc_file_name, target_gauge_col=DEFAULT_RAIN_COL, time_res=GPCC_TIME_RES_CONVERSION[time_res]
    )
    return gpcc_data


def get_hourly_gdsr_network(
    path_to_gdsr_dir: str,
    target_id: str,
    distance_threshold: int = 50,
    n_closest: int = 10,
    min_overlap_days: int = 500,
) -> pl.DataFrame:
    gdsr_obj = data_readers.GDSRNetworkReader(path_to_gdsr_dir=path_to_gdsr_dir)
    nearby_ids = list(
        gdsr_obj.get_nearest_overlapping_neighbours_to_target(
            target_id=target_id,
            distance_threshold=distance_threshold,
            n_closest=n_closest,
            min_overlap_days=min_overlap_days,
        )
    )
    nearby_ids.append(target_id)
    nearby_data_paths = gdsr_obj.metadata.filter(pl.col("station_id").is_in(nearby_ids))["path"]
    gdsr_network = gdsr_obj.load_network_data(data_paths=nearby_data_paths)
    return gdsr_network


@pytest.fixture
def hourly_gdsr_data() -> pl.DataFrame:
    data_path = "./tests/data/GDSR/DE_02483.txt"  # TODO: maybe randomise this with every call? Or use parameterise
    return data_readers.read_gdsr_data_from_file(data_path, raw_data_time_res="hourly")


@pytest.fixture()
def gdsr_metadata() -> dict:
    # TODO: maybe randomise this with every call? Or use parameterise
    data_path = "./tests/data/GDSR/DE_02483.txt"
    # read in metadata of gauge
    return data_readers.read_gdsr_metadata(data_path)


@pytest.fixture()
def gpcc_metadata() -> dict:
    data_path = "./tests/data/GPCC/tw_2483.zip"
    # read in metadata of gauge
    return data_readers.read_gpcc_metadata_from_zip(data_path, time_res="daily", gpcc_file_format=".dat")


@pytest.fixture
def daily_gdsr_data() -> pl.DataFrame:
    data_path = "./tests/data/GDSR/DE_02483.txt"
    gdsr_data = data_readers.read_gdsr_data_from_file(data_path, raw_data_time_res="hourly")
    # convert to daily
    gdsr_data_daily = data_readers.convert_gdsr_hourly_to_daily(
        gdsr_data, rain_cols=[DEFAULT_RAIN_COL], hour_offset=DEFAULT_GDSR_OFFSET
    )
    return gdsr_data_daily


@pytest.fixture
def gdsr_gauge_network() -> pl.DataFrame:
    return data_readers.load_gdsr_gauge_network_metadata(path_to_gdsr_dir="./tests/data/GDSR/")


@pytest.fixture()
def daily_gpcc_data() -> pl.DataFrame:
    gpcc_data_daily = get_gpcc_data(time_res="tw")
    return gpcc_data_daily


@pytest.fixture()
def monthly_gpcc_data() -> pl.DataFrame:
    gpcc_data_monthly = get_gpcc_data(time_res="mw")
    return gpcc_data_monthly


@pytest.fixture()
def daily_gpcc_network() -> pl.DataFrame:
    gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/", time_res="tw")
    target_id = "310"
    nearby_ids = list(
        gpcc_obj.get_nearest_overlapping_neighbours_to_target(
            target_id=target_id, distance_threshold=50, n_closest=10, min_overlap_days=500
        )
    )
    nearby_ids.append(target_id)
    nearby_data_paths = gpcc_obj.metadata.filter(pl.col("station_id").is_in(nearby_ids))["path"]
    gpcc_network = gpcc_obj.load_network_data(data_paths=nearby_data_paths, target_gauge_col=DEFAULT_RAIN_COL)
    return gpcc_network


@pytest.fixture()
def monthly_gpcc_network() -> pl.DataFrame:
    gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/", time_res="mw")
    target_id = "310"
    nearby_ids = list(
        gpcc_obj.get_nearest_overlapping_neighbours_to_target(
            target_id=target_id, distance_threshold=50, n_closest=10, min_overlap_days=500
        )
    )
    nearby_ids.append(target_id)
    nearby_data_paths = gpcc_obj.metadata.filter(pl.col("station_id").is_in(nearby_ids))["path"]
    gpcc_network = gpcc_obj.load_network_data(data_paths=nearby_data_paths, target_gauge_col=DEFAULT_RAIN_COL)
    return gpcc_network


@pytest.fixture()
def mins15_gdsr_network() -> pl.DataFrame:
    hourly_gdsr_network = get_hourly_gdsr_network(path_to_gdsr_dir="./tests/data/GDSR/", target_id="DE_00310")
    mins15_gdsr_network = hourly_gdsr_network.upsample("time", every="15m")
    mins15_gdsr_network = mins15_gdsr_network.with_columns(
        [pl.col(col).forward_fill(limit=3) for col in mins15_gdsr_network.columns[1:]]  # hours
    )
    mins15_gdsr_network = mins15_gdsr_network[50000:]
    return mins15_gdsr_network


@pytest.fixture()
def hourly_gdsr_network() -> pl.DataFrame:
    return get_hourly_gdsr_network(path_to_gdsr_dir="./tests/data/GDSR/", target_id="DE_00310")


@pytest.fixture()
def daily_gdsr_network() -> pl.DataFrame:
    gdsr_network = get_hourly_gdsr_network(path_to_gdsr_dir="./tests/data/GDSR/", target_id="DE_00310")

    # convert to daily
    daily_gdsr_network = data_readers.convert_gdsr_hourly_to_daily(
        gdsr_network, rain_cols=gdsr_network.columns[1:], hour_offset=DEFAULT_GDSR_OFFSET
    )
    return daily_gdsr_network


@pytest.fixture()
def monthly_gdsr_network() -> pl.DataFrame:
    gdsr_network = get_hourly_gdsr_network(path_to_gdsr_dir="./tests/data/GDSR/", target_id="DE_00310")

    # convert to daily
    daily_gdsr_network = data_readers.convert_gdsr_hourly_to_daily(
        gdsr_network, rain_cols=gdsr_network.columns[1:], hour_offset=DEFAULT_GDSR_OFFSET
    )

    # convert to monthly
    monthly_gdsr_network = data_utils.convert_daily_data_to_monthly(
        daily_gdsr_network, rain_cols=daily_gdsr_network.columns[1:], perc_for_valid_month=95
    )
    return monthly_gdsr_network


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
def gauge_comparison_data():
    return pl.DataFrame(
        {
            "time": pl.date_range(
                datetime.date(year=2006, month=1, day=1), datetime.date(year=2006, month=1, day=17), eager=True
            ),
            "gauge1": [
                np.nan,
                np.nan,
                0.1,
                None,
                None,
                4.0,
                np.nan,
                None,
                None,
                0.8,
                None,
                1.9,
                0.4,
                None,
                1.2,
                None,
                2.1,
            ],
            "gauge2": [
                np.nan,
                np.nan,
                0.4,
                None,
                None,
                2.1,
                None,
                0.0,
                None,
                0.2,
                None,
                0.7,
                np.nan,
                None,
                1.2,
                None,
                0.1,
            ],
        }
    )


@pytest.fixture()
def test_binary_data():
    return pl.DataFrame(
        {
            "time": pl.date_range(
                datetime.date(year=2006, month=1, day=1), datetime.date(year=2006, month=1, day=17), eager=True
            ),
            "col1": [
                1,
                1,
                1,
                0,
                1,
                1,
                0,
                1,
                0,
                0,
                1,
                0,
                0,
                1,
                1,
                0,
                0,
            ],
        }
    )


@pytest.fixture()
def inconsistent_timestep_data():
    return pl.DataFrame(
        {
            "time": [
                datetime.datetime(2023, 1, 1, 0, 0),
                datetime.datetime(2023, 1, 1, 0, 1),  # +1 min
                datetime.datetime(2023, 1, 1, 0, 4),  # +3 min
                datetime.datetime(2023, 1, 1, 0, 5),  # +1 min
                datetime.datetime(2023, 1, 1, 0, 10),  # +5 min
            ],
            DEFAULT_RAIN_COL: [0.0, 1.2, 1.3, 1.4, 1.6],
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
