"""
routes/machines.py
Machines blueprint — machine list, individual machine detail, downtime, production.
"""
from flask import Blueprint, render_template, jsonify, request
from services import data_service as ds
from services import kpi_calculator as kpi

machines_bp = Blueprint("machines", __name__)


def _parse_filters() -> dict:
    f: dict = {}
    if request.args.get("start_date"):
        f["start_date"] = request.args["start_date"]
    if request.args.get("end_date"):
        f["end_date"] = request.args["end_date"]
    if request.args.get("shifts"):
        f["shifts"] = request.args["shifts"].split(",")
    return f


@machines_bp.route("/machines")
def machines_page():
    return render_template("machines.html")


@machines_bp.route("/api/machines")
def api_machines():
    machines   = ds.get_machines()
    filters    = _parse_filters()
    prod       = ds.get_production_records(filters)
    plant_data = kpi.aggregate_oee_for_plant(prod)
    result = []
    for m in machines:
        mid = m["id"]
        oee_data = plant_data["machines"].get(mid, {})
        result.append({
            **m,
            "oee":          round(oee_data.get("oee", 0) * 100, 1),
            "availability": round(oee_data.get("availability", 0) * 100, 1),
            "performance":  round(oee_data.get("performance", 0) * 100, 1),
            "quality":      round(oee_data.get("quality", 0) * 100, 1),
        })
    return jsonify(result)


@machines_bp.route("/api/machines/<machine_id>")
def api_machine_detail(machine_id: str):
    machines = ds.get_machines()
    machine  = next((m for m in machines if m["id"] == machine_id), None)
    if not machine:
        return jsonify({"error": f"Machine {machine_id} not found"}), 404
    filters  = _parse_filters()
    filters["machine_ids"] = [machine_id]
    prod     = ds.get_production_records(filters)
    oee_data = kpi.aggregate_oee_for_machine(prod)
    prod_sum = ds.summarize_production(prod)
    return jsonify({
        "machine":    machine,
        "oee":        oee_data,
        "production": prod_sum,
    })


@machines_bp.route("/api/machines/<machine_id>/downtime")
def api_machine_downtime(machine_id: str):
    filters = _parse_filters()
    filters["machine_ids"] = [machine_id]
    events  = ds.get_downtime_events(filters)
    summary = ds.summarize_downtime(events)
    return jsonify({"events": events, "summary": summary})


@machines_bp.route("/api/machines/<machine_id>/production")
def api_machine_production(machine_id: str):
    filters = _parse_filters()
    filters["machine_ids"] = [machine_id]
    records = ds.get_production_records(filters)
    summary = ds.summarize_production(records)
    return jsonify({"records": records, "summary": summary})

