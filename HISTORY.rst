=======
History
=======

0.1.6 (2025-06-13)
------------------
* rename dry and wet spell flags so they include time resolution
* fix list comprehension so it iterates over copy of neighbouring cols
* rename QC11 from 'check_annual_exceedance_etccdi_rx1day' to 'check_hourly_exceedance_etccdi_rx1day'
* Add hourly qc framework check
* Add 15min support for QC11 and QC14
* Remove daily support for QC13 and QC15 (only works on hourly)

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
* Add data readers for GPCC and GDSR data from intense

0.0.6 (2025-05-09)
------------------
* Add QC12-QC15
* Add GPCC and GDSR daily fixtures
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
