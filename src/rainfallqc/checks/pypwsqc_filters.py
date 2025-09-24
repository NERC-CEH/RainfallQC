# -*- coding: utf-8 -*-
"""
Quality control checks translated from the pyPWSQC framework (https://pypwsqc.readthedocs.io/en/latest/).

The PWSQC framework includes filters originally develop for automated PWS within the COST Action OPENSENSE.

'run_' and 'check_' relate to the algorithms from pyPWSQC.

Functions are ordered alphabetically.
"""

from typing import List

import polars as pl
import poligrain as plg
import pypwsqc.flagging
import xarray as xr

from rainfallqc.checks import neighbourhood_checks
from rainfallqc.utils import data_utils

MAX_DISTANCE_M = 10e3

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
    target_gauge_col: str,
    neighbouring_gauge_cols: List[str],
    time_res: str,
    time_units: str,
    projection: str,
    max_distance_for_neighbours: int | float,
    nint: int,
    n_stat: int,
    rainfall_attributes: dict = DEFAULT_RAINFALL_ATTRIBUTES,
    lat_lon_attributes: dict = DEFAULT_LAT_LON_ATTRIBUTES,
) -> xr.Dataset:
    """
    Will flag ...

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col
    neighbour_metadata :
        Metadata for the rainfall data with 'latitude' and 'longitude'
    target_gauge_col :
        Target gauge column
    neighbouring_gauge_cols:
        List of columns with neighbouring gauges
    time_res :
        Time resolution of data
    time_units :
        Units and encoding of the 'time' column
    projection :
        cartesian/metric coordinate system
    max_distance_for_neighbours :
        Maximum distance to consider for neighbours
    nint :
        nint
    n_stat :
        n_stat
    rainfall_attributes :
        Attributes for rainfall in the xarray Dataset
    lat_lon_attributes :
        Attributes for lat and lon in the xarray Dataset

    Returns
    -------
    neighbour_data :
        todo

    Examples
    --------
    available at: https://pypwsqc.readthedocs.io/en/latest/notebooks/merged_filters.html

    """
    # 0. Initial checks
    data_utils.check_data_is_specific_time_res(neighbour_data, time_res)
    neighbouring_gauge_cols_new = neighbouring_gauge_cols.copy()  # make copy
    if target_gauge_col in neighbouring_gauge_cols_new:
        # Remove target col from list so it is not included as a neighbour of itself.
        neighbouring_gauge_cols_new.remove(target_gauge_col)
    neighbourhood_checks.check_neighbouring_gauge_columns(neighbour_data, target_gauge_col, neighbouring_gauge_cols_new)

    # 1. filter metadata to only be nearby

    # 2. convert to xarray
    neighbour_data_ds = neighbour_data.to_pandas().set_index("time").to_xarray().to_array(dim="id")
    neighbour_data_ds = neighbour_data_ds.to_dataset(name="rainfall")

    # 3. assign coords
    neighbour_data_ds = neighbour_data_ds.assign_coords(
        longitude=("id", neighbour_metadata["longitude"].to_numpy()),
        latitude=("id", neighbour_metadata["latitude"].to_numpy()),
        elevation=("id", neighbour_metadata["elevation"].to_numpy()),
    )

    # 4. set encoding attribute for time
    neighbour_data_ds.time.encoding["units"] = time_units
    # coordiante attributes
    neighbour_data_ds["time"] = neighbour_data_ds["time"].assign_attrs({"unit": time_units})

    # 5. Assign attributes
    neighbour_data_ds["rainfall"] = neighbour_data_ds["rainfall"].assign_attrs(rainfall_attributes)
    neighbour_data_ds["longitude"] = neighbour_data_ds["longitude"].assign_attrs(lat_lon_attributes)
    neighbour_data_ds["latitude"] = neighbour_data_ds["latitude"].assign_attrs(lat_lon_attributes)

    # 6. reproject xarray
    neighbour_data_ds.coords["x"], neighbour_data_ds.coords["y"] = plg.spatial.project_point_coordinates(
        x=neighbour_data_ds.longitude, y=neighbour_data_ds.latitude, target_projection=projection
    )

    # 7. compute distance matrix (if not already exists)
    distance_matrix = plg.spatial.calc_point_to_point_distances(neighbour_data_ds, neighbour_data_ds)
    distance_matrix.load()

    # 8. select nearest neighbours with max_distance buffer
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

    # 9. run FZ filter
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


def run_indicatior_correlation(neighbour_data: pl.DataFrame) -> None:
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


def check_station_outlier(neighbour_data: pl.DataFrame) -> None:
    """
    Station outlier.

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
