=======
History
=======

0.4.0 (2025-01-27)
------------------
* Add support for 15 min data resolution
* Change group_by_dynamic to include 'closed='left'' and 'label' parameters for better resampling control
* Add resample_data_by_time_step utility function
* Set default min_count to 50% of expected values when resampling data
* Update neighbourhood checks to handle 15 min data and resampling

0.3.2 (2025-01-22)
------------------
* Bug fix, return only neighbours when calculating nearest neighbour ids

0.3.1 (2025-10-23)
------------------
* Publish to Zenodo

0.3.0 (2025-10-23)
------------------
* Overhaul tutorials, quickstart and examples on readthedocs
* allow user-defined qc frameworks to be passed to apply_qc_framework function
* check for data input to haversine function are convertible to float
* rename data_resolution parameter to smallest_measurable_rainfall_amount
* rename neighbouring_gauge_col to nearest_neighbour
* rename neighbouring_gauges_cols to list_of_nearest_neighbours
* get_ids_of_n_nearest_overlapping_neighbouring_gauges now returns list not set
* update all unit tests to reflect changes above

0.2.5 (2025-10-22)
------------------
* Add AUTHORS.rst file to include contributors
* Update README.rst examples to remove comments
* rename GDSR to GSDR

0.2.4 (2025-10-13)
------------------
* Fix haversine function so inputs are cast to np.ndarray

0.2.3 (2025-10-09)
------------------
* Fix bug in all_qc_checks decorator so that args are bound when checking for target_gauge_col and neighbouring_gauge_col(s)
* automatically remove columns with non-finite values when running neighbourhood checks

0.2.2 (2025-10-07)
------------------
* Add decorator to all QC checks to optionally check for negative values in the rainfall columns
* Fix bug in intermittency check to check for inconistent time steps
* Fix bug of missing values in GPCC loader (now -999.9 are treated as missing values)
* Allow users to set station id, start_ and end_datetime column names in neighbourhood utility functions
* Add Haversine distance function to spatial utils

0.2.1 (2025-08-27)
------------------
* Add converter functions for 'Faulty_zeros' and 'Station Outliers' from pyPWSQC

0.2.0 (2025-08-27)
------------------
* Add basic documentation

0.1.8 (2025-07-30)
------------------
* Update intermittency check to whether intermitent period is followed by zeros.

0.1.7 (2025-07-03)
------------------
* Add hour offset to neighbour methods to prevent incorrect aggregation from hourly to daily
* affinity_index method now checks for length of binary columns

0.1.6 (2025-06-13)
------------------
* rename dry and wet spell flags so they include time resolution
* fix list comprehension so it iterates over copy of neighbouring cols for QC16-QC19
* rename QC11 from 'check_annual_exceedance_etccdi_rx1day' to 'check_hourly_exceedance_etccdi_rx1day'
* Add 15min support for QC11 and QC14
* Remove daily support for QC13 and QC15 (only works on hourly)
* Add hourly qc framework fixture for unit tests

0.1.5 (2025-06-12)
------------------
* Methods now return only the flags and time column

0.1.4 (2025-06-04)
------------------
* Rename 'rain_col' to 'target_gauge_col'
* fix scipy problem with loading in xarray data ('ScipyArrayWrapper' object has no attribute 'oindex')
* fix 'None > int' problem in method: flag_n_hours_accumulation_based_on_threshold
* remove print statements

0.1.3 (2025-05-29)
------------------
* Add QC21-25
* Add all to IntenseQC framework dictionary

0.1.2 (2025-05-28)
------------------
* Add QC18-QC20

0.1.1 (2025-05-22)
------------------
* *Hotfix* reupload to PyPi

0.1.0 (2025-05-22)
------------------
* First release to PyPi

0.0.9 (2025-05-21)
------------------
* Add methods to run QC frameworks
* Handle np.nans

0.0.8 (2025-05-20)
------------------
* *Hotfix* so nans are ignored when flagging
* also rename accumulation functions & rename n_neighbours_ignored

0.0.7 (2025-05-20)
------------------
* Add QC16-QC17
* Add neighbourhood utility functions
* Add data readers for GPCC and GSDR data from intense

0.0.6 (2025-05-09)
------------------
* Add QC12-QC15
* Add GPCC and GSDR daily fixtures
* Package ETCCDI data with RainfallQC
* Add description of each different type of QC check to header of files
* Add checks for temporal resolution of data inputs
* remove unnecessary files

0.0.5 (2025-04-29)
------------------
* Add QC8-11
* Add hourly and daily fixtures for testing

0.0.4 (2025-04-22)
------------------
* Add QC1-QC7 (gauge_checks) and associated tests
* Fill out some of the data loader utils
* remove tox.ini, flake8, black and conda config
* add conftest.py with data fixtures

0.0.3 (2025-02-13)
------------------
* remove setup py in favour for pyproject.toml only
* set up module

0.0.2 (2025-02-07)
------------------
* Set up environment, pyproject, setup and tox ini files in prep for development
* Write docstrings

0.0.1 (2025-01-16)
------------------
* Create project via cookiecutter-pypackage.
