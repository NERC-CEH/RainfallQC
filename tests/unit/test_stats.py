#!/usr/bin/env python

"""Test statistics."""

import numpy as np

from rainfallqc.utils import stats


def test_pettitt_test(example_array):
    tau, p = stats.pettitt_test(example_array)
    # assert np.round(tau, 2) == 1.54
    assert np.round(p, 2) == 0.04
