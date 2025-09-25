# -*- coding: utf-8 -*-
"""In-built QC frameworks to apply to rainfall data to create quality controlled data."""

from rainfallqc.checks import comparison_checks, gauge_checks, neighbourhood_checks, pypwsqc_filters, timeseries_checks

INTENSE_QC = {
    "QC1": {"function": gauge_checks.check_years_where_nth_percentile_is_zero},
    "QC2": {"function": gauge_checks.check_years_where_annual_mean_k_top_rows_are_zero},
    "QC3": {"function": gauge_checks.check_temporal_bias},
    "QC4": {"function": gauge_checks.check_temporal_bias},
    "QC5": {"function": gauge_checks.check_intermittency},
    "QC6": {"function": gauge_checks.check_breakpoints},
    "QC7": {"function": gauge_checks.check_min_val_change},
    "QC8": {"function": comparison_checks.check_annual_exceedance_etccdi_r99p},
    "QC9": {"function": comparison_checks.check_annual_exceedance_etccdi_prcptot},
    "QC10": {"function": comparison_checks.check_exceedance_of_rainfall_world_record},
    "QC11": {"function": comparison_checks.check_hourly_exceedance_etccdi_rx1day},
    "QC12": {"function": timeseries_checks.check_dry_period_cdd},
    "QC13": {"function": timeseries_checks.check_daily_accumulations},
    "QC14": {"function": timeseries_checks.check_monthly_accumulations},
    "QC15": {"function": timeseries_checks.check_streaks},
    "QC16": {"function": neighbourhood_checks.check_wet_neighbours},
    "QC17": {"function": neighbourhood_checks.check_wet_neighbours},
    "QC18": {"function": neighbourhood_checks.check_dry_neighbours},
    "QC19": {"function": neighbourhood_checks.check_dry_neighbours},
    "QC20": {"function": neighbourhood_checks.check_monthly_neighbours},
    "QC21": {"function": neighbourhood_checks.check_timing_offset},
    "QC22": {"function": neighbourhood_checks.check_neighbour_affinity_index},
    "QC23": {"function": neighbourhood_checks.check_neighbour_correlation},
    "QC24": {"function": neighbourhood_checks.check_daily_factor},
    "QC25": {"function": neighbourhood_checks.check_monthly_factor},
}

PYPWSQC = {
    "BC": {"function": pypwsqc_filters.run_bias_correction},
    "EBF": {"function": pypwsqc_filters.run_event_based_filter},
    "IC": {"function": pypwsqc_filters.run_indicator_correlation},
    "FZ": {"function": pypwsqc_filters.check_faulty_zeros},
    "HI": {"function": pypwsqc_filters.check_high_influx_filter},
    "PRF": {"function": pypwsqc_filters.run_peak_removal},
    "SO": {"function": pypwsqc_filters.check_station_outlier},
}

INBUILT_QC_FRAMEWORKS = {"IntenseQC": INTENSE_QC, "pypwsqc": PYPWSQC}
