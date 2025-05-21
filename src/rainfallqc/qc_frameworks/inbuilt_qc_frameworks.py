# -*- coding: utf-8 -*-
"""In-built QC frameworks to apply to rainfall data to create quality controlled data."""

from rainfallqc.checks import comparison_checks, gauge_checks, neighbourhood_checks, timeseries_checks

INTENSE_QC = {
    "QC1": {"function": gauge_checks.get_years_where_nth_percentile_is_zero},
    "QC2": {"function": gauge_checks.get_years_where_annual_mean_k_top_rows_are_zero},
    "QC3": {"function": gauge_checks.check_temporal_bias},
    "QC4": {"function": gauge_checks.check_temporal_bias},
    "QC5": {"function": gauge_checks.intermittency_check},
    "QC6": {"function": gauge_checks.breakpoints_check},
    "QC7": {"function": gauge_checks.min_val_change},
    "QC8": {"function": comparison_checks.check_annual_exceedance_etccdi_r99p},
    "QC9": {"function": comparison_checks.check_annual_exceedance_etccdi_prcptot},
    "QC10": {"function": comparison_checks.check_exceedance_of_rainfall_world_record},
    "QC11": {"function": comparison_checks.check_annual_exceedance_etccdi_rx1day},
    "QC12": {"function": timeseries_checks.dry_period_cdd_check},
    "QC13": {"function": timeseries_checks.daily_accumulations},
    "QC14": {"function": timeseries_checks.monthly_accumulations},
    "QC15": {"function": timeseries_checks.streaks_check},
    "QC16": {"function": neighbourhood_checks.wet_neighbour_check},
}

INBUILT_QC_FRAMEWORKS = {"IntenseQC": INTENSE_QC}
