#!/usr/bin/env python

"""Tests for data loaders."""

import pytest

from rainfallqc.utils import data_readers

# test when start_datetime not found


def test_load_CDD_ETCCDI_data():
    data_readers.load_etccdi_data(etccdi_var="CDD")


def test_load_CWD_ETCCDI_data():
    data_readers.load_etccdi_data(etccdi_var="CWD")


def test_load_PRCPTOT_ETCCDI_data():
    data_readers.load_etccdi_data(etccdi_var="PRCPTOT")


def test_load_R99p_ETCCDI_data():
    data_readers.load_etccdi_data(etccdi_var="R99p")


def test_load_Rx1day_ETCCDI_data():
    data_readers.load_etccdi_data(etccdi_var="Rx1day")


def test_load_SDII_ETCCDI_data():
    data_readers.load_etccdi_data(etccdi_var="SDII")


def test_load_userpath_ETCCDI_data():
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
        path_to_gpcc_dir="./tests/data/GPCC/", gpcc_file_format=".dat"
    )
    assert len(result) == 20
    assert result["station_id"][2] == 6303
    assert result["location"][5] == "Battenberg-Hof Karlsburg"


def test_gdsr_network_reader():
    gdsr_obj = data_readers.GDSRNetworkReader(path_to_gdsr_dir="./tests/data/GDSR/")
    assert hasattr(gdsr_obj, "metadata")
    assert hasattr(gdsr_obj, "data_paths")


def test_gpcc_network_reader():
    gpcc_obj = data_readers.GPCCNetworkReader(path_to_gpcc_dir="./tests/data/GPCC/")
    assert hasattr(gpcc_obj, "metadata")
    assert hasattr(gpcc_obj, "data_paths")
