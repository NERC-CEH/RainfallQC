import polars as pl

TIME_STEP_CONVERSION = {"15m": "15m", "1h": "hourly"}


def apply_conditional_rule(data: pl.DataFrame, condition: pl.Expr, val_col: str) -> pl.DataFrame:
    """
    Apply a conditional rule.

    Parameters
    ----------
    data:
        Data to check condition from
    condition:
        Condition to check in given val_col
    val_col:
        Column with data to check against condition

    Returns
    -------
    data:
        Mask of column based on condition
    """
    return data.with_columns(pl.when(condition).then(None).otherwise(pl.col(val_col)).alias(val_col))


def apply_rowbased_rulebase_to_one_station(
    flags_by_row: pl.DataFrame,
    rules_to_apply: dict,
    station_id: str,
    time_step: str,
    return_counts: bool = True,
) -> pl.DataFrame | tuple[pl.DataFrame, dict]:
    """
    Apply rulebase to a single gauge worth of data.

    Note: will overlap the count of rules removed

    Parameters
    ----------
    flags_by_row:
        Data with flags by row
    rules_to_apply:
        Conditions to remove data from data
    station_id:
        Gauge ID
    time_step:
        The time resolution of the data
    return_counts:
        Whether you should return counts of removed rows (default: True)

    Returns
    -------
    rule_removed_rows:
        Input data with rows removed based on rulebase
    num_rows_removed_by_rule:
        Returned if return counts == True
    """
    num_rows_removed_by_rule = {}
    num_rows_removed_by_rule["station_id"] = station_id
    rule_removed_rows = flags_by_row
    for rule_id, rule in rules_to_apply.items():
        if callable(rule):
            rule = rule(station_id, TIME_STEP_CONVERSION[time_step])
        rule_removed_rows = apply_conditional_rule(rule_removed_rows, rule, station_id)
        num_rows_removed_by_rule[rule_id] = flags_by_row.filter(rule).height
    if return_counts:
        return rule_removed_rows, num_rows_removed_by_rule
    return rule_removed_rows


def apply_r1(
    flags_by_row: pl.DataFrame, station_id: str, qc2_list: list, return_count=True
) -> pl.DataFrame | tuple[pl.DataFrame, int]:
    """
    Apply rule 1 from the IntenseQC framework.

    Needs to be applied last, as it can remove entire years

    Parameters
    ----------
    flags_by_row:
        Data with flags by row
    station_id:
        Gauge ID
    qc2_list:
        The time resolution of the data
    return_counts:
        Whether you should return counts of removed rows (default: True)

    Returns:
    --------
    rule_removed_rows:
        Input data with rows removed based on rulebase
    num_rows_removed_by_rule:
        Returned if return counts == True

    """
    num_rows_removed = 0
    rule_removed_rows = flags_by_row

    for year in qc2_list:
        num_rows_removed += rule_removed_rows.filter(pl.col("time").dt.year() == year).height
        rule_removed_rows = apply_conditional_rule(rule_removed_rows, (pl.col("time").dt.year() == year), station_id)
    if return_count:
        return rule_removed_rows, num_rows_removed
    return rule_removed_rows


def get_r7(station_id: str, time_step: str) -> pl.Expr:
    """
    Apply rule 7 from the IntenseQC framework.

    Parameters
    ----------
    station_id:
        Gauge ID
    time_step:
        The time resolution of the data

    Returns
    -------
    condition:
        Expression for subsetting data

    """
    return (pl.col(f"wet_spell_flag_{TIME_STEP_CONVERSION[time_step]}") == 3) & (
        pl.col(station_id) > 2 * pl.col(station_id).filter(pl.col(station_id) > 0).mean()
    )


def get_rulebase_conditions(time_step: str) -> dict:
    """
    Get all rulebase conditions.

    Parameters
    ----------
    time_step:
        The time resolution of the data

    Returns
    -------
    dict:
        Rulebase expressions

    """
    return {
        "R2": pl.col("daily_accumulation") == 1,
        "R3": pl.col("monthly_accumulation") == 1,
        "R4": (pl.col("streak_flag1").fill_nan(0) > 0)
        | (pl.col("streak_flag3").fill_nan(0) > 0)
        | (pl.col("streak_flag4").fill_nan(0) > 0)
        | (pl.col("streak_flag5").fill_nan(0) > 0),
        "R5": pl.col("world_record_check").fill_nan(0) > 0,
        "R6": pl.col("rx1day_check").fill_nan(0) > 0,
        "R7": get_r7,  # needs to be run first, as it checks the rainfall column
        "R9": (pl.col(f"dry_spell_flag_{TIME_STEP_CONVERSION[time_step]}") == 3)
        & (pl.col("dry_spell_flag").fill_nan(0.0) > 0),
        "R11": pl.col("majority_monthly_flag").fill_nan(0) >= 4,
    }


def get_rulebase_conditions_w_subhourlyqc(time_step: str) -> dict:
    """
    Get all rulebase conditions.

    Parameters
    ----------
    time_step:
        The time resolution of the data

    Returns
    -------
    dict:
        Rulebase expressions

    """
    return {
        "R2": pl.col("daily_accumulation") == 1,
        "R3": pl.col("monthly_accumulation") == 1,
        "R4": (pl.col("streak_flag1").fill_nan(0) > 0)
        | (pl.col("streak_flag3").fill_nan(0) > 0)
        | (pl.col("streak_flag4").fill_nan(0) > 0)
        | (pl.col("streak_flag5").fill_nan(0) > 0),
        "R5": pl.col("world_record_check").fill_nan(0) > 0,
        "R6": pl.col("rx1day_check").fill_nan(0) > 0,
        "R7": get_r7,  # needs to be run first, as it checks the rainfall column
        "R9": (pl.col(f"dry_spell_flag_{TIME_STEP_CONVERSION[time_step]}") == 3)
        & (pl.col("dry_spell_flag").fill_nan(0.0) > 0),
        "R11": pl.col("majority_monthly_flag").fill_nan(0) >= 4,
        "SHQC_R1": pl.col("UK_1hr_record_flag").fill_nan(0.0) > 0,
        "SHQC_R2": pl.col("UK_24hr_record_flag").fill_nan(0.0) > 0,
        "SHQC_R3": pl.col("UK_24hr_rolling_record_flag").fill_nan(0.0) > 0,
        "SHQC_R4": pl.col("streak_flag_20mm").fill_nan(0.0) > 0,
        "SHQC_R5": pl.col("freq_res_flag").fill_nan(0.0) > 0,
        "SHQC_R6": (pl.col("month_15min_threshold_flag").fill_nan(0.0) > 0)
        | (pl.col("month_1hr_threshold_flag").fill_nan(0.0) > 0),
    }


def apply_intenseQC_rulebase(
    all_flags: dict, station_id: str, time_step: str, return_counts=True
) -> pl.DataFrame | tuple[pl.DataFrame, dict]:
    """
    Apply the IntenseQC rulebase (11 rules).

    Parameters
    ----------
    all_flags:
        Data with flags by row
    station_id:
        Gauge ID
    qc2_list:
        The time resolution of the data
    return_counts:
        Whether you should return counts of removed rows (default: True)

    Returns:
    --------
    rule_removed_rows:
        Input data with rows removed based on rulebase
    num_rows_removed_by_rule:
        Returned if return counts == True

    """
    # apply R2-R11 (the row-wise rules)
    rule_removed_rows, n_rows_removed = apply_rowbased_rulebase_to_one_station(
        all_flags["all_flags_by_row"],
        get_rulebase_conditions(time_step),
        station_id,
        time_step=time_step,
        return_counts=return_counts,
    )

    # apply R1, which removes whole years
    # has to be run after R7 which updates the data
    rule_removed_rows, n_qc2_rows_removed = apply_r1(
        rule_removed_rows, station_id, all_flags["QC2"], return_count=return_counts
    )

    # update n_rows_removed
    n_rows_removed["R1"] = n_qc2_rows_removed

    if return_counts:
        return rule_removed_rows, n_rows_removed
    return rule_removed_rows


def apply_intenseQC_w_subhourlyQC_rulebase(
    all_flags: dict, station_id: str, time_step: str, return_counts=True
) -> pl.DataFrame | tuple[pl.DataFrame, dict]:
    """
    Apply the IntenseQC rulebase (11 rules) and 6 rules from SubHourlyQC.

    Parameters
    ----------
    all_flags:
        Data with flags by row
    station_id:
        Gauge ID
    qc2_list:
        The time resolution of the data
    return_counts:
        Whether you should return counts of removed rows (default: True)

    Returns:
    --------
    rule_removed_rows:
        Input data with rows removed based on rulebase
    num_rows_removed_by_rule:
        Returned if return counts == True

    """
    # apply R2-R11 (the row-wise rules)
    rule_removed_rows, n_rows_removed = apply_rowbased_rulebase_to_one_station(
        all_flags["all_flags_by_row"],
        get_rulebase_conditions_w_subhourlyqc(time_step),
        station_id,
        time_step=time_step,
        return_counts=return_counts,
    )

    # apply R1, which removes whole years
    # has to be run after R7 which updates the data
    rule_removed_rows, n_qc2_rows_removed = apply_r1(
        rule_removed_rows, station_id, all_flags["QC2"], return_count=return_counts
    )

    # update n_rows_removed
    n_rows_removed["R1"] = n_qc2_rows_removed

    if return_counts:
        return rule_removed_rows, n_rows_removed
    return rule_removed_rows
