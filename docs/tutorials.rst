=========
Tutorials
=========

RainfallQC contains four modules:

1. ``gauge_checks`` - For detecting abnormalities in summary and descriptive statistics.
2. ``comparison_checks`` - For detecting abnormalities by comparing to benchmark data.
3. ``timeseries_checks`` - For detecting abnormalities in patterns of the data record.
4. ``neighbourhood_checks`` - For detecting abnormalities based on measurements in neighbouring gauges.
5. ``pypwsqc_filters`` - For applying quality assurance protocols and filters for rainfall data from `pyPWSQC package <https://pypwsqc.readthedocs.io/en/latest/index.html>`


Each one of these modules contains individual QC check methods, which begin with the syntax ``check_``.
For example to run a streaks check you can run: ``rainfallqc.timeseries_checks.check_streaks(data, **kwargs)``


Example overview
================
How you use RainfallQC will depend on the format of your data. The table below outlines a few potential formats and how to use RainfallQC with them.

+--------------------------------------+-----------------------------------------------+--------------------------------------------------------------+
| Data format                         | Description                                   | Example usage                                                |
+======================================+===============================================+==============================================================+
| Single rain gauge data              | Data from a single rain gauge in a tabular    |
|                                      | format (e.g. CSV) with a timestamp column     | See Example 1 below                                          |
|                                      | and a rainfall measurement column.            |                                                              |
+--------------------------------------+-----------------------------------------------+--------------------------------------------------------------+
| Rain gauge network data (one large CSV)             | Data from multiple rain gauges in a tabular   | See Example 2 below                                          |
|                                      | format (e.g. CSV) with a timestamp column     |
|                                      | and multiple rainfall measurement columns.    |                                                              |
+--------------------------------------+-----------------------------------------------+--------------------------------------------------------------+
| Rain gauge network data (multiple paths)          | Data from multiple rain gauges stored in      | See Example 2 below                                          |
|                                      | separate files (e.g. CSVs) with a timestamp   |
|                                      | column and a rainfall measurement column.     |                                                              |
+--------------------------------------+-----------------------------------------------+--------------------------------------------------------------+
| Data in xarray format                | Data stored in xarray format, e.g. from       | See Example 3 below                                          |
|                                      | NetCDF files or OpenDAP sources.              |                                                              |
+--------------------------------------+-----------------------------------------------+--------------------------------------------------------------+





Example 1. - Individual quality checks on single rain gauge
===========================================================

.. code-block:: python

        import polars as pl
        from rainfallqc import gauge_checks, comparison_checks

        data = pl.read_csv("rain_gauge_data.csv")
        intermittency_flag = gauge_checks.check_intermittency(data, target_gauge_col="rain_mm")


Example 2. - Neighbourhood quality checks for the global sub-daily rain gauge network (GSDR)
============================================================================================

.. code-block:: python

        from rainfallqc import neighbourhood_checks
        from rainfallqc.utils import data_readers

        distance_threshold = 50  # km
        n_closest = 10 # number of closest neighbours to consider
        min_overlap_days = 500  # minimum overlapping days to be considered a neighbour

        gsdr_obj = data_readers.GSDRNetworkReader(path_to_gsdr_dir="path/to/GSDR/data")

        nearby_ids = list(
            gsdr_obj.get_nearest_overlapping_neighbours_to_target(
                target_id="DE_00310", distance_threshold=distance_threshold, n_closest=n_closest, min_overlap_days=min_overlap_days
            )
        )
        nearby_ids.append(target_id)
        nearby_data_paths = gsdr_obj.metadata.filter(pl.col("station_id").is_in(nearby_ids))["path"]

        # Load those nearest gauges from network metadata
        gsdr_network = gsdr_obj.load_network_data(data_paths=nearby_data_paths)

        # Run wet neighbour check
        extreme_wet_flags = neighbourhood_checks.check_wet_neighbours(
            gsdr_network,
            target_gauge_col="rain_mm_DE_02483",
            neighbouring_gauge_cols=gsdr_network.columns[1:],  # exclude time
            time_res="hourly",
            wet_threshold=1.0, # threshold for rainfall intensity to be considered
            min_n_neighbours=5, # number of neighbours needed for comparison
            n_neighbours_ignored=0, # ignore no neighbours and include all
        )


Example 3. - Applying a framework of QC methods (e.g. IntenseQC)
================================================================

.. code-block:: python

        from rainfallqc.qc_frameworks import apply_qc_framework

        # 1. Decide which QC methods of IntenseQC will be run
        qc_framework = "IntenseQC"
        qc_methods_to_run = ["QC1", "QC8", "QC9", "QC10", "QC11", "QC12", "QC14", "QC15", "QC16"]

        # 2 Decide which parameters for QC
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

        # 3. Run QC methods on network data
        qc_result = apply_qc_framework.run_qc_framework(
            daily_gpcc_network, qc_framework=qc_framework, qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
        )


Also see example Jupyter Notebooks here: https://github.com/Thomasjkeel/RainfallQC-notebooks/tree/main
