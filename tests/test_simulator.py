"""
tests/test_simulator.py
Unit tests for services/simulator.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services.simulator import simulate_improvements

BASELINE = {
    "total_planned":              500000,
    "total_actual":               380000,
    "total_good":                 362000,
    "total_rejected":             18000,
    "total_paper_input_kg":       850000,
    "total_waste_kg":             60000,
    "total_cost_inr":             12000000,
    "planned_time_minutes":       259200,   # 6 machines * 480 min/shift * 90 shifts
    "unplanned_downtime_minutes": 25000,
    "ideal_speed_boxes_per_hour": 100,
    "paper_rate_inr_per_kg":      38,
    "rejection_rate_pct":         4.74,
    "waste_pct":                  7.06,
    "oee":                        0.62,
}

ZERO_PARAMS = {
    "downtime_reduction_pct":  0,
    "waste_reduction_pct":     0,
    "rejection_reduction_pct": 0,
    "speed_improvement_pct":   0,
}

MODERATE_PARAMS = {
    "downtime_reduction_pct":  30,
    "waste_reduction_pct":     20,
    "rejection_reduction_pct": 40,
    "speed_improvement_pct":   10,
}

AGGRESSIVE_PARAMS = {
    "downtime_reduction_pct":  80,
    "waste_reduction_pct":     60,
    "rejection_reduction_pct": 80,
    "speed_improvement_pct":   50,
}


# ── Structure tests ───────────────────────────────────────────────────────────

def test_result_has_required_keys():
    result = simulate_improvements(BASELINE, ZERO_PARAMS)
    for key in ("baseline", "simulated", "delta", "assumptions", "caveats", "params_applied"):
        assert key in result

def test_baseline_keys():
    result = simulate_improvements(BASELINE, ZERO_PARAMS)
    for key in ("total_actual_boxes", "total_good_boxes", "total_waste_kg",
                "total_cost_inr", "oee", "rejection_rate_pct"):
        assert key in result["baseline"]

def test_simulated_keys():
    result = simulate_improvements(BASELINE, ZERO_PARAMS)
    for key in ("total_actual_boxes", "total_good_boxes", "total_waste_kg",
                "total_cost_inr", "oee", "rejection_rate_pct"):
        assert key in result["simulated"]

def test_delta_has_abs_pct():
    result = simulate_improvements(BASELINE, MODERATE_PARAMS)
    assert "abs" in result["delta"]["total_actual_boxes"]
    assert "pct" in result["delta"]["total_actual_boxes"]

def test_assumptions_non_empty():
    result = simulate_improvements(BASELINE, ZERO_PARAMS)
    assert len(result["assumptions"]) > 0

def test_caveats_non_empty():
    result = simulate_improvements(BASELINE, ZERO_PARAMS)
    assert len(result["caveats"]) > 0


# ── Zero params: simulated ≈ baseline ────────────────────────────────────────

def test_zero_params_actual_unchanged():
    result = simulate_improvements(BASELINE, ZERO_PARAMS)
    # With all zeros: extra from dt=0, extra from speed=0 → actual stays same
    assert result["simulated"]["total_actual_boxes"] == pytest.approx(
        result["baseline"]["total_actual_boxes"], rel=0.01)

def test_zero_params_waste_unchanged():
    result = simulate_improvements(BASELINE, ZERO_PARAMS)
    assert result["simulated"]["total_waste_kg"] == pytest.approx(
        result["baseline"]["total_waste_kg"], rel=0.05)


# ── Moderate params: improvements are positive ────────────────────────────────

def test_moderate_params_actual_increases():
    result = simulate_improvements(BASELINE, MODERATE_PARAMS)
    assert result["simulated"]["total_actual_boxes"] > result["baseline"]["total_actual_boxes"]

def test_moderate_params_good_increases():
    result = simulate_improvements(BASELINE, MODERATE_PARAMS)
    assert result["simulated"]["total_good_boxes"] > result["baseline"]["total_good_boxes"]

def test_moderate_params_waste_decreases():
    result = simulate_improvements(BASELINE, MODERATE_PARAMS)
    assert result["simulated"]["total_waste_kg"] < result["baseline"]["total_waste_kg"]

def test_moderate_params_oee_increases():
    result = simulate_improvements(BASELINE, MODERATE_PARAMS)
    assert result["simulated"]["oee"] >= result["baseline"]["oee"]

def test_moderate_params_rejection_rate_decreases():
    result = simulate_improvements(BASELINE, MODERATE_PARAMS)
    assert result["simulated"]["rejection_rate_pct"] < result["baseline"]["rejection_rate_pct"]


# ── OEE bounds ────────────────────────────────────────────────────────────────

def test_oee_clamped_to_one():
    result = simulate_improvements(BASELINE, AGGRESSIVE_PARAMS)
    assert result["simulated"]["oee"] <= 1.0

def test_oee_non_negative():
    result = simulate_improvements(BASELINE, AGGRESSIVE_PARAMS)
    assert result["simulated"]["oee"] >= 0.0


# ── Param clamping ────────────────────────────────────────────────────────────

def test_over_100_params_clamped():
    params = {
        "downtime_reduction_pct":  200,
        "waste_reduction_pct":     150,
        "rejection_reduction_pct": 110,
        "speed_improvement_pct":   999,
    }
    result = simulate_improvements(BASELINE, params)
    # Speed capped at 50%
    assert result["params_applied"]["speed_improvement_pct"] == pytest.approx(50.0)
    assert result["simulated"]["oee"] <= 1.0

def test_negative_params_treated_as_zero():
    params = {
        "downtime_reduction_pct":  -10,
        "waste_reduction_pct":     -5,
        "rejection_reduction_pct": -20,
        "speed_improvement_pct":   -15,
    }
    result = simulate_improvements(BASELINE, params)
    assert result["params_applied"]["downtime_reduction_pct"]  == 0.0
    assert result["params_applied"]["waste_reduction_pct"]     == 0.0


# ── Empty / zero baseline ─────────────────────────────────────────────────────

def test_empty_baseline():
    result = simulate_improvements({}, MODERATE_PARAMS)
    assert result["simulated"]["total_actual_boxes"] >= 0

def test_zero_baseline():
    zero = {k: 0 for k in BASELINE}
    result = simulate_improvements(zero, MODERATE_PARAMS)
    assert result["simulated"]["total_actual_boxes"] == 0
    assert result["simulated"]["total_waste_kg"]     == 0

def test_financial_saving_reported():
    result = simulate_improvements(BASELINE, MODERATE_PARAMS)
    assert "waste_saving_inr" in result["delta"]

def test_params_applied_in_result():
    result = simulate_improvements(BASELINE, MODERATE_PARAMS)
    pa = result["params_applied"]
    assert pa["downtime_reduction_pct"]  == pytest.approx(30.0)
    assert pa["waste_reduction_pct"]     == pytest.approx(20.0)
    assert pa["rejection_reduction_pct"] == pytest.approx(40.0)
    assert pa["speed_improvement_pct"]   == pytest.approx(10.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

