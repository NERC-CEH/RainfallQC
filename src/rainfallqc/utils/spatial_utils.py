# -*- coding: utf-8 -*-
"""
All spatial operations.

Classes and functions ordered alphabetically.
"""

import numpy as np
import xarray as xr


def compute_spatial_mean_xr(data: xr.Dataset, var_name: str) -> xr.Dataset:
    """
    Get the value at the nearest ETCCDI grid cell to the gauge coordinates.

    Parameters
    ----------
    data
        Data with variable to compute mean from. Should have lat/lon and time (as axis 0)
    var_name :
        Variable to make mean value of

    Returns
    -------
    data :
        Data with spatial mean

    """
    # 1. Transpose so time is at 0-th index
    data = data.transpose("time", ...)

    # 2. Mask invalid data
    data_masked = np.ma.masked_invalid(data[var_name])

    # 3. Compute lat/lon mean
    data[f"{var_name}_mean"] = (
        ("lat", "lon"),
        np.ma.mean(data_masked, axis=0),
    )  # axis 0 is time
    return data
