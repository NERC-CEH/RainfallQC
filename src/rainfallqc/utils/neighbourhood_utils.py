# -*- coding: utf-8 -*-
"""
All neighbourhood and nearby related operations.

Classes and functions ordered alphabetically.
"""

import xarray as xr


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
