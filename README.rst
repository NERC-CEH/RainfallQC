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

..
    image:: https://readthedocs.org/projects/rainfallqc/badge/?version=latest
        :target: https://rainfallqc.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


Provides methods for running rainfall quality control.

Installation
------------
RainfallQC can be installed from PyPi:

.. code-block:: bash

    pip install rainfallqc


Example use
-----------

Example 1. - Individual quality checks on single rain gauge
===========================================================
Let's say you have data for a single rain gauge stored in "hourly_rain_gauge_data.csv" which looks like this:

.. code-block:: csv

        time,rain_mm
        2020-01-01 00:00,0.0
        2020-01-01 01:00,0.1
        2020-01-01 02:00,0.0
        2020-01-01 03:00,1.0
        2020-01-01 04:00,0.6
        ...

You can run individual quality control checks as follows:

.. code-block:: python

        import polars as pl
        from rainfallqc import gauge_checks

        data = pl.read_csv("hourly_rain_gauge_data.csv")
        intermittency_flag = gauge_checks.check_intermittency(data, target_gauge_col="rain_mm")


Example 2. - Applying a framework of QC methods (e.g. IntenseQC)
================================================================
You may have data that you want to run as part of a workflow of QC methods, e.g. the IntenseQC framework.
Let's say you have data for a multiple rain gauge stored in "hourly_rain_gauge_network.csv" which looks like this:

.. code-block:: csv

        time,rain_mm_gauge_1,rain_mm_gauge_2,rain_mm_gauge_3
        2020-01-01 00:00,0.0,0.5,0.0
        2020-01-01 01:00,0.5,0.0,1.0
        2020-01-01 02:00,0.0,1.0,0.0
        2020-01-01 03:00,1.0,0.0,0.5
        2020-01-01 04:00,0.0,0.5,0.0
        ...

To run some of the location-specific checks you will also need metadata for the gauges, e.g.:

.. code-block:: csv

        gauge_id,latitude,longitude
        rain_mm_gauge_1,52.0,-1.5
        rain_mm_gauge_2,52.1,-1.6
        rain_mm_gauge_3,52.2,-1.4
        ...


.. code-block:: python

        import polars as pl
        from rainfallqc.qc_frameworks import apply_qc_framework

        rain_gauge_network = pl.read_csv("hourly_rain_gauge_network.csv")

        qc_methods_to_run = ["QC1", "QC8", "QC9", "QC10", "QC11", "QC12", "QC14", "QC15", "QC16"]

        # Decide which parameters for QC
        qc_kwargs = {
            "QC1": {"quantile": 5},
            "QC14": {"wet_day_threshold": 1.0, "accumulation_multiplying_factor": 2.0},
            "QC16": {
                "neighbouring_gauge_cols": rain_gauge_network.columns[2:],
                "wet_threshold": 1.0,
                "min_n_neighbours": 5,
                "n_neighbours_ignored": 0,
            },
            "shared": {
                "target_gauge_col": "rain_mm_gauge_1",
                "gauge_lat": gpcc_metadata["latitude"],
                "gauge_lon": gpcc_metadata["longitude"],
                "time_res": "daily",
                "data_resolution": 0.1,
            },
        }

        # Run QC methods
        qc_result = apply_qc_framework.run_qc_framework(
            rain_gauge_network, qc_framework=qc_framework, qc_methods_to_run=qc_methods_to_run, qc_kwargs=qc_kwargs
        )


Other examples
===================
Of course, your data may not be tabular, or may not be stored in a single file. Therefore, please see our other `Tutorials <https://rainfallqc.readthedocs.io/en/latest/tutorials.html>`_.
There is also a `**demo notebook**<https://github.com/Thomasjkeel/RainfallQC-notebooks/blob/main/notebooks/demo/rainfallQC_demo.ipynb>`_.
Finally, different QC methods are suitable for different temporal resolutions - see our `Which checks are suitable for my data's temporal resolution? <https://rainfallqc.readthedocs.io/en/latest/quickstart.html>`_ for more information.

Documentation and License
-------------------------
* RainfallQC is developed and maintained by UKCEH.
* Free software: GNU General Public License v3
* Documentation: https://rainfallqc.readthedocs.io.


Features
--------

- 27 rainfall QC methods (25 from IntenseQC, 2 from pyPWSQC)
- polars DataFrame support for fast data processing
- modular structure so you can pick and choose which checks to run
- support for single gauges or networks of gauges
- editable parameters so you can tweak thresholds, streak or accumulation lengths, and distances to neighbouring gauges

Credits
-------
* Builds upon `IntenseQC <https://github.com/nclwater/intense-qc/tree/master>`_, and (is compatible with) `pyPWSQC <https://github.com/OpenSenseAction/pypwsqc>`_:
* Please email tomkee@ceh.ac.uk if you have any questions.
* This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
