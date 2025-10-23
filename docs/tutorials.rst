=========
Tutorials
=========

RainfallQC contains four modules:

1. ``gauge_checks`` - For detecting abnormalities in summary and descriptive statistics.
2. ``comparison_checks`` - For detecting abnormalities by comparing to benchmark data.
3. ``timeseries_checks`` - For detecting abnormalities in patterns of the data record.
4. ``neighbourhood_checks`` - For detecting abnormalities based on measurements in neighbouring gauges.
5. ``pypwsqc_filters`` - For applying quality assurance protocols and filters for rainfall data from `pyPWSQC <https://pypwsqc.readthedocs.io/en/latest/index.html>`_


Each one of these modules contains individual QC check methods, which begin with the syntax ``check_``.
For example to run a streaks check you can run: ``rainfallqc.timeseries_checks.check_streaks(data, **kwargs)``


Getting started
===============

What's the format of your data?
-------------------------------
How you use RainfallQC will depend on the format of your data. The table below outlines a few potential formats and how to use RainfallQC with them.

+--------------------------------------------+--------------+--------------------------------------------------------------+
| Data format                                | See...       | Notes                                                        |
+============================================+==============+==============================================================+
| Single rain gauge (e.g. 1 CSV)             | Example 1    |                                                              |
+--------------------------------------------+--------------+--------------------------------------------------------------+
| Rain gauge network data (e.g. 1 CSV        | Example 2    | You will need to define which of those gauges are considered |
| with multiple columns)                     |              | to be neighbouring to a target gauge. Therefore you also     |
|                                            |              | need metadata with gauge locations.                          |
+--------------------------------------------+--------------+--------------------------------------------------------------+
| Rain gauge network data (multiple file     | Example 3    | Load in metadata with gauge locations, then read in only     |
| paths)                                     |              | nearby gauges to a given target.                             |
+--------------------------------------------+--------------+--------------------------------------------------------------+
| Rain gauge data in netCDF format           | Example 4    | Be careful as you will lose metadata.                        |
+--------------------------------------------+--------------+--------------------------------------------------------------+
| Tablular data you want to convert to       | Example 5    | Required if you want to run pyPWSQC methods, but your data   |
| xarray for pyPWSQC                         |              | is CSVs. Sets your data's time format and projection using   |
|                                            |              | deafults to create metadata.                                 |
+--------------------------------------------+--------------+--------------------------------------------------------------+


Which scenario best suits you?
------------------------------
Do you have a single rain gauge, or a whole network? Do you want to run a single check or use RainfallQC as part of a data processing pipeline?
The table below outlines some common scenarios and advice on how to proceed.

+---------------------------------------------------+--------------------------------------------------------------+
| Scenario                                          | Advice                                                       |
+===================================================+==============================================================+
| Running a single QC check                         | See Examples 1-4 below.                                      |
+---------------------------------------------------+--------------------------------------------------------------+
| Running multiple QC checks on a single gauge      | Use the `.apply_qc_framework()` method. See Example 6 below. |
+---------------------------------------------------+--------------------------------------------------------------+
| Running multiple QC checks on a network of gauges | Use the `.apply_qc_framework()` method in a loop and store   |
|                                                   | a summary. See Example 7 below.                              |
+---------------------------------------------------+--------------------------------------------------------------+
| Running a sensitivity analysis                    | You will need to create your own qc_framework specs. See     |
|                                                   | Example 8 below.                                             |
+---------------------------------------------------+--------------------------------------------------------------+


Examples
========

Example 1. - Running individual checks on a single rain gauge
-------------------------------------------------------------
Let's say you have data for a single rain gauge stored in "hourly_rain_gauge_data.csv" which looks like this:

.. code-block:: csv
    :caption: **Example data** Single rain gauge data example

        time,rain_mm
        2020-01-01 00:00,0.0
        2020-01-01 01:00,0.1
        2020-01-01 02:00,0.0
        2020-01-01 03:00,1.0
        2020-01-01 04:00,0.6
        ...


For the majority of the checks in RainfallQC, you can load in your data using `polars <https://pola-rs.github.io/polars-book/>`_ and run the checks directly.
Below, we run a check from the ``gauge_checks`` and ``comparison_checks`` modules.

.. code-block:: python
    :caption: Running individual quality checks on a single rain gauge


        import polars as pl
        from rainfallqc import gauge_checks, timeseries_checks

        data = pl.read_csv("hourly_rain_gauge_data.csv")

        intermittency_flags = gauge_checks.check_intermittency(data, target_gauge_col="rain_mm")

        daily_accumulation_flags = timeseries_checks.check_daily_accumulations(
            data,
            target_gauge_col="rain_mm",
            gauge_lat=50.0,
            gauge_lon=8.0,
            data_resolution=0.1,
        )


Example 2. - Run individual checks on rain gauge network data (single source)
-----------------------------------------------------------------------------
Let's say you have data for a multiple rain gauge stored in "hourly_rain_gauge_network.csv" which looks like this:

.. code-block:: csv

        time,rain_mm_gauge_1,rain_mm_gauge_2,rain_mm_gauge_3
        2020-01-01 00:00,0.0,0.5,0.0
        2020-01-01 01:00,0.5,0.0,1.0
        2020-01-01 02:00,0.0,1.0,0.0
        2020-01-01 03:00,1.0,0.0,0.5
        2020-01-01 04:00,0.0,0.5,0.0
        ...

.. code-block:: python

        import polars as pl
        from rainfallqc import neighbourhood_checks

        data = pl.read_csv("hourly_rain_gauge_network.csv")

        wet_neighbour_flags = neighbourhood_checks.check_wet_neighbours(
            data,
            target_gauge_col="rain_mm_gauge_1",
            neighbouring_gauge_cols=["rain_mm_gauge_2", "rain_mm_gauge_3"],
            time_res="hourly",
            wet_threshold=1.0, # threshold for rainfall intensity to be considered
            min_n_neighbours=1, # number of neighbours needed for comparison
            n_neighbours_ignored=0, # ignore no neighbours and include all
        )


Example 3. - Run single checks on rain gauge network data (multiple sources)
-----------------------------------------------------------------------------
Let's say you have data for a multiple rain gauge stored in multiple CSV files, with metadata stored in "rain_gauge_metadata.csv" which looks like this:

.. code-block:: csv

        station_id,latitude,longitude,path
        gauge_1,50.0,8.0,path/to/gauge_1.csv
        gauge_2,50.1,8.1,path/to/gauge_2.csv
        gauge_3,49.9,7.9,path/to/gauge_3.csv
        ...

Bear in mind, you could create the 'path' column programmatically if needed.




Example 4. - Individual quality checks on a single rain gauge
-------------------------------------------------------------


Example 5. - Individual quality checks on a single rain gauge
-------------------------------------------------------------





Example X. - Neighbourhood quality checks for the global sub-daily rain gauge network (GSDR)
--------------------------------------------------------------------------------------------

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
-----------------------------------------------------------------

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
