"""Top-level package for RainfallQC."""

__author__ = """Tom Keel"""
__email__ = "tomkee@ceh.ac.uk"
__version__ = "0.1.5"

from rainfallqc.checks import (
    comparison_checks,
    gauge_checks,
    neighbourhood_checks,
    timeseries_checks,
)
from rainfallqc.qc_frameworks import apply_qc_framework

__all__ = [
    "apply_qc_framework",
    "comparison_checks",
    "gauge_checks",
    "neighbourhood_checks",
    "timeseries_checks",
    "apply_qc_framework",
]
