#!/usr/bin/env python

"""Test statistics."""

import polars as pl

from rainfallqc.utils import stats


def test_pettitt_test(example_array):
    tau, p = stats.pettitt_test(example_array)
    assert tau == 6
    assert round(p, 2) == 0.03


def test_pettitt_test_pl(example_array):
    example_series = pl.Series(example_array)
    tau, p = stats.pettitt_test(example_series)
    assert tau == 6
    assert round(p, 2) == 0.03
