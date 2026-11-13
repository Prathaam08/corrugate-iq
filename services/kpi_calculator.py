"""
services/kpi_calculator.py
All OEE / production / quality / cost KPI formulas for CORRUGATE IQ.
Every public function validates inputs via services.validation helpers
and returns a float (0–1 for rates, raw values for counts/costs).
"""
from __future__ import annotations
from typing import Any
from services.validation import safe_divide, clamp


# ── Production ────────────────────────────────────────────────────────────────

def production_achievement(actual: float, planned: float) -> float:
    """
    Ratio of actual output to planned output.

    Args:
        actual:  Actual boxes produced in the period.
        planned: Planned boxes for the period.

    Returns:
        Float in [0, ∞); values > 1 indicate over-production.
    """
    return safe_divide(actual, planned, default=0.0)


def production_gap(planned: float, actual: float) -> float:
    """
    Absolute shortfall of actual vs. planned production.

    Args:
        planned: Planned boxes for the period.
        actual:  Actual boxes produced.

    Returns:
        Non-negative float.  Returns 0 when actual >= planned.
    """
    gap = (planned or 0) - (actual or 0)
    return max(0.0, gap)


def production_rate(actual_output: float, running_hours: float) -> float:
    """
    Actual production rate (boxes per hour).

    Args:
        actual_output: Total boxes produced.
        running_hours: Hours machine was actually running.

    Returns:
        Boxes per hour; 0.0 when running_hours is zero.
    """
    return safe_divide(actual_output, running_hours, default=0.0)


# ── OEE Components ───────────────────────────────────────────────────────────

def machine_availability(running_time: float, planned_time: float) -> float:
    """
    Availability = Running Time / Planned Time.
    Clamped to [0, 1].

    Args:
        running_time: Actual run time in minutes (or any consistent unit).
        planned_time: Scheduled production time in the same unit.

    Returns:
        Float in [0, 1].
    """
    return clamp(safe_divide(running_time, planned_time, default=0.0), 0.0, 1.0)


def machine_performance(actual_output: float, ideal_output_at_running_time: float) -> float:
    """
    Performance = Actual Output / Ideal Output at Running Time.
    Ideal output = ideal_speed * running_hours.
    Clamped to [0, 1].

    Args:
        actual_output:              Boxes actually produced.
        ideal_output_at_running_time: Boxes at theoretical maximum speed for the
                                      same running duration.

    Returns:
        Float in [0, 1].
    """
    return clamp(safe_divide(actual_output, ideal_output_at_running_time, default=0.0), 0.0, 1.0)


def quality_rate(good_output: float, total_output: float) -> float:
    """
    Quality Rate = Good Output / Total Output.
    Clamped to [0, 1].

    Args:
        good_output:  Units passing quality inspection.
        total_output: Total units produced (good + rejected).

    Returns:
        Float in [0, 1].
    """
    return clamp(safe_divide(good_output, total_output, default=0.0), 0.0, 1.0)


def calculate_oee(availability: float, performance: float, quality: float) -> float:
    """
    Overall Equipment Effectiveness = Availability × Performance × Quality.
    All inputs should be in [0, 1].

    Args:
        availability: Machine availability factor.
        performance:  Machine performance factor.
        quality:      Quality rate factor.

    Returns:
        Float in [0, 1].
    """
    return clamp((availability or 0.0) * (performance or 0.0) * (quality or 0.0), 0.0, 1.0)


# ── Material / Waste ─────────────────────────────────────────────────────────

def paper_waste_percentage(waste_kg: float, paper_input_kg: float) -> float:
    """
    Paper Waste % = waste_kg / paper_input_kg × 100.

    Args:
        waste_kg:       Total waste paper in kg.
        paper_input_kg: Total paper input in kg.

    Returns:
        Percentage float; 0.0 when paper_input_kg is zero.
    """
    return safe_divide(waste_kg, paper_input_kg, default=0.0) * 100.0


def material_yield(good_output_kg: float, paper_input_kg: float) -> float:
    """
    Material Yield % = good_output_kg / paper_input_kg × 100.

    Args:
        good_output_kg: Good product weight in kg.
        paper_input_kg: Total paper input in kg.

    Returns:
        Percentage float; 0.0 when paper_input_kg is zero.
    """
    return safe_divide(good_output_kg, paper_input_kg, default=0.0) * 100.0


# ── Quality / Rejection ──────────────────────────────────────────────────────

def rejection_rate(rejected_units: float, total_units: float) -> float:
    """
    Rejection Rate % = rejected_units / total_units × 100.

    Args:
        rejected_units: Boxes failing quality check.
        total_units:    Total boxes produced.

    Returns:
        Percentage float; 0.0 when total_units is zero.
    """
    return safe_divide(rejected_units, total_units, default=0.0) * 100.0


# ── Downtime / Reliability ───────────────────────────────────────────────────

def downtime_percentage(unplanned_downtime: float, planned_time: float) -> float:
    """
    Unplanned Downtime % = unplanned_downtime / planned_time × 100.

    Args:
        unplanned_downtime: Unplanned downtime in minutes.
        planned_time:       Scheduled production time in minutes.

    Returns:
        Percentage float.
    """
    return safe_divide(unplanned_downtime, planned_time, default=0.0) * 100.0


def calculate_mttr(total_repair_time: float, num_repairs: int) -> float:
    """
    Mean Time To Repair = total repair time / number of repair events.

    Args:
        total_repair_time: Cumulative repair duration in minutes.
        num_repairs:       Count of repair events.

    Returns:
        Average repair duration in minutes; 0.0 when no repairs.
    """
    return safe_divide(total_repair_time, num_repairs, default=0.0)


def calculate_mtbf(operating_time: float, num_failures: int) -> float:
    """
    Mean Time Between Failures = operating_time / num_failures.

    Args:
        operating_time: Total operating time in minutes (excludes downtime).
        num_failures:   Count of failure events.

    Returns:
        Average time between failures in minutes; 0.0 when no failures.
    """
    return safe_divide(operating_time, num_failures, default=0.0)


# ── Cost ─────────────────────────────────────────────────────────────────────

def cost_per_1000_boxes(total_cost: float, good_boxes: float) -> float:
    """
    Manufacturing cost per 1000 good boxes (₹ / 1000 boxes).

    Args:
        total_cost: Sum of labour + electricity + maintenance costs in INR.
        good_boxes: Good boxes produced.

    Returns:
        INR per 1000 boxes; 0.0 when good_boxes is zero.
    """
    return safe_divide(total_cost, good_boxes, default=0.0) * 1000.0


def estimated_wastage_cost(waste_kg: float, rate_per_kg: float) -> float:
    """
    Financial cost of wasted paper material.

    Args:
        waste_kg:    Waste paper in kg.
        rate_per_kg: Paper procurement rate in INR per kg.

    Returns:
        INR value of waste.
    """
    return (waste_kg or 0.0) * (rate_per_kg or 0.0)


def calculate_production_loss_minutes(planned: float, actual: float, ideal_speed: float) -> float:
    """
    Equivalent downtime minutes lost due to production shortfall.

    production_loss_minutes = (planned - actual) / ideal_speed * 60

    Args:
        planned:     Planned output in boxes.
        actual:      Actual output in boxes.
        ideal_speed: Machine ideal speed in boxes/hour.

    Returns:
        Minutes of equivalent production loss; 0.0 if no gap or ideal_speed is zero.
    """
    gap = max(0.0, (planned or 0) - (actual or 0))
    return safe_divide(gap, ideal_speed, default=0.0) * 60.0


# ── Aggregation ──────────────────────────────────────────────────────────────

def aggregate_oee_for_machine(production_records_list: list[dict]) -> dict:
    """
    Compute OEE components for a single machine across multiple records.

    Args:
        production_records_list: List of production record dicts, each with
            running_time_minutes, planned_time_minutes, actual_output,
            ideal_speed, good_output.

    Returns:
        Dict with keys: availability, performance, quality, oee,
        total_running_min, total_planned_min, total_actual, total_good.
    """
    total_running = sum(r.get("running_time_minutes", 0) for r in production_records_list)
    total_planned = sum(r.get("planned_time_minutes", 0) for r in production_records_list)
    total_actual  = sum(r.get("actual_output", 0) for r in production_records_list)
    total_good    = sum(r.get("good_output", 0) for r in production_records_list)

    # Ideal output = sum(ideal_speed * running_hours per record)
    ideal_total = sum(
        r.get("ideal_speed", 0) * (r.get("running_time_minutes", 0) / 60.0)
        for r in production_records_list
    )

    avail = machine_availability(total_running, total_planned)
    perf  = machine_performance(total_actual, ideal_total)
    qual  = quality_rate(total_good, total_actual)
    oee   = calculate_oee(avail, perf, qual)

    return {
        "availability":    round(avail, 4),
        "performance":     round(perf, 4),
        "quality":         round(qual, 4),
        "oee":             round(oee, 4),
        "total_running_min": total_running,
        "total_planned_min": total_planned,
        "total_actual":    total_actual,
        "total_good":      total_good,
    }


def aggregate_oee_for_plant(all_production_records: list[dict]) -> dict:
    """
    Compute OEE for the entire plant and per-machine breakdown.

    Args:
        all_production_records: All production records (all machines, all periods).

    Returns:
        Dict with keys: plant_oee (dict), machines (dict mapping machine_id -> oee dict).
    """
    from collections import defaultdict
    by_machine: dict[str, list] = defaultdict(list)
    for r in all_production_records:
        by_machine[r.get("machine_id", "UNKNOWN")].append(r)

    machines_oee = {mid: aggregate_oee_for_machine(recs)
                    for mid, recs in by_machine.items()}
    plant_oee = aggregate_oee_for_machine(all_production_records)

    return {
        "plant_oee": plant_oee,
        "machines":  machines_oee,
    }

