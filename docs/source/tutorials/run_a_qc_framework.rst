==================
Run a QC framework
==================

.. contents::
   :local:
   :depth: 2

.. _example-6:


Example 6. - Running multiple QC checks on a single target gauge
----------------------------------------------------------------
To run multiple QC checks, you can use the `apply_qc_framework() <rainfallqc.checks.html#rainfallqc.qc_frameworks.html#module-rainfallqc.qc_frameworks.apply_qc_framework>`_
method to run QC methods from a given framework (e.g. IntenseQC).

Let's say you have hourly rainfall values from a rain gauge network data like
:ref:`example data 2 <example-data-table-2>` and metadata like :ref:`example metadata 1 <example-metadata-table-1>`.
You can then run multiple QC checks at once by defining a QC framework, the methods to run and parameters for those methods.

As of RainfallQC v0.5.0, there are three QC frameworks:

- 1. "intenseqc" - All 25 checks from IntenseQC/GSDR-QC with names like: "QC1", "QC2" ... "QC25",
- 2. "pypwsqc" - 2 checks from pyPWSQC with the names: "FZ" and "SO",
- 3. "custom" - Allows the user to select a custom set of checks (see Example 8).

Let's run some QC checks from intenseqc framework below:


.. code-block:: python
    :caption: Apply checks from a QC framework to a rain gauge data

        import polars as pl
        from rainfallqc.qc_frameworks import apply_qc_framework

        network_data = pl.read_csv("hourly_rain_gauge_network.csv")
        metadata = pl.read_csv("rain_gauge_metadata.csv")

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
            daily_rain_gauge_network, qc_framework=qc_framework, qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
        )


Because lots of the checks share the same parameters with a standard vocabulary, you can use the "shared" part of the ``qc_kwargs`` dictionary to set those.


.. _example-7:

Example 7. - Looping through rain gauges and running multiple QC checks
-----------------------------------------------------------------------
This example is a little more involved and less well-explained (please email me: tomkee@ceh.ac.uk if you have any questions).

This example shows you to run a loop over multiple gauges and how to store the outputs of the QC checks.
How you store things depends on the use-case.
Below, we give an example of storing a summary of the QC runs as the number of rows with flags for each check.
Some of the checks from RainfallQC do not return rows, but instead numbers or lists.
So first, we need to decide which checks will run, and which of those are row-wise.

.. code-block:: python
    :caption: Set up QC framework to loop over

    from rainfallqc.qc_frameworks.inbuilt_qc_frameworks import NON_ROWWISE_QC_CHECKS, NON_ROWWISE_QC_CONVERTER

    DATA_RESOLUTION = 0.2
    MIN_N_NEIGHBOURS_FOR_CALC = 8

    # Specificiations for QC run (NOTE: QC6 is heavy as using Pettit test)
    qc_to_run = ["QC1", "QC2", "QC3", "QC4", "QC5", "QC7", "QC8",
                "QC9", "QC10", "QC11", "QC12", "QC13", "QC14",
                "QC15", "QC17", "QC19", "QC21", "QC22", "QC23"]


    qc_kwargs = {
        "QC1": {"quantile": 5},
        "QC2": {"k": 3},
        "QC3": {"time_granularity": "hour"},
        "QC4": {"time_granularity": "weekday"},
        "QC5": {"no_data_threshold" : 2}, # days
        "QC7": {"expected_min_val": DATA_RESOLUTION},
        "QC13": {"accumulation_multiplying_factor": 2.0},
        "QC14": {"accumulation_multiplying_factor": 2.0},
        "shared": {
            "time_res": "hourly",
            "smallest_measurable_rainfall_amount": DATA_RESOLUTION,
            "wet_threshold": 1.0,
            "min_n_neighbours": MIN_N_NEIGHBOURS_FOR_CALC,
            "n_neighbours_ignored": 0
        }
    }

    # all checks that are computed as summary of overall data or once per year (so not one flag for every data point)
    non_rowwise_checks = NON_ROWWISE_QC_CHECKS
    non_rowwise_checks_converter = NON_ROWWISE_QC_CONVERTER


We will also need a function/class that will load in our nearby_metadata for each gauge (based on code from :ref:`Example 3 <example-3>`.
Please note that this makes very specific assumptions about the format of the data, and this may be different for your own purposes.

.. code-block:: python
    :caption: Code for loading neighbouring metadata and rainfall amount to a given target gauge ID
    
    from functools import reduce

    def load_gauge_neighbour_metadata_and_data(target_station_id, metadata):
        """
        Loads metadata and rainfall data from 10 nearest neighbours to a given target gauge
        """
        ten_nearest_neighbour_ids = get_ids_of_n_nearest_overlapping_neighbouring_gauges(
            metadata,
            target_id=target_station_id,
            distance_threshold=50,  # in km
            min_overlap_days=365*5,  # in days
            n_closest=10,  # number of neighbours to return
            start_datetime_col="start_datetime",
            end_datetime_col="end_datetime",
        )

        nearby_metadata = metadata.filter((pl.col('station_id').is_in(ten_nearest_neighbour_ids)) |
                                        (pl.col('station_id') == target_station_id))

        nearby_rainfall_data_list = []
        for path in nearby_metadata['path']:
            one_gauge = pl.read_csv(path, try_parse_dates=True)
            one_gauge = one_gauge.select(['time', 'rain_mm']) # assuming each file has these columns
            gauge_rain_col = path.split('/')[-1].split(f'.csv')[0] # create unique column name
            one_gauge = one_gauge.rename({'rain_mm': gauge_rain_col})
            nearby_rainfall_data_list.append(one_gauge)

        # Join all data together (consider 'how' to merge)
        nearby_rainfall_data = reduce(lambda left, right: left.join(right, on="time", how="left"), nearby_rainfall_data_list)

        return nearby_metadata, nearby_rainfall_data




Next, we can begin the loop, which in turn is going load data in from file paths and overwrite some of the keyword arguments in  ``qc_kwargs``
such as setting a new "target_gauge_col" each time.
We assume the data is stored in seperate CSV files (like :ref:`example data 1 <example-data-table-1>`) and there is metadata with paths to that data like :ref:`example metadata 1 <example-metadata-table-1>` (see :ref:`Example 3 <example-3>` also).

**Advice**, you may want to include ``try`` and ``except`` statements to capture rain gauges that may throw errors.
My plan is to update this example after some feedback.


**More advice** because this example assumes the data is hourly, the data is explicitly upsampled to 'hourly' in the loop with the Polars method ``.upsample("time", every="1h")``

.. code-block:: python
    :caption: Apply checks from a QC framework to multiple rain gauges and store summary statistics for each gauge

        import polars as pl
        from rainfallqc.qc_frameworks import apply_qc_framework

        network_data = pl.read_csv("hourly_rain_gauge_network.csv")
        metadata = pl.read_csv("rain_gauge_metadata.csv")

        overall_summary_of_qc = []

        # begin loop
        for station_id in metadata['station_id'].unique():
            nearby_metadata, nearby_rainfall_data = load_gauge_neighbour_metadata_and_data(target_station_id=station_id, metadata=metadata)

            target_gauge_col = station_id

            # get nearest neighbour
            nearby_gauge_distances = compute_km_distances_from_target_id(nearby_metadata, target_id=target_station_id, station_id_col='station_id')
            if len(nearby_gauge_distances) == 0:
                print(station_id, "no neighbours skipping")
                continue
            nearest_neighbour_id = nearby_gauge_distances.sort('distance')[0]['station_id'].item()

            # Update all the shared keyword arguments
            qc_kwargs["shared"]["rain_col"] = target_gauge_col
            qc_kwargs["shared"]["target_gauge_col"] = target_gauge_col
            qc_kwargs["shared"]["nearest_neighbour"] = nearest_neighbour_id
            qc_kwargs["shared"]["list_of_nearest_stations"] = nearby_rainfall_data.columns[1:]
            qc_kwargs["shared"]["gauge_lat"] = nearby_metadata.filter(pl.col("station_id") == target_gauge_col)['latitude']
            qc_kwargs["shared"]["gauge_lon"] = nearby_metadata.filter(pl.col("station_id") == target_gauge_col)['longitude']

            # Try to run the apply QC framework
            try:
                result = rainfallqc.apply_qc_framework.run_qc_framework(
                    data=nearby_rainfall_data.upsample("time", every="1h"),
                    qc_framework='IntenseQC',
                    qc_methods_to_run=qc_to_run,
                    qc_kwargs=qc_kwargs,
                )
            except Exception as e:
                print(station_id, e)
                continue

            # join all flags together for the given target rain gauge
            all_flags = {}
            all_flags['all_flags_by_row'] = nearby_rainfall_data["time", target_gauge_col]
            for qc in result:
                if isinstance(result[qc], pl.DataFrame):
                    try:
                        all_flags['all_flags_by_row'] = all_flags['all_flags_by_row'].join(result[qc], on="time")
                    except Exception as e:
                        print(e, station_id)
                else:
                    all_flags[qc] = result[qc]

            # Calculate summary statistics of flags
            all_flags['all_flags_by_row'] = all_flags['all_flags_by_row'].with_columns(
                pl.when(
                    pl.any_horizontal(pl.all().exclude(["time", target_gauge_col]).fill_null(0.0).map_elements(lambda col: col > 0))
                )
                    .then(1)
                    .otherwise(0)
                    .alias("is_flagged")
            )
            flagged_rows = all_flags['all_flags_by_row']['is_flagged'].value_counts().filter(pl.col("is_flagged") == 1)['count']
            not_flagged_rows = all_flags['all_flags_by_row']['is_flagged'].value_counts().filter(pl.col("is_flagged") == 0)['count']
            total_rows = flagged_rows + not_flagged_rows
            perc_flagged = ((flagged_rows/total_rows)*100)
            perc_flagged = perc_flagged.item() if perc_flagged.len() == 1 else 0
            print(f"Station ID: {station_id}\t\tFlag rate: {perc_flagged: .2f}%")

            # add to overall QC summary

            summary_of_qc = {}
            summary_of_qc['gauge_id'] = target_gauge_col
            summary_of_qc['num_nearby_gauges'] = len(nearby_metadata) - 1 # do not count the target
            summary_of_qc['perc_flagged'] = round(perc_flagged, 3)
            summary_of_qc['total_flagged_rows'] = flagged_rows[0] if flagged_rows.len() > 0 else 0
            summary_of_qc['total_rows'] = len(all_flags['all_flags_by_row'])

            for qc_key in non_rowwise_checks:
                if isinstance(all_flags[qc_key], list):
                    # sum number of years flagged
                    summary_of_qc[non_rowwise_checks_converter[qc_key]] = sum(item != 0 for item in all_flags[qc_key])
                else:
                    summary_of_qc[non_rowwise_checks_converter[qc_key]] = all_flags[qc_key]

            for col in all_flags['all_flags_by_row'].columns[2:]:
                summary_of_qc[col] = len(all_flags['all_flags_by_row'].filter(pl.col(col) > 0).drop_nans()[col])
            overall_summary_of_qc.append(summary_of_qc)


