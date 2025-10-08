# -*- coding: utf-8 -*-
"""All neighbourhood and nearby related operations."""

import datetime

import geopy.distance
import numpy as np
import polars as pl
import xarray as xr

from rainfallqc.utils import spatial_utils

STATION_ID_COL = "station_id"
START_DATETIME_COL = "start_datetime"
END_DATETIME_COL = "end_datetime"


def get_target_neighbour_non_zero_minima(
    data: pl.DataFrame, target_col: str, other_col: str, default_minima: float = 0.1
) -> float:
    """
    Get minimum  non-zero value in rainfall data between target and neighbour.

    Parameters
    ----------
    data :
        Rainfall data
    target_col :
        Target rainfall column
    other_col :
        Other rainfall column
    default_minima :
        Default minimum to use for non-zero value

    Returns
    -------
    non_zero_minima :
        Minimum non-zero value.

    """
    target_col_min = np.around(data.filter(pl.col(target_col) >= default_minima).min()[target_col], 1)[0]
    other_col_min = np.around(
        data.filter(pl.col(other_col) >= default_minima).min()[other_col],
        1,
    )[0]
    non_zero_minima = max(float(target_col_min), float(other_col_min), default_minima)
    return non_zero_minima


def make_rain_not_minima_column_target_or_neighbour(
    data: pl.DataFrame, target_col: str, other_col: str, data_minima: float
) -> pl.DataFrame:
    """
    Get rain values that are not minima rainfall for target or neighbour.

    Parameters
    ----------
    data :
        Rainfall data
    target_col :
        Target rainfall column
    other_col :
        Other rainfall column
    data_minima :
        Data minimum (i.e. lowest non-zero value)

    Returns
    -------
    data :
     Rainfall data with "rain_not_minima" column

    """
    valid_data = pl.col(target_col).is_not_nan() & pl.col(other_col).is_not_nan()
    return data.with_columns(
        pl.when(valid_data & (pl.col(target_col) > data_minima) & (pl.col(other_col) > data_minima))
        .then(1)
        .when(
            valid_data & (pl.col(target_col) == data_minima) & (pl.col(other_col) == data_minima),
        )
        .then(1)
        .when(
            valid_data & (pl.col(target_col) == data_minima) & (pl.col(other_col) > data_minima),
        )
        .then(0)
        .when(valid_data & (pl.col(target_col) > data_minima) & (pl.col(other_col) == data_minima))
        .then(0)
        .otherwise(np.nan)
        .alias("rain_not_minima")
    )


def get_rain_not_minima_column(data: pl.DataFrame, target_col: str, other_col: str) -> pl.DataFrame:
    """
    Get rain not equal to minima column.

    Combines two functions for getting non_zero_minima i.e. 0.1 and then get 'rain_not_minima'

    Parameters
    ----------
    data :
        Rainfall data
    target_col :
        Target rainfall column
    other_col :
        Other rainfall column

    Returns
    -------
    data_w_minima_col :
        Rainfall data with rain is minima column

    """
    non_zero_minima = get_target_neighbour_non_zero_minima(data, target_col=target_col, other_col=other_col)
    # 2.3 make 'rain_not_minima' column
    data_w_minima_col = make_rain_not_minima_column_target_or_neighbour(
        data,
        target_col=target_col,
        other_col=other_col,
        data_minima=non_zero_minima,
    )
    return data_w_minima_col


def get_ids_of_n_nearest_overlapping_neighbouring_gauges(
    gauge_network_metadata: pl.DataFrame,
    target_id: str,
    distance_threshold: int | float,
    n_closest: int,
    min_overlap_days: int,
    station_id_col: str = STATION_ID_COL,
    start_datetime_col: str = START_DATETIME_COL,
    end_datetime_col: str = END_DATETIME_COL,
) -> set:
    """
    Get gauge IDs of nearest n time-overlapping neighbouring gauges.

    Parameters
    ----------
    gauge_network_metadata :
        Metadata for gauge network. Each gauge must have 'longitude' and 'latitude'.
    target_id :
        Target gauge to compare against.
    distance_threshold :
        Threshold for maximum distance considered
    n_closest :
        Number of closest neighbours.
    min_overlap_days :
        Minimum overlap between target and neighbouring gauges
    station_id_col :
        Column name for station ID in gauge_network_metadata (default 'station_id')
    start_datetime_col  :
        Column name for start datetime in gauge_network_metadata (default 'start_datetime')
    end_datetime_col  :
        Column name for end datetime in gauge_network_metadata (default 'end_datetime')

    Returns
    -------
    neighbouring_gauge_id :
        IDs of neighbouring gauges within a given distance to target and min overlapping days

    """
    # 1. Compute distances between neighbours and target
    neighbour_distances_df = compute_km_distances_from_target_id(
        gauge_network_metadata, target_id=target_id, station_id_col=station_id_col
    )

    # 2. Compute overlapping days between neighbours and target
    neighbour_overlap_days_df = compute_temporal_overlap_days_from_target_id(
        gauge_network_metadata,
        target_id=target_id,
        station_id_col=station_id_col,
        start_datetime_col=start_datetime_col,
        end_datetime_col=end_datetime_col,
    )

    # 3. Subset n_closest based on distance threshold
    neighbour_distances_df = get_n_closest_neighbours(
        neighbour_distances_df, distance_threshold=distance_threshold, n_closest=n_closest
    )

    # 4. Subset based on min overlap days
    neighbour_overlap_days_df = get_neighbours_with_min_overlap_days(
        neighbour_overlap_days_df, min_overlap_days=min_overlap_days
    )

    # 5. get all ids of neighbouring gauges
    neighbour_distances_ids = neighbour_distances_df[station_id_col].to_list()
    neighbour_overlap_ids = neighbour_overlap_days_df[station_id_col].to_list()

    # 6. Select gauge IDs meeting both conditions
    all_neighbour_ids = set(neighbour_distances_ids).intersection(set(neighbour_overlap_ids))
    return all_neighbour_ids


def compute_temporal_overlap_days(
    start_1: datetime.datetime, end_1: datetime.datetime, start_2: datetime.datetime, end_2: datetime.datetime
) -> int:
    """
    Compute temporal overlap in days.

    Note: assumes that the data is contiguous.

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


def compute_temporal_overlap_days_from_target_id(
    gauge_network_metadata: pl.DataFrame,
    target_id: str,
    station_id_col: str,
    start_datetime_col: str,
    end_datetime_col: str,
) -> pl.DataFrame:
    """
    Compute overlap in days between target gauges and its neighbours.

    Note: assumes that the data is contiguous.

    Parameters
    ----------
    gauge_network_metadata :
        Metadata for gauge network. Each gauge must have 'longitude' and 'latitude'.
    target_id :
        Target gauge to compare against.
    station_id_col :
        Column name for station ID in gauge_network_metadata
    start_datetime_col  :
        Column name for start datetime in gauge_network_metadata
    end_datetime_col  :
        Column name for end datetime in gauge_network_metadata

    Returns
    -------
    neighbour_overlap_days_df :
        Neighbouring gauges with overlap days to target gauge.

    """
    # 1. Get target station and start and end date
    target_station = gauge_network_metadata.filter(pl.col(station_id_col) == target_id)
    start_1, end_1 = (
        target_station[start_datetime_col].item(),
        target_station[end_datetime_col].item(),
    )

    # 2. Compute overlap days between target station to other start and end date
    neighbour_overlap_days = {}
    for other_station_id, start_2, end_2 in gauge_network_metadata[
        [station_id_col, start_datetime_col, end_datetime_col]
    ].rows():
        if target_id == other_station_id:
            continue

        neighbour_overlap_days[other_station_id] = compute_temporal_overlap_days(start_1, end_1, start_2, end_2)

    # 3. Convert to pl.Dataframe
    neighbour_overlap_days_df = pl.DataFrame(
        {
            station_id_col: neighbour_overlap_days.keys(),
            "overlap_days": neighbour_overlap_days.values(),
        }
    )
    return neighbour_overlap_days_df


def get_neighbours_with_min_overlap_days(
    neighbour_overlap_days_df: pl.DataFrame, min_overlap_days: int
) -> pl.DataFrame:
    """
    Get neighbours around gauge at least min_overlap_days of overlapping time steps.

    Note: assumes that the data is contiguous.

    Parameters
    ----------
    neighbour_overlap_days_df :
        Neighbouring gauges with overlap days to target gauge.
    min_overlap_days :
        Minimum overlap between target and neighbouring gauges

    Returns
    -------
    neighbour_overlap_days_df :
        Neighbouring gauges with at least min_overlap_days overlap days.

    """
    return neighbour_overlap_days_df.filter(pl.col("overlap_days") >= min_overlap_days)


def compute_km_distances_from_target_id(
    gauge_network_metadata: pl.DataFrame, target_id: str, station_id_col: str
) -> pl.DataFrame:
    """
    Compute kilometre distances between gauges in network and target gauges.

    Parameters
    ----------
    gauge_network_metadata :
        Metadata for gauge network. Each gauge must have 'longitude' and 'latitude'.
    target_id :
        Target gauge to compare against.
    station_id_col :
        Column name for station ID in gauge_network_metadata

    Returns
    -------
    neighbour_distances_df :
        Data of distances to a target gauge in kilometers

    """
    # 1. Get target station lat and lon
    target_station = gauge_network_metadata.filter(pl.col(station_id_col) == target_id)
    target_latlon = (
        target_station["latitude"].item(),
        target_station["longitude"].item(),
    )

    # 2. Calculate lat/lon distances from the target gauge
    neighbour_distances = {}
    for other_station_id, other_lat, other_lon in gauge_network_metadata[
        [station_id_col, "latitude", "longitude"]
    ].rows():
        neighbour_distances[other_station_id] = geopy.distance.geodesic(
            target_latlon, (other_lat, other_lon)
        ).kilometers

    # 3. Convert to pl.Dataframe
    neighbour_distances_df = pl.DataFrame(
        {
            station_id_col: neighbour_distances.keys(),
            "distance": neighbour_distances.values(),
        }
    )

    return neighbour_distances_df


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


def get_nearest_non_nan_etccdi_val_to_gauge(
    etccdi_data: xr.Dataset,
    etccdi_name: str,
    gauge_lat: int | float,
    gauge_lon: int | float,
    max_distance_km: int | float = 500,
) -> xr.Dataset:
    """
    Get the value at the nearest non-nan ETCCDI grid cell to the gauge coordinates.

    Parameters
    ----------
    etccdi_data
        ETCCDI data with given variable to check
    etccdi_name :
        ETCCDI variable name to check
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge
    max_distance_km :
        Maximum distance in km to search for a non-nan value (default 500 km)

    Returns
    -------
    nearby_etccdi_data :
        ETCCDI data at the nearest grid cell with non-nan values

    """
    # 1. Stack lat/lon into a single dimension
    stacked = etccdi_data.stack(points=("lat", "lon"))

    # 2. Compute haversine distance to each point
    dists = spatial_utils.haversine(stacked["lon"], stacked["lat"], gauge_lon, gauge_lat)

    # 3. Sort by distance
    sorted_idx = dists.argsort()

    # Loop through points in ascending distance order
    for idx in sorted_idx.values:
        dist_km = dists.isel(points=idx).item()
        if dist_km <= max_distance_km:
            if not np.isnan(stacked[etccdi_name].isel(points=idx)).all():
                sel_lon = stacked["lon"].isel(points=idx).item()
                sel_lat = stacked["lat"].isel(points=idx).item()
                return etccdi_data.sel(lon=sel_lon, lat=sel_lat)
        else:
            # Because sorted by distance, if we've exceeded max distance, we can break early
            break

    raise ValueError(
        f"""No non-NaN point found within {max_distance_km} km of ({gauge_lat}, {gauge_lon}).
        Assuming EPSG:4326 coordinates."""
    )
