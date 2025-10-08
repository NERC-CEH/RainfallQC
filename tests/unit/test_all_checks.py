#!/usr/bin/env python

"""Tests all QC checks."""

from rainfallqc.core import all_qc_checks


def test_all_qc_checks():
    """Test that all QC checks are registered."""
    assert isinstance(all_qc_checks.QC_CHECKS, dict)
    assert len(all_qc_checks.QC_CHECKS) == 22  # Update this if more checks are added
    for name, func in all_qc_checks.QC_CHECKS.items():
        assert callable(func), f"QC check '{name}' is not callable."
        assert func.__name__ == name, f"QC check function name '{func.__name__}' does not match registry name '{name}'."
        assert func.__doc__ is not None, f"QC check '{name}' does not have a docstring."
    all_qc_checks.qc_check(name="func")  # Ensure decorator can be called
