#!/usr/bin/env python

"""Tests for time-series QC checks."""

import xarray as xr

from rainfallqc.utils import spatial_utils


def test_haversine():
    result = spatial_utils.haversine(xr.DataArray([10]), xr.DataArray([24]), "100", "56")
    assert round(result.values[0]) == 7816
