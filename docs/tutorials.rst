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

.. table:: Example data 1. Single rain gauge
    :widths: auto
    :align: center

    +---------------------+---------+
    | time                | rain_mm |
    +=====================+=========+
    | 2020-01-01 00:00    | 0.0     |
    +---------------------+---------+
    | 2020-01-01 01:00    | 0.1     |
    +---------------------+---------+
    | 2020-01-01 02:00    | 0.0     |
    +---------------------+---------+
    | 2020-01-01 03:00    | 1.0     |
    +---------------------+---------+
    | 2020-01-01 04:00    | 0.6     |
    +---------------------+---------+


For the majority of the checks in RainfallQC, you can load in your data using `polars <https://pola-rs.github.io/polars-book/>`_ and run the checks directly.
Below, we run a check from the ``gauge_checks`` and ``timeseries_checks`` modules.

.. code-block:: python
    :caption: Running a daily accumulation check on a single rain gauge


        import polars as pl
        from rainfallqc import gauge_checks, timeseries_checks

        data = pl.read_csv("hourly_rain_gauge_data.csv")

        intermittency_flags = gauge_checks.check_intermittency(data, target_gauge_col="rain_mm")

        daily_accumulation_flags = timeseries_checks.check_daily_accumulations(
            data,
            target_gauge_col="rain_mm",
            gauge_lat=50.0,
            gauge_lon=8.0,
            smallest_measurable_rainfall_amount=0.1,
        )


Please note that some checks may require additional metadata, such as gauge location (latitude and longitude) or smallest measurable rainfall amount (e.g. 0.1 mm).
This could look like:

.. table:: Example metadata 1. Rain gauge metadata
    :widths: auto
    :align: center

    +--------------------+----------+-----------+------------------+------------------+---------------------+
    | station_id         | latitude | longitude | start_datetime   | end_datetime     | path                |
    +====================+==========+===========+==================+==================+=====================+
    | rain_mm_gauge_1    | 53.0     | 2.0       | 2020-01-01 00:00 | 2024-01-01 00:00 | path/to/gauge_1.csv |
    +--------------------+----------+-----------+------------------+------------------+---------------------+
    | rain_mm_gauge_2    | 54.1     | -0.5      | 2018-01-01 00:00 | 2023-01-01 00:00 | path/to/gauge_2.csv |
    +--------------------+----------+-----------+------------------+------------------+---------------------+
    | rain_mm_gauge_3    | 56.9     | 1.9       | 2015-01-01 00:00 | 2025-01-01 00:00 | path/to/gauge_3.csv |
    +--------------------+----------+-----------+------------------+------------------+---------------------+
    | ...                | ...      | ...       |                  |                  | ...                 |
    +--------------------+----------+-----------+------------------+------------------+---------------------+

You could then run checks that require metadata like:

.. code-block:: python
    :caption: Running a check for annual exceedance of maximum PRCPTOT from ETCCDI dataset.

        import polars as pl
        from rainfallqc import comparison_checks

        data = pl.read_csv("hourly_rain_gauge_data_gauge_1.csv")
        metadata = pl.read_csv("rain_gauge_metadata.csv")

        target_gauge_id = "rain_mm_gauge_1"

        target_gauge_lat = metadata.filter(pl.col("station_id") == target_gauge_id)["latitude"][0]
        target_gauge_lon = metadata.filter(pl.col("station_id") == target_gauge_id)["longitude"][0]

        comparison_checks.check_annual_exceedance_etccdi_prcptot(
            data, target_gauge_col=target_gauge_col, gauge_lat=target_gauge_lat, gauge_lon=target_gauge_lon
        )


Example 2. - Run individual checks on rain gauge network data (single file)
---------------------------------------------------------------------------
Let's say you have data for a multiple rain gauge stored in "hourly_rain_gauge_network.csv" which looks like this:

.. table:: Example data 2. Rain gauge network
    :widths: auto
    :align: center

    +---------------------+-----------------+-----------------+-----------------+
    | time                | rain_mm_gauge_1 | rain_mm_gauge_2 | rain_mm_gauge_3 |
    +=====================+=================+=================+=================+
    | 2020-01-01 00:00    | 0.0             | 0.5             | 0.0             |
    +---------------------+-----------------+-----------------+-----------------+
    | 2020-01-01 01:00    | 0.5             | 0.0             | 1.0             |
    +---------------------+-----------------+-----------------+-----------------+
    | 2020-01-01 02:00    | 0.0             | 1.0             | 0.0             |
    +---------------------+-----------------+-----------------+-----------------+
    | 2020-01-01 03:00    | 1.0             | 0.0             | 0.5             |
    +---------------------+-----------------+-----------------+-----------------+
    | 2020-01-01 04:00    | 0.0             | 0.5             | 0.0             |
    +---------------------+-----------------+-----------------+-----------------+
    | ...                 | ...             | ...             | ...             |
    +---------------------+-----------------+-----------------+-----------------+


You can then run a neighbourhood check from the ``neighbourhood_checks`` module.
Please note, you will need explicitly define which gauges are considered neighbouring to the target gauge.
You can do this with the `get_ids_of_n_nearest_overlapping_neighbouring_gauges <rainfallqc.utils.html#rainfallqc.utils.neighbourhood_utils.get_ids_of_n_nearest_overlapping_neighbouring_gauges>`_ function.
An example of its use is given in Example 3.

.. code-block:: python
    :caption: Running a wet neighbours check on a rain gauge network

        import polars as pl
        from rainfallqc import neighbourhood_checks

        data = pl.read_csv("hourly_rain_gauge_network.csv")

        wet_neighbour_flags = neighbourhood_checks.check_wet_neighbours(
            data,
            target_gauge_col="rain_mm_gauge_1",
            list_of_nearest_stations=["rain_mm_gauge_2", "rain_mm_gauge_3"],
            time_res="hourly",
            wet_threshold=1.0, # threshold for rainfall intensity to be considered
            min_n_neighbours=1, # number of neighbours needed for comparison
            n_neighbours_ignored=0, # ignore no neighbours and include all
        )


Example 3. - Run single checks on rain gauge network data (multiple file paths)
-------------------------------------------------------------------------------
Let's say you have data for a multiple rain gauge stored in multiple CSV files, you could use metadata to store the paths to them e.g. in "rain_gauge_metadata.csv" (Example metadata 1).
Because you may not want to load in all gauges to memory at once, you can read in only the nearby gauges to a given target gauge.
You can do this with the `get_ids_of_n_nearest_overlapping_neighbouring_gauges <rainfallqc.utils.html#rainfallqc.utils.neighbourhood_utils.get_ids_of_n_nearest_overlapping_neighbouring_gauges>`_ function.
(this example assumes all the CSVs look like Example data 1):

.. code-block:: python
    :caption: Making a pl.DataFrame of only nearby gauges to a target gauge

        import polars as pl
        from rainfallqc.utils.neighbourhood_utils import get_ids_of_n_nearest_overlapping_neighbouring_gauges, compute_km_distances_from_target_id

        data = pl.read_csv("hourly_rain_gauge_network.csv")
        metadata = pl.read_csv("rain_gauge_metadata.csv")

        target_gauge_id = "rain_mm_gauge_1"

        ten_nearest_neighbour_ids = get_ids_of_n_nearest_overlapping_neighbouring_gauges(
            metadata,
            target_id=target_gauge_id,
            distance_threshold=50,  # in km
            min_overlap_days=365*5,  # in days
            n_closest=10,  # number of neighbours to return
            start_datetime_col="start_datetime",
            end_datetime_col="end_datetime",
        )

        nearby_gauge_distances = neighbourhood_utils.compute_km_distances_from_target_id(metadata, target_id=target_gauge_id, station_id_col='station_id')

        nearest_gauge_id = nearby_gauge_distances.filter(
            pl.col("station_id").is_in(ten_nearest_neighbour_ids)
        ).sort('distance')[0]['station_id'].item()

        nearby_metadata = metadata.filter((pl.col('station_id').is_in(ten_nearest_neighbour_ids)) |
                                        (pl.col('station_id') == target_gauge_id))

        nearby_rainfall_data_list = []
        for path in nearby_metadata['path']:
            one_gauge = pl.read_csv(path, try_parse_dates=True)
            one_gauge = one_gauge.select(['time', 'rain_mm']) # assuming each file has these columns
            gauge_rain_col = path.split('/')[-1].split(f'.csv')[0] # create unique column name
            one_gauge = one_gauge.rename({'rain_mm': gauge_rain_col})
            nearby_rainfall_data_list.append(one_gauge)

        # Join all data together (consider 'how' to merge)
        nearby_rainfall_data = reduce(lambda left, right: left.join(right, on="time", how="left"), nearby_rainfall_data_list)


You can then run checks as normal e.g.:

.. code-block:: python
    :caption: Running correlation with nearest neighbour check

        from rainfallqc import neighbourhood_checks

        neighbour_correlation = neighbourhood_checks.check_neighbour_correlation(
                                        nearby_rainfall_data,
                                        target_gauge_col=target_gauge_id,
                                        nearest_neighbour=nearest_gauge_id
                                        )



Example 4. - Running check when your rain gauge data in netCDF format
---------------------------------------------------------------------




Example 5. - Tablular data you want to convert to xarray for pyPWSQC
--------------------------------------------------------------------



Example 6. - Running multiple QC checks on a single gauge
---------------------------------------------------------
To run multiple QC checks, you can use the `apply_qc_framework() <rainfallqc.checks.html#rainfallqc.qc_frameworks.html#module-rainfallqc.qc_frameworks.apply_qc_framework>`_
method to run QC methods from a given framework (e.g. IntenseQC).

Let's say you have daily rain gauge network data stored in a Polars DataFrame `daily_gpcc_network` (from a file like **Example data 2**)
and metadata stored in a dictionary `gpcc_metadata` (from a file like **Example data 3**). You can then run multiple QC checks by defining which framework as follows:


.. code-block:: python

        import polars as pl
        from rainfallqc.qc_frameworks import apply_qc_framework

        daily_gpcc_network = pl.read_csv("daily_gpcc_network.csv")  # Load your daily rain gauge network data
        daily_gpcc_metadata = pl.read_csv("daily_gpcc_metadata.csv")  # Load your metadata

        # 1. Decide which QC methods of IntenseQC will be run
        qc_framework = "IntenseQC"
        qc_methods_to_run = ["QC1", "QC8", "QC9", "QC10", "QC11", "QC12", "QC14", "QC15", "QC16"]

        # 2. Determine nearest neighbouring gauges for neighbourhood checks
        gauge_lat = gpcc_metadata["latitude"]
        gauge_lon = gpcc_metadata["longitude"]
        nearest_neighbourhours = ["rain_mm_gauge_2", "rain_mm_gauge_3", ...] # or see Example 3 if not determined

        # 2 Decide which parameters for QC
        qc_kwargs = {
            "QC1": {"quantile": 5},
            "QC14": {"wet_day_threshold": 1.0, "accumulation_multiplying_factor": 2.0},
            "QC16": {
                "list_of_nearest_stations": nearest_neighbourhours,
                "wet_threshold": 1.0,
                "min_n_neighbours": 5,
                "n_neighbours_ignored": 0,
            },
            "shared": {
                "target_gauge_col": "rain_mm_gauge_1",
                "gauge_lat": gauge_lat,
                "gauge_lon": gauge_lon,
                "time_res": "daily",
                "smallest_measurable_rainfall_amount": 0.1,
            },
        }

        # 3. Run QC methods on network data
        qc_result = apply_qc_framework.run_qc_framework(
            daily_gpcc_network, qc_framework=qc_framework, qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
        )


Because lots of the checks share the same parameters with a standard vocabulary, you can use the "shared" part of the ``qc_kwargs`` dictionary to set those.

Example 7. - Running multiple QC checks on a network of gauges
--------------------------------------------------------------



Example 8. - Running a sensitivity analysis
-------------------------------------------



Also see example Jupyter Notebooks here: https://github.com/Thomasjkeel/RainfallQC-notebooks/tree/main
