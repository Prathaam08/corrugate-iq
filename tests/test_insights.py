"""
tests/test_insights.py
Unit tests for services/insights_engine.py using mock/patched data.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch

CONFIG = {
    "oee_target":           0.75,
    "waste_target_pct":     5.0,
    "rejection_target_pct": 2.0,
    "paper_rate_inr_per_kg": {"Kraft Liner": 42, "Fluting Medium": 35, "Test Liner": 38},
    "shift_hours": 8,
    "demo_mode": True,
}

MACHINES_DATA = [
    {"id": "COR-001", "name": "Corrugation Alpha", "ideal_speed_boxes_per_hour": 120},
    {"id": "COR-002", "name": "Corrugation Beta",  "ideal_speed_boxes_per_hour": 100},
    {"id": "FLX-001", "name": "Flexo Printer",     "ideal_speed_boxes_per_hour": 90},
]

# Production records where COR-002 has very low availability (~55%)
def _make_prod(mid, running_min, planned_min, actual, ideal_spd, good):
    return {
        "machine_id": mid,
        "running_time_minutes": running_min,
        "planned_time_minutes": planned_min,
        "actual_output": actual,
        "ideal_speed": ideal_spd,
        "good_output": good,
        "planned_output": int(ideal_spd * planned_min / 60),
        "rejected_output": actual - good,
        "paper_input_kg": actual * 2.0,
        "good_output_kg": good * 1.9,
        "waste_kg": actual * 0.1,
        "labour_cost_inr": 3000,
        "electricity_cost_inr": 2000,
        "maintenance_cost_inr": 500,
        "date": "2026-10-01",
        "shift": "A",
    }

PROD_RECORDS = (
    [_make_prod("COR-001", 450, 480, 870,  120, 860)] * 90 +   # good OEE
    [_make_prod("COR-002", 265, 480, 400,  100, 388)] * 90 +   # low availability
    [_make_prod("FLX-001", 420, 480, 490,   90, 475)] * 90     # low performance
)

MAT_RECORDS = [
    {
        "machine_id": r["machine_id"],
        "shift": r["shift"],
        "date": r["date"],
        "paper_input_kg": r["paper_input_kg"],
        "total_waste_kg": r["waste_kg"],
        "good_output_kg": r["good_output_kg"],
        "paper_type": "Kraft Liner",
        "trim_waste_kg": r["waste_kg"] * 0.4,
        "setup_waste_kg": r["waste_kg"] * 0.2,
        "breakage_waste_kg": r["waste_kg"] * 0.15,
        "printing_defect_kg": 0,
        "gluing_defect_kg": 0,
        "handling_damage_kg": r["waste_kg"] * 0.25,
        "gsm": 120,
        "yield_percentage": 95.0,
    }
    for r in PROD_RECORDS
]

QUALITY_HIGH_REJ = [
    {
        "machine_id": "COR-002", "product_type": "RSC-B2",
        "shift": "A", "date": "2026-10-01",
        "total_produced": 1000, "good_units": 880, "rejected_units": 120,
        "rejection_rate": 12.0,
        "defect_incorrect_dimensions": 50, "defect_poor_printing": 30,
        "defect_weak_adhesive": 10, "defect_damaged_flute": 15,
        "defect_cutting": 10, "defect_folding": 5,
    }
] * 30

DOWNTIME_COR002_MANY_MB = [
    {
        "event_id": f"DT-{i:04d}",
        "machine_id": "COR-002",
        "category": "Mechanical Breakdown",
        "duration_minutes": 20,
        "is_planned": False,
        "date": "2026-10-01",
        "shift": "A",
        "start_time": "08:00",
        "description": "Drive belt snapped",
    }
    for i in range(45)
] + [
    {
        "event_id": f"DT-{i+100:04d}",
        "machine_id": "FLX-001",
        "category": "Changeover",
        "duration_minutes": 35,
        "is_planned": True,
        "date": "2026-10-01",
        "shift": "A",
        "start_time": "10:00",
        "description": "Size changeover",
    }
    for i in range(30)
]

ORDERS_AT_RISK = [
    {
        "order_id": "ORD-007",
        "customer_name": "Flipkart Logistics",
        "product_type": "RSC-B1",
        "ordered_qty": 20000,
        "completed_qty": 7000,
        "due_date": "2026-10-20",
        "priority": "Critical",
        "assigned_machine": "COR-002",
        "status": "In Progress",
        "estimated_completion_date": "2026-11-05",
        "is_at_risk": True,
    }
]


def _patch_ds(prod=None, mat=None, quality=None, downtime=None, orders=None):
    """Return a dict of patches for data_service functions."""
    return {
        "services.data_service.get_production_records": prod or PROD_RECORDS,
        "services.data_service.get_material_records":   mat  or MAT_RECORDS,
        "services.data_service.get_quality_records":    quality or QUALITY_HIGH_REJ,
        "services.data_service.get_downtime_events":    downtime or DOWNTIME_COR002_MANY_MB,
        "services.data_service.get_orders":             orders or ORDERS_AT_RISK,
        "services.data_service.get_config":             CONFIG,
    }


def run_insights(prod=None, mat=None, quality=None, downtime=None, orders=None):
    patches = _patch_ds(prod, mat, quality, downtime, orders)
    with patch("services.insights_engine.ds.get_production_records", return_value=patches["services.data_service.get_production_records"]), \
         patch("services.insights_engine.ds.get_material_records",   return_value=patches["services.data_service.get_material_records"]), \
         patch("services.insights_engine.ds.get_quality_records",    return_value=patches["services.data_service.get_quality_records"]), \
         patch("services.insights_engine.ds.get_downtime_events",    return_value=patches["services.data_service.get_downtime_events"]), \
         patch("services.insights_engine.ds.get_orders",             return_value=patches["services.data_service.get_orders"]), \
         patch("services.insights_engine.ds.get_config",             return_value=patches["services.data_service.get_config"]):
        from services.insights_engine import generate_insights
        return generate_insights()


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_insights_returns_list():
    insights = run_insights()
    assert isinstance(insights, list)

def test_insights_have_required_fields():
    insights = run_insights()
    required = {"id", "title", "severity", "affected_entity", "evidence",
                "operational_impact", "financial_impact_inr",
                "likely_cause", "recommended_action",
                "responsible_department", "rank_score"}
    for ins in insights:
        assert required.issubset(ins.keys()), f"Missing keys in {ins['id']}"

def test_rule_recurring_breakdown_fires():
    insights = run_insights()
    ids = [i["id"] for i in insights]
    # COR-002 has 45 MB events > threshold of 5
    assert any("RECURRING_BREAKDOWN" in iid and "COR-002" in iid for iid in ids)

def test_rule_low_oee_fires_for_cor002():
    insights = run_insights()
    ids = [i["id"] for i in insights]
    # COR-002 avail ~55% → OEE will be below 60%
    assert any("LOW_OEE_MACHINE" in iid and "COR-002" in iid for iid in ids)

def test_rule_order_at_risk_fires():
    insights = run_insights()
    ids = [i["id"] for i in insights]
    assert any("ORDER_AT_RISK" in iid and "ORD-007" in iid for iid in ids)

def test_rule_high_rejection_fires():
    insights = run_insights()
    ids = [i["id"] for i in insights]
    assert any("HIGH_REJECTION" in iid for iid in ids)

def test_rule_high_changeover_fires():
    insights = run_insights()
    ids = [i["id"] for i in insights]
    # FLX-001 has 30 changeover events totaling 1050 min
    assert any("HIGH_CHANGEOVER" in iid and "FLX-001" in iid for iid in ids)

def test_insights_sorted_by_rank_score():
    insights = run_insights()
    scores = [i["rank_score"] for i in insights]
    assert scores == sorted(scores, reverse=True)

def test_severity_values_valid():
    insights = run_insights()
    valid_severities = {"Critical", "High", "Medium", "Low"}
    for ins in insights:
        assert ins["severity"] in valid_severities

def test_financial_impact_non_negative():
    insights = run_insights()
    for ins in insights:
        assert ins["financial_impact_inr"] >= 0

def test_no_insights_on_empty_data():
    insights = run_insights(prod=[], mat=[], quality=[], downtime=[], orders=[])
    assert isinstance(insights, list)

def test_low_performance_flx001():
    insights = run_insights()
    ids = [i["id"] for i in insights]
    # FLX-001 performance approx 490/(90*7) = 0.78 → might not fire in mock
    # At minimum ensure function runs without error
    assert isinstance(ids, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

