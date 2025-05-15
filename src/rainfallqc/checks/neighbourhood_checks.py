# -*- coding: utf-8 -*-
"""
Quality control checks using neighbouring gauges to identify suspicious data.

Neighbourhood checks are QC checks that: "detect abnormalities in a gauges given measurements in neighbouring gauges."

Classes and functions ordered by appearance in IntenseQC framework.
"""


# def wet_neighbour_check(target_gauge_id: str, gauge_network_path: str, time_res: str) -> pl.DataFrame:
#     """
#     Run neighbour check (wet) for hourly or daily data.
#
#     Parameters
#     ----------
#     target_gauge_id :
#     time_res
#
#     Returns
#     -------
#
#     """
#     # data_utils.check_data_is_specific_time_res(data, time_res)
#     return target_gauge_id
