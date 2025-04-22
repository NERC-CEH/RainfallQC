# -*- coding: utf-8 -*-
"""
Statistical tests.

Classes and functions ordered alphabetically.

"""

import numpy as np
import polars as pl


def pettitt_test(arr: pl.Series | np.ndarray) -> (float, float):
    """
    Pettitt test calculated following Pettitt (1979): https://www.jstor.org/stable/2346729?seq=4#metadata_info_tab_contents.

    TAKEN FROM: https://stackoverflow.com/questions/58537876/how-to-run-standard-normal-homogeneity-test-for-a-time-series-data.

    Parameters
    ----------
    arr :
        Array with data to be tested.

    Returns
    -------
    tau :
        tau for test statistic.
    p  :
        p-value for test statistic.

    """
    len_arr = len(arr)
    second_arr = []
    for t in range(len_arr):  # t is used to split arr into two subseries
        arr_stack = np.zeros((t, len(arr[t:]) + 1), dtype=int)
        arr_stack[:, 0] = arr[:t]  # first column is each element of the first subseries
        arr_stack[:, 1:] = arr[t:]  # all rows after the first element are the second subseries
        second_arr.append(
            np.sign(arr_stack[:, 0] - arr_stack[:, 1:].transpose()).sum()
        )  # sign test between each element of the first subseries and all elements of the second subseries, summed.

    tau = np.argmax(np.abs(second_arr))  # location of change (first data point of second sub-series)
    max_second_arr = np.max(np.abs(second_arr))
    p = 2 * np.exp(-6 * max_second_arr**2 / (len_arr**3 + len_arr**2))
    return tau, p
