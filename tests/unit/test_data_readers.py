#!/usr/bin/env python

"""Tests for data loaders."""

from rainfallqc.utils import data_readers

# test when start_datetime not found


def test_load_R99p_ETCCDI_data():
    data_readers.load_ETCCDI_data(etccdi_var="R99p")
