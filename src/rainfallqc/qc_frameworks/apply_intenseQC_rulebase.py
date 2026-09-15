import polars as pl

TIME_STEP_CONVERSION = {"15m": "15m", "1h": "hourly"}


def apply_conditional_rule(data: pl.DataFrame, condition: pl.Expr, val_col: str) -> pl.DataFrame:
    return data.with_columns(pl.when(condition).then(None).otherwise(pl.col(val_col)).alias(val_col))


def apply_rowbased_rulebase_to_one_station(
    flags_by_row: pl.DataFrame,
    rules_to_apply: dict,
    station_id: str,
    time_step: str,
    return_counts: bool = True,
) -> pl.DataFrame | tuple[pl.DataFrame, dict]:
    """
    Note: will overlap the count of rules removed
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
    Needs to be applied last, as it can remove entire years
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
    return (pl.col(f"wet_spell_flag_{TIME_STEP_CONVERSION[time_step]}") == 3) & (
        pl.col(station_id) > 2 * pl.col(station_id).filter(pl.col(station_id) > 0).mean()
    )


def get_rulebase_conditions(time_step: str) -> dict:
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


def apply_intenseQC_rulebase(
    all_flags: dict, station_id: str, time_step: str, return_counts=True
) -> pl.DataFrame | tuple[pl.DataFrame, dict]:
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
