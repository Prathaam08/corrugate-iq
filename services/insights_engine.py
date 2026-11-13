"""
services/insights_engine.py
Deterministic rule-based engine that evaluates 8 operational rules
and returns ranked, actionable insight objects.

Each insight dict has:
  id, title, severity, affected_entity, evidence (dict),
  operational_impact (str), financial_impact_inr (float),
  likely_cause (str), recommended_action (str),
  responsible_department (str), rank_score (float)
"""
from __future__ import annotations
from collections import defaultdict
from services import data_service as ds
from services import kpi_calculator as kpi
from services.validation import safe_divide


# ── Severity levels (for sorting) ────────────────────────────────────────────
_SEV_RANK = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}


def _insight(rule_id, title, severity, entity, evidence,
             op_impact, fin_impact, cause, action, dept):
    """Factory for a well-formed insight dict."""
    return {
        "id":                   rule_id,
        "title":                title,
        "severity":             severity,
        "affected_entity":      entity,
        "evidence":             evidence,
        "operational_impact":   op_impact,
        "financial_impact_inr": round(float(fin_impact), 2),
        "likely_cause":         cause,
        "recommended_action":   action,
        "responsible_department": dept,
        "rank_score":           _SEV_RANK.get(severity, 1) * 10 + min(fin_impact / 10000, 9),
    }


# ── Individual rule evaluators ────────────────────────────────────────────────

def _rule_high_waste(prod_records, mat_records, config) -> list[dict]:
    """RULE_HIGH_WASTE — plant-level waste > config waste_target_pct."""
    target = config.get("waste_target_pct", 5.0)
    summary = ds.summarize_material(mat_records)
    if not summary:
        return []
    waste_pct = summary.get("waste_pct", 0.0)
    if waste_pct <= target:
        return []
    fin = summary.get("total_waste_kg", 0) * config.get(
        "paper_rate_inr_per_kg", {}).get("Kraft Liner", 42)
    return [_insight(
        "RULE_HIGH_WASTE",
        f"Plant paper waste at {waste_pct:.1f}% — above {target}% target",
        "High",
        "Plant",
        {"waste_pct": waste_pct, "target_pct": target,
         "total_waste_kg": summary.get("total_waste_kg")},
        f"Material utilisation loss of {waste_pct - target:.1f}% above target.",
        fin,
        "Incorrect tension settings, frequent paper breaks, or poor splice quality.",
        "Audit tension control and splicer settings; retrain operators on reel handling.",
        "Production Engineering",
    )]


def _rule_low_oee_machine(prod_records, config) -> list[dict]:
    """RULE_LOW_OEE_MACHINE — any machine OEE < 60%."""
    threshold = 0.60
    plant_data = kpi.aggregate_oee_for_plant(prod_records)
    insights = []
    for mid, oee_data in plant_data["machines"].items():
        oee = oee_data["oee"]
        if oee < threshold:
            fin_loss = oee_data["total_planned_min"] / 60 * 100 * 42 * (threshold - oee)
            insights.append(_insight(
                f"RULE_LOW_OEE_MACHINE_{mid}",
                f"{mid} OEE at {oee*100:.1f}% — critically below 60% threshold",
                "Critical" if oee < 0.45 else "High",
                mid,
                {"oee": round(oee, 4),
                 "availability": oee_data["availability"],
                 "performance":  oee_data["performance"],
                 "quality":      oee_data["quality"]},
                f"Machine running at {oee*100:.1f}% efficiency — significant capacity wasted.",
                fin_loss,
                "High downtime, slow running speed, or quality losses.",
                "Perform root-cause analysis on the lowest OEE component; prioritise breakdown reduction.",
                "Maintenance" if oee_data["availability"] < 0.70 else "Production",
            ))
    return insights


def _rule_recurring_breakdown(downtime_events, config) -> list[dict]:
    """RULE_RECURRING_BREAKDOWN — machine with >5 mechanical breakdown events."""
    threshold = 5
    by_machine: dict[str, list] = defaultdict(list)
    for e in downtime_events:
        if e.get("category") == "Mechanical Breakdown":
            by_machine[e["machine_id"]].append(e)
    insights = []
    for mid, events in by_machine.items():
        if len(events) > threshold:
            total_min = sum(e.get("duration_minutes", 0) for e in events)
            fin = total_min / 60 * 100 * 42  # rough boxes * paper cost
            insights.append(_insight(
                f"RULE_RECURRING_BREAKDOWN_{mid}",
                f"{mid} has {len(events)} mechanical breakdowns this period",
                "Critical",
                mid,
                {"breakdown_count": len(events), "total_downtime_min": total_min,
                 "threshold": threshold},
                f"{total_min} minutes ({total_min/60:.1f} hrs) of unplanned downtime from breakdowns.",
                fin,
                "Aging components, deferred preventive maintenance, or inadequate lubrication.",
                "Escalate to planned maintenance; replace critical wear parts; implement lubrication schedule.",
                "Maintenance",
            ))
    return insights


def _rule_low_performance(prod_records, config) -> list[dict]:
    """RULE_LOW_PERFORMANCE — machine performance factor < 0.70."""
    threshold = 0.70
    plant_data = kpi.aggregate_oee_for_plant(prod_records)
    insights = []
    for mid, oee_data in plant_data["machines"].items():
        perf = oee_data["performance"]
        if perf < threshold:
            fin = oee_data["total_running_min"] / 60 * (threshold - perf) * 80 * 42
            insights.append(_insight(
                f"RULE_LOW_PERFORMANCE_{mid}",
                f"{mid} performance factor {perf*100:.1f}% — below 70% threshold",
                "High",
                mid,
                {"performance": round(perf, 4), "threshold": threshold,
                 "availability": oee_data["availability"]},
                "Machine producing significantly fewer boxes than its rated speed allows.",
                fin,
                "Speed restrictions, micro-stops, material feed issues, or operator-paced running.",
                "Investigate micro-stops and idling; validate machine speed settings; review operator SOP.",
                "Production Engineering",
            ))
    return insights


def _rule_high_rejection(quality_records, config) -> list[dict]:
    """RULE_HIGH_REJECTION — product/machine rejection > config rejection_target_pct."""
    target = config.get("rejection_target_pct", 2.0)
    by_key: dict[str, dict] = defaultdict(lambda: {"total": 0, "rejected": 0})
    for r in quality_records:
        key = f"{r.get('machine_id')}|{r.get('product_type')}"
        by_key[key]["total"]    += r.get("total_produced", 0)
        by_key[key]["rejected"] += r.get("rejected_units", 0)
    insights = []
    for key, agg in by_key.items():
        mid, product = key.split("|")
        rr = safe_divide(agg["rejected"], agg["total"]) * 100
        if rr > target:
            fin = agg["rejected"] * 0.002 * 42 * 100  # approx scrap cost
            insights.append(_insight(
                f"RULE_HIGH_REJECTION_{mid}_{product}",
                f"{mid} rejection rate {rr:.1f}% for {product} — exceeds {target}% target",
                "Critical" if rr > 10 else "High" if rr > 5 else "Medium",
                f"{mid} / {product}",
                {"rejection_rate_pct": round(rr, 2), "target_pct": target,
                 "total": agg["total"], "rejected": agg["rejected"]},
                f"{agg['rejected']} boxes rejected — rework/scrap cost and delivery risk.",
                fin,
                "Die wear, misaligned guides, incorrect settings, or material quality issues.",
                "Inspect die condition; recalibrate guides; conduct SPC on critical dimensions.",
                "Quality Assurance",
            ))
    return insights


def _rule_order_at_risk(orders, config) -> list[dict]:
    """RULE_ORDER_AT_RISK — order completion behind schedule by >15%."""
    insights = []
    for o in orders:
        if not o.get("is_at_risk"):
            continue
        ordered   = o.get("ordered_qty", 1)
        completed = o.get("completed_qty", 0)
        behind_pct = safe_divide(ordered - completed, ordered) * 100
        if behind_pct > 15:
            fin = (ordered - completed) * 0.005 * 42 * 100  # penalty estimate
            insights.append(_insight(
                f"RULE_ORDER_AT_RISK_{o['order_id']}",
                f"Order {o['order_id']} ({o.get('customer_name')}) at risk — {behind_pct:.0f}% behind",
                "Critical" if o.get("priority") == "Critical" else "High",
                o["order_id"],
                {"order_id": o["order_id"], "ordered": ordered,
                 "completed": completed, "behind_pct": round(behind_pct, 1),
                 "due_date": o.get("due_date"),
                 "estimated_completion": o.get("estimated_completion_date")},
                f"Delivery to {o.get('customer_name')} may be delayed; customer SLA breach risk.",
                fin,
                "Machine downtime on assigned machine or insufficient production scheduling.",
                "Re-schedule on alternate machine; prioritise order; communicate revised date to customer.",
                "Planning & Scheduling",
            ))
    return insights


def _rule_shift_waste(mat_records, config) -> list[dict]:
    """RULE_SHIFT_WASTE — shift waste significantly above plant average."""
    by_shift: dict[str, dict] = defaultdict(lambda: {"input": 0.0, "waste": 0.0})
    for r in mat_records:
        s = r.get("shift", "?")
        by_shift[s]["input"] += r.get("paper_input_kg", 0)
        by_shift[s]["waste"] += r.get("total_waste_kg", 0)
    if not by_shift:
        return []
    total_in  = sum(v["input"] for v in by_shift.values())
    total_wst = sum(v["waste"] for v in by_shift.values())
    plant_avg = safe_divide(total_wst, total_in) * 100
    insights = []
    for shift, agg in by_shift.items():
        shift_pct = safe_divide(agg["waste"], agg["input"]) * 100
        if shift_pct > plant_avg * 1.10 and shift_pct > config.get("waste_target_pct", 5.0):
            excess_kg = agg["waste"] - agg["input"] * plant_avg / 100
            fin = excess_kg * 42
            insights.append(_insight(
                f"RULE_SHIFT_WASTE_SHIFT_{shift}",
                f"Shift {shift} paper waste {shift_pct:.1f}% — above plant average {plant_avg:.1f}%",
                "Medium",
                f"Shift {shift}",
                {"shift_waste_pct": round(shift_pct, 2),
                 "plant_avg_pct":   round(plant_avg, 2),
                 "excess_waste_kg": round(excess_kg, 2)},
                f"Shift {shift} consuming excess paper vs. other shifts.",
                fin,
                "Night-shift fatigue, different operator skill levels, or less supervision.",
                "Review Shift C standard operating procedures; additional shift supervisor monitoring.",
                "Human Resources / Production",
            ))
    return insights


def _rule_high_changeover(downtime_events, config) -> list[dict]:
    """RULE_HIGH_CHANGEOVER — changeover downtime >20% of machine's total downtime."""
    by_machine: dict[str, dict] = defaultdict(lambda: {"total": 0, "changeover": 0})
    for e in downtime_events:
        mid = e.get("machine_id", "?")
        dur = e.get("duration_minutes", 0)
        by_machine[mid]["total"] += dur
        if e.get("category") == "Changeover":
            by_machine[mid]["changeover"] += dur
    threshold = 0.20
    insights = []
    for mid, agg in by_machine.items():
        if agg["total"] == 0:
            continue
        co_pct = safe_divide(agg["changeover"], agg["total"])
        if co_pct > threshold:
            fin = agg["changeover"] / 60 * 80 * 38  # lost production value
            insights.append(_insight(
                f"RULE_HIGH_CHANGEOVER_{mid}",
                f"{mid} changeover time {co_pct*100:.1f}% of downtime — above 20% threshold",
                "Medium",
                mid,
                {"changeover_pct": round(co_pct * 100, 1),
                 "changeover_min":  agg["changeover"],
                 "total_downtime_min": agg["total"]},
                f"{agg['changeover']} minutes lost to changeovers on {mid}.",
                fin,
                "High product variety, non-standardised changeover procedures, or tooling delays.",
                "Implement SMED methodology; pre-stage tooling; create changeover checklists.",
                "Production Engineering",
            ))
    return insights


# ── Public API ────────────────────────────────────────────────────────────────

def generate_insights(filters: dict | None = None) -> list[dict]:
    """
    Run all 8 rules and return insights sorted by rank_score descending.

    Args:
        filters: Optional dict passed to data_service getters (date/machine/shift).

    Returns:
        List of insight dicts, highest rank first.
    """
    config      = ds.get_config()
    prod        = ds.get_production_records(filters)
    mat         = ds.get_material_records(filters)
    quality     = ds.get_quality_records(filters)
    downtime    = ds.get_downtime_events(filters)
    orders      = ds.get_orders()

    all_insights = []
    all_insights.extend(_rule_high_waste(prod, mat, config))
    all_insights.extend(_rule_low_oee_machine(prod, config))
    all_insights.extend(_rule_recurring_breakdown(downtime, config))
    all_insights.extend(_rule_low_performance(prod, config))
    all_insights.extend(_rule_high_rejection(quality, config))
    all_insights.extend(_rule_order_at_risk(orders, config))
    all_insights.extend(_rule_shift_waste(mat, config))
    all_insights.extend(_rule_high_changeover(downtime, config))

    all_insights.sort(key=lambda x: x["rank_score"], reverse=True)
    return all_insights

