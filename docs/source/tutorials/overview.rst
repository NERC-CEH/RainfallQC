=================
Tutorial overview
=================

RainfallQC contains five modules:

1. ``gauge_checks`` - For detecting abnormalities in summary and descriptive statistics.
2. ``comparison_checks`` - For detecting abnormalities by comparing to benchmark data.
3. ``timeseries_checks`` - For detecting abnormalities in patterns of the data record.
4. ``neighbourhood_checks`` - For detecting abnormalities based on measurements in neighbouring gauges.
5. ``pypwsqc_filters`` - For applying quality assurance protocols and filters for rainfall data from `pyPWSQC <https://pypwsqc.readthedocs.io/en/latest/index.html>`_


Each one of these modules contains individual QC check methods, which begin with the syntax ``check_``.
For example to run a QC check that will check whether there are streaks of repeating values in your data, you can run: ``timeseries_checks.check_streaks(data, **kwargs)``.

Various example of errors in rainfall data can be viewed on this `web map <https://thomasjkeel.github.io/UK-Rain-Gauge-Network/qc_map.html>`_.


Getting started
===============

What's the format of your data?
-------------------------------
How you use RainfallQC will depend on the format of your data. The table below outlines a few potential formats and how to use RainfallQC with them.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Data format
     - See...
     - Notes
   * - Single rain gauge (e.g. 1 CSV)
     - :ref:`Example 1 <example-1>`
     - All RainfallQC checks were built to run on tabular data
   * - Rain gauge network data (e.g. 1 CSV with multiple columns)
     - :ref:`Example 2 <example-2>`
     - You will need to define which gauges are considered neighbouring to a target gauge. Therefore you also need metadata with gauge locations.
   * - Rain gauge network data (multiple file paths)
     - :ref:`Example 3 <example-3>`
     - Load in metadata with gauge locations, then read in only nearby gauges to a given target.
   * - Rain gauge data as xarray Dataset
     - :ref:`Example 4 <example-4>`
     - If your data is in NetCDF format, for example. Be careful as you will lose metadata.
   * - Tabular data you want to convert to xarray for pyPWSQC
     - :ref:`Example 5 <example-5>`
     - Required if you want to run pyPWSQC methods, but your data is CSVs. Sets your data's time format and projection using defaults to create metadata.

Which scenario best suits you?
------------------------------
Do you have a single rain gauge, or a whole network? Do you want to run a single check or use RainfallQC as part of a data processing pipeline?
The table below outlines some common scenarios and advice on how to proceed.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Scenario
     - Advice
   * - Running a single QC check
     - See Examples :ref:`1 <example-1>`, :ref:`2 <example-2>` and :ref:`3 <example-3>`.
   * - Running multiple QC checks on a single gauge
     - Use the :py:meth:`.apply_qc_framework() <rainfallqc.qc_frameworks.apply_qc_framework.run_qc_framework>` method. See :ref:`Example 6 <example-6>` below.
   * - Running multiple QC checks on multiple gauges
     - Use the :py:meth:`.apply_qc_framework() <rainfallqc.qc_frameworks.apply_qc_framework.run_qc_framework>` method in a loop and store a summary. See :ref:`Example 7 <example-7>` below.
   * - Defining your own sensitivity analysis
     - You will need to create your own qc_framework specs. See :ref:`Example 8 <example-8>` below.



----------------

Real coding example for RainfallQC are available as Jupyter Notebooks at: https://github.com/Thomasjkeel/RainfallQC-notebooks/tree/main

----------------
