# -*- coding: utf-8 -*-
"""
Quality control checks relying on comparison with a benchmark dataset.

Classes and functions ordered alphabetically.
"""

import polars as pl


def check_annual_exceedance_ETCCDI_R99p(data: pl.DataFrame, rain_col: str) -> list:
    """
    Check annual exceedance of maximum R99p from ETCCDI dataset.

    Parameters
    ----------
    data :
        Rainfall data
    rain_col :
        Column with rainfall data


    Returns
    -------
    flag_list :
        List of flags

    """
    flag_list = []

    return flag_list
