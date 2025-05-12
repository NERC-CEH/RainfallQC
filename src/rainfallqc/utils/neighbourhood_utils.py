# -*- coding: utf-8 -*-
"""
All neighbourhood and nearby related operations.

Classes and functions ordered alphabetically.
"""

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
        Dataframe with distances to target gauge in kilometers

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
            "distances": neighbour_distances.values(),
        }
    )

    return neighbour_distances_df


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
