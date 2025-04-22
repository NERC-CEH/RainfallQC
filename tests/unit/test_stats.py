#!/usr/bin/env python

"""Tests for statstics."""

from rainfallqc.utils import stats


def test_pettitt_test(example_array):
    stats.pettitt_test(example_array)
