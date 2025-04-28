# -*- coding: utf-8 -*-
"""
Quality control checks relying on comparison with a benchmark dataset.

Classes and functions ordered alphabetically.
"""

import numpy as np
import polars as pl

from rainfallqc.utils import data_readers


def check_annual_exceedance_ETCCDI_R99p(
    data: pl.DataFrame, rain_col: str, gauge_lat: int | float, gauge_lon: int | float
) -> list:
    """
    Check annual exceedance of maximum R99p from ETCCDI dataset.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data
    gauge_lat :
        latitude of the rain gauge
    gauge_lon :
        longitude of the rain gauge

    Returns
    -------
    flag_list :
        List of flags

    """
    # Load R99p data
    etcddi_r99p = data_readers.load_ETCCDI_data(etccdi_var="R99p")

    # Get maximum R99p value
    max_r99p = np.max(etcddi_r99p["R99p"])

    # Get local R99p data
    one_gauge_r99p = etcddi_r99p.sel(
        lon=gauge_lon,
        lat=gauge_lat,
        method="nearest",
    )

    flag_list = []

    return flag_list, one_gauge_r99p, max_r99p
