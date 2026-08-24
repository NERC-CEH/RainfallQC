.. highlight:: shell

============
Quick Start
============
The easiest way to start using the package is to install it using :code:`pip install rainfallqc`.

.. tab-set::
    :class: outline padded-tabs

    .. tab-item:: :iconify:`devicon:python` python

        To use `RainfallQC` in a project, a `polars dataframe <https://docs.pola.rs/api/python/stable/reference/dataframe/index.html/>`_ can be directly input to the QC checks like:
                
        .. code-block:: python

            import polars as pl
            import rainfallqc.gauge_checks

            data = pl.read_csv("path/to/your/rain_gauge_data.csv")
            flags = rainfallqc.gauge_checks.check_intermittency(data, target_gauge_col="rain_mm")


All quality control checks in the RainfallQC package begin with ``check_``

Content overview
----------------

RainfallQC contains six modules:

1. ``gauge_checks`` - For detecting abnormalities in summary and descriptive statistics.
2. ``comparison_checks`` - For detecting abnormalities by comparing to benchmark data.
3. ``timeseries_checks`` - For detecting abnormalities in patterns of the data record.
4. ``neighbourhood_checks`` - For detecting abnormalities based on measurements in neighbouring gauges.
5. ``subhourlyqc_checks`` - An extension for IntenseQC to be applied to sub-hourly rainfall data.
6. ``pypwsqc_filters`` - For applying quality assurance protocols and filters for rainfall data.

You can find a jupyter notebook with an easy-to-follow example `here <https://github.com/Thomasjkeel/RainfallQC-notebooks/blob/main/notebooks/demo/rainfallQC_demo.ipynb>`_

Which checks are suitable for my data's temporal resolution?
------------------------------------------------------------
As you can imagine, not all quality control checks are suitable for all temporal resolutions.
Therefore, we have created a table that shows which checks are suitable for which temporal resolutions,
and which can be applied after aggregating data ("agg") to a coarser temporal resolution.

.. :dark-green:`✓`
.. :red:`☓`

.. role:: green
   :class: qc-green

.. role:: dark-green
   :class: qc-dark-green

.. role:: yellow
   :class: qc-yellow

.. role:: red
   :class: qc-red


.. table:: Which checks are suitable for my data's time-resolution
   :widths: 10 40 19 17 17 17 17
   :align: left

   ===================== ======================================================================================================================================================================== ================= ================= ================= ================= =================
   Short name            Long name                                                                                                                                                                <15-min           15-min            hourly            daily             monthly
   ===================== ======================================================================================================================================================================== ================= ================= ================= ================= =================
   QC1                   `Percentiles <api/generated/rainfallqc.checks.gauge_checks.html#ranfallqc.checks.gauge_checks.check_years_where_nth_percentile_is_zero>`_                                :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   QC2                   `K-largest <api/generated/rainfallqc.checks.gauge_checks.html#rainfallqc.checks.gauge_checks.check_years_where_annual_kth_largest_value_is_zero>`_                       :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   QC3                   `Days of week <api/generated/rainfallqc.checks.gauge_checks.html#rainfallqc.checks.gauge_checks.check_day_of_week>`_                                                     :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC4                   `Hours of day <api/generated/rainfallqc.checks.gauge_checks.html#rainfallqc.checks.gauge_checks.check_hour_of_day>`_                                                     :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`
   QC5                   `Intermittency <api/generated/rainfallqc.checks.gauge_checks.html#rainfallqc.checks.gauge_checks.check_intermittency>`_                                                  :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   QC6                   `Breakpoints <api/generated/rainfallqc.checks.gauge_checks.html#rainfallqc.checks.gauge_checks.check_breakpoints>`_                                                      :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC7                   `Minimum value change <api/generated/rainfallqc.checks.gauge_checks.html#rainfallqc.checks.gauge_checks.check_min_val_change>`_                                          :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   QC8                   `R99p <api/generated/rainfallqc.checks.comparison_checks.html#rainfallqc.checks.comparison_checks.check_annual_exceedance_etccdi_r99p>`_                                 :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC9                   `PRCPTOT <api/generated/rainfallqc.checks.comparison_checks.html#rainfallqc.checks.comparison_checks.check_annual_exceedance_etccdi_prcptot>`_                           :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC10                  `World Record <api/generated/rainfallqc.checks.comparison_checks.html#rainfallqc.checks.comparison_checks.check_exceedance_of_rainfall_world_record>`_                   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC11                  `Rx1day <api/generated/rainfallqc.checks.comparison_checks.html#rainfallqc.checks.comparison_checks.check_hourly_exceedance_etccdi_rx1day>`_                             :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`
   QC12                  `CDD (Dry spells) <api/generated/rainfallqc.checks.timeseries_checks.html#rainfallqc.checks.timeseries_checks.check_dry_period_cdd>`_                                    :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC13                  `Daily accumulations <api/generated/rainfallqc.checks.timeseries_checks.html#rainfallqc.checks.timeseries_checks.check_daily_accumulations>`_                            :dark-green:`agg` :dark-green:`agg` :green:`✓`        :green:`✓`        :red:`☓`
   QC14                  `Monthly accumulations <api/generated/rainfallqc.checks.timeseries_checks.html#rainfallqc.checks.timeseries_checks.check_monthly_accumulations>`_                        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC15                  `Streaks <api/generated/rainfallqc.checks.timeseries_checks.html#rainfallqc.checks.timeseries_checks.check_streaks>`_                                                    :dark-green:`agg` :dark-green:`agg` :green:`✓`        :green:`✓`        :red:`☓`
   QC16                  `Daily neighbours (wet) <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_wet_neighbours_daily>`_                  :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC17                  `Hourly neighbours (wet) <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_wet_neighbours_hourly>`_                :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`
   QC18                  `Daily neighbours (dry) <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_dry_neighbours_daily>`_                  :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC19                  `Hourly neighbours (dry) <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_dry_neighbours_hourly>`_                :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`
   QC20                  `Monthly neighbours <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_monthly_neighbours>`_                        :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :green:`✓`
   QC21                  `Timing offset <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_timing_offset>`_                                  :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   QC22                  `Pre-QC affinity index <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_neighbour_affinity_index>`_               :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓` 
   QC23                  `Pre-QC pearson correlation <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_neighbour_correlation>`_             :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   QC24                  `Daily factor <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_daily_factor>`_                                    :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :green:`✓`        :red:`☓`
   QC25                  `Monthly factor <api/generated/rainfallqc.checks.neighbourhood_checks.html#rainfallqc.checks.neighbourhood_checks.check_monly_factor>`_                                  :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :green:`✓`
   HQC_UK1hr             `Check exceedance of UK 1h record <api/generated/rainfallqc.checks.subhourlyqc.html#rainfallqc.checks.subhourlyqc.check_exceedance_of_UK_1hr_record>`_                   :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   HQC_UK24hr            `Check exceedance of UK 24h record <api/generated/rainfallqc.checks.subhourlyqc.html#rainfallqc.checks.subhourlyqc.check_exceedance_of_UK_24hr_record>`_                 :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   HQC_UK24hr_rolling    `Check 24h-sum exceedance of UK 24h record <api/generated/rainfallqc.checks.subhourlyqc.html#rainfallqc.checks.subhourlyqc.check_daily_exceedance_of_UK_24hr_record>`_   :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   HQC_streaks_20mm      `Check streaks (20 mm min) <api/generated/rainfallqc.checks.subhourlyqc.html#rainfallqc.checks.subhourlyqc.check_streaks_20mm>`_                                         :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   SHQC_freqResChecker   `Check data has sub-hourly frequency <api/generated/rainfallqc.checks.subhourlyqc.html#rainfallqc.checks.subhourlyqc.check_freq_is_subhourly>`_                          :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   SHQC_subH_checkr      `Check sub-hourly rainfall thresholds <api/generated/rainfallqc.checks.subhourlyqc.html#rainfallqc.checks.subhourlyqc.check_subhourly_thresholds>`_                      :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   FZ                    `Faulty Zeros <api/generated/rainfallqc.checks.pypwsqc_filters.html#rainfallqc.checks.pypwsqc_filters.check_faulty_zeros>`_                                              :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   SO                    `Station Outliers <api/generated/rainfallqc.checks.pypwsqc_filters.html#rainfallqc.checks.pypwsqc_filters.check_station_outlier>`_                                       :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`     
   ===================== ======================================================================================================================================================================== ================= ================= ================= ================= =================
