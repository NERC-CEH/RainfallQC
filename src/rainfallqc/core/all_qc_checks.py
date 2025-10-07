# -*- coding: utf-8 -*-
"""Registry of all the QC checks in RainfallQC."""

import functools

import polars as pl

from rainfallqc.utils import data_utils

QC_CHECKS = {}


def qc_check(name: str, require_non_negative: bool = False) -> callable:
    """
    Register a QC check and check for non-negative values if required.

    Parameters
    ----------
    name :
        Name of the QC check.
    require_non_negative :
        If True, check that the target gauge column has no negative values before running the QC check

    Returns
    -------
    callable :
        Decorator to register the QC check.

    Raises
    ------
    ValueError :
        If require_non_negative is True and the target gauge column contains negative values.

    """

    def decorator(func: callable) -> callable:
        @functools.wraps(func)
        def wrapper(df: pl.DataFrame, *args, **kwargs) -> list:
            # Determine which column the user wants checked
            target_gauge_col = kwargs.get("target_gauge_col")
            if target_gauge_col is None:
                raise ValueError(f"{name} requires 'target_gauge_col' to be provided.")

            # Optional non-negative pre-check
            if require_non_negative:
                if data_utils.check_for_negative_values(df, target_gauge_col):
                    raise ValueError(f"{name} failed: column '{target_gauge_col}' contains negative values.")

            # Run the actual QC check
            return func(df, *args, **kwargs)

        # Register for later use
        QC_CHECKS[name] = wrapper
        return wrapper

    return decorator
