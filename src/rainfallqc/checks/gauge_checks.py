# -*- coding: utf-8 -*-
"""
Quality control checks examining suspicious rain gauges.

Classes and functions ordered alphabetically.
"""

import polars as pl


def get_years_where_percentiles_are_zero(data: pl.DataFrame) -> list:
    """
    Return years where the n-th percentiles is zero.

    This QC1 from the IntenseQC framework

    Parameters
    ----------
    data :
        Rainfall data

    Returns
    -------
    year_list :
        List of years where n-th percentile is zero.

    """
    year_list = [data[0]]

    return year_list
