.. highlight:: shell

============
Quick Start
============
The easiest way to start using the package is to install it using :code:`pip install rainfallqc`.

.. note::
    You can then use `RainfallQC` in a project, with syntax like:

    .. code-block:: python

        import polars as pl
        import rainfallqc.gauge_checks

        data = pl.read_csv("path/to/your/rain_gauge_data.csv")
        flags = rainfallqc.gauge_checks.check_intermittency(data, target_gauge_col="rain_mm")


RainfallQC contains four modules:

1. ``gauge_checks`` - For detecting abnormalities in summary and descriptive statistics.
2. ``comparison_checks`` - For detecting abnormalities by comparing to benchmark data.
3. ``timeseries_checks`` - For detecting abnormalities in patterns of the data record.
4. ``neighbourhood_checks`` - For detecting abnormalities based on measurements in neighbouring gauges.
5. ``pypwsqc_filters`` - For applying quality assurance protocols and filters for rainfall data.

.. note::
    All quality control checks in RainfallQC begin with ``check_`` so to run a streaks check this would be ``rainfallqc.timeseries_checks.check_intermittency(data, **kwargs)``

You can find a jupyter notebook with an easy-to-follow example here: https://github.com/Thomasjkeel/RainfallQC-notebooks/blob/main/notebooks/demo/rainfallQC_demo.ipynb
