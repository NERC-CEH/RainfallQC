# -*- coding: utf-8 -*-
"""
Data loading tools.

Classes for reading rain gauge network data at bottom of file.
"""

import datetime
import glob
import os.path
import zipfile
from abc import ABC, abstractmethod
from importlib import resources
from typing import Iterable

import pandas as pd
import polars as pl
import xarray as xr

from rainfallqc.utils import data_utils

MULTIPLYING_FACTORS = {"hourly": 24, "daily": 1}  # compared to daily reference


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


def read_gpcc_metadata_from_zip(data_path: str, gpcc_file_format: str = ".dat") -> dict:
    """
    Read GPCC metadata from zip file.

    Parameters
    ----------
    data_path :
        path to GPCC zip file.
    gpcc_file_format :
        Default GPCC file format (default: .dat)

    Returns
    -------
    metadata :
        Metadata from GPCC file

    """
    assert "zip" in data_path, "Data needs to be a zip file"
    gpcc_file_name = data_path.split("/")[-1].split(".zip")[0]
    gpcc_unzip = zipfile.ZipFile(data_path).open(f"{gpcc_file_name}{gpcc_file_format}", "r")
    with gpcc_unzip:
        gpcc_header = gpcc_unzip.readline().decode("utf-8")
    gpcc_headers = gpcc_header.split()

    # Extract values
    gpcc_metadata = {
        "station_id": int(gpcc_headers[0]),
        "latitude": float(gpcc_headers[1]),
        "longitude": float(gpcc_headers[2]),
        "country": gpcc_headers[3],
        "location": " ".join(gpcc_headers[4:]),  # Join remaining parts as location name
    }
    return gpcc_metadata


def read_gpcc_data_from_zip(
    data_path: str, gpcc_file_name: str, rain_col: str, time_res: str, missing_val: int | float = -999
) -> pl.DataFrame:
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
    time_res :
        'daily' or 'monthly'
    missing_val :
        Missing value (default: -999)

    Returns
    -------
    gpcc_data : dict
        Data from GPCC file

    """
    assert ".zip" in data_path, "Data needs to be a zip file"
    # 0. Load GPCC data
    f = zipfile.ZipFile(data_path).open(gpcc_file_name)
    gpcc_data = pl.from_pandas(pd.read_csv(f, skiprows=1, header=None, sep=r"\s+"))

    if time_res == "daily":
        # 1. drop unnecessary columns
        gpcc_data = gpcc_data.drop([str(i) for i in range(4, len(gpcc_data.columns))])
        # 2. make daily datetime column (apparently it's 7am-7pm)
        gpcc_data = gpcc_data.with_columns(pl.datetime(pl.col("2"), pl.col("1"), pl.col("0"), 7).alias("time")).drop(
            ["0", "1", "2"]
        )
        # 3. rename and reorder
        gpcc_data = gpcc_data.rename({"3": rain_col})
    elif time_res == "monthly":
        # 1. drop unnecessary columns
        gpcc_data = gpcc_data.drop([str(i) for i in range(3, len(gpcc_data.columns))])
        # 2. make monthly datetime column
        gpcc_data = gpcc_data.with_columns(pl.datetime(year=pl.col("1"), month=pl.col("0"), day=1).alias("time")).drop(
            ["0", "1"]
        )
        # 3. rename and reorder
        gpcc_data = gpcc_data.rename({"2": rain_col})
    else:
        raise ValueError(f"Time resolution={time_res} not recognized. Please use 'daily' or 'monthly'")

    # 4. Check data is specific format
    try:
        data_utils.check_data_is_specific_time_res(gpcc_data, time_res)
    except ValueError as ve:
        print(ve)
        print(f"Attempting to resample into {time_res}")
        gpcc_data = gpcc_data.group_by_dynamic("time", every=data_utils.TEMPORAL_CONVERSIONS[time_res]).agg(
            pl.col(rain_col).first()
        )

    # 5. Select time and rain col
    gpcc_data = gpcc_data.select(["time", rain_col])  # Reorder (to look nice)

    # 6. Replace missing value
    gpcc_data = data_utils.replace_missing_vals_with_nan(gpcc_data, rain_col=rain_col, missing_val=missing_val)

    return gpcc_data


def read_gdsr_data_from_file(data_path: str, raw_data_time_res: str, gdsr_header_rows: int = 20) -> pl.DataFrame:
    """
    Read GDSR data from file.

    Note: this was developed on the GDSR data available from IntenseQC. So please number of header rows in data.

    Parameters
    ----------
    data_path :
        Path to GDSR data file
    raw_data_time_res :
        Time resolution of data record i.e. 'hourly' or 'daily'
    gdsr_header_rows :
        Number of rows to skip in the header of the GSDR data (default=20)

    Returns
    -------
    gdsr_data :
        GDSR data as Pandas DataFrame

    """
    # read in metadata of gauge
    gdsr_metadata = read_gdsr_metadata(data_path)
    rain_col = f"rain_{gdsr_metadata['original_units']}"

    # read in gauge data
    gdsr_data = pl.read_csv(
        data_path,
        skip_rows=gdsr_header_rows,
        schema_overrides={rain_col: pl.Float64},
    )

    # add datetime column to data
    gdsr_data = add_datetime_to_gdsr_data(
        gdsr_data, gdsr_metadata, multiplying_factor=MULTIPLYING_FACTORS[raw_data_time_res]
    )
    gdsr_data = data_utils.replace_missing_vals_with_nan(
        gdsr_data, rain_col=rain_col, missing_val=int(gdsr_metadata["no_data_value"])
    )
    return gdsr_data


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
    delta_days = ((end_date + datetime.timedelta(days=1)) - start_date).days
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


def load_gpcc_gauge_network_metadata(path_to_gpcc_dir: str, gpcc_file_format: str = ".dat") -> pl.DataFrame:
    """
    Load metadata from GPCC gauges from a directory.

    Parameters
    ----------
    path_to_gpcc_dir :
        Path to directory with GPCC gauges
    gpcc_file_format :
        Format of file (default is .dat)

    Returns
    -------
    all_station_metadata :
        All GPCC gauges metadata as one dataframe.

    """
    # 1. Glob all metadata paths
    if not os.path.isdir(path_to_gpcc_dir):
        raise ValueError(f"Invalid GPCC metadata directory at {path_to_gpcc_dir}")
    all_metadata_data_paths = glob.glob(f"{path_to_gpcc_dir}*.zip")

    # 2. Load all GPCC metadata from data
    all_station_metadata_list = []
    for zip_file in all_metadata_data_paths:
        one_station_metadata = read_gpcc_metadata_from_zip(data_path=zip_file, gpcc_file_format=gpcc_file_format)
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
        g_id_path = glob.glob(f"{dir_path}*{g_id}*{file_format}")
        try:
            all_data_paths[g_id] = g_id_path[0]
        except IndexError:
            print(f"Cannot find data for {g_id} in directory {dir_path} with file format {file_format}.")
        all_data_paths[g_id] = g_id_path[0]
    return all_data_paths


class GaugeNetworkReader(ABC):
    """Base class for reading rain gauge networks."""

    def __init__(self, path_to_gauge_network: str):
        """Load network reader."""
        self.path_to_gauge_network = path_to_gauge_network
        self.metadata = self.load_metadata()

    @abstractmethod
    def _load_metadata(self) -> dict:
        """Must be implemented by subclasses to load gauge network metadata."""
        pass

    # @abstractmethod
    # def load_network_data(self) -> pl.DataFrame:
    #     """Must be implemented by subclasses to load gauge network data."""
    #     pass


class GDSRNetworkReader(GaugeNetworkReader):
    """GDSR rain gauge network reader."""

    def __init__(self, path_to_gdsr_dir: str, file_format: str = ".txt"):
        """Load network reader."""
        self.path_to_gdsr_dir = path_to_gdsr_dir
        self.file_format = file_format
        super().__init__(path_to_gdsr_dir)
        self.metadata = self._load_metadata()
        self.data_paths = self._get_data_paths()

    def _load_metadata(self) -> pl.DataFrame:
        """
        Load metadata from GDSR gauge metadata path.

        Returns
        -------
        metadata :
            Metadata of GDSR gauges.

        """
        metadata = load_gdsr_gauge_network_metadata(self.path_to_gdsr_dir, self.file_format)
        return metadata

    def _get_data_paths(self) -> dict:
        """
        Get paths to gauge network of GDSR gauges.

        Returns
        -------
        gauge_paths :
            Dataframe of all GDSR gauges rain record.

        """
        gauge_paths = get_paths_using_gauge_ids(self.metadata["station_id"], self.path_to_gdsr_dir, self.file_format)
        return gauge_paths


class GPCCNetworkReader(GaugeNetworkReader):
    """GPCC rain gauge network reader."""

    def __init__(self, path_to_gpcc_dir: str, file_format: str = ".zip"):
        """Load network reader."""
        self.path_to_gpcc_dir = path_to_gpcc_dir
        self.file_format = file_format
        super().__init__(path_to_gpcc_dir)
        self.metadata = self._load_metadata()
        self.data_paths = self._get_data_paths()

    def _load_metadata(self) -> pl.DataFrame:
        """
        Load metadata from GPCC gauge metadata path.

        Returns
        -------
        metadata :
            Metadata of GPCC gauges.

        """
        metadata = load_gpcc_gauge_network_metadata(self.path_to_gpcc_dir)
        return metadata

    def _get_data_paths(self) -> dict:
        """
        Get paths to gauge network of GPCC gauges.

        Returns
        -------
        gauge_paths :
            Dataframe of all GDSR gauges rain record.

        """
        gauge_paths = get_paths_using_gauge_ids(self.metadata["station_id"], self.path_to_gpcc_dir, self.file_format)
        return gauge_paths
