# -*- coding: utf-8 -*-
"""
Statistical tests.

Classes and functions ordered alphabetically.

"""

import numpy as np
import polars as pl


def pettitt_test(arr: pl.Series | np.ndarray) -> int | float:
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

    # Compute rank matrix difference in a vectorized way
    for t in range(n):
        left = arr[:t]
        right = arr[t:]
        if left.size > 0 and right.size > 0:
            K[t] = np.sum(np.sign(left[:, None] - right[None, :]))

    tau = int(np.argmax(np.abs(K)))
    U = np.max(np.abs(K))
    p = 2 * np.exp((-6 * U**2) / (n**3 + n**2))
    print(tau, p)
    return tau, p
