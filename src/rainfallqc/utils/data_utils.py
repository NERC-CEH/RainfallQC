# -*- coding: utf-8 -*-
"""
All data operations.

Classes and functions ordered alphabetically.
"""

import numpy as np
import polars as pl


def replace_missing_vals_with_nan_gdsr_data(
    gdsr_data: pl.DataFrame,
    rain_col: str,
    missing_val: int = None,
) -> pl.DataFrame:
    """
    Replace no data value with numpy.nan in GDSR data.

    Parameters
    ----------
    gdsr_data :
        GDSR data
    rain_col :
        Column of rainfall
    missing_val :
        Missing value identifier

    Returns
    -------
    gdsr_data
        GDSR data with missing values replaced

    """
    return gdsr_data.with_columns(
        pl.when(pl.col(rain_col) == missing_val).then(np.nan).otherwise(pl.col(rain_col)).alias(rain_col)
    )
