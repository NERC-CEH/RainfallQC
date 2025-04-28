# -*- coding: utf-8 -*-
"""
Quality control checks relying on comparison with a benchmark dataset.

Classes and functions ordered alphabetically.
"""

import polars as pl

from rainfallqc.utils import data_readers


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
    etcddi_r99p = data_readers.load_ETCCDI_data(etccdi_var="R99p")

    flag_list = []

    return flag_list, etcddi_r99p
