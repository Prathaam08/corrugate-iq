"""
routes/dashboard.py
Main dashboard blueprint — page renders and all primary API endpoints.
"""
from __future__ import annotations
from collections import defaultdict
from flask import Blueprint, render_template, jsonify, request
from services import data_service as ds
from services import kpi_calculator as kpi
from services.insights_engine import generate_insights

dashboard_bp = Blueprint("dashboard", __name__)


def _parse_filters() -> dict:
    """Extract common query-string filters from the request."""
    f: dict = {}
    if request.args.get("start_date"):
        f["start_date"] = request.args["start_date"]
    if request.args.get("end_date"):
        f["end_date"] = request.args["end_date"]
    if request.args.get("machines"):
        f["machine_ids"] = request.args["machines"].split(",")
    if request.args.get("shifts"):
        f["shifts"] = request.args["shifts"].split(",")
    return f


# ── Page routes ───────────────────────────────────────────────────────────────

@dashboard_bp.route("/")
def index():
    return render_template("dashboard.html")

@dashboard_bp.route("/production")
def production_page():
    return render_template("production.html")

@dashboard_bp.route("/materials")
def materials_page():
    return render_template("materials.html")

@dashboard_bp.route("/quality")
def quality_page():
    return render_template("quality.html")

@dashboard_bp.route("/orders")
def orders_page():
    return render_template("orders.html")

@dashboard_bp.route("/settings")
def settings_page():
    return render_template("settings.html")


# ── API: KPIs ─────────────────────────────────────────────────────────────────

@dashboard_bp.route("/api/kpis")
def api_kpis():
    filters = _parse_filters()
    prod    = ds.get_production_records(filters)
    mat     = ds.get_material_records(filters)
    events  = ds.get_downtime_events(filters)
    config  = ds.get_config()

    prod_summary = ds.summarize_production(prod)
    mat_summary  = ds.summarize_material(mat)
    dt_summary   = ds.summarize_downtime(events)
    plant_data   = kpi.aggregate_oee_for_plant(prod)

    return jsonify({
        "production":  prod_summary,
        "material":    mat_summary,
        "downtime":    dt_summary,
        "plant_oee":   plant_data["plant_oee"],
        "config":      config,
    })


# ── API: Production chart (daily trend) ───────────────────────────────────────

@dashboard_bp.route("/api/production-chart")
def api_production_chart():
    filters = _parse_filters()
    prod    = ds.get_production_records(filters)
    by_date: dict[str, dict] = defaultdict(lambda: {"planned": 0, "actual": 0, "good": 0})
    for r in prod:
        d = r["date"]
        by_date[d]["planned"] += r.get("planned_output", 0)
        by_date[d]["actual"]  += r.get("actual_output", 0)
        by_date[d]["good"]    += r.get("good_output", 0)
    dates = sorted(by_date)
    return jsonify({
        "labels":  dates,
        "planned": [by_date[d]["planned"] for d in dates],
        "actual":  [by_date[d]["actual"]  for d in dates],
        "good":    [by_date[d]["good"]    for d in dates],
    })


# ── API: OEE comparison per machine ──────────────────────────────────────────

@dashboard_bp.route("/api/oee-comparison")
def api_oee_comparison():
    filters    = _parse_filters()
    prod       = ds.get_production_records(filters)
    plant_data = kpi.aggregate_oee_for_plant(prod)
    config     = ds.get_config()
    machines   = ds.get_machines()
    name_map   = {m["id"]: m["name"] for m in machines}
    result = []
    for mid, oee_data in plant_data["machines"].items():
        result.append({
            "machine_id":   mid,
            "machine_name": name_map.get(mid, mid),
            "oee":          round(oee_data["oee"] * 100, 1),
            "availability": round(oee_data["availability"] * 100, 1),
            "performance":  round(oee_data["performance"] * 100, 1),
            "quality":      round(oee_data["quality"] * 100, 1),
            "oee_target":   round(config.get("oee_target", 0.75) * 100, 1),
        })
    return jsonify(result)


# ── API: Downtime Pareto ──────────────────────────────────────────────────────

@dashboard_bp.route("/api/downtime-pareto")
def api_downtime_pareto():
    filters  = _parse_filters()
    events   = ds.get_downtime_events(filters)
    summary  = ds.summarize_downtime(events)
    by_cat   = summary.get("by_category", {})
    # Sort descending
    sorted_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in sorted_cats) or 1
    cumulative = 0
    rows = []
    for cat, mins in sorted_cats:
        cumulative += mins
        rows.append({
            "category": cat,
            "minutes":  mins,
            "pct":      round(mins / total * 100, 1),
            "cumulative_pct": round(cumulative / total * 100, 1),
        })
    return jsonify({
        "pareto":    rows,
        "summary":   summary,
    })


# ── API: Waste breakdown ──────────────────────────────────────────────────────

@dashboard_bp.route("/api/waste-breakdown")
def api_waste_breakdown():
    filters = _parse_filters()
    mat     = ds.get_material_records(filters)
    totals = {
        "trim_waste_kg":        sum(r.get("trim_waste_kg", 0)        for r in mat),
        "setup_waste_kg":       sum(r.get("setup_waste_kg", 0)       for r in mat),
        "breakage_waste_kg":    sum(r.get("breakage_waste_kg", 0)    for r in mat),
        "printing_defect_kg":   sum(r.get("printing_defect_kg", 0)   for r in mat),
        "gluing_defect_kg":     sum(r.get("gluing_defect_kg", 0)     for r in mat),
        "handling_damage_kg":   sum(r.get("handling_damage_kg", 0)   for r in mat),
    }
    total_waste = sum(totals.values()) or 1
    breakdown = [{"label": k.replace("_kg","").replace("_"," ").title(),
                  "kg": round(v, 1),
                  "pct": round(v / total_waste * 100, 1)}
                 for k, v in sorted(totals.items(), key=lambda x: x[1], reverse=True)]
    return jsonify(breakdown)


# ── API: Quality breakdown ────────────────────────────────────────────────────

@dashboard_bp.route("/api/quality-breakdown")
def api_quality_breakdown():
    filters = _parse_filters()
    quality = ds.get_quality_records(filters)
    summary = ds.summarize_quality(quality)
    # Per-machine rejection rates
    by_machine: dict[str, dict] = defaultdict(lambda: {"total": 0, "rejected": 0})
    for r in quality:
        mid = r.get("machine_id", "?")
        by_machine[mid]["total"]    += r.get("total_produced", 0)
        by_machine[mid]["rejected"] += r.get("rejected_units", 0)
    from services.validation import safe_divide
    machines_rr = [{
        "machine_id": mid,
        "total":      agg["total"],
        "rejected":   agg["rejected"],
        "rejection_rate_pct": round(safe_divide(agg["rejected"], agg["total"]) * 100, 2),
    } for mid, agg in by_machine.items()]
    return jsonify({"summary": summary, "by_machine": machines_rr})


# ── API: Shift performance ────────────────────────────────────────────────────

@dashboard_bp.route("/api/shift-performance")
def api_shift_performance():
    filters = _parse_filters()
    prod    = ds.get_production_records(filters)
    mat     = ds.get_material_records(filters)
    from services.validation import safe_divide
    shifts = ["A", "B", "C"]
    result = []
    for shift in shifts:
        p = [r for r in prod if r.get("shift") == shift]
        m = [r for r in mat  if r.get("shift") == shift]
        ps = ds.summarize_production(p)
        ms = ds.summarize_material(m)
        result.append({
            "shift":          shift,
            "total_actual":   ps.get("total_actual", 0),
            "total_good":     ps.get("total_good", 0),
            "achievement_pct":ps.get("achievement_pct", 0),
            "rejection_pct":  ps.get("rejection_rate_pct", 0),
            "waste_pct":      ms.get("waste_pct", 0),
        })
    return jsonify(result)


# ── API: Production loss ──────────────────────────────────────────────────────

@dashboard_bp.route("/api/production-loss")
def api_production_loss():
    filters  = _parse_filters()
    prod     = ds.get_production_records(filters)
    machines = ds.get_machines()
    id_map   = {m["id"]: m for m in machines}
    by_machine: dict[str, dict] = defaultdict(lambda: {"planned": 0, "actual": 0, "speed": 0, "count": 0})
    for r in prod:
        mid = r.get("machine_id", "?")
        by_machine[mid]["planned"] += r.get("planned_output", 0)
        by_machine[mid]["actual"]  += r.get("actual_output", 0)
        by_machine[mid]["speed"]   += r.get("ideal_speed", id_map.get(mid, {}).get("ideal_speed_boxes_per_hour", 100))
        by_machine[mid]["count"]   += 1
    result = []
    for mid, agg in by_machine.items():
        avg_speed = agg["speed"] / agg["count"] if agg["count"] else 100
        loss_min = kpi.calculate_production_loss_minutes(agg["planned"], agg["actual"], avg_speed)
        result.append({
            "machine_id":    mid,
            "planned":       agg["planned"],
            "actual":        agg["actual"],
            "gap":           kpi.production_gap(agg["planned"], agg["actual"]),
            "loss_minutes":  round(loss_min, 1),
        })
    return jsonify(result)


# ── API: Insights ─────────────────────────────────────────────────────────────

@dashboard_bp.route("/api/insights")
def api_insights():
    filters   = _parse_filters()
    insights  = generate_insights(filters)
    return jsonify(insights)


# ── API: Production Detail ────────────────────────────────────────────────────

@dashboard_bp.route("/api/production")
def api_production():
    filters = _parse_filters()
    records = ds.get_production_records(filters)
    summary = ds.summarize_production(records)
    return jsonify({
        "summary": summary,
        "records": records[:100],
    })


# ── API: Materials Detail ─────────────────────────────────────────────────────

@dashboard_bp.route("/api/materials")
def api_materials():
    filters = _parse_filters()
    records = ds.get_material_records(filters)
    summary = ds.summarize_material(records)
    return jsonify({
        "summary": summary,
        "records": records[:100],
    })


# ── API: Orders Detail ────────────────────────────────────────────────────────

@dashboard_bp.route("/api/orders")
def api_orders():
    filters = _parse_filters()
    orders = ds.get_orders()
    # Apply date/status filtering to orders
    if filters.get("start_date"):
        orders = [o for o in orders if o.get("due_date", "") >= filters["start_date"]]
    if filters.get("end_date"):
        orders = [o for o in orders if o.get("due_date", "") <= filters["end_date"]]
    if filters.get("machine_ids"):
        machine_set = set(filters["machine_ids"])
        orders = [o for o in orders if o.get("assigned_machine") in machine_set]
    total = len(orders)
    in_progress = sum(1 for o in orders if o.get("status") == "In Progress")
    completed = sum(1 for o in orders if o.get("status") == "Completed")
    at_risk = sum(1 for o in orders if o.get("is_at_risk"))
    return jsonify({
        "summary": {
            "total": total,
            "in_progress": in_progress,
            "completed": completed,
            "at_risk": at_risk,
        },
        "orders": orders,
    })


# ── API: Config ───────────────────────────────────────────────────────────────

@dashboard_bp.route("/api/config")
def api_config():
    return jsonify(ds.get_config())


