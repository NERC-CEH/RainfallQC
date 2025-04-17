# -*- coding: utf-8 -*-
"""Data reading tools."""


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
    return metadata
