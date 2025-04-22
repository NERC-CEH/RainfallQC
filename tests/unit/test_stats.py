#!/usr/bin/env python

"""Test statistics."""

from rainfallqc.utils import stats


def test_pettitt_test(example_array):
    tau, p = stats.pettitt_test(example_array)
    assert tau == 6
    assert round(p, 2) == 0.03
