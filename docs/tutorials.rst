=========
Tutorials
=========

RainfallQC contains four modules:

1. ``gauge_checks`` - For detecting abnormalities in summary and descriptive statistics.
2. ``comparison_checks`` - For detecting abnormalities by comparing to benchmark data.
3. ``timeseries_checks`` - For detecting abnormalities in patterns of the data record.
4. ``neighbourhood_checks`` - For detecting abnormalities based on measurements in neighbouring gauges.


Each one of these modules contains individual QC check methods, which begin with the syntax ``check_``.
For example to run a streaks check you can run: ``rainfallqc.timeseries_checks.check_streaks(data, **kwargs)``


All QC checks in package
------------------------
These are the quality control checks currently implemented in the package:

.. table:: All QC checks
   :widths: auto
   :align: left

   =========================================================================================================================  ====================  ====================================================================================  ===============
   Check                                                                                                                      Sub-module            QC Framework                                                                          Note
   =========================================================================================================================  ====================  ====================================================================================  ===============
   `Percentiles <rainfallqc.checks.html#rainfallqc.checks.gauge_checks.check_years_where_nth_percentile_is_zero>`_            Gauge checks          `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_    QC1
   `K-largest <rainfallqc.checks.html#rainfallqc.checks.gauge_checks.check_years_where_annual_mean_k_top_rows_are_zero>`_     Gauge checks          IntenseQC                                                                             QC2
   `Days of week <rainfallqc.checks.html#rainfallqc.checks.gauge_checks.check_temporal_bias>`_                                Gauge checks          IntenseQC                                                                             QC3
   `Hours of day <rainfallqc.checks.html#rainfallqc.checks.gauge_checks.check_temporal_bias>`_                                Gauge checks          IntenseQC                                                                             QC4
   `Intermittency <rainfallqc.checks.html#rainfallqc.checks.gauge_checks.check_intermittency>`_                               Gauge checks          IntenseQC                                                                             QC5
   `Breakpoints <rainfallqc.checks.html#rainfallqc.checks.gauge_checks.check_breakpoints>`_                                   Gauge checks          IntenseQC                                                                             QC6
   `Minimum value change <rainfallqc.checks.html#rainfallqc.checks.gauge_checks.check_min_val_change>`_                       Gauge checks          IntenseQC                                                                             QC7
   `R99p <rainfallqc.checks.html#rainfallqc.checks.comparison_checks.check_annual_exceedance_etccdi_r99p>`_                   Comparison checks     IntenseQC                                                                             QC8
   `PRCPTOT <rainfallqc.checks.html#rainfallqc.checks.comparison_checks.check_annual_exceedance_etccdi_prcptot>`_             Comparison checks     IntenseQC                                                                             QC9
   `World Record <rainfallqc.checks.html#rainfallqc.checks.comparison_checks.check_exceedance_of_rainfall_world_record>`_     Comparison checks     IntenseQC                                                                             QC10
   `Rx1day <rainfallqc.checks.html#rainfallqc.checks.comparison_checks.check_hourly_exceedance_etccdi_rx1day>`_               Comparison checks     IntenseQC                                                                             QC11
   `CDD (Dry spells) <rainfallqc.checks.html#rainfallqc.checks.timeseries_checks.check_dry_period_cdd>`_                      Timeseries checks     IntenseQC                                                                             QC12
   `Daily accumulations <rainfallqc.checks.html#rainfallqc.checks.timeseries_checks.check_daily_accumulations>`_              Timeseries checks     IntenseQC                                                                             QC13
   `Monthly accumulations <rainfallqc.checks.html#rainfallqc.checks.timeseries_checks.check_monthly_accumulations>`_          Timeseries checks     IntenseQC                                                                             QC14
   `Streaks <rainfallqc.checks.html#rainfallqc.checks.timeseries_checks.check_streaks>`_                                      Timeseries checks     IntenseQC                                                                             QC15
   `Daily neighbours (wet) <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_wet_neighbours>`_             Neighbourhood checks  IntenseQC                                                                             QC16
   `Hourly neighbours (wet) <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_wet_neighbours>`_            Neighbourhood checks  IntenseQC                                                                             QC17
   `Daily neighbours (dry) <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_dry_neighbours>`_             Neighbourhood checks  IntenseQC                                                                             QC18
   `Daily neighbours (dry) <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_dry_neighbours>`_             Neighbourhood checks  IntenseQC                                                                             QC19
   `Monthly neighbiours <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_monthly_neighbours>`_            Neighbourhood checks  IntenseQC                                                                             QC20
   `Timing offset <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_timing_offset>`_                       Neighbourhood checks  IntenseQC                                                                             QC21
   `Pre-QC affinity index <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_neighbour_affinity_index>`_    Neighbourhood checks  IntenseQC                                                                             QC22
   `Pre-QC pearson correlation <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_neighbour_correlation>`_  Neighbourhood checks  IntenseQC                                                                             QC23
   `Daily factor <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_daily_factor>`_                         Neighbourhood checks  IntenseQC                                                                             QC24
   `Monthly factor <rainfallqc.checks.html#rainfallqc.checks.neighbourhood_checks.check_monly_factor>`_                       Neighbourhood checks  IntenseQC                                                                             QC25
   =========================================================================================================================  ====================  ====================================================================================  ===============





Example 1. - Individual quality checks on single rain gauge
===========================================================

.. code-block:: python

        # Load two types of QC'ing modules from RainfallQC
        from rainfallqc import gauge_checks, comparison_checks

        # 1. Simple 1 gauge QC
        # 1.1. Run 1 qc method for 1 gauge
        intermittency_flag = gauge_checks.check_intermittency(data, target_gauge_col="rain_mm")

        # 1.2. Run 1 qc method for 1 gauge using in-built comparison dataset
        wr_flags = comparison_checks.check_exceedance_of_rainfall_world_record(data, target_gauge_col="rain_mm", time_res='hourly')

        # 1.3. Run 1 qc method for 1 gauge using in-built comparison dataset and location of gauge
        rx1day_flags = comparison_checks.check_annual_exceedance_etccdi_rx1day(data, target_gauge_col="rain_mm", gauge_lon=1.0, gauge_lat=55.0)


Example 2. - Individual quality checks on networks of rain gauges
=================================================================

.. code-block:: python

        # 2. Run neighbour/network checks on a subset of a rain gauge network
        from rainfallqc import neighbourhood_checks
        from rainfallqc.utils import data_readers

        # 2.1. Read in GDSR gauge network metadata
        gdsr_obj = data_readers.GDSRNetworkReader(path_to_gdsr_dir="./tests/data/GDSR/")

        # 2.2. subset by max 10 gauges within 50 km and with at least 500 days of overlap
        nearby_ids = list(
            gdsr_obj.get_nearest_overlapping_neighbours_to_target(
                target_id="DE_00310", distance_threshold=50, n_closest=10, min_overlap_days=500
            )
        )
        nearby_ids.append(target_id)
        nearby_data_paths = gdsr_obj.metadata.filter(pl.col("station_id").is_in(nearby_ids))["path"]

        # 2.3. Load those nearest gauges from network metadata
        gdsr_network = gdsr_obj.load_network_data(data_paths=nearby_data_paths)

        # 2.4 Run a neighbourhood check (checking if suspiciously large rainfall values were seen in neighbours)
        extreme_wet_flags = neighbourhood_checks.check_wet_neighbours(
            gdsr_network,
            target_gauge_col="rain_mm_DE_02483",
            neighbouring_gauge_cols=gdsr_network.columns[1:],  # exclude time
            time_res="hourly",
            wet_threshold=1.0, # threshold for rainfall intensity to be considered
            min_n_neighbours=5, # number of neighbours needed for comparison
            n_neighbours_ignored=0, # ignore no neighbours and include all
        )

Example 3. - Applying a framework of QC methods (e.g. IntenseQC)
================================================================

.. code-block:: python

        # 3. Applying multiple QC methods in framework (e.g. IntenseQC)
        from rainfallqc.qc_frameworks import apply_qc_framework

        # 3.1. Decide which QC methods of IntenseQC will be run
        qc_framework = "IntenseQC"
        qc_methods_to_run = ["QC1", "QC8", "QC9", "QC10", "QC11", "QC12", "QC14", "QC15", "QC16"]

        # 3.2 Decide which parameters for QC
        qc_kwargs = {
            "QC1": {"quantile": 5},
            "QC14": {"wet_day_threshold": 1.0, "accumulation_multiplying_factor": 2.0},
            "QC16": {
                "neighbouring_gauge_cols": daily_gpcc_network.columns[2:],
                "wet_threshold": 1.0,
                "min_n_neighbours": 5,
                "n_neighbours_ignored": 0,
            },
            # Shared defaults applied to all
            "shared": {
                "target_gauge_col": "rain_mm_DE_02483",
                "gauge_lat": gpcc_metadata["latitude"],
                "gauge_lon": gpcc_metadata["longitude"],
                "time_res": "daily",
                "data_resolution": 0.1,
            },
        }

        # 3.3. Run QC methods on network data
        qc_result = apply_qc_framework.run_qc_framework(
            daily_gpcc_network, qc_framework=qc_framework, qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
        )


Also see example Jupyter Notebooks here: https://github.com/Thomasjkeel/RainfallQC-notebooks/tree/main
