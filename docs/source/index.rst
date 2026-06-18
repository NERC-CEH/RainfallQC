.. _index:

:layout: landing


.. container::
    :name: home-head

    .. image:: /_static/rainfallqc_logo_grey.png
        :alt: RainfallQC
        :width: 350
    

    .. container::

        .. raw:: html

            <h1>RainfallQC</h1>
            <h2>Run quality control on timeseries rainfall data</h2>

        .. container:: badges
           :name: badges

           .. image:: https://img.shields.io/badge/Humans-999999?style=flat&logo=Made by&label=Made By&labelColor=2BD962
              :alt: Made by humans

           .. image:: https://badges.frapsoft.com/os/v1/open-source.svg?v=103
              :alt: Open Source
              
           .. image:: https://img.shields.io/badge/License-GPLv3-blue.svg
              :alt: GPL v3 License

           .. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
              :alt: UV

           .. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
              :alt: Ruff Version



.. rst-class:: lead




.. container:: buttons

    `Docs <installation.html>`_
    `Usage <usage.html>`_
    `Codeberg <https://codeberg.org/CEH-HOTDOG/RainfallQC>`_
    `GitHub <https://github.com/NERC-CEH/RainfallQC>`_

.. grid:: 1 1 2 3
    :class-row: surface
    :padding: 0
    :gutter: 2

    .. grid-item-card:: :octicon:`repo-template` Getting Started
      :link: quickstart.html

      A collection of tutorials for setting up and using RainfallQC. 

    .. grid-item-card:: :octicon:`alert` Issues
      :link: https://github.com/NERC-CEH/RainfallQC/issues

      Use this link you need to report any bugs or request new features.

    .. grid-item-card:: :octicon:`people` More FDRI projects
      :link: https://fdri.org.uk/

      Learn more about the UK's Floods & Droughts Research Infrastructure Project.


What is RainfallQC?
===================

RainfallQC is a package for running quality control (QC) on rain gauge data in a flexible, user-driven way.
At its core, the package offers:  

- 27 QC checks for rainfall data as of v0.2.5 (25 from `IntenseQC <https://www.sciencedirect.com/science/article/pii/S1364815221002127>`_ and 2 from `pyPWSQC <https://doi.org/10.5281/zenodo.4501919>`_)
- Customizable parameters – adjust thresholds, streak or accumulation lengths, and distances to neighboring gauges
- A modular QC framework – users can select which QC methods to apply, and configure them according to their project’s requirements

It is designed to help everyone, from individual researchers to industrial-scale users, apply standardised QC checks to rainfall observations. 
RainfallQC is built on top of `Polars <https://docs.pola.rs/>`_, which handles efficient DataFrame processes (like Pandas, but quicker).

.. container:: image-row

   .. container:: image-item

      .. figure:: _static/ukceh_logo.png
         :alt: UKCEH
         :height: 100px
         :target: https://www.ceh.ac.uk

   .. container:: image-item

      .. figure:: _static/fdri_logo.png
         :alt: FDRI
         :height: 100px
         :target: https://fdri.org.uk


Community
=========

Developed at `UKCEH <https://www.ceh.ac.uk/>`_, welcoming community engagement and contributions.

License
=======

This project is licensed under the `GNU GPL v3.0 <https://github.com/NERC-CEH/RainfallQC/blob/main/LICENSE>`_.


.. toctree::
    :hidden:
    :maxdepth: 2
    :caption: Getting started
    
    intro
    installation
    quickstart

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: User Guide
   :numbered:

   tutorials
   api

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: Other

    contributing
    credits
    changelog


.. Current version: |release|