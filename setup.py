#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""

from setuptools import find_packages, setup

NAME = "rainfall_qc"
DESCRIPTION = "Quality control procedure for rainfall data."
URL = "https://github.com/Thomasjkeel/jsmetrics"
AUTHOR = "Thomas Keel"
AUTHOR_EMAIL = "thomasjames.keel@gmail.com"
REQUIRES_PYTHON = ">=3.10.0"
VERSION = "0.0.2-alpha"
LICENSE = "GNU License"

KEYWORDS = "jet-stream climate metrics algorithms xarray"

with open("README.rst", encoding="utf-8") as file:
    readme = file.read()

with open("HISTORY.rst", encoding="utf-8") as history_file:
    history = history_file.read()

requirements = [
    "numpy",
]

dev_requirements = []
with open("requirements_dev.txt", "r", encoding="utf8") as dev:
    for dependency in dev.readlines():
        dev_requirements.append(dependency)

setup(
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Environmental Science",
        "Topic :: Scientific/Engineering :: Hydrology",
    ],
    description=DESCRIPTION,
    python_requires=REQUIRES_PYTHON,
    install_requires=requirements,
    license=LICENSE,
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/x-rst",
    include_package_data=True,
    keywords=KEYWORDS,
    name=NAME,
    packages=find_packages(),
    tests_require=["pytest", "parameterized"],
    extras_require={
        "dev": dev_requirements,
    },
    url=URL,
    version=VERSION,
    zip_safe=False,
)
