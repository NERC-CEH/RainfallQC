.. image:: https://github.com/NERC-CEH/RainfallQC/blob/main/docs/logos/rainfallQC_logo.png
   :align: center
   :height: 180px
   :width: 200 px
   :alt: RainfallQC

===============================================
RainfallQC - Quality control for rainfall data
===============================================

.. image:: https://img.shields.io/pypi/v/rainfallqc.svg
        :target: https://pypi.python.org/pypi/rainfallqc

.. image:: https://github.com/NERC-CEH/RainfallQC/actions/workflows/deploy-docs.yml/badge.svg
   :target: https://github.com/NERC-CEH/RainfallQC/actions/workflows/deploy-docs.yml
   :alt: Deploy docs

.. image:: https://zenodo.org/badge/917722737.svg
        :target: https://doi.org/10.5281/zenodo.17457013

Provides methods for running rainfall quality control.

Installation
============
RainfallQC can be installed from PyPi:

.. code-block:: bash

    pip install rainfallqc


Example use
===========

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
    | 2020-01-01 03:00    | 105.0   |
    +---------------------+---------+
    | 2020-01-01 04:00    | 0.6     |
    +---------------------+---------+
    | ...                 | ...     |
    +---------------------+---------+


For the majority of the checks in RainfallQC, you can load in your data using `polars <https://pola-rs.github.io/polars-book/>`_ and run the checks directly.
Below, we run 2 example QC checks:

- 1) ``check_intermittency`` - to flag years where there are periods of non-zero bounded by 0 (see Figure 1.),
- 2) ``daily_accumulations`` - to flag accumulations of hourly values into daily.

.. figure:: https://thomasjkeel.github.io/UK-Rain-Gauge-Network/example_images/intermittency.png
   :align: center
   :height: 250px
   :width: 300px

   **Figure 1.** Example of an intermittency issue within the rainfall record

.. code-block:: python

        import polars as pl
        from rainfallqc import gauge_checks, timeseries_checks

        data = pl.read_csv("hourly_rain_gauge_data.csv")

        intermittent_years = gauge_checks.check_intermittency(data, target_gauge_col="rain_mm")

        daily_accumulation_flags = timeseries_checks.check_daily_accumulations(
            data,
            target_gauge_col="rain_mm",
            gauge_lat=52.0,
            gauge_lon=2.0,
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

You could then run checks that require metadata i.e. the ``check_hourly_exceedance_etccdi_rx1day`` QC check which flags rainfall values exceeding
the hourly day rainfall 1-day record at a given location (see Figure 2):

.. figure:: https://thomasjkeel.github.io/UK-Rain-Gauge-Network/example_images/rx1day_check.png
   :align: center
   :height: 250px
   :width: 300px

   **Figure 2.** Example of an Rx1day check from the IntenseQC framework

The code for that check looks like:

.. code-block:: python

        import polars as pl
        from rainfallqc import comparison_checks

        data = pl.read_csv("hourly_rain_gauge_data_gauge_1.csv")
        metadata = pl.read_csv("rain_gauge_metadata.csv")

        target_gauge_id = "rain_mm_gauge_1"
        target_metadata = metadata.filter(pl.col("station_id") == target_gauge_id)

        rx1day_check = comparison_checks.check_hourly_exceedance_etccdi_rx1day(
             data,
             target_gauge_col=target_gauge_col,
             gauge_lat=target_metadata["latitude"],
             gauge_lon=target_metadata["longitude"]
        )

Output flags will then look like:

.. table:: Example flag outputs for the Rx1day QC check
    :widths: auto
    :align: center

    +---------------------+--------------+
    | time                | rx1day_check |
    +=====================+==============+
    | 2020-01-01 00:00    | 0            |
    +---------------------+--------------+
    | 2020-01-01 01:00    | 0            |
    +---------------------+--------------+
    | 2020-01-01 02:00    | 0            |
    +---------------------+--------------+
    | 2020-01-01 03:00    | 1            |
    +---------------------+--------------+
    | 2020-01-01 04:00    | 0            |
    +---------------------+--------------+
    | ...                 | ...          |
    +---------------------+--------------+

Example 2. - Running multiple QC checks on a single target gauge
----------------------------------------------------------------
To run multiple QC checks, you can use the `apply_qc_framework() <rainfallqc.checks.html#rainfallqc.qc_frameworks.html#module-rainfallqc.qc_frameworks.apply_qc_framework>`_
method to run QC methods from a given framework (e.g. IntenseQC).

For more information about how to run multiple checks in a framework see `Example 4 in the docs <https://nerc-ceh.github.io/RainfallQC/tutorials/running_multiple_qc_checks.html>`_

Other examples
--------------
Of course, your data may not be tabular, or may not be stored in a single file. Therefore, please see our other `Tutorials <https://nerc-ceh.github.io/RainfallQC/tutorials/overview.html>`_.


QC frameworks in RainfallQC
===========================

As of RainfallQC v1.1.0, there are three QC frameworks:

1. "intenseqc" - All 25 checks from IntenseQC/GSDR-QC with names like: "QC1", "QC2" ... "QC25",
2. "pypwsqc" - 2 checks from pyPWSQC with the names: "FZ" and "SO",
3. "subhourlyqc" - Checks to extent intenseqc for subhourly data (7 new, 12 shared with intenseqc), with names like "HQC_QC1", "SHQC_freqResChecker":
4. and "custom" - Allows the user to select a custom set of checks (see Example 8 in `Tutorials <https://nerc-ceh.github.io/RainfallQC/tutorials/run_a_sensitivity_analysis.html>`_).


.. role:: green
   :class: qc-green

.. role:: dark-green
   :class: qc-dark-green

.. role:: red
   :class: qc-red


.. table:: QC checks and appropriate time-resolution
   :widths: auto
   :align: left

   =========================================== =====================  ==================================================================================== ================= ================= ================= ================= =================
   Long name                                   Sub-module             QC Framework                                                                         <15-min           15-min            hourly            daily             monthly
   =========================================== =====================  ==================================================================================== ================= ================= ================= ================= =================
   Percentiles                                 Gauge checks           `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   K-largest                                   Gauge checks           `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   Days of week                                Gauge checks           `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   Hours of day                                Gauge checks           `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`
   Intermittency                               Gauge checks           `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   Breakpoints                                 Gauge checks           `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   Minimum value change                        Gauge checks           `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   R99p                                        Comparison checks      `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   PRCPTOT                                     Comparison checks      `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   World Record                                Comparison checks      `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   Rx1day                                      Comparison checks      `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`
   CDD (Dry spells)                            Timeseries checks      `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   Daily accumulations                         Timeseries checks      `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :dark-green:`agg` :dark-green:`agg` :green:`✓`        :green:`✓`        :red:`☓`
   Monthly accumulations                       Timeseries checks      `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   Streaks                                     Timeseries checks      `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :dark-green:`agg` :dark-green:`agg` :green:`✓`        :green:`✓`        :red:`☓`
   Daily neighbours (wet)                      Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   Hourly neighbours (wet)                     Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`
   Daily neighbours (dry)                      Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   Hourly neighbours (dry)                     Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`
   Monthly neighbours                          Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :green:`✓`
   Timing offset                               Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   Pre-QC affinity index                       Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓` 
   Pre-QC pearson correlation                  Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`
   Daily factor                                Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :green:`✓`        :red:`☓`
   Monthly factor                              Neighbourhood checks   `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_   :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :dark-green:`agg` :green:`✓`
   Check exceedance of UK 1h record            Sub-hourly thresholds  `SubHourlyQC <https://doi.org/10.1002/qj.4357>`_                                     :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   Check exceedance of UK 24h record           Sub-hourly thresholds  `SubHourlyQC <https://doi.org/10.1002/qj.4357>`_                                     :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   Check 24h-sum exceedance of UK 24h record   Sub-hourly thresholds  `SubHourlyQC <https://doi.org/10.1002/qj.4357>`_                                     :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   Check streaks (20 mm min)                   Sub-hourly thresholds  `SubHourlyQC <https://doi.org/10.1002/qj.4357>`_                                     :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   Check data has sub-hourly frequency         Sub-hourly thresholds  `SubHourlyQC <https://doi.org/10.1002/qj.4357>`_                                     :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   Check sub-hourly rainfall thresholds        Sub-hourly thresholds  `SubHourlyQC <https://doi.org/10.1002/qj.4357>`_                                     :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`          :red:`☓`
   Faulty Zeros                                pyPWSQC filters        `pyPWSQC <https://doi.org/10.5281/zenodo.4501919>`_                                  :green:`✓`        :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`
   Station Outliers                            pyPWSQC filters        `pyPWSQC <https://doi.org/10.5281/zenodo.4501919>`_                                  :green:`✓`        :green:`✓`        :green:`✓`        :red:`☓`          :red:`☓`     
   =========================================== =====================  ==================================================================================== ================= ================= ================= ================= =================



Documentation and License
=========================
* RainfallQC is developed and maintained by UKCEH.
* Free software: GNU General Public License v3
* Documentation: https://nerc-ceh.github.io/RainfallQC/


Features
========

- 33 rainfall QC methods (25 from IntenseQC, 6 from SubHourlyQC and 2 from pyPWSQC)
- polars DataFrame support for fast data processing
- modular structure so you can pick and choose which checks to run
- support for single gauges or networks of gauges
- editable parameters so you can tweak thresholds, streak or accumulation lengths, and distances to neighbouring gauges

Note on time aggregation
========================
Hourly data is aggregated with 'label=right', so 07:00:01 to 08:00 is labelled 08:00.
For daily and monthly aggregation, label is left, so n-hour on D to n-hour on D+1 is D.

How to cite this package
========================
To cite a specific version of RainfallQC, please see `Zenodo <https://zenodo.org/records/17457184>`_ DOI. 
For v0.3.1: https://doi.org/10.5281/zenodo.17457013

Credits
=======
* Builds upon `IntenseQC <https://github.com/nclwater/intense-qc/tree/master>`_, `SubHourlyQC <https://github.com/nclwater/SubHourlyQC/tree/main>`_  and (is compatible with) `pyPWSQC <https://github.com/OpenSenseAction/pypwsqc>`_:
* Please email tomkee@ceh.ac.uk if you have any questions.
* This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
