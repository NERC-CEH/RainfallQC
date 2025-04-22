# -*- coding: utf-8 -*-
"""
Statistical tests.

Classes and functions ordered alphabetically.

"""

from typing import Tuple, Union

import numpy as np
import polars as pl


def pettitt_test(arr: Union[pl.Series, np.ndarray]) -> Tuple[float, float]:
    """
    Pettitt test for detecting a change point in a time series.

    Calculated following Pettitt (1979): https://www.jstor.org/stable/2346729?seq=4#metadata_info_tab_contents.

    TAKEN FROM: https://stackoverflow.com/questions/58537876/how-to-run-standard-normal-homogeneity-test-for-a-time-series-data.

    Parameters
    ----------
    arr : pl.Series or np.ndarray
        The input time series data.

    Returns
    -------
    tau : int
        Index of the change point (first point of the second segment).
    p : float
        p-value for the test statistic.

    """
    if isinstance(arr, pl.Series):
        arr = arr.to_numpy()

    n = len(arr)
    K = np.zeros(n)

    for t in range(n):
        s = 0
        for i in range(t):
            for j in range(t, n):
                s += np.sign(arr[i] - arr[j])
        K[t] = s

    tau = int(np.argmax(np.abs(K)))
    U = np.max(np.abs(K))
    p = 2 * np.exp((-6 * U**2) / (n**3 + n**2))

    return tau, p
