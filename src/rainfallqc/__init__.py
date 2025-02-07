"""Top-level package for RainfallQC."""

__author__ = """Tom Keel"""
__email__ = "tomkee@ceh.ac.uk"
__version__ = "0.0.3-alpha"

from rainfallqc.checks import (
    comparison_checks,
    gauge_checks,
    neighbour_checks,
    timeseries_checks,
)
from rainfallqc.rulebases import intense_qc_rulebase
