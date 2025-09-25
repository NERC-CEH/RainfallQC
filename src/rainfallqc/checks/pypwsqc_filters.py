# -*- coding: utf-8 -*-
"""
Quality control checks translated from the pyPWSQC framework (https://pypwsqc.readthedocs.io/en/latest/).

The PWSQC framework includes filters originally develop for automated PWS within the COST Action OPENSENSE.

'run_' and 'check_' relate to the algorithms from pyPWSQC.

Functions are ordered alphabetically.
"""

from typing import List

import numpy as np
import polars as pl
import poligrain as plg
import pypwsqc.flagging
import xarray as xr

from rainfallqc.utils import data_utils

MAX_DISTANCE_M = 10e3

DEFAULT_TIME_UNITS = "seconds since 1970-01-01 00:00:00"
DEFAULT_RAINFALL_ATTRIBUTES = {
    "name": "rainfall",
    "long_name": "rainfall amount per time unit",
    "units": "mm",
    "coverage_contant_type": "physicalMeasurement",
}
DEFAULT_LAT_LON_ATTRIBUTES = {"unit": "degrees in WGS84 projection"}
DEFAULT_ELEVATION_ATTRIBUTES = {"units": "meters", "longname": "meters_above_sea"}


def run_bias_correction(neighbour_data: pl.DataFrame) -> None:
    """
    Bias correction.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def run_event_based_filter(neighbour_data: pl.DataFrame) -> None:
    """
    Event based filter (EBF).

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def check_faulty_zeros(
    neighbour_data: pl.DataFrame,
    neighbour_metadata: pl.DataFrame,
    neighbouring_gauge_ids: List[str],  # TODO: consider if this would break if integers
    neighbour_metadata_gauge_id_col: str,
    time_res: str,
    projection: str,
    nint: int,
    n_stat: int,
    max_distance_for_neighbours: int | float = MAX_DISTANCE_M,
    time_units: str = DEFAULT_TIME_UNITS,
    rainfall_attributes: dict = DEFAULT_RAINFALL_ATTRIBUTES,
    lat_lon_attributes: dict = DEFAULT_LAT_LON_ATTRIBUTES,
    global_attributes: dict = None,
) -> xr.Dataset:
    """
    Will flag faulty zeros based on neighbours ...

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col
    neighbour_metadata :
        Metadata for the rainfall data with 'latitude' and 'longitude'
    neighbour_metadata_gauge_id_col :
        Column with the gauge ID
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_ids:
        List of ids with neighbouring gauges
    time_res :
        Time resolution of data
    projection :
        cartesian/metric coordinate system
    nint :
        Number of intervals
    n_stat :
        Number of stations
    max_distance_for_neighbours :
        Maximum distance to consider for neighbours
    time_units :
        Units and encoding of the 'time' column
    rainfall_attributes :
        Attributes for rainfall in the xarray Dataset
    lat_lon_attributes :
        Attributes for lat and lon in the xarray Dataset
    global_attributes :
        Global attributes for xarray Dataset

    Returns
    -------
    neighbour_data_ds_filtered :
        Data with flags for faulty zeros

    Examples
    --------
    available at: https://pypwsqc.readthedocs.io/en/latest/notebooks/merged_filters.html

    """
    # 0. Initial checks
    data_utils.check_data_is_specific_time_res(neighbour_data, time_res)
    for gauge_id in neighbouring_gauge_ids:
        assert gauge_id in neighbour_metadata[neighbour_metadata_gauge_id_col], (
            f"ID: '{gauge_id}' needs to be a value in the metadata."
        )
        assert gauge_id in neighbour_data.columns, f"ID: '{gauge_id}' needs to be a column be in data."

    # 1. filter metadata to only be nearby
    neighbour_metadata = neighbour_metadata.filter(
        pl.col(neighbour_metadata_gauge_id_col).is_in(neighbouring_gauge_ids)
    )

    # 2. convert to xarray
    neighbour_data_ds = convert_neighbour_data_to_xarray(
        neighbour_data=neighbour_data,
        neighbour_metadata=neighbour_metadata,
        time_units=time_units,
        projection=projection,
        rainfall_attributes=rainfall_attributes,
        lat_lon_attributes=lat_lon_attributes,
        global_attributes=global_attributes,
    )

    # 3. compute distance matrix (if not already exists)
    distance_matrix = compute_distance_matrix(neighbour_data_ds)

    # 4. filter distance matrix
    neighbour_data_ds = subset_distance_matrix(
        neighbour_data_ds=neighbour_data_ds,
        distance_matrix=distance_matrix,
        max_distance_for_neighbours=max_distance_for_neighbours,
    )

    # 5. run FZ filter
    neighbour_data_ds_filtered = pypwsqc.flagging.fz_filter(neighbour_data_ds, nint=nint, n_stat=n_stat)

    return neighbour_data_ds_filtered


def check_high_influx_filter(neighbour_data: pl.DataFrame) -> None:
    """
    High influx filter.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def run_indicator_correlation(neighbour_data: pl.DataFrame) -> None:
    """
    Run indicator correlation.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def run_peak_removal(neighbour_data: pl.DataFrame) -> None:
    """
    Peak removal.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def check_station_outlier(
    neighbour_data: pl.DataFrame,
    neighbour_metadata: pl.DataFrame,
    neighbouring_gauge_ids: List[str],  # TODO: consider if this would break if integers
    neighbour_metadata_gauge_id_col: str,
    time_res: str,
    projection: str,
    evaluation_period: int,
    mmatch: int,
    gamma: float,
    n_stat: int,
    max_distance_for_neighbours: int | float = MAX_DISTANCE_M,
    time_units: str = DEFAULT_TIME_UNITS,
    rainfall_attributes: dict = DEFAULT_RAINFALL_ATTRIBUTES,
    lat_lon_attributes: dict = DEFAULT_LAT_LON_ATTRIBUTES,
    global_attributes: dict = None,
) -> xr.Dataset:
    """
    Station outlier.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col
    neighbour_metadata :
        Metadata for the rainfall data with 'latitude' and 'longitude'
    neighbour_metadata_gauge_id_col :
        Column with the gauge ID
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_ids:
        List of ids with neighbouring gauges
    time_res :
        Time resolution of data
    projection :
        cartesian/metric coordinate system
    evaluation_period
        length of (rolling) window for correlation calculation
    mmatch
        threshold for number of matching rainy intervals in
        evaluation period
    gamma
        threshold for rolling median pearson correlation
    n_stat :
        Number of stations
    max_distance_for_neighbours :
        Maximum distance to consider for neighbours
    time_units :
        Units and encoding of the 'time' column
    rainfall_attributes :
        Attributes for rainfall in the xarray Dataset
    lat_lon_attributes :
        Attributes for lat and lon in the xarray Dataset
    global_attributes :
        Global attributes for xarray Dataset

    Returns
    -------
    neighbour_data_ds_filtered :
        Data with flags for station outliers

    Examples
    --------
    available at: https://pypwsqc.readthedocs.io/en/latest/notebooks/merged_filters.html


    """
    # 0. Initial checks
    data_utils.check_data_is_specific_time_res(neighbour_data, time_res)
    for gauge_id in neighbouring_gauge_ids:
        assert gauge_id in neighbour_metadata[neighbour_metadata_gauge_id_col], (
            f"ID: '{gauge_id}' needs to be a value in the metadata."
        )
        assert gauge_id in neighbour_data.columns, f"ID: '{gauge_id}' needs to be a column be in data."

    # 1. filter metadata to only be nearby
    neighbour_metadata = neighbour_metadata.filter(
        pl.col(neighbour_metadata_gauge_id_col).is_in(neighbouring_gauge_ids)
    )

    # 2. convert to xarray
    neighbour_data_ds = convert_neighbour_data_to_xarray(
        neighbour_data=neighbour_data,
        neighbour_metadata=neighbour_metadata,
        time_units=time_units,
        projection=projection,
        rainfall_attributes=rainfall_attributes,
        lat_lon_attributes=lat_lon_attributes,
        global_attributes=global_attributes,
    )

    # 3. compute distance matrix (if not already exists)
    distance_matrix = compute_distance_matrix(neighbour_data_ds)

    # 4. filter distance matrix
    neighbour_data_ds = subset_distance_matrix(
        neighbour_data_ds=neighbour_data_ds,
        distance_matrix=distance_matrix,
        max_distance_for_neighbours=max_distance_for_neighbours,
    )

    # 5. Initialise SO flags
    neighbour_data_ds["so_flag"] = xr.DataArray(
        np.ones((len(neighbour_data_ds.id), len(neighbour_data_ds.time))) * -999, dims=("id", "time")
    )
    neighbour_data_ds["median_corr_nbrs"] = xr.DataArray(
        np.ones((len(neighbour_data_ds.id), len(neighbour_data_ds.time))) * -999, dims=("id", "time")
    )
    neighbour_data_ds["gamma"] = xr.DataArray(
        np.ones((len(neighbour_data_ds.id), len(neighbour_data_ds.time))) * gamma, dims=("id", "time")
    )

    # 6. run SO filter
    neighbour_data_ds_filtered = pypwsqc.flagging.so_filter(
        neighbour_data_ds,
        distance_matrix=distance_matrix,
        evaluation_period=evaluation_period,
        mmatch=mmatch,
        gamma=gamma,
        n_stat=n_stat,
        max_distance=max_distance_for_neighbours,
    )

    return neighbour_data_ds_filtered


def convert_neighbour_data_to_xarray(
    neighbour_data: pl.DataFrame,
    neighbour_metadata: pl.DataFrame,
    projection: str,
    time_units: str = DEFAULT_TIME_UNITS,
    rainfall_attributes: dict = DEFAULT_RAINFALL_ATTRIBUTES,
    lat_lon_attributes: dict = DEFAULT_LAT_LON_ATTRIBUTES,
    global_attributes: dict = None,
) -> xr.Dataset:
    """
    Convert neighbour data in polars format to xarray dataset.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col
    neighbour_metadata :
        Metadata for the rainfall data with 'latitude' and 'longitude'
    projection :
        cartesian/metric coordinate system
    time_units :
        Units and encoding of the 'time' column
    rainfall_attributes :
        Attributes for rainfall in the xarray Dataset
    lat_lon_attributes :
        Attributes for lat and lon in the xarray Dataset
    global_attributes :
        Global attributes for xarray Dataset

    Returns
    -------
    neighbour_data_ds :
        xarray dataset with assigned attributes

    """
    # 1. convert to xarray via pandas
    neighbour_data_ds = neighbour_data.to_pandas().set_index("time").to_xarray().to_array(dim="id")
    neighbour_data_ds = neighbour_data_ds.to_dataset(name="rainfall")

    # 2. assign coords
    neighbour_data_ds = neighbour_data_ds.assign_coords(
        longitude=("id", neighbour_metadata["longitude"].to_numpy()),
        latitude=("id", neighbour_metadata["latitude"].to_numpy()),
    )

    # 3. set encoding attribute for time
    neighbour_data_ds.time.encoding["units"] = time_units
    neighbour_data_ds["time"] = neighbour_data_ds["time"].assign_attrs({"unit": time_units})

    # 4. Assign variable attributes
    neighbour_data_ds["rainfall"] = neighbour_data_ds["rainfall"].assign_attrs(rainfall_attributes)
    neighbour_data_ds["longitude"] = neighbour_data_ds["longitude"].assign_attrs(lat_lon_attributes)
    neighbour_data_ds["latitude"] = neighbour_data_ds["latitude"].assign_attrs(lat_lon_attributes)

    # 5. Assign global attributes
    neighbour_data_ds = neighbour_data_ds.assign_attrs(global_attributes)

    # 6. reproject xarray
    neighbour_data_ds.coords["x"], neighbour_data_ds.coords["y"] = plg.spatial.project_point_coordinates(
        x=neighbour_data_ds.longitude, y=neighbour_data_ds.latitude, target_projection=projection
    )

    return neighbour_data_ds


def compute_distance_matrix(neighbour_data_ds: xr.Dataset) -> xr.Dataset:
    """
    Compute a distance matrix.

    Parameters
    ----------
    neighbour_data_ds :
        xarray dataset of neighbour data

    Returns
    -------
    distance_matrix :
        A distance matrix of all neighbouring gauges

    """
    distance_matrix = plg.spatial.calc_point_to_point_distances(neighbour_data_ds, neighbour_data_ds)
    return distance_matrix


def subset_distance_matrix(
    neighbour_data_ds: xr.Dataset, distance_matrix: xr.Dataset, max_distance_for_neighbours: int | float
) -> xr.Dataset:
    """
    Compute a distance matrix.

    Parameters
    ----------
    neighbour_data_ds :
        xarray dataset of neighbour data
    distance_matrix :
        A distance matrix of all neighbouring gauges
    max_distance_for_neighbours :
        Maximum distance to consider for neighbours

    Returns
    -------
    neighbour_data_ds :
        A distance matrix of all neighbouring gauges

    """
    # 1. to remove
    distance_matrix.load()

    # 2. select nearest neighbours with max_distance buffer
    nbrs_not_nan = []
    reference = []

    for pws_id in neighbour_data_ds.id.data:
        neighbor_ids = distance_matrix.id.data[
            (distance_matrix.sel(id=pws_id) < max_distance_for_neighbours) & (distance_matrix.sel(id=pws_id) > 0)
        ]

        N = neighbour_data_ds.rainfall.sel(id=neighbor_ids).notnull().sum(dim="id")  # noqa: PD004
        nbrs_not_nan.append(N)

        median = neighbour_data_ds.sel(id=neighbor_ids).rainfall.median(dim="id")
        reference.append(median)

    neighbour_data_ds["nbrs_not_nan"] = xr.concat(nbrs_not_nan, dim="id")
    neighbour_data_ds["reference"] = xr.concat(reference, dim="id")
    return neighbour_data_ds
