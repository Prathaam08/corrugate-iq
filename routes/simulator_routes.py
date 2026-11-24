"""
routes/simulator_routes.py
Simulator blueprint — POST /api/simulate runs the what-if engine.
"""
from flask import Blueprint, jsonify, request
from services import data_service as ds
from services import kpi_calculator as kpi
from services.simulator import simulate_improvements

simulator_bp = Blueprint("simulator", __name__)


@simulator_bp.route("/api/simulate", methods=["POST"])
def api_simulate():
    body = request.get_json(force=True, silent=True) or {}
    params = body.get("params", {})

    # Build baseline from full dataset
    prod     = ds.get_production_records()
    mat      = ds.get_material_records()
    downtime = ds.get_downtime_events()
    config   = ds.get_config()

    prod_sum = ds.summarize_production(prod)
    mat_sum  = ds.summarize_material(mat)
    dt_sum   = ds.summarize_downtime(downtime)
    plant    = kpi.aggregate_oee_for_plant(prod)

    # Determine average paper rate (dynamic — works with any number of paper types)
    paper_rates = config.get("paper_rate_inr_per_kg", {})
    avg_paper_rate = sum(paper_rates.values()) / len(paper_rates) if paper_rates else 38.0

    baseline_data = {
        "total_planned":              prod_sum.get("total_planned", 0),
        "total_actual":               prod_sum.get("total_actual", 0),
        "total_good":                 prod_sum.get("total_good", 0),
        "total_rejected":             prod_sum.get("total_rejected", 0),
        "total_paper_input_kg":       mat_sum.get("total_paper_input_kg", 0),
        "total_waste_kg":             mat_sum.get("total_waste_kg", 0),
        "total_cost_inr":             prod_sum.get("total_cost_inr", 0),
        "planned_time_minutes":       sum(r.get("planned_time_minutes", 0) for r in prod),
        "unplanned_downtime_minutes": dt_sum.get("unplanned_minutes", 0),
        "ideal_speed_boxes_per_hour": 100,  # plant average
        "paper_rate_inr_per_kg":      avg_paper_rate,
        "rejection_rate_pct":         prod_sum.get("rejection_rate_pct", 0),
        "waste_pct":                  prod_sum.get("waste_pct", 0),
        "oee":                        plant["plant_oee"].get("oee", 0.60),
    }

    result = simulate_improvements(baseline_data, params)
    return jsonify(result)

