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

**NOTEBOOK DEMO AVAILABLE** `HERE <https://github.com/Thomasjkeel/RainfallQC-notebooks/blob/main/notebooks/demo/rainfallQC_demo.ipynb>`_

Please email tomkee@ceh.ac.uk if you have any questions.

Installation
------------
RainfallQC can be installed from PyPi:

.. code-block:: bash

    pip install rainfallqc


Example use
-----------

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


Other examples
===================
Also see example Jupyter Notebooks here: https://github.com/Thomasjkeel/RainfallQC-notebooks/tree/main

Documents
---------
* Free software: GNU General Public License v3
* Documentation: https://rainfallqc.readthedocs.io.


Features
--------

- 25 rainfall QC methods (all from IntenseQC)
- editable parameters so you can tweak thresholds, streak or accumulation lengths, and distances to neighbouring gauges

Credits
-------
Based on the IntenseQC: https://github.com/nclwater/intense-qc/tree/master


This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
