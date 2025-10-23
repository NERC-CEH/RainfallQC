.. highlight:: shell

============
Quick Start
============
The easiest way to start using the package is to install it using :code:`pip install rainfallqc`.

.. note::
    To use `RainfallQC` in a project, the syntax will be like:

    .. code-block:: python

        import polars as pl
        import rainfallqc.gauge_checks

        data = pl.read_csv("path/to/your/rain_gauge_data.csv")
        flags = rainfallqc.gauge_checks.check_intermittency(data, target_gauge_col="rain_mm")


All quality control checks in the RainfallQC package begin with ``check_``

Content overview
----------------

RainfallQC contains five modules:

1. ``gauge_checks`` - For detecting abnormalities in summary and descriptive statistics.
2. ``comparison_checks`` - For detecting abnormalities by comparing to benchmark data.
3. ``timeseries_checks`` - For detecting abnormalities in patterns of the data record.
4. ``neighbourhood_checks`` - For detecting abnormalities based on measurements in neighbouring gauges.
5. ``pypwsqc_filters`` - For applying quality assurance protocols and filters for rainfall data.

You can find a jupyter notebook with an easy-to-follow example `here <https://github.com/Thomasjkeel/RainfallQC-notebooks/blob/main/notebooks/demo/rainfallQC_demo.ipynb>`_

Which checks are suitable for my data's temporal resolution?
------------------------------------------------------------
As you can imagine, not all quality control checks are suitable for all temporal data resolutions (e.g. 15 min, hourly, daily, monthly).
Therefore, we have created a table that shows which checks are suitable for which temporal data resolutions.


.. image:: https://github.com/NERC-CEH/RainfallQC/blob/main/docs/images/qc_applicability_table.png
   :align: center
   :height: 300px
   :width: 200 px
   :alt: Temporal applicability QC table
