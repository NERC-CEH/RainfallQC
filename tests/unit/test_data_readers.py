#!/usr/bin/env python

"""Tests for data loaders."""

from rainfallqc.utils import data_readers

# test when start_datetime not found


def test_load_CDD_ETCCDI_data():
    data_readers.load_ETCCDI_data(etccdi_var="CDD")


def test_load_CWD_ETCCDI_data():
    data_readers.load_ETCCDI_data(etccdi_var="CWD")


def test_load_PRCPTOT_ETCCDI_data():
    data_readers.load_ETCCDI_data(etccdi_var="PRCPTOT")


def test_load_R99p_ETCCDI_data():
    data_readers.load_ETCCDI_data(etccdi_var="R99p")


def test_load_Rx1day_ETCCDI_data():
    data_readers.load_ETCCDI_data(etccdi_var="Rx1day")


def test_load_SDII_ETCCDI_data():
    data_readers.load_ETCCDI_data(etccdi_var="SDII")


def test_load_userpath_ETCCDI_data():
    data_readers.load_ETCCDI_data(etccdi_var="PRCPTOT", path_to_etccdi="./src/rainfallqc/data/ETCCDI/")
