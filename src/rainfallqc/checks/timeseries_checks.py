# -*- coding: utf-8 -*-
"""
Quality control checks based on suspicious time-series artefacts.

Time-series checks are defined as QC checks that: "detect abnormalities in patterns of the data record."

Classes and functions ordered by appearance in IntenseQC framework.
"""

import numpy as np
import polars as pl
import xarray as xr

from rainfallqc.utils import data_readers, data_utils, neighbourhood_utils


def dry_period_cdd_check(
    data: pl.DataFrame, rain_col: str, gauge_lat: int | float, gauge_lon: int | float
) -> pl.DataFrame:
    """
    Identify suspiciously long dry periods in time-series using the ETCCDI Consecutive Dry Days (CDD) index.

    This is QC11 from the IntenseQC framework.

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
    data_w_cdd_flags :
        Data with CDD flags

    """
    # 1. Load CDD data
    etccdi_cdd = data_readers.load_etccdi_data(etccdi_var="CDD")

    # 2. Make dry spell days column from ETCCDI data
    dry_spell_days = compute_dry_spell_days(etccdi_cdd)

    # 3. Get nearest local CDD value to the gauge coordinates
    nearby_dry_spell_days = neighbourhood_utils.get_nearest_etccdi_val_to_gauge(dry_spell_days, gauge_lat, gauge_lon)

    return data[rain_col], nearby_dry_spell_days


def compute_dry_spell_days(dry_spell_data: xr.Dataset) -> xr.Dataset:
    """
    Compute dry spells in ddys from ETCCDI Consecutive Dry Days data.

    Parameters
    ----------
    dry_spell_data :
        ETCCDI CDD index data

    Returns
    -------
    dry_spell_days :
        ETCCDI CDD index data with `CDD_days` variable

    """
    # Convert CDD from seconds to days
    dry_spell_days = data_utils.convert_datarray_seconds_to_days(dry_spell_data["CDD"])

    # Mask out non-land data
    dry_spell_days[dry_spell_days < 0.0] = np.nan

    # Remove errors from data where more than 366 days are dry
    dry_spell_days[dry_spell_days > 366] = np.nan  # remove errors

    # Remove invalid data
    dry_spell_days = np.ma.masked_invalid(dry_spell_days)

    # Make CDD days variable
    dry_spell_data["CDD_days"] = (("lat", "lon"), np.ma.max(dry_spell_days, axis=0))

    return dry_spell_data
