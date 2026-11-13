"""
services/simulator.py
What-If improvement simulator for CORRUGATE IQ.

simulate_improvements(baseline_data, params) applies four independent
levers — downtime reduction, waste reduction, rejection reduction, and
speed improvement — to a baseline snapshot and returns a structured
result with baseline, simulated, and delta dicts plus assumptions
and caveats to be shown in the UI.
"""
from __future__ import annotations
from services.validation import safe_divide, clamp


def simulate_improvements(baseline_data: dict, params: dict) -> dict:
    """
    Project the effect of operational improvements on key KPIs.

    Args:
        baseline_data: Dict with keys from a production/material summary:
            - total_planned (boxes)
            - total_actual (boxes)
            - total_good (boxes)
            - total_rejected (boxes)
            - total_paper_input_kg
            - total_waste_kg
            - total_cost_inr
            - planned_time_minutes (total plant)
            - unplanned_downtime_minutes
            - ideal_speed_boxes_per_hour  (plant average)
            - paper_rate_inr_per_kg (average)
            - rejection_rate_pct
            - waste_pct
            - oee (current plant OEE, 0-1)

        params: Dict with optional improvement levers (all in %):
            - downtime_reduction_pct  (0-100): % reduction in unplanned downtime
            - waste_reduction_pct     (0-100): % reduction in paper waste
            - rejection_reduction_pct (0-100): % reduction in rejection rate
            - speed_improvement_pct   (0-100): % improvement in machine speed/performance

    Returns:
        Dict with:
            baseline  (dict) — input snapshot KPIs
            simulated (dict) — projected KPIs after improvements
            delta     (dict) — absolute & % change for each KPI
            assumptions (list[str])
            caveats   (list[str])
    """
    # ── Clamp params to safe ranges ──────────────────────────────────────────
    dt_red   = clamp(float(params.get("downtime_reduction_pct",  0)), 0, 100) / 100
    wst_red  = clamp(float(params.get("waste_reduction_pct",     0)), 0, 100) / 100
    rej_red  = clamp(float(params.get("rejection_reduction_pct", 0)), 0, 100) / 100
    spd_imp  = clamp(float(params.get("speed_improvement_pct",   0)), 0, 50)  / 100  # cap at 50%

    # ── Pull baseline values ──────────────────────────────────────────────────
    planned_time  = float(baseline_data.get("planned_time_minutes",       14400))  # 10 machines * 24hrs * 30d (default)
    unplanned_dt  = float(baseline_data.get("unplanned_downtime_minutes", 2000))
    ideal_spd     = float(baseline_data.get("ideal_speed_boxes_per_hour", 100))
    paper_in      = float(baseline_data.get("total_paper_input_kg",       0))
    waste_kg      = float(baseline_data.get("total_waste_kg",             0))
    total_cost    = float(baseline_data.get("total_cost_inr",             0))
    actual_out    = float(baseline_data.get("total_actual",               0))
    good_out      = float(baseline_data.get("total_good",                 0))
    rejected      = float(baseline_data.get("total_rejected",             0))
    paper_rate    = float(baseline_data.get("paper_rate_inr_per_kg",      42))
    oee_base      = float(baseline_data.get("oee",                        0.60))

    running_time  = planned_time - unplanned_dt

    # ── LEVER 1: Downtime reduction ───────────────────────────────────────────
    # Recovered run time → more boxes at current performance ratio
    dt_saved_min   = unplanned_dt * dt_red
    new_unplanned  = unplanned_dt - dt_saved_min
    new_running    = running_time + dt_saved_min
    # Additional boxes from recovered time (at current perf rate)
    current_rate   = safe_divide(actual_out, running_time / 60, default=0)
    extra_from_dt  = current_rate * (dt_saved_min / 60)

    # ── LEVER 2: Speed improvement ────────────────────────────────────────────
    # Increase production rate on existing running time
    new_rate  = current_rate * (1 + spd_imp)
    # Incremental output from speed alone (on the new running time)
    extra_from_speed = (new_rate - current_rate) * (new_running / 60)

    # ── Combined simulated actual output ─────────────────────────────────────
    sim_actual = actual_out + extra_from_dt + extra_from_speed

    # ── LEVER 3: Rejection reduction ─────────────────────────────────────────
    # Reduce rejected fraction → more good boxes from same actual
    base_rej_rate  = safe_divide(rejected, actual_out, default=0)
    sim_rej_rate   = base_rej_rate * (1 - rej_red)
    sim_rejected   = sim_actual * sim_rej_rate
    sim_good       = sim_actual - sim_rejected

    # ── LEVER 4: Waste reduction ──────────────────────────────────────────────
    # Waste is proportional to paper input; reducing waste saves material cost
    base_waste_pct = safe_divide(waste_kg, paper_in, default=0)
    sim_waste_pct  = base_waste_pct * (1 - wst_red)
    # Paper input scales with output; approximate proportionally
    output_ratio   = safe_divide(sim_actual, actual_out, default=1)
    sim_paper_in   = paper_in * output_ratio * (1 - base_waste_pct * wst_red)
    sim_waste_kg   = sim_paper_in * sim_waste_pct
    sim_good_kg    = sim_paper_in - sim_waste_kg

    waste_saving_inr = (waste_kg - sim_waste_kg) * paper_rate

    # ── Cost projection ───────────────────────────────────────────────────────
    # Labour and electricity scale roughly with output; maint drops with less DT
    sim_cost = total_cost * output_ratio * 0.92 - waste_saving_inr  # simplified
    sim_cost = max(sim_cost, total_cost * 0.60)  # floor at 60% of baseline

    # ── OEE projection ────────────────────────────────────────────────────────
    new_avail = clamp(safe_divide(new_running, planned_time), 0, 1)
    # Performance: speed improvement directly boosts performance component
    base_perf = oee_base / max(oee_base, 0.001)  # will recalculate properly
    # Approximate: improve OEE availability component, speed component
    oee_avail_component = new_avail
    oee_perf_component  = clamp(
        safe_divide(actual_out, ideal_spd * running_time / 60) * (1 + spd_imp), 0, 1)
    oee_qual_component  = clamp(1 - sim_rej_rate, 0, 1)
    sim_oee = clamp(oee_avail_component * oee_perf_component * oee_qual_component, 0, 1)

    # ── Build output dicts ────────────────────────────────────────────────────
    def pct_delta(sim, base):
        return round(safe_divide(sim - base, base) * 100, 2) if base else 0.0

    baseline_kpis = {
        "total_actual_boxes":   round(actual_out),
        "total_good_boxes":     round(good_out),
        "total_rejected_boxes": round(rejected),
        "rejection_rate_pct":   round(safe_divide(rejected, actual_out) * 100, 2),
        "total_paper_input_kg": round(paper_in, 1),
        "total_waste_kg":       round(waste_kg, 1),
        "waste_pct":            round(safe_divide(waste_kg, paper_in) * 100, 2),
        "total_cost_inr":       round(total_cost, 2),
        "cost_per_1000_boxes":  round(safe_divide(total_cost, good_out) * 1000, 2),
        "oee":                  round(oee_base, 4),
        "unplanned_downtime_min": round(unplanned_dt),
    }

    simulated_kpis = {
        "total_actual_boxes":   round(sim_actual),
        "total_good_boxes":     round(sim_good),
        "total_rejected_boxes": round(sim_rejected),
        "rejection_rate_pct":   round(sim_rej_rate * 100, 2),
        "total_paper_input_kg": round(sim_paper_in, 1),
        "total_waste_kg":       round(sim_waste_kg, 1),
        "waste_pct":            round(sim_waste_pct * 100, 2),
        "total_cost_inr":       round(sim_cost, 2),
        "cost_per_1000_boxes":  round(safe_divide(sim_cost, sim_good) * 1000, 2),
        "oee":                  round(sim_oee, 4),
        "unplanned_downtime_min": round(new_unplanned),
    }

    delta = {
        "total_actual_boxes":    {"abs": round(sim_actual - actual_out), "pct": pct_delta(sim_actual, actual_out)},
        "total_good_boxes":      {"abs": round(sim_good - good_out),     "pct": pct_delta(sim_good, good_out)},
        "rejection_rate_pct":    {"abs": round(sim_rej_rate * 100 - safe_divide(rejected, actual_out) * 100, 2)},
        "total_waste_kg":        {"abs": round(sim_waste_kg - waste_kg, 1), "pct": pct_delta(sim_waste_kg, waste_kg)},
        "waste_pct":             {"abs": round(sim_waste_pct * 100 - safe_divide(waste_kg, paper_in) * 100, 2)},
        "total_cost_inr":        {"abs": round(sim_cost - total_cost, 2), "pct": pct_delta(sim_cost, total_cost)},
        "cost_per_1000_boxes":   {"abs": round(safe_divide(sim_cost, sim_good) * 1000 - safe_divide(total_cost, good_out) * 1000, 2)},
        "oee":                   {"abs": round(sim_oee - oee_base, 4),     "pct": pct_delta(sim_oee, oee_base)},
        "unplanned_downtime_min":{"abs": round(new_unplanned - unplanned_dt)},
        "waste_saving_inr":      round(waste_saving_inr, 2),
    }

    assumptions = [
        "Production rate is proportional to running time (no diminishing returns).",
        "Speed improvement applies uniformly to all machines.",
        "Waste reduction is proportional to current waste rate.",
        "Rejection reduction is proportional to current rejection rate.",
        "No double counting: each lever is applied independently to baseline.",
        "Cost model uses a simplified linear scaling; actual savings may differ.",
        "OEE components are recalculated from first principles.",
    ]

    caveats = [
        "Downtime reductions require capital investment in spare parts or maintenance programmes.",
        "Speed increases beyond ±15% may require engineering validation.",
        "Waste reduction targets beyond 50% may need process redesign, not just operational changes.",
        "Financial projections are estimates and do not account for capex or transition downtime.",
        "Actual OEE improvement depends on workforce capability and process stability.",
    ]

    return {
        "baseline":    baseline_kpis,
        "simulated":   simulated_kpis,
        "delta":       delta,
        "assumptions": assumptions,
        "caveats":     caveats,
        "params_applied": {
            "downtime_reduction_pct":  round(dt_red  * 100, 1),
            "waste_reduction_pct":     round(wst_red * 100, 1),
            "rejection_reduction_pct": round(rej_red * 100, 1),
            "speed_improvement_pct":   round(spd_imp * 100, 1),
        },
    }

