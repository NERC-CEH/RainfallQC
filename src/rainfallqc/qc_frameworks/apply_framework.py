# -*- coding: utf-8 -*-
"""Methods to apply QC qc_frameworks to apply to rainfall data to create quality controlled data."""

import inspect

import polars as pl

from rainfallqc.qc_frameworks import inbuilt_qc_frameworks


def run_qc_framework(
    data: pl.DataFrame, qc_framework: dict | str, qc_methods_to_run: list, kwargs_map: dict
) -> pl.DataFrame:
    """
    Run QC methods from a QC framework.

    Parameters
    ----------
    data :
        Rainfall data to QC.
    qc_framework :
        QC framework to run, can be 'in-built' type i.e. IntenseQC or user defined
    qc_methods_to_run :
        Which methods should be run within that framework i.e. [QC1, QC2]
    kwargs_map :
        Keyword arguments to pass to QC framework methods.

    Returns
    -------
    qc_results :
        Results of running QC.

    """
    qc_results = {}
    shared_kwargs = kwargs_map.get("shared", {})

    if type(qc_framework) is str:
        if qc_framework in inbuilt_qc_frameworks.keys():
            # select in-built qc framework by name
            qc_framework = inbuilt_qc_frameworks[qc_framework]
        else:
            raise KeyError(
                f"QC framework '{qc_framework}' is not known."
                f"In-built QC frameworks include: {inbuilt_qc_frameworks.keys()}."
            )

    for qc_method in qc_methods_to_run:
        qc_func = qc_framework[qc_method]["function"]
        specific_kwargs = kwargs_map.get(qc_method, {})
        combined_kwargs = {**shared_kwargs, **specific_kwargs}

        # Filter kwargs to only those the function accepts
        sig = inspect.signature(qc_func)
        accepted_keys = set(sig.parameters.keys())
        filtered_kwargs = {
            k: v
            for k, v in combined_kwargs.items()
            if k in accepted_keys or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        }

        qc_results[qc_method] = qc_func(data, **filtered_kwargs)

    return qc_results
