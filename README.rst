==========
RainfallQC
==========

.. image:: https://img.shields.io/pypi/v/RainfallQC.svg
        :target: https://pypi.python.org/pypi/RainfallQC

.. image:: https://readthedocs.org/projects/rainfallqc/badge/?version=latest
        :target: https://rainfallqc.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status




Quality control procedure for rainfall data


Proof of concept
----------------
Running quality control measure:

.. code-black:: python

        ## Simple qc not dependent external data or neighbours
        cleaned_raingauge_data = rainfall_qc.accumulation_checks.run(data)
        cleaned_raingauge_data = rainfall_qc.comparison_checks.run(data, comparison_data)

        ## Simple qc with flags returned
        cleaned_raingauge_data, returned_flags = rainfall_qc.comparison_checks.run(data, comparison_data, return_flags=True)

        ## Run neighbour checks
        cleaned_raingauge_data = rainfall_qc.neighbour_checks.run(data, gauge_metadata, return_flags=False)

        ## Applying multiple QCs in framework:
        qc_runner = QCRunner()
        qc_runner.set_up_qc(data, "intense_qc_flagging") # will run lots of checks on data and return useful
        qc_runner.run()



Running rulebase:

.. code-black:: python

        formatted_data = rainfall_qc.intense_qc_rulebase.apply_rulebase(rainguage_data, gauge_metadata, CDCC_data)
        formatted_data, flags = rainfall_qc.intense_qc_rulebase.apply_rulebase(rainguage_data, gauge_metadata, CDCC_data, return_flags=True)


Notes on rulebase application:
* maybe uses dictionaries/json to set rules that can be more easily tweaked.



* Free software: GNU General Public License v3
* Documentation: https://rainfallqc.readthedocs.io.


Features
--------

* TODO:
        - setup.py and setup.cfg
        - bump2version
        - precommit

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
