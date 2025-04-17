# -*- coding: utf-8 -*-
"""Data reading tools."""
import datetime


def read_gdsr_metadata(data_path: str) -> dict:
    """
    Read the specific format and header of Global Sub-Daily Rainfall (GDSR) files.

    Parameters
    ----------
    data_path : str
        path to GDSR data file (.txt)

    Returns
    -------
    metadata : dict
        Metadata from GDSR file

    """
    metadata = {}

    with open(data_path, "r", encoding="utf-8") as f:
        while True:
            key, val = f.readline().strip().split(":", maxsplit=1)
            key = key.lower().replace(" ", "_")
            metadata[key.strip()] = val.strip()
            if key == "other":
                break
    metadata = convert_gdsr_metadata_dates_to_datetime(metadata)
    return metadata


def convert_gdsr_metadata_dates_to_datetime(metadata: dict) -> dict:
    """
    Convert GDSR metadata date string column to datetime.

    Parameters
    ----------
    metadata :
        Metadata from GDSR file

    Returns
    -------
    metadata : dict
    Metadata from GDSR file with start and end date column

    """
    metadata["start_datetime"] = datetime.datetime.strptime(
        metadata["start_datetime"], "%Y%m%d%H"
    )
    metadata["end_datetime"] = datetime.datetime.strptime(
        metadata["end_datetime"], "%Y%m%d%H"
    )
    return metadata
