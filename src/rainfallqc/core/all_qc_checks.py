# -*- coding: utf-8 -*-
"""Registry of all the QC checks in RainfallQC."""

import functools
import itertools

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
            columns_to_check = []
            columns_to_check = get_columns_in_kwargs(
                kwargs, kwarg_name="target_gauge_col", column_list=columns_to_check, name=name
            )

            for kwarg_name in ["neighbouring_gauge_col", "neighbouring_gauge_cols"]:
                if kwarg_name in kwargs:
                    columns_to_check = get_columns_in_kwargs(
                        kwargs, kwarg_name=kwarg_name, column_list=columns_to_check, name=name
                    )

            # flatten column list for neighbouring_gauge_cols
            columns_to_check = list(
                itertools.chain.from_iterable(col if isinstance(col, list) else [col] for col in columns_to_check)
            )

            # Optional non-negative pre-check
            for col in columns_to_check:
                if require_non_negative and data_utils.check_for_negative_values(df, col):
                    raise ValueError(f"{name} failed: column '{col}' contains negative values.")

            # Run the actual QC check
            return func(df, *args, **kwargs)

        # Register for later use
        QC_CHECKS[name] = wrapper
        return wrapper

    return decorator


def get_columns_in_kwargs(kwargs: dict, kwarg_name: str, column_list: list, name: str) -> list:
    """
    Check that a column exists in the DataFrame.

    Parameters
    ----------
    kwargs :
        Dictionary of keyword arguments.
    kwarg_name :
        Name of the kwarg to check.
    column_list :
        List to append the column_name to if it exists.
    name :
        Name of the QC check (for error messages).

    Raises
    ------
    ValueError :
        If the column does not exist in the DataFrame.

    """
    col_name = kwargs.get(kwarg_name)  # user defined column name for that kwarg

    if col_name is None:
        raise ValueError(f"{name} requires '{kwarg_name}' to be provided.")
    column_list.append(col_name)
    return column_list
