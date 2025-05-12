# -*- coding: utf-8 -*-
"""Data loading tools."""

import datetime
import glob
import os.path
import zipfile
from importlib import resources
from typing import Iterable

import pandas as pd
import polars as pl
import xarray as xr


def read_gdsr_metadata(data_path: str) -> dict:
    """
    Read the specific format and header of Global Sub-Daily Rainfall (GDSR) files.

    Parameters
    ----------
    data_path :
        path to GDSR data file (.txt)

    Returns
    -------
    metadata :
        Metadata from GDSR file

    """
    metadata = {}
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if ":" not in line:
                continue  # these rows are not metadata
            key, val = line.strip().split(":", maxsplit=1)
            key = key.lower().replace(" ", "_").strip()
            val = val.strip()
            metadata[key] = val
            if key == "other":
                break
    metadata = convert_gdsr_metadata_dates_to_datetime(metadata)
    return metadata


def read_gpcc_data_from_zip(data_path: str, gpcc_file_name: str, rain_col: str) -> pl.DataFrame:
    """
    Read the specific format and header of Global Precipitation Climatology Centre (GPCC) files.

    Parameters
    ----------
    data_path :
        path to GPCC zip file
    gpcc_file_name :
        Name of GPCC file within zip
    rain_col :
        Name of rainfall column

    Returns
    -------
    gpcc_data : dict
        Data from GPCC file

    """
    # 0. Load GPCC data
    f = zipfile.ZipFile(data_path).open(gpcc_file_name)
    gpcc_data = pl.from_pandas(pd.read_csv(f, skiprows=1, header=None, sep=r"\s+"))

    # 1. drop unnecessary columns
    gpcc_data = gpcc_data.drop([str(i) for i in range(4, 16)])

    # 2. make datetime column (apparently it's 7am-7pm)
    gpcc_data = gpcc_data.with_columns(pl.datetime(pl.col("2"), pl.col("1"), pl.col("0"), 7).alias("time")).drop(
        ["0", "1", "2"]
    )

    # 3. rename and reorder
    gpcc_data = gpcc_data.rename({"3": rain_col})
    gpcc_data = gpcc_data.select(["time", rain_col])  # Reorder (to look nice)

    return gpcc_data


def convert_gdsr_metadata_dates_to_datetime(gdsr_metadata: dict) -> dict:
    """
    Convert GDSR metadata date string column to datetime.

    Parameters
    ----------
    gdsr_metadata :
        Metadata from GDSR file

    Returns
    -------
    gdsr_metadata : dict
    Metadata from GDSR file with start and end date column

    """
    gdsr_metadata["start_datetime"] = datetime.datetime.strptime(gdsr_metadata["start_datetime"], "%Y%m%d%H")
    gdsr_metadata["end_datetime"] = datetime.datetime.strptime(gdsr_metadata["end_datetime"], "%Y%m%d%H")
    return gdsr_metadata


def add_datetime_to_gdsr_data(
    gdsr_data: pl.DataFrame, gdsr_metadata: dict, multiplying_factor: int | float
) -> pl.DataFrame:
    """
    Add datetime column to GDSR gauge data using metadata from that gauge.

    NOTE: Could maybe extend so can find metadata if not provided?

    Parameters
    ----------
    gdsr_data :
        GDSR data
    gdsr_metadata :
        Metadata from GDSR file
    multiplying_factor : int or float
        Factor to multiply the data by.

    Returns
    -------
    gdsr_data
        GDSR data with datetime column added

    """
    start_date = gdsr_metadata["start_datetime"]
    end_date = gdsr_metadata["end_datetime"]
    assert isinstance(start_date, datetime.datetime), (
        "Please convert start_ and end_datetime to datetime.datetime objects"
    )

    date_interval = []
    delta_days = (end_date + datetime.timedelta(days=1) - start_date).days
    for i in range(delta_days * multiplying_factor):
        date_interval.append(start_date + datetime.timedelta(hours=i))

    # add time column
    assert len(gdsr_data) == len(date_interval)
    gdsr_data = gdsr_data.with_columns(time=pl.Series(date_interval))

    return gdsr_data


def convert_gdsr_hourly_to_daily(hourly_data: pl.DataFrame, rain_col: str, offset: str) -> pl.DataFrame:
    """
    Group hourly data into daily and check for at least 24 daily time steps per day.

    Parameters
    ----------
    hourly_data :
        Hourly rainfall data
    rain_col :
        Column with rainfall data
    offset :
        Time offset in hours

    Returns
    -------
    daily_data :
        Daily rainfall data

    """
    # resample into daily (also round to 1 decimal place)
    return (
        hourly_data.group_by_dynamic("time", every="1d", offset=offset, closed="right")
        .agg([pl.len().alias("n_hours"), pl.col(rain_col).mean().round(1).alias(rain_col)])
        .filter(pl.col("n_hours") == 24)
        .drop("n_hours")
    )


def load_etccdi_data(etccdi_var: str, path_to_etccdi: str = None) -> xr.Dataset:
    """
    Load ETCCDI data.

    Parameters
    ----------
    etccdi_var :
        variable to load from ETCCDI
    path_to_etccdi :
        path to ETCCDI data (default is location of data in tests)

    Returns
    -------
    etccdi_data :
        Loaded data

    """
    if not path_to_etccdi:
        netcdf_file = f"RawData_HADEX2_{etccdi_var}_1951-2010_ANN_from-90to90_from-180to180.nc"
        path_to_etccdi_data = resources.files("rainfallqc.data.ETCCDI").joinpath(netcdf_file)
        return xr.open_dataset(str(path_to_etccdi_data), decode_timedelta=True)
    else:
        print(f"User defined path to ETCCDI being used: {path_to_etccdi}")
        return xr.open_dataset(
            f"{path_to_etccdi}RawData_HADEX2_{etccdi_var}_1951-2010_ANN_from-90to90_from-180to180.nc",
            decode_timedelta=True,
        )


def load_gdsr_gauge_network_metadata(path_to_gdsr_dir: str, file_format: str = ".txt") -> pl.DataFrame:
    """
    Load metadata from GDSR gauges from a directory.

    Parameters
    ----------
    path_to_gdsr_dir :
        Path to directory with GDSR gauges
    file_format :
        Format of file (default is .txt)

    Returns
    -------
    all_station_metadata :
        All GDSR gauges metadata as one dataframe.

    """
    # 1. Glob all metadata paths
    if not os.path.isdir(path_to_gdsr_dir):
        raise ValueError(f"Invalid GDSR metadata directory at {path_to_gdsr_dir}")
    all_metadata_data_paths = glob.glob(f"{path_to_gdsr_dir}*{file_format}")

    # 2. Load all GDSR metadata from data
    all_station_metadata_list = []
    for file in all_metadata_data_paths:
        one_station_metadata = read_gdsr_metadata(data_path=file)
        all_station_metadata_list.append(one_station_metadata)

    # 3. Convert to pl.DataFrame
    all_station_metadata = pl.from_dicts(all_station_metadata_list)

    all_station_metadata = all_station_metadata.with_columns(
        pl.col("latitude").cast(pl.Float64), pl.col("longitude").cast(pl.Float64)
    )

    return all_station_metadata


def get_paths_using_gauge_ids(gauge_ids: Iterable, dir_path: str, file_format: str) -> dict:
    """
    Get data path of Gauge IDs.

    Parameters
    ----------
    gauge_ids :
        Array of gauge IDs
    dir_path :
        Path to data directory
    file_format :
        Format of files in directory.

    Returns
    -------
    gauge_paths :
        Dictionary of gauge ID and path

    """
    all_data_paths = {}
    for g_id in gauge_ids:
        g_id_path = glob.glob(f"{dir_path}{g_id}{file_format}")
        all_data_paths[g_id] = g_id_path[0]
    return all_data_paths
