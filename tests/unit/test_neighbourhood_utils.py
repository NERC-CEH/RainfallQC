#!/usr/bin/env python

"""Tests for neighbourhood utility functions."""

import datetime

import polars as pl

from rainfallqc.utils import neighbourhood_utils


def test_compute_distance_from_target_id(gdsr_gauge_network):
    result = neighbourhood_utils.compute_km_distances_from_target_id(
        gauge_network_metadata=gdsr_gauge_network, target_id="DE_00310"
    )
    assert round(result.filter(pl.col("station_id") == "DE_02483")["distance"][0], 2) == 13.13
    assert round(result.filter(pl.col("station_id") == "DE_00310")["distance"][0], 2) == 0.0


def test_get_n_closest_neighbours(gdsr_gauge_network):
    neighbouring_gauges = neighbourhood_utils.compute_km_distances_from_target_id(
        gauge_network_metadata=gdsr_gauge_network, target_id="DE_00310"
    )
    # distance should be in km
    result = neighbourhood_utils.get_n_closest_neighbours(neighbouring_gauges, distance_threshold=50, n_closest=10)
    assert len(result) == 10
    assert round(result["distance"].min(), 2) == 9.35
    result = neighbourhood_utils.get_n_closest_neighbours(neighbouring_gauges, distance_threshold=10, n_closest=10)
    assert len(result) == 1


def test_compute_temporal_overlap_days():
    result = neighbourhood_utils.compute_temporal_overlap_days(
        datetime.datetime(2001, 1, 1),
        datetime.datetime(2004, 5, 1),
        datetime.datetime(1997, 1, 1),
        datetime.datetime(2002, 5, 1),
    )
    assert result == 485

    result = neighbourhood_utils.compute_temporal_overlap_days(
        datetime.datetime(2001, 1, 1),
        datetime.datetime(2004, 5, 1),
        datetime.datetime(1997, 1, 1),
        datetime.datetime(2000, 5, 1),
    )
    assert result == 0


def test_compute_temporal_overlap_days_from_target_id(gdsr_gauge_network):
    result = neighbourhood_utils.compute_temporal_overlap_days_from_target_id(gdsr_gauge_network, target_id="DE_00310")
    assert result.filter(pl.col("station_id") == "DE_02483")["overlap_days"][0] == 1825
    assert result.filter(pl.col("station_id") == "DE_00389")["overlap_days"][0] == 425


def test_get_neighbours_with_min_overlap_days(gdsr_gauge_network):
    neighbour_overlap_days_df = neighbourhood_utils.compute_temporal_overlap_days_from_target_id(
        gdsr_gauge_network, target_id="DE_00310"
    )
    result = neighbourhood_utils.get_neighbours_with_min_overlap_days(neighbour_overlap_days_df, min_overlap_days=1500)
    assert len(result) == 8
    assert len(neighbour_overlap_days_df) == 10


def test_get_ids_of_n_nearest_overlapping_neighbouring_gauges(gdsr_gauge_network):
    result = neighbourhood_utils.get_ids_of_n_nearest_overlapping_neighbouring_gauges(
        gdsr_gauge_network, target_id="DE_00310", distance_threshold=50, n_closest=10, min_overlap_days=1500
    )
    assert len(result) == 8

    result = neighbourhood_utils.get_ids_of_n_nearest_overlapping_neighbouring_gauges(
        gdsr_gauge_network, target_id="DE_00310", distance_threshold=50, n_closest=10, min_overlap_days=500
    )
    assert len(result) == 9


def test_get_target_neighbour_non_zero_minima(gauge_comparison_data):
    result = neighbourhood_utils.get_target_neighbour_non_zero_minima(
        gauge_comparison_data, target_col="gauge1", other_col="gauge2", default_minima=0.1
    )
    assert result == 0.1
    result = neighbourhood_utils.get_target_neighbour_non_zero_minima(
        gauge_comparison_data, target_col="gauge1", other_col="gauge2", default_minima=1.0
    )
    assert result == 1.2


def test_get_gauges_not_minima_column_target_or_neighbour(gauge_comparison_data):
    result = neighbourhood_utils.get_gauges_not_minima_column_target_or_neighbour(
        gauge_comparison_data, target_col="gauge1", other_col="gauge2", data_minima=0.1
    )
    assert result["gauges_not_minima"].value_counts().filter(pl.col("gauges_not_minima") == 0)["count"].item() == 2
    assert result["gauges_not_minima"].value_counts().filter(pl.col("gauges_not_minima") == 1)["count"].item() == 4
    result = neighbourhood_utils.get_gauges_not_minima_column_target_or_neighbour(
        gauge_comparison_data, target_col="gauge1", other_col="gauge2", data_minima=0.7
    )
    assert result["gauges_not_minima"].value_counts().filter(pl.col("gauges_not_minima") == 0)["count"].item() == 1
    assert result["gauges_not_minima"].value_counts().filter(pl.col("gauges_not_minima") == 1)["count"].item() == 2
    result = neighbourhood_utils.get_gauges_not_minima_column_target_or_neighbour(
        gauge_comparison_data, target_col="gauge1", other_col="gauge2", data_minima=2.0
    )
    assert result["gauges_not_minima"].value_counts().filter(pl.col("gauges_not_minima") == 1)["count"].item() == 1
