# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 10:11:35 2019

@author: Roberto Villalobos

Automated checks for high precipitation hours

"""

import numpy as np
import polars as pl

from rainfallqc.core.all_qc_checks import qc_check
from rainfallqc.checks.comparison_checks import flag_exceedance_of_ref_val_as_col
from rainfallqc.checks.timeseries_checks import get_streaks_above_threshold, get_streaks_of_repeated_values, flag_streaks_exceeding_wet_day_rainfall_threshold
from rainfallqc.utils import data_utils


# OG imports
# import intense_Roberto_03 as ex
# # import intense_.intense_CW as ex
import scipy.stats as stats2
import statistics as stats
import pandas as pd
import zipfile
import math
import glob

UK_1hr_record = 92  # mm
UK_24hr_record = 341.4  # mm


@qc_check("check_exceedance_of_UK_1hr_record", require_non_negative=True)
def check_exceedance_of_UK_1hr_record(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Check exceedance of UK 1-hour record.

    This is QCX from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of UK 1hr Record

    """
    return get_subhourly_exceedance_of_given_record(
        data=data,
        target_gauge_col=target_gauge_col,
        record_rainfall_amount=UK_1hr_record,
        flag_col_name="UK_1hr_record_check",
    )


@qc_check("check_exceedance_of_UK_24hr_record", require_non_negative=True)
def check_exceedance_of_UK_24hr_record(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Check exceedance of UK 24-hour record.

    This is QCX from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of UK 24hr Record
    """
    return get_subhourly_exceedance_of_given_record(
        data=data,
        target_gauge_col=target_gauge_col,
        record_rainfall_amount=UK_24hr_record,
        flag_col_name="UK_24hr_record_check",
    )


@qc_check("check_daily_exceedance_of_UK_24hr_record", require_non_negative=True)
def check_daily_exceedance_of_UK_24hr_record(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Check exceedance of UK 24-hour record when aggregating to 24 hours.

    This is QCX from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of UK 24hr rolling record
    """
    # 1. Check data is sub-hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["1m", "15m"])
    time_step = data_utils.get_data_timestep_as_str(data)

    # 2. Aggregate data to daily
    original_data = data.clone()
    daily_data = data.group_by_dynamic("time", every="1d").agg(pl.col(target_gauge_col).sum())

    if time_step == "15m":
        time_step_per_day = 96  # 96x 15-min periods per day
    if time_step == "1m":
        time_step_per_day = 1440  # 1440 x 1-min periods per day

    # 3. Flag exceedance of world record value
    data_w_flags = flag_exceedance_of_ref_val_as_col(
        daily_data, target_gauge_col, ref_val=UK_24hr_record, new_col_name="UK_24hr_rolling_record_check"
    )

    # 4. Disaggregate data back to original resolution
    data_w_flags_disag = data_utils.downsample_and_fill_columns(
        high_res_data=original_data,
        low_res_data=data_w_flags,
        data_cols="UK_24hr_rolling_record_check",
        fill_limit=time_step_per_day - 1,
        fill_method="backward",
    )
    return data_w_flags_disag.select(["time", "UK_24hr_rolling_record_check"])


@qc_check("check_streaks_20mm", require_non_negative=True)
def check_streaks_20mm(data: pl.DataFrame, target_gauge_col: str, flag_col_name: str="streak_flag_20mm") -> pl.DataFrame:
    """
    Check streaks with fixed minimum hourly threshold of 20 mm.

    This is QCX from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data
    flag_col_name :
        Name for flag column (default: 'streak_flag_20mm')

    Returns
    -------
    data_w_flags:
        Rainfall data with flags dennotting period of repeating streak above 20mm
    """
    # 1. Check data is sub-hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["1m", "15m"])
    time_step = data_utils.get_data_timestep_as_str(data)

    # 2. Aggregate data to hourly
    original_data = data.clone()
    hourly_data = data.group_by_dynamic("time", every="1h").agg(pl.col(target_gauge_col).sum())

    if time_step == "15m":
        time_step_per_hour = 4  # 4x 15-min periods per hour
    if time_step == "1m":
        time_step_per_hour = 60  # 60 x 1-min periods per hour

    # 3. Get streaks in data
    streak_data = get_streaks_of_repeated_values(hourly_data, target_gauge_col)

    # 4. Flag streaks of 2 or more repeated large values exceeding 20 mm
    streak_data_w_flags = flag_streaks_exceeding_wet_day_rainfall_threshold(
        streak_data, target_gauge_col, min_streak_length=2, accumulation_threshold=20, flag_col_name=flag_col_name
    )

    # 5. Disaggregate data back to original resolution
    data_w_flags_disag = data_utils.downsample_and_fill_columns(
        high_res_data=original_data,
        low_res_data=streak_data_w_flags,
        data_cols=flag_col_name,
        fill_limit=time_step_per_hour - 1,
        fill_method="backward",
    )
    return data_w_flags_disag.select(["time", flag_col_name])


@qc_check("check_freq_is_subhourly", require_non_negative=True)
def check_freq_is_subhourly(data: pl.DataFrame, target_gauge_col: str) -> pl.DataFrame:
    """
    Checks frequency and resolution of data is subhourly.
    Specifically, it will check monthly periods with frequencies >= 30 minutes, or where the resolution is
    1 mm (usually an indicator of tip counts not tip amounts in the data), and replace them with NAN.

    Flags:
    1 == when month has suspect frequency or resolution

    This is freqResChecker (Function 1 of the SHQC process) from the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data

    Returns
    -------

    """
    # 1. Get all unique timestep in the data
    unique_timesteps = data_utils.get_data_timesteps(data)
    
    # 2. If there are more than 1 time-step then apply check
    if len(unique_timesteps) > 1:
        # 3. Check frequency of data; I am uncertain of this, because what if very few values in month
        data_freqs = data.with_columns([pl.col("time").diff().alias("time_step")])
        most_common_freq_by_mo = data_freqs.group_by_dynamic("time", every="1mo").agg(pl.col("time_step").mode().first().alias("most_common_freq"))

        # 4. Check resolution of the data (checking mode of rainfall); I am uncertain of this, because what if very few values in month
        most_common_res_by_mo = data.group_by_dynamic("time", every="1mo").agg(pl.col(target_gauge_col).mode().first().alias("most_common_res"))
        
        # 5. Combine
        freq_and_res = pl.concat([most_common_freq_by_mo, most_common_res_by_mo])

        # 6. Flag months where freq >= 30 mins or and resolution >=1.0
        freq_and_res_w_flags = freq_and_res.with_columns(
            pl.when(
                (pl.col("most_common_freq") >= datetime.timedelta(minutes=30)) |
                (pl.col("most_common_res") >= 1.0)
                )
            .then(1)
            .otherwise(0)
            .alias("freq_res_flag")
        )

        # 7. Disaggregate data back to original resolution
        data_w_flags_disag = data_utils.downsample_and_fill_columns(
            high_res_data=original_data,
            low_res_data=freq_and_res_w_flags,
            data_cols="freq_res_flag",
            fill_limit=None,
            fill_method="backward",
        )
    else:
        # Check data has consistent resolution that is 1-min or 15-min 
        data_utils.check_data_is_specific_time_res(data, time_res=["1m", "15m"])
        data_w_flags_disag = data.with_columns(freq_res_flag=0)
    return data_w_flags_disag


def get_subhourly_exceedance_of_given_record(
    data: pl.DataFrame, target_gauge_col: str, record_rainfall_amount: [int | float], flag_col_name: str
) -> pl.DataFrame:
    """
    Check sub-houlry exceedance of given record.

    Used in QCX and QCX of the SubHourlyQC framework.

    Parameters
    ----------
    data :
        Rainfall data (15-min or 1-min)
    target_gauge_col :
        Column with rainfall data
    record_rainfall_amount :
        given record rainfall amount
    flag_col_name :
        Name for flag column

    Returns
    -------
    data_w_flags:
        Rainfall data with exceedance of given rainfall record (see `flag_exceedance_of_ref_val_as_col` function)
    """
    # 1. Check data is sub-hourly
    data_utils.check_data_is_specific_time_res(data, time_res=["1m", "15m"])
    time_step = data_utils.get_data_timestep_as_str(data)

    # 2. Aggregate data to hourly
    original_data = data.clone()
    hourly_data = data.group_by_dynamic("time", every="1h").agg(pl.col(target_gauge_col).sum())

    if time_step == "15m":
        time_step_per_hour = 4  # 4x 15-min periods per hour
    if time_step == "1m":
        time_step_per_hour = 60  # 60 x 1-min periods per hour

    # 3. Flag exceedance of world record value
    data_w_flags = flag_exceedance_of_ref_val_as_col(
        hourly_data, target_gauge_col, ref_val=record_rainfall_amount, new_col_name=flag_col_name
    )

    # 4. Disaggregate data back to original resolution
    data_w_flags_disag = data_utils.downsample_and_fill_columns(
        high_res_data=original_data,
        low_res_data=data_w_flags,
        data_cols=flag_col_name,
        fill_limit=time_step_per_hour - 1,
        fill_method="backward",
    )
    return data_w_flags_disag.select(["time", flag_col_name])


def freqResChecker(input_file_zip_pair, outdir):  # (file, outdir):
    """
    Function 1 of the SHQC process

    Reads in subhourly data and examines it's frequency and resolution
    Monthly periods with frequencies >= 30 minutes, or where the resolution is
    1 mm (usually an indicator of tip counts not tip amounts in the data), are
    replaced with NAN.

    An output file is generated to keep track of changes.
    """

    # Reading from zipfile
    input_file = input_file_zip_pair[0]
    zip_folder = input_file_zip_pair[1]
    zf_in = zipfile.ZipFile(zip_folder, "r")
    d = zf_in.open(input_file, mode="r")

    try:
        data = pd.read_csv(d)

        # Get datetime index
        data.index = pd.DatetimeIndex(data["ob_time"])
        # Get metadata in file
        station_id = data["id"][1]
        station_name = data["src_id"][1]
    except:
        print("Could not read data for " + input_file)

    d.close()
    zf_in.close()

    # read station data
    """ Old read method
    try:
        data = pd.read_csv(file)
        
        # Get datetime index
        data.index = pd.DatetimeIndex(data['ob_time'])
        # Get metadata in file
        station_id = data['id'][1]
        station_name = data['src_id'][1]
    except:
        print('Could not read data for '+file)
    """

    out = pd.DataFrame(
        columns=["Station_id", "Station_name", "Removed", "N_months", "obs_rem", "pobs_rem", "mm_rem", "pmm_rem"]
    )

    og_data = data.copy()
    # Drop un-needed columns
    data = pd.DataFrame(data["accum"])
    data = data.dropna()

    # Calculate time difference vector to identify if data is 15-min or other type
    tdifs = data.index.to_series().diff() / np.timedelta64(1, "s")
    tdifs = tdifs.resample("M").apply(lambda x: stats2.mode(x)[0])

    # Calculate data resolution, by month
    res = data.resample("M").apply(lambda x: stats2.mode(x)[0])
    # Concatenate checks
    checks = pd.concat([tdifs, res], axis=1)

    # If time resolution is >= 30mins or if resolution == 0.5, flag
    checks["remove"] = np.where(
        (checks["ob_time"] >= 1800) | ((checks["ob_time"] >= 1800) & (checks["accum"] == 0.5)) | (checks["accum"] >= 1),
        1,
        0,
    )

    # If data has been flagged, remove and write
    if max(checks["remove"]) > 0:
        # Create mask to remove data
        months = checks[checks["remove"] == 1].dropna().index
        mask = months.to_period("M")

        # Fill erroneous periods with 'NA' values and write
        clean_data = og_data.copy()
        clean_data["accum"] = np.where(clean_data.index.to_period("M").isin(mask), np.nan, clean_data["accum"])
        clean_data.to_csv(outdir + "/" + station_id + ".txt", index=False)

        # Calculate data removed
        og_mis = og_data.accum.isnull().sum()
        cl_mis = clean_data.accum.isnull().sum()
        H_rem = cl_mis - og_mis
        ph_rem = H_rem * 100 / og_data.shape[0]  # percentage of data entries replaced with NAN

        # Calculate rainfall removed
        r_rem = og_data.accum.sum() - clean_data.accum.sum()
        pr_rem = r_rem * 100 / og_data.accum.sum()

        rem = "True"
        n_mon = checks[checks["remove"] > 0].shape[0]

    # Otherwise write out un-changed data
    else:
        og_data.to_csv(outdir + "/" + station_id + ".txt", index=False)
        rem = "False"
        n_mon = 0
        H_rem = 0
        ph_rem = 0
        r_rem = 0
        pr_rem = 0

    out = out.append(
        {
            "Station_id": station_id,
            "Station_name": station_name,
            "Removed": rem,
            "N_months": n_mon,
            "obs_rem": H_rem,
            "pobs_rem": ph_rem,
            "mm_rem": r_rem,
            "pmm_rem": pr_rem,
        },
        ignore_index=True,
    )

    return out


def subH_checkr(file, metadir, thresholds60, thresholds15, thresholds1, outdir):
    """
    Function 2 of the SHQC process

    Here a threshold-based approach is used to examine rainfall data at a sub-hourly
    resolution to identify and discard suspicious periods. Hourly, 15-min and 1-min
    thresholds are used, as well as a fast-tipping frequency check. Suspicious 3-hr
    periods are replaced with NAN in the subhourly data.

    A log file is prepared, and every removed interval is registered.
    """

    # Read station data
    try:
        data = pd.read_csv(file)

        # Get datetime index
        data.index = pd.DatetimeIndex(data["ob_time"])
        # Get metadata in file
        station_id = data["id"][1]
        station_name = data["src_id"][1]
    except:
        print("Could not read data for " + file)

    # Additional metadata
    try:
        its = ex.readIntense(metadir + station_id + ".txt", only_metadata=False)
    except:
        print("Could not read metadata for " + file)

    # Copy original data, resample for hourly search
    og_data = data.copy()
    hourly = data["accum"].resample("H", closed="right", label="right").sum()

    # Check for suspect hours using monthly thresholds
    suspect = hourly.loc[
        ((hourly.index.month == 1) & (hourly >= thresholds60[1]))  # or
        | ((hourly.index.month == 2) & (hourly >= thresholds60[2]))
        | ((hourly.index.month == 3) & (hourly >= thresholds60[3]))
        | ((hourly.index.month == 4) & (hourly >= thresholds60[4]))
        | ((hourly.index.month == 5) & (hourly >= thresholds60[5]))
        | ((hourly.index.month == 6) & (hourly >= thresholds60[6]))
        | ((hourly.index.month == 7) & (hourly >= thresholds60[7]))
        | ((hourly.index.month == 8) & (hourly >= thresholds60[8]))
        | ((hourly.index.month == 9) & (hourly >= thresholds60[9]))
        | ((hourly.index.month == 10) & (hourly >= thresholds60[10]))
        | ((hourly.index.month == 11) & (hourly >= thresholds60[11]))
        | ((hourly.index.month == 12) & (hourly >= thresholds60[12]))
    ]

    # The checks only run if we have big hourly values
    if len(suspect) > 0:
        output = pd.DataFrame(
            columns=[
                "Station_ID",
                "Station_Name",
                "Latitude",
                "Longitude",
                "datetime",
                "magnitude",
                "timestep",
                "QC_status",
                "removed",
                "Fast-tips",
                "Large 15s",
                "Large minutes",
            ]
        )

        #######################################################################

        # Iterate over suspect hours
        for hour in suspect.index:
            # Reset output parameters
            mag = hourly.loc[hour]
            fTips = "False"
            removed = "False"

            # Get month value
            month = hour.month

            # Extract 3 hour window and calculate time differential between tips
            # Extraction is made from un-touched data so deletions won't affect event extraction
            event = og_data[
                (hour - pd.DateOffset(hours=1)).strftime("%Y-%m-%d %H") : (hour + pd.DateOffset(hours=1)).strftime(
                    "%Y-%m-%d %H"
                )
            ].copy()

            # Get QC status of event:
            x = int(stats2.mode(event["q"])[0])
            if x == 1:
                event_q = "S"
            elif x == 2:
                event_q = "U"
            elif x == 3:
                event_q = "M"
            else:
                event_q = ""

            event = event["accum"]
            # event['Time stamp'] = pd.to_datetime(event['Time stamp'],format = '%d/%m/%Y %H:%M:%S')
            tdif = event.index.to_series().diff() / np.timedelta64(1, "s")
            tdif = tdif[~tdif.isna()]
            ###################################################################

            freq = None
            if event.shape[0] > 3:
                freq = pd.infer_freq(event.index)
                try:
                    if (freq == None) & (int(stats2.mode(tdif)[0]) == 900):
                        freq = "15T"
                    # elif(freq == None )& (stats.mode(tdif).total_seconds() == 1800):
                    #    freq = '30T'
                    # elif(freq == None )& (stats.mode(tdif).total_seconds() == 3600):
                    #    freq = '60T'
                except:
                    freq = None
            elif event.shape[0] == 1:
                freq = "15T"
            elif event.shape[0] == 2:  # likely to be a single large 15-min value and a zero
                if (int(math.ceil(stats2.mode(tdif)[0] / 100.0)) * 100) >= 900:
                    freq = "15T"
            elif event.shape[0] == 3:
                if round((tdif.sum() / 2)) >= 900:
                    freq = "15T"

            # Add catch for hourly data -> interrupt check if hourly or semi-hourly
            # Minute data rules ###############################################
            if freq != "15T":  # If tip times are available:
                timestep = "1m"
                try:
                    intertip = int(stats2.mode(tdif)[0])
                except:
                    intertip = round((tdif.sum() / len(event)))

                if intertip < 2:  # If most inter-tip times are smaller than 2 seconds, reject event
                    fTips = "True"
                    removed = "True"

                    Tots_m = np.nan
                    Tots_15 = np.nan
                    # remove data
                    data.loc[
                        (hour - pd.DateOffset(hours=1)).strftime("%Y-%m-%d %H") : (
                            hour + pd.DateOffset(hours=1)
                        ).strftime("%Y-%m-%d %H"),
                        "accum",
                    ] = np.nan
                else:
                    event_min = event.resample("1min").sum()
                    event_15 = event.resample("15min").sum()

                    # Count large minutes and large 15-min values
                    Tots_m = len(event_min[event_min > thresholds1[month]])
                    Tots_15 = len(event_15[event_15 > thresholds15[month]])

                    if (Tots_m != 0) | (Tots_15 != 0):  # Winter, more conservative rule, adopted for all months
                        # if (sm!=0)|((sm!=0)&(s15!=0)): # alternative summer rule
                        removed = "True"
                        data.loc[
                            (hour - pd.DateOffset(hours=1)).strftime("%Y-%m-%d %H") : (
                                hour + pd.DateOffset(hours=1)
                            ).strftime("%Y-%m-%d %H"),
                            "accum",
                        ] = np.nan

            # 15 minute total rules ###########################################
            # Winter
            elif month in [1, 2, 3, 4, 11, 12]:  # If data is 15-minute totals
                timestep = "15m"
                event_15 = event.resample("15min").sum()
                Tots_15 = len(event_15[event_15 > thresholds15[month]])
                Tots_m = np.nan

                if Tots_15 != 0:
                    removed = "True"
                    data.loc[
                        (hour - pd.DateOffset(hours=1)).strftime("%Y-%m-%d %H") : (
                            hour + pd.DateOffset(hours=1)
                        ).strftime("%Y-%m-%d %H"),
                        "accum",
                    ] = np.nan
            # Summer
            else:  # If data is 15-minute totals
                timestep = "15m"
                event_15 = event.resample("15min").sum()
                Tots_15 = len(event_15[event_15 > thresholds15[month]])
                Tots_m = np.nan

                # Average event intensity for wet 15-minute intervals
                avg_15 = sum(event_15[event_15 > 1]) / len(event_15[event_15 > 1])
                if (Tots_15 == 1) & (avg_15 > thresholds15[month]):
                    removed = "True"
                    data.loc[
                        (hour - pd.DateOffset(hours=1)).strftime("%Y-%m-%d %H") : (
                            hour + pd.DateOffset(hours=1)
                        ).strftime("%Y-%m-%d %H"),
                        "accum",
                    ] = np.nan
                elif Tots_15 > 1:
                    removed = "True"
                    data.loc[
                        (hour - pd.DateOffset(hours=1)).strftime("%Y-%m-%d %H") : (
                            hour + pd.DateOffset(hours=1)
                        ).strftime("%Y-%m-%d %H"),
                        "accum",
                    ] = np.nan

            # Append data to output dataframe #################################
            output = output.append(
                {
                    "Station_ID": station_id,
                    "Station_Name": station_name,
                    "Latitude": its.latitude,
                    "Longitude": its.longitude,
                    "datetime": hour,
                    "magnitude": mag,
                    "timestep": timestep,
                    "QC_status": event_q,
                    "removed": removed,
                    "Fast-tips": fTips,
                    "Large 15s": Tots_15,
                    "Large minutes": Tots_m,
                },
                ignore_index=True,
                sort=True,
            )

            # Order columns
            output = output[
                [
                    "Station_ID",
                    "Station_Name",
                    "Latitude",
                    "Longitude",
                    "datetime",
                    "magnitude",
                    "timestep",
                    "QC_status",
                    "removed",
                    "Fast-tips",
                    "Large 15s",
                    "Large minutes",
                ]
            ]

        # Output, still inside if suspect > 0
        data.to_csv(outdir + "/" + station_id + ".txt", index=False)

        return output
