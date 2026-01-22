#!/usr/bin/env python

"""Tests for neighbourhood utility functions."""

import datetime

import numpy as np
import polars as pl
import pytest

from rainfallqc.utils import data_readers, neighbourhood_utils


def test_compute_distance_from_target_id(gsdr_gauge_network):
    result = neighbourhood_utils.compute_km_distances_from_target_id(
        gauge_network_metadata=gsdr_gauge_network, target_id="DE_00310", station_id_col="station_id"
    )
    assert round(result.filter(pl.col("station_id") == "DE_02483")["distance"][0], 2) == 13.13
    assert len(result.filter(pl.col("station_id") == "DE_00310")) == 0.


def test_get_n_closest_neighbours(gsdr_gauge_network):
    neighbouring_gauges = neighbourhood_utils.compute_km_distances_from_target_id(
        gauge_network_metadata=gsdr_gauge_network, target_id="DE_00310", station_id_col="station_id"
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


def test_compute_temporal_overlap_days_from_target_id(gsdr_gauge_network):
    result = neighbourhood_utils.compute_temporal_overlap_days_from_target_id(
        gsdr_gauge_network,
        target_id="DE_00310",
        station_id_col="station_id",
        start_datetime_col="start_datetime",
        end_datetime_col="end_datetime",
    )
    assert result.filter(pl.col("station_id") == "DE_02483")["overlap_days"][0] == 1825
    assert result.filter(pl.col("station_id") == "DE_00389")["overlap_days"][0] == 425


def test_get_neighbours_with_min_overlap_days(gsdr_gauge_network):
    neighbour_overlap_days_df = neighbourhood_utils.compute_temporal_overlap_days_from_target_id(
        gsdr_gauge_network,
        target_id="DE_00310",
        station_id_col="station_id",
        start_datetime_col="start_datetime",
        end_datetime_col="end_datetime",
    )
    result = neighbourhood_utils.get_neighbours_with_min_overlap_days(neighbour_overlap_days_df, min_overlap_days=1500)
    assert len(result) == 8
    assert len(neighbour_overlap_days_df) == 10


def test_get_ids_of_n_nearest_overlapping_neighbouring_gauges(gsdr_gauge_network):
    result = neighbourhood_utils.get_ids_of_n_nearest_overlapping_neighbouring_gauges(
        gsdr_gauge_network, target_id="DE_00310", distance_threshold=50, n_closest=10, min_overlap_days=1500
    )
    assert len(result) == 8

    result = neighbourhood_utils.get_ids_of_n_nearest_overlapping_neighbouring_gauges(
        gsdr_gauge_network, target_id="DE_00310", distance_threshold=50, n_closest=10, min_overlap_days=500
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


def test_make_rain_not_minima_column_target_or_neighbour(gauge_comparison_data):
    result = neighbourhood_utils.make_rain_not_minima_column_target_or_neighbour(
        gauge_comparison_data, target_col="gauge1", other_col="gauge2", data_minima=0.1
    )
    assert result["rain_not_minima"].value_counts().filter(pl.col("rain_not_minima") == 0)["count"].item() == 2
    assert result["rain_not_minima"].value_counts().filter(pl.col("rain_not_minima") == 1)["count"].item() == 4
    result = neighbourhood_utils.make_rain_not_minima_column_target_or_neighbour(
        gauge_comparison_data, target_col="gauge1", other_col="gauge2", data_minima=0.7
    )
    assert result["rain_not_minima"].value_counts().filter(pl.col("rain_not_minima") == 0)["count"].item() == 1
    assert result["rain_not_minima"].value_counts().filter(pl.col("rain_not_minima") == 1)["count"].item() == 2
    result = neighbourhood_utils.make_rain_not_minima_column_target_or_neighbour(
        gauge_comparison_data, target_col="gauge1", other_col="gauge2", data_minima=2.0
    )
    assert result["rain_not_minima"].value_counts().filter(pl.col("rain_not_minima") == 1)["count"].item() == 1


def test_get_nearest_non_nan_etccdi_val_to_gauge():
    etccdi_r99p = data_readers.load_etccdi_data(etccdi_var="R99p")

    result = neighbourhood_utils.get_nearest_non_nan_etccdi_val_to_gauge(
        etccdi_r99p, etccdi_name="R99p", gauge_lat=50.0, gauge_lon=10.0
    )
    assert round(float(result["R99p"].max()), 2) == 91.68

    result = neighbourhood_utils.get_nearest_non_nan_etccdi_val_to_gauge(
        etccdi_r99p, etccdi_name="R99p", gauge_lat=50.0, gauge_lon=10.0, max_distance_km=90
    )

    with pytest.raises(ValueError):
        result = neighbourhood_utils.get_nearest_non_nan_etccdi_val_to_gauge(
            etccdi_r99p, etccdi_name="R99p", gauge_lat=50.0, gauge_lon=10.0, max_distance_km=1
        )

    neighbourhood_utils.get_nearest_non_nan_etccdi_val_to_gauge(
        etccdi_r99p,
        etccdi_name="R99p",
        gauge_lat=pl.Series("latitude", [52.14]),
        gauge_lon=pl.Series("latitude", [0.25]),
    )

    with pytest.raises(ValueError):
        neighbourhood_utils.get_nearest_non_nan_etccdi_val_to_gauge(
            etccdi_r99p, etccdi_name="R99p", gauge_lat="invalid", gauge_lon=10.0
        )
    with pytest.raises(TypeError):
        neighbourhood_utils.get_nearest_non_nan_etccdi_val_to_gauge(
            etccdi_r99p, etccdi_name="R99p", gauge_lat=np.array([50.0, 51.1]), gauge_lon=10.0
        )
