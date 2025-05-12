#!/usr/bin/env python

"""Tests for neighbourhood utility functions."""

from rainfallqc.utils import neighbourhood_utils


def test_compute_distance_from_target_id(gdsr_gauge_network):
    result = neighbourhood_utils.compute_km_distance_from_target_id(
        gauge_network_metadata=gdsr_gauge_network, target_id="DE_00310"
    )
    assert round(result["DE_02483"], 2) == 13.13
