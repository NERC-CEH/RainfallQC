==========
RainfallQC
==========

.. image:: https://img.shields.io/pypi/v/rainfallqc.svg
        :target: https://pypi.python.org/pypi/rainfallqc

.. image:: https://readthedocs.org/projects/rainfallqc/badge/?version=latest
        :target: https://rainfallqc.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status



Quality control procedure for rainfall data

**WORK IN PROGRESS**

Please email tomkee@ceh.ac.uk if you have any questions.

Project ToDos:

- check https://github.com/nclwater/intense-qc/tree/affinity_indx
- add meaning of flags
- Use timestep str maker to the checks

Proof of concept
----------------
Example showing uses of package:

.. code-block:: python

        # Load three types of QC'ing modules from RainfallQC
        from rainfallqc import gauge_checks, comparison_checks, neighbourhood_checks

        # Run 1 qc method for 1 gauge
        intermittency_flag = gauge_checks.intermittency_check(data)

        # Simple qc with flags returned
        cleaned_raingauge_data, returned_flags = comparison_checks.check_exceedance_of_rainfall_world_record(data, time_res='hourly', return_flags=True)

        # Run neighbour checks
        cleaned_raingauge_data = neighbourhood_checks.daily_neighbours_dry(data, gauge_metadata, return_flags=False)

        # Applying multiple QCs in framework:
        qc_runner = QCRunner()
        qc_runner.set_up_qc(data, "intense_qc_flagging") # will run lots of checks on data and return useful
        qc_runner.run()



Running rulebase:

.. code-block:: python

        formatted_data = rainfallqc.intense_qc_rulebase.apply_rulebase(rainguage_data, gauge_metadata, CDCC_data)
        formatted_data, flags = rainfallqc.intense_qc_rulebase.apply_rulebase(rainguage_data, gauge_metadata, CDCC_data, return_flags=True)


Notes on rulebase application:
* maybe uses dictionaries/json to set rules that can be more easily tweaked.


Also see example Jupyter Notebooks here: https://github.com/Thomasjkeel/RainfallQC-notebooks/tree/main


* Free software: GNU General Public License v3
* Documentation: https://rainfallqc.readthedocs.io.


Features
--------

*TODO*
    - 25 rainfall QC methods

Credits
-------
Based on the IntenseQC: https://github.com/nclwater/intense-qc/tree/master


This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
