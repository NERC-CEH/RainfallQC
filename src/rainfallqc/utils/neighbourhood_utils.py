# -*- coding: utf-8 -*-
"""
All neighbourhood and nearby related operations.

Classes and functions ordered alphabetically.
"""

import datetime

import geopy.distance
import polars as pl
import xarray as xr


def compute_km_distance_from_target_id(gauge_network_metadata: pl.DataFrame, target_id: str) -> pl.DataFrame:
    """
    Compute kilometre distances between gauges in network and target gauges.

    Parameters
    ----------
    gauge_network_metadata :
        Metadata for gauge network. Each gauge must have 'longitude' and 'latitude'.
    target_id :
        Target gauge to compare against.

    Returns
    -------
    neighbour_distances_df :
        Data of distances to a target gauge in kilometers

    """
    # 1. Get target station lat and lon
    target_station = gauge_network_metadata.filter(pl.col("station_id") == target_id)
    target_latlon = (
        target_station["latitude"].item(),
        target_station["longitude"].item(),
    )

    # 2. Calculate lat/lon distances from the target gauge
    neighbour_distances = {}
    for other_station_id, other_lat, other_lon in gauge_network_metadata[
        ["station_id", "latitude", "longitude"]
    ].rows():
        neighbour_distances[other_station_id] = geopy.distance.geodesic(
            target_latlon, (other_lat, other_lon)
        ).kilometers

    # 3. Convert to pl.Dataframe
    neighbour_distances_df = pl.DataFrame(
        {
            "station_id": neighbour_distances.keys(),
            "distance": neighbour_distances.values(),
        }
    )

    return neighbour_distances_df


def compute_temporal_overlap_days(
    start_1: datetime.datetime, end_1: datetime.datetime, start_2: datetime.datetime, end_2: datetime.datetime
) -> int:
    """
    Compute temporal overlap in days.

    Note: assumes that the data is contiguous

    Parameters
    ----------
    start_1 :
        Start time of timestamp 1
    end_1 :
        End time of timestamp 2
    start_2 :
        Start time of timestamp 2
    end_2 :
        End time of timestamp 2

    Returns
    -------
    overlap_days :
        Days that overlap between the two timestamps

    """
    overlap_start = max(start_1, start_2)
    overlap_end = min(end_1, end_2)
    overlap_days = max(0, (overlap_end - overlap_start).days)
    return overlap_days


def get_n_closest_neighbours(
    neighbour_distances_df: pl.DataFrame, distance_threshold: int | float, n_closest: int
) -> pl.DataFrame:
    """
    Get closest neighbours from neighbour distances data.

    Will return more than number of n_closest if there is multiple values that are equal at that index.
    Will not return values that are 0 dist away.

    Parameters
    ----------
    neighbour_distances_df :
        Data of distances to a target gauge
    distance_threshold :
        Threshold for maximum distance considered
    n_closest :
        Number of closest neighbours.

    Returns
    -------
    n_closest_neighbour_df :
        Data of n_closest neighbours

    """
    # 1. Subset based on distance threshold
    close_neighbours = neighbour_distances_df.filter(
        (pl.col("distance") <= distance_threshold) & (pl.col("distance") != 0)
    )

    # 2. Sort neighbours by distance
    sorted_close_neighbours = close_neighbours.sort("distance")

    # 3. Get distances at the n-th position
    if sorted_close_neighbours.height < n_closest:
        # 3.1 return all if not enough rows
        return sorted_close_neighbours
    else:
        nth_distance = sorted_close_neighbours[n_closest - 1, "distance"]
        # 3.2 Filter all neighbours by distance less or equal to nth_closest
        return sorted_close_neighbours.filter(pl.col("distance") <= nth_distance)


def get_nearest_etccdi_val_to_gauge(
    etccdi_data: xr.Dataset, gauge_lat: int | float, gauge_lon: int | float
) -> xr.Dataset:
    """
    Get the value at the nearest ETCCDI grid cell to the gauge coordinates.

    Parameters
    ----------
    etccdi_data
        ETCCDI data with given variable to check
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge

    Returns
    -------
    nearby_etccdi_data :
        ETCCDI data at the nearest grid cell

    """
    # 1. Get local data
    nearby_etccdi_data = etccdi_data.sel(
        lon=gauge_lon,
        lat=gauge_lat,
        method="nearest",
    )
    return nearby_etccdi_data
