#!/usr/bin/env python

"""Tests for applying QC frameworks."""

import polars as pl
import pytest

from rainfallqc.qc_frameworks import apply_qc_framework

TARGET_GAUGE_ID = "tw_2483"


def test_apply_qc_frameworks(daily_gpcc_network, gpcc_metadata):
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
            "neighbouring_gauge_cols": daily_gpcc_network.columns[2:],
            "n_neighbours_ignored": 0,
        },
        "QC24": {"averaging_method": "mean"},
        # Shared defaults applied to all
        "shared": {
            "target_gauge_col": f"rain_mm_{TARGET_GAUGE_ID}",
            "gauge_lat": gpcc_metadata["latitude"],
            "gauge_lon": gpcc_metadata["longitude"],
            "time_res": "daily",
            "data_resolution": 0.1,
            "wet_threshold": 1.0,
            "min_n_neighbours": 5,
            "neighbouring_gauge_col": "rain_mm_tw_310",  # filling as nearest neighbour to target gauge
        },
    }
    result = apply_qc_framework.run_qc_framework(
        daily_gpcc_network, qc_framework="IntenseQC", qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
    )
    assert len(result.keys()) == 14
    assert len(result["QC15"].filter(pl.col("streak_flag1") > 0)) == 6
    assert result["QC21"] == 0  # timing offset
    assert round(result["QC22"], 2) == 0.97  # affinity index
    assert round(result["QC23"], 2) == 0.31  # correlation
    assert round(result["QC24"], 2) == 2.04  # daily factor diff

    with pytest.raises(KeyError):
        apply_qc_framework.run_qc_framework(
            daily_gpcc_network, qc_framework="WrongQC", qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
        )
