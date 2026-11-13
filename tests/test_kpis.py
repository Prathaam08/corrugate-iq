"""
tests/test_kpis.py
Unit tests for all functions in services/kpi_calculator.py.
Covers happy paths, zero values, edge cases, and aggregation logic.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services.kpi_calculator import (
    production_achievement,
    production_gap,
    production_rate,
    machine_availability,
    machine_performance,
    quality_rate,
    calculate_oee,
    paper_waste_percentage,
    material_yield,
    rejection_rate,
    downtime_percentage,
    calculate_mttr,
    calculate_mtbf,
    cost_per_1000_boxes,
    estimated_wastage_cost,
    calculate_production_loss_minutes,
    aggregate_oee_for_machine,
    aggregate_oee_for_plant,
)


# ── production_achievement ────────────────────────────────────────────────────

def test_production_achievement_normal():
    assert production_achievement(800, 1000) == pytest.approx(0.80)

def test_production_achievement_over_production():
    assert production_achievement(1100, 1000) == pytest.approx(1.10)

def test_production_achievement_zero_planned():
    assert production_achievement(500, 0) == 0.0

def test_production_achievement_zero_actual():
    assert production_achievement(0, 1000) == 0.0

def test_production_achievement_perfect():
    assert production_achievement(1000, 1000) == pytest.approx(1.0)


# ── production_gap ────────────────────────────────────────────────────────────

def test_production_gap_normal():
    assert production_gap(1000, 800) == pytest.approx(200)

def test_production_gap_no_gap():
    assert production_gap(1000, 1000) == 0.0

def test_production_gap_over_production():
    assert production_gap(1000, 1100) == 0.0

def test_production_gap_zero_actual():
    assert production_gap(500, 0) == 500.0


# ── production_rate ───────────────────────────────────────────────────────────

def test_production_rate_normal():
    assert production_rate(480, 8) == pytest.approx(60.0)

def test_production_rate_zero_hours():
    assert production_rate(480, 0) == 0.0

def test_production_rate_zero_output():
    assert production_rate(0, 8) == 0.0


# ── machine_availability ──────────────────────────────────────────────────────

def test_availability_normal():
    assert machine_availability(400, 480) == pytest.approx(400/480)

def test_availability_full():
    assert machine_availability(480, 480) == pytest.approx(1.0)

def test_availability_zero_running():
    assert machine_availability(0, 480) == 0.0

def test_availability_zero_planned():
    assert machine_availability(300, 0) == 0.0

def test_availability_clamped():
    # Can't exceed 1.0 even if running > planned
    assert machine_availability(500, 480) == pytest.approx(1.0)


# ── machine_performance ───────────────────────────────────────────────────────

def test_performance_normal():
    assert machine_performance(600, 800) == pytest.approx(0.75)

def test_performance_perfect():
    assert machine_performance(800, 800) == pytest.approx(1.0)

def test_performance_zero_ideal():
    assert machine_performance(600, 0) == 0.0

def test_performance_clamped():
    assert machine_performance(900, 800) == pytest.approx(1.0)


# ── quality_rate ──────────────────────────────────────────────────────────────

def test_quality_rate_normal():
    assert quality_rate(950, 1000) == pytest.approx(0.95)

def test_quality_rate_perfect():
    assert quality_rate(1000, 1000) == pytest.approx(1.0)

def test_quality_rate_zero_total():
    assert quality_rate(0, 0) == 0.0

def test_quality_rate_zero_good():
    assert quality_rate(0, 1000) == 0.0


# ── calculate_oee ─────────────────────────────────────────────────────────────

def test_oee_normal():
    oee = calculate_oee(0.90, 0.85, 0.95)
    assert oee == pytest.approx(0.90 * 0.85 * 0.95)

def test_oee_perfect():
    assert calculate_oee(1.0, 1.0, 1.0) == pytest.approx(1.0)

def test_oee_any_zero():
    assert calculate_oee(0.0, 0.85, 0.95) == 0.0
    assert calculate_oee(0.90, 0.0, 0.95) == 0.0
    assert calculate_oee(0.90, 0.85, 0.0) == 0.0

def test_oee_clamped():
    assert calculate_oee(1.1, 1.0, 1.0) == pytest.approx(1.0)


# ── paper_waste_percentage ────────────────────────────────────────────────────

def test_waste_pct_normal():
    assert paper_waste_percentage(50, 1000) == pytest.approx(5.0)

def test_waste_pct_zero_input():
    assert paper_waste_percentage(50, 0) == 0.0

def test_waste_pct_no_waste():
    assert paper_waste_percentage(0, 1000) == 0.0


# ── material_yield ────────────────────────────────────────────────────────────

def test_yield_normal():
    assert material_yield(950, 1000) == pytest.approx(95.0)

def test_yield_plus_waste_sums_to_100():
    waste = paper_waste_percentage(50, 1000)
    yld   = material_yield(950, 1000)
    assert waste + yld == pytest.approx(100.0)


# ── rejection_rate ────────────────────────────────────────────────────────────

def test_rejection_rate_normal():
    assert rejection_rate(20, 1000) == pytest.approx(2.0)

def test_rejection_rate_zero_total():
    assert rejection_rate(5, 0) == 0.0

def test_rejection_rate_no_rejections():
    assert rejection_rate(0, 1000) == 0.0


# ── downtime_percentage ───────────────────────────────────────────────────────

def test_downtime_pct_normal():
    assert downtime_percentage(48, 480) == pytest.approx(10.0)

def test_downtime_pct_no_downtime():
    assert downtime_percentage(0, 480) == 0.0


# ── calculate_mttr ────────────────────────────────────────────────────────────

def test_mttr_normal():
    assert calculate_mttr(300, 5) == pytest.approx(60.0)

def test_mttr_zero_repairs():
    assert calculate_mttr(300, 0) == 0.0


# ── calculate_mtbf ────────────────────────────────────────────────────────────

def test_mtbf_normal():
    assert calculate_mtbf(1200, 4) == pytest.approx(300.0)

def test_mtbf_zero_failures():
    assert calculate_mtbf(1200, 0) == 0.0


# ── cost_per_1000_boxes ───────────────────────────────────────────────────────

def test_cost_per_1000_normal():
    assert cost_per_1000_boxes(5000, 1000) == pytest.approx(5000.0)

def test_cost_per_1000_zero_boxes():
    assert cost_per_1000_boxes(5000, 0) == 0.0


# ── estimated_wastage_cost ────────────────────────────────────────────────────

def test_wastage_cost():
    assert estimated_wastage_cost(100, 42) == pytest.approx(4200.0)

def test_wastage_cost_zero():
    assert estimated_wastage_cost(0, 42) == 0.0


# ── calculate_production_loss_minutes ────────────────────────────────────────

def test_loss_minutes_normal():
    # gap = 200 boxes at 100 boxes/hr = 2 hrs = 120 min
    assert calculate_production_loss_minutes(1000, 800, 100) == pytest.approx(120.0)

def test_loss_minutes_no_gap():
    assert calculate_production_loss_minutes(1000, 1000, 100) == 0.0

def test_loss_minutes_over_production():
    assert calculate_production_loss_minutes(1000, 1200, 100) == 0.0

def test_loss_minutes_zero_speed():
    assert calculate_production_loss_minutes(1000, 800, 0) == 0.0


# ── aggregate_oee_for_machine ─────────────────────────────────────────────────

SAMPLE_RECORDS = [
    {"running_time_minutes": 420, "planned_time_minutes": 480,
     "actual_output": 800, "ideal_speed": 120, "good_output": 760},
    {"running_time_minutes": 400, "planned_time_minutes": 480,
     "actual_output": 750, "ideal_speed": 120, "good_output": 720},
]

def test_aggregate_oee_machine_keys():
    result = aggregate_oee_for_machine(SAMPLE_RECORDS)
    for key in ("availability", "performance", "quality", "oee",
                "total_running_min", "total_planned_min", "total_actual", "total_good"):
        assert key in result

def test_aggregate_oee_machine_values():
    result = aggregate_oee_for_machine(SAMPLE_RECORDS)
    assert 0 <= result["oee"] <= 1
    assert 0 <= result["availability"] <= 1
    assert 0 <= result["performance"] <= 1
    assert 0 <= result["quality"] <= 1

def test_aggregate_oee_empty():
    result = aggregate_oee_for_machine([])
    assert result["oee"] == 0.0

def test_aggregate_oee_plant():
    records = [
        {**r, "machine_id": "COR-001"} for r in SAMPLE_RECORDS
    ] + [
        {**r, "machine_id": "FLX-001"} for r in SAMPLE_RECORDS
    ]
    result = aggregate_oee_for_plant(records)
    assert "plant_oee" in result
    assert "machines" in result
    assert "COR-001" in result["machines"]
    assert "FLX-001" in result["machines"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

