#!/usr/bin/env python

"""Tests for data loaders."""

import pytest

from rainfallqc.utils import data_readers

DEFAULT_RAIN_COL = "rain_mm"


def test_load_cdd_etccdi_data():
    data_readers.load_etccdi_data(etccdi_var="CDD")


def test_load_cwd_etccdi_data():
    data_readers.load_etccdi_data(etccdi_var="CWD")


def test_load_prcptot_etccdi_data():
    data_readers.load_etccdi_data(etccdi_var="PRCPTOT")


def test_load_r99p_etccdi_data():
    data_readers.load_etccdi_data(etccdi_var="R99p")


def test_load_rx1day_etccdi_data():
    data_readers.load_etccdi_data(etccdi_var="Rx1day")


def test_load_sdii_etccdi_data():
    data_readers.load_etccdi_data(etccdi_var="SDII")


def test_load_userpath_etccdi_data():
    data_readers.load_etccdi_data(etccdi_var="PRCPTOT", path_to_etccdi="./src/rainfallqc/data/ETCCDI/")


def test_load_gsdr_gauge_network_metadata():
    result = data_readers.load_gsdr_gauge_network_metadata(path_to_gsdr_dir="./tests/data/GSDR/")
    assert len(result.columns) == 21
    assert len(result) == 11

    with pytest.raises(ValueError):
        data_readers.load_gsdr_gauge_network_metadata(path_to_gsdr_dir="./tests/data/GSDR_test")


def test_get_paths_using_gauge_ids():
    result = data_readers.get_paths_using_gauge_ids(
        gauge_ids={"DE_00310", "DE_00390"}, dir_path="./tests/data/GSDR/", file_format=".txt"
    )
    assert len(result) == 2
    with pytest.raises(IndexError):
        data_readers.get_paths_using_gauge_ids(
            gauge_ids={"DE_00310", "DE_00390"}, dir_path="./tests/data/GSDR/", file_format=".dat"
        )

    result = data_readers.get_paths_using_gauge_ids(
        gauge_ids={"310", "6303"}, dir_path="./tests/data/GPCC/", file_format=".zip", time_res="mw"
    )
    assert len(result) == 2
    assert "mw" in result["6303"]


def test_read_gpcc_metadata_from_zip():
    with pytest.raises(ValueError):
        data_readers.read_gpcc_metadata_from_zip(
            data_path="./tests/data/GPCC/mw_310.zip", time_res="decadal", gpcc_file_format=".dat"
        )


def test_read_gpcc_data_from_zip():
    result = data_readers.read_gpcc_data_from_zip(
        data_path="./tests/data/GPCC/tw_310.zip",
        gpcc_file_name="tw_310.dat",
        target_gauge_col="rain_mm",
        time_res="daily",
    )
    assert result["rain_mm"][0] == 5.2
    result = data_readers.read_gpcc_data_from_zip(
        data_path="./tests/data/GPCC/mw_310.zip",
        gpcc_file_name="mw_310.dat",
        target_gauge_col="rain_mm",
        time_res="monthly",
    )
    assert result["rain_mm"][0] == 69.0
    with pytest.raises(AssertionError):
        data_readers.read_gpcc_data_from_zip(
            data_path="./tests/data/GPCC/mw_310",
            gpcc_file_name="mw_310.dat",
            target_gauge_col="rain_mm",
            time_res="monthly",
        )

    with pytest.raises(ValueError):
        data_readers.read_gpcc_data_from_zip(
            data_path="./tests/data/GPCC/mw_310.zip",
            gpcc_file_name="mw_310.dat",
            target_gauge_col="rain_mm",
            time_res="decadal",
        )


def test_load_gpcc_gauge_network_metadata():
    with pytest.raises(ValueError):
        data_readers.load_gpcc_gauge_network_metadata(path_to_gpcc_dir="GPCC/", time_res="mw", gpcc_file_format=".dat")
    result = data_readers.load_gpcc_gauge_network_metadata(
        path_to_gpcc_dir="./tests/data/GPCC/", time_res="mw", gpcc_file_format=".dat"
    )
    assert len(result) == 10
    assert sorted(result["station_id"])[2] == "310"
    assert sorted(result["location"])[5] == "Meschede"
    result = data_readers.load_gpcc_gauge_network_metadata(
        path_to_gpcc_dir="./tests/data/GPCC/", time_res="tw", gpcc_file_format=".dat"
    )
    assert len(result) == 10
    assert sorted(result["station_id"])[2] == "310"
    assert sorted(result["location"])[5] == "Meschede"


def test_gsdr_network_reader():
    gsdr_obj = data_readers.GSDRNetworkReader(path_to_gsdr_dir="./tests/data/GSDR/")
    assert hasattr(gsdr_obj, "metadata")
    assert hasattr(gsdr_obj, "data_paths")


def test_gsdr_network_nearest_neighbours():
    gsdr_obj = data_readers.GSDRNetworkReader(path_to_gsdr_dir="./tests/data/GSDR/")
    result = gsdr_obj.get_nearest_overlapping_neighbours_to_target(
        target_id="DE_03215", distance_threshold=30, n_closest=3, min_overlap_days=1000
    )
    assert sorted(list(result)) == ["DE_02483", "DE_02718", "DE_06303"]


def test_gsdr_network_load_network_data():
    gsdr_obj = data_readers.GSDRNetworkReader(path_to_gsdr_dir="./tests/data/GSDR/")
    result = gsdr_obj.load_network_data(
        rain_col_prefix="rain",
        data_paths=[
            "./tests/data/GSDR/DE_06303.txt",
            "./tests/data/GSDR/DE_00310.txt",
            "./tests/data/GSDR/DE_02483.txt",
        ],
    )
    assert len(result.columns) == 4


def test_gpcc_network_reader():
    gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/", time_res="tw")
    assert hasattr(gpcc_obj, "metadata")
    assert hasattr(gpcc_obj, "data_paths")


def test_gpcc_network_nearest_neighbours():
    gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/", time_res="tw")
    result = gpcc_obj.get_nearest_overlapping_neighbours_to_target(
        target_id="310", distance_threshold=30, n_closest=3, min_overlap_days=1000
    )
    assert sorted(list(result)) == ["2483", "480", "5610"]


def test_gpcc_network_load_network_data():
    gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/", time_res="tw")
    result = gpcc_obj.load_network_data(
        data_paths=["./tests/data/GPCC/tw_310.zip", "./tests/data/GPCC/tw_480.zip", "./tests/data/GPCC/tw_6303.zip"],
        target_gauge_col=DEFAULT_RAIN_COL,
    )
    assert len(result.columns) == 4
    assert result[-2]["rain_mm_tw_310"].item() == 0.9
    assert result[-2]["rain_mm_tw_480"].item() == 0.3
    assert result[-2]["rain_mm_tw_6303"].item() == 4.7

    gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/", time_res="mw")
    gpcc_obj.load_network_data(data_paths=["./tests/data/GPCC/mw_310.zip"], target_gauge_col=DEFAULT_RAIN_COL)

    with pytest.raises(AssertionError):
        gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/", time_res="tw")
        gpcc_obj.load_network_data(data_paths=["./tests/data/GPCC/mw_310.zip"], target_gauge_col=DEFAULT_RAIN_COL)
