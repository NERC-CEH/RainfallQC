"""Top-level package for RainfallQC."""

__author__ = """Tom Keel"""
__email__ = "tomkee@ceh.ac.uk"
__version__ = "0.0.8"

from rainfallqc.checks import (
    comparison_checks,
    gauge_checks,
    neighbourhood_checks,
    timeseries_checks,
)
from rainfallqc.qc_frameworks import apply_framework

__all__ = [
    "apply_framework",
    "comparison_checks",
    "gauge_checks",
    "neighbourhood_checks",
    "timeseries_checks",
]
