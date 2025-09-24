# -*- coding: utf-8 -*-
"""
Quality control checks translated from the pyPWSQC framework (https://pypwsqc.readthedocs.io/en/latest/).

The PWSQC framework includes filters originally develop for automated PWS within the COST Action OPENSENSE.

'run_' and 'check_' relate to the algorithms from pyPWSQC.

Functions are ordered alphabetically.
"""

import polars as pl


def run_bias_correction(neighbour_data: pl.DataFrame) -> None:
    """
    Bias correction.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def run_event_based_filter(neighbour_data: pl.DataFrame) -> None:
    """
    Event based filter (EBF).

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def check_faulty_zeros(neighbour_data: pl.DataFrame) -> None:
    """
    Will flag ...

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    Examples
    --------
    available at: https://pypwsqc.readthedocs.io/en/latest/notebooks/merged_filters.html

    """
    pass


def check_high_influx_filter(neighbour_data: pl.DataFrame) -> None:
    """
    High influx filter.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def run_indicatior_correlation(neighbour_data: pl.DataFrame) -> None:
    """
    Run indicator correlation.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def run_peak_removal(neighbour_data: pl.DataFrame) -> None:
    """
    Peak removal.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass


def check_station_outlier(neighbour_data: pl.DataFrame) -> None:
    """
    Station outlier.

    Parameters
    ----------
    neighbour_data :
        Rainfall data of neighbouring gauges with time col

    Returns
    -------
    neighbour_data :
        todo

    """
    pass
