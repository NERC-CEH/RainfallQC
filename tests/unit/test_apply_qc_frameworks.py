#!/usr/bin/env python

"""Tests for applying QC frameworks."""

import numpy as np
import polars as pl
import pytest

from rainfallqc import gauge_checks
from rainfallqc.qc_frameworks import apply_qc_framework

TARGET_GPCC_ID = "tw_2483"
TARGET_GSDR_ID = "DE_00310"


def test_apply_qc_frameworks_daily(daily_gpcc_network, gpcc_metadata):
    qc_methods_to_run = [
        "QC1",
        "QC8",
        "QC9",
        "QC10",
        "QC12",
        "QC14",
        "QC16",
        "QC21",
        "QC22",
        "QC23",
        "QC24",
    ]
    qc_kwargs = {
        "QC1": {"quantile": 5},
        "QC13": {"accumulation_multiplying_factor": 2.0},
        "QC14": {"accumulation_multiplying_factor": 2.0},
        "QC16": {
            "list_of_nearest_stations": daily_gpcc_network.columns[2:],
            "n_neighbours_ignored": 0,
        },
        "QC24": {"averaging_method": "mean"},
        # Shared defaults applied to all
        "shared": {
            "target_gauge_col": f"rain_mm_{TARGET_GPCC_ID}",
            "gauge_lat": gpcc_metadata["latitude"],
            "gauge_lon": gpcc_metadata["longitude"],
            "time_res": "daily",
            "smallest_measurable_rainfall_amount": 0.1,
            "wet_threshold": 1.0,
            "min_n_neighbours": 5,
            "neighbouring_gauge_col": "rain_mm_tw_310",  # filling as nearest neighbour to target gauge
        },
    }
    result = apply_qc_framework.run_qc_framework(
        daily_gpcc_network, qc_framework="IntenseQC", qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
    )
    assert len(result.keys()) == 11
    assert result["QC21"] == 0  # timing offset
    assert round(result["QC22"], 2) == 0.97  # affinity index
    assert round(result["QC23"], 2) == 0.85  # correlation
    assert round(result["QC24"], 2) == 2.04  # daily factor diff

    with pytest.raises(KeyError):
        apply_qc_framework.run_qc_framework(
            daily_gpcc_network, qc_framework="WrongQC", qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
        )


def test_apply_qc_frameworks_hourly(hourly_gsdr_network, gsdr_metadata):
    qc_methods_to_run = [
        "QC1",
        "QC8",
        "QC9",
        "QC10",
        "QC11",
        "QC12",
        "QC13",
        "QC14",
        "QC15",
        "QC17",
        "QC19",
        "QC21",
        "QC22",
        "QC23",
    ]
    qc_kwargs = {
        "QC1": {"quantile": 5},
        # Shared defaults applied to all
        "shared": {
            "target_gauge_col": f"rain_mm_{TARGET_GSDR_ID}",
            "gauge_lat": gsdr_metadata["latitude"],
            "gauge_lon": gsdr_metadata["longitude"],
            "time_res": "hourly",
            "smallest_measurable_rainfall_amount": 0.1,
            "wet_threshold": 1.0,
            "min_n_neighbours": 5,
            "neighbouring_gauge_col": "rain_mm_DE_02483",  # filling as nearest neighbour to target gauge
            "accumulation_multiplying_factor": 2.0,
            "list_of_nearest_stations": hourly_gsdr_network.columns[2:],
            "n_neighbours_ignored": 0,
        },
    }
    result = apply_qc_framework.run_qc_framework(
        hourly_gsdr_network, qc_framework="IntenseQC", qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
    )
    assert len(result.keys()) == 14
    assert len(result["QC15"].filter(pl.col("streak_flag1") > 0)) == 0
    assert result["QC21"] == 0  # timing offset
    assert round(result["QC22"], 2) == 0.81  # affinity index
    assert round(result["QC23"], 2) == 0.03  # correlation


def test_apply_qc_frameworks_15min(mins15_gsdr_network, gsdr_metadata):
    qc_methods_to_run = [
        "QC1",
        "QC8",
        "QC9",
        "QC10",
        "QC11",
        "QC12",
        "QC14",
        "QC17",
        "QC19",
        "QC21",
        "QC22",
        "QC23",
    ]
    qc_kwargs = {
        "QC1": {"quantile": 5},
        # Shared defaults applied to all
        "shared": {
            "target_gauge_col": f"rain_mm_{TARGET_GSDR_ID}",
            "gauge_lat": gsdr_metadata["latitude"],
            "gauge_lon": gsdr_metadata["longitude"],
            "time_res": "15m",
            "smallest_measurable_rainfall_amount": 0.1,
            "wet_threshold": 1.0,
            "min_n_neighbours": 5,
            "neighbouring_gauge_col": "rain_mm_DE_02483",  # filling as nearest neighbour to target gauge
            "accumulation_multiplying_factor": 2.0,
            "list_of_nearest_stations": mins15_gsdr_network.columns[2:],
            "n_neighbours_ignored": 0,
        },
    }
    result = apply_qc_framework.run_qc_framework(
        mins15_gsdr_network, qc_framework="IntenseQC", qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
    )
    assert len(result.keys()) == 12
    assert result["QC21"] == 0  # timing offset
    assert round(result["QC22"], 2) == 0.8  # affinity index
    assert round(result["QC23"], 2) == 0.31  # correlation


def test_apply_pypwsqc_framework(hourly_gsdr_network_no_prefix, gsdr_gauge_network):
    all_neighbour_cols = hourly_gsdr_network_no_prefix.columns[1:]  # exclude time
    assert len(all_neighbour_cols) == 10
    qc_methods_to_run = [
        "FZ",
        "SO",
    ]
    qc_kwargs = {
        "FZ": {"nint": 24},
        "SO": {"evaluation_period": 8064, "mmatch": 200, "gamma": 0.15},
        # Shared defaults applied to all
        "shared": {
            "neighbour_metadata": gsdr_gauge_network,
            "neighbouring_gauge_ids": all_neighbour_cols,
            "neighbour_metadata_gauge_id_col": "station_id",
            "time_res": "hourly",
            "projection": "EPSG:25832",
            "n_stat": 5,
            "max_distance_for_neighbours": 50000,
            "global_attributes": {"title": "GSDR", "year": "2025"},
        },
    }
    result = apply_qc_framework.run_qc_framework(
        hourly_gsdr_network_no_prefix, qc_framework="pypwsqc", qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
    )
    assert len(result.keys()) == 2
    _, fz_counts = np.unique(result["FZ"]["fz_flag"], return_counts=True)
    _, so_counts = np.unique(result["SO"]["so_flag"], return_counts=True)
    print("FZ: ", fz_counts)
    print("SO: ", so_counts)
    assert all([a == b for a, b in zip(fz_counts, [19208, 418223, 809], strict=False)])
    assert all([a == b for a, b in zip(so_counts, [98112, 329181, 10947], strict=False)])


def test_apply_custom_framework(daily_gpcc_network):
    custom_framework = {
        "QC7_pnt2": {
            "function": gauge_checks.check_min_val_change,
            "description": "QC7 from IntenseQC.",
        },
        "QC7_pnt1": {
            "function": gauge_checks.check_min_val_change,
            "description": "QC7 from IntenseQC.",
        },
    }
    qc_methods_to_run = ["QC7_pnt2", "QC7_pnt1"]
    qc_kwargs = {
        "QC7_pnt2": {"expected_min_val": 0.2},
        "QC7_pnt1": {"expected_min_val": 0.1},
        "shared": {"target_gauge_col": f"rain_mm_{TARGET_GPCC_ID}"},
    }

    result = apply_qc_framework.run_qc_framework(
        daily_gpcc_network,
        qc_framework="custom",
        qc_methods_to_run=qc_methods_to_run,
        qc_kwargs=qc_kwargs,
        user_defined_framework=custom_framework,
    )

    assert len(result.keys()) == 2
    assert len(result["QC7_pnt2"]) == 64
    assert len(result["QC7_pnt1"]) == 0
