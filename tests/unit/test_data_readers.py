#!/usr/bin/env python

"""Tests for data loaders."""

import pytest

from rainfallqc.utils import data_readers

DEFAULT_RAIN_COL = "rain_mm"

# TODO: test when start_datetime not found


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


def test_load_gdsr_gauge_network_metadata():
    result = data_readers.load_gdsr_gauge_network_metadata(path_to_gdsr_dir="./tests/data/GDSR/")
    assert len(result.columns) == 21
    assert len(result) == 11

    with pytest.raises(ValueError):
        data_readers.load_gdsr_gauge_network_metadata(path_to_gdsr_dir="./tests/data/GDSR_test")


def test_get_paths_using_gauge_ids():
    result = data_readers.get_paths_using_gauge_ids(
        gauge_ids={"DE_00310", "DE_00390"}, dir_path="./tests/data/GDSR/", file_format=".txt"
    )
    assert len(result) == 2
    with pytest.raises(IndexError):
        data_readers.get_paths_using_gauge_ids(
            gauge_ids={"DE_00310", "DE_00390"}, dir_path="./tests/data/GDSR/", file_format=".dat"
        )

    result = data_readers.get_paths_using_gauge_ids(
        gauge_ids={"310", "6303"}, dir_path="./tests/data/GPCC/", file_format=".zip", time_res="mw"
    )
    assert len(result) == 2
    assert "mw" in result["6303"]


def test_read_gpcc_data_from_zip():
    result = data_readers.read_gpcc_data_from_zip(
        data_path="./tests/data/GPCC/tw_310.zip", gpcc_file_name="tw_310.dat", rain_col="rain_mm", time_res="daily"
    )
    assert result["rain_mm"][0] == 5.2
    result = data_readers.read_gpcc_data_from_zip(
        data_path="./tests/data/GPCC/mw_310.zip", gpcc_file_name="mw_310.dat", rain_col="rain_mm", time_res="monthly"
    )
    assert result["rain_mm"][0] == 69.0
    with pytest.raises(AssertionError):
        data_readers.read_gpcc_data_from_zip(
            data_path="./tests/data/GPCC/mw_310", gpcc_file_name="mw_310.dat", rain_col="rain_mm", time_res="monthly"
        )


def test_load_gpcc_gauge_network_metadata():
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


def test_gdsr_network_reader():
    gdsr_obj = data_readers.GDSRNetworkReader(path_to_gdsr_dir="./tests/data/GDSR/")
    assert hasattr(gdsr_obj, "metadata")
    assert hasattr(gdsr_obj, "data_paths")


def test_gdsr_network_nearest_neighbours():
    gdsr_obj = data_readers.GDSRNetworkReader(path_to_gdsr_dir="./tests/data/GDSR/")
    result = gdsr_obj.get_nearest_overlapping_neighbours_to_target(
        target_id="DE_03215", distance_threshold=30, n_closest=3, min_overlap_days=1000
    )
    assert sorted(list(result)) == ["DE_02483", "DE_02718", "DE_06303"]


def test_gdsr_network_load_network_data():
    gdsr_obj = data_readers.GDSRNetworkReader(path_to_gdsr_dir="./tests/data/GDSR/")
    result = gdsr_obj.load_network_data(
        data_paths=[
            "./tests/data/GDSR/DE_06303.txt",
            "./tests/data/GDSR/DE_00310.txt",
            "./tests/data/GDSR/DE_02483.txt",
        ]
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
        rain_col=DEFAULT_RAIN_COL,
    )
    print(result)
    assert len(result.columns) == 4
    assert result[-2]["rain_mm_tw_310"].item() == 0.9
    assert result[-2]["rain_mm_tw_480"].item() == 0.3
    assert result[-2]["rain_mm_tw_6303"].item() == 4.7

    gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/", time_res="mw")
    gpcc_obj.load_network_data(data_paths=["./tests/data/GPCC/mw_310.zip"], rain_col=DEFAULT_RAIN_COL)

    with pytest.raises(AssertionError):
        gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/", time_res="tw")
        gpcc_obj.load_network_data(data_paths=["./tests/data/GPCC/mw_310.zip"], rain_col=DEFAULT_RAIN_COL)
