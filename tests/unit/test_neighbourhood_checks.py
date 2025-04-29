#!/usr/bin/env python

"""Tests for neighbourhood quality control checks."""

import numpy.testing
import pytest

from rainfallqc.checks import neighbour_checks

DEFAULT_RAIN_COL = "rain_mm"
DISTANCE_THRESHOLD = 50  # 50 km
OVERLAP_THRESHOLD = 365 * 3  # three years

test = (DEFAULT_RAIN_COL, pytest, numpy.testing, neighbour_checks)
