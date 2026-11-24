"""
services/data_service.py
Central data-access layer.  Loads JSON files from the data/ directory
and provides filtered, summarized views consumed by all route handlers.
"""
from __future__ import annotations
import json
import os
from typing import Any

# Root of the project (parent of services/)
_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_HERE, "..", "data")

# ── In-memory cache (avoids re-reading JSON on every API call) ────────────
_CACHE: dict[str, Any] = {}


# ── I/O ──────────────────────────────────────────────────────────────────────

def load_json(filename: str) -> Any:
    """Load and return parsed JSON from data/<filename>, cached in memory."""
    if filename not in _CACHE:
        path = os.path.join(_DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as fh:
            _CACHE[filename] = json.load(fh)
    return _CACHE[filename]


def clear_cache() -> None:
    """Clear all cached data (useful for testing or data refresh)."""
    _CACHE.clear()


# ── Raw getters (with optional filtering) ────────────────────────────────────

def get_production_records(filters: dict | None = None) -> list[dict]:
    """Return production records, optionally filtered by date/machine/shift."""
    records = load_json("production.json")
    return _apply_filters(records, filters)


def get_machines() -> list[dict]:
    """Return the machines configuration list."""
    return load_json("machines.json")


def get_downtime_events(filters: dict | None = None) -> list[dict]:
    """Return downtime events, optionally filtered."""
    records = load_json("downtime.json")
    return _apply_filters(records, filters)


def get_material_records(filters: dict | None = None) -> list[dict]:
    """Return material records, optionally filtered."""
    records = load_json("material.json")
    return _apply_filters(records, filters)


def get_quality_records(filters: dict | None = None) -> list[dict]:
    """Return quality records, optionally filtered."""
    records = load_json("quality.json")
    return _apply_filters(records, filters)


def get_orders(filters: dict | None = None) -> list[dict]:
    """Return customer orders, optionally filtered."""
    records = load_json("orders.json")
    if not filters:
        return records
    result = records
    if filters.get("status"):
        result = [r for r in result if r.get("status") == filters["status"]]
    if filters.get("priority"):
        result = [r for r in result if r.get("priority") == filters["priority"]]
    if filters.get("is_at_risk") is not None:
        result = [r for r in result if r.get("is_at_risk") == filters["is_at_risk"]]
    return result


def get_config() -> dict:
    """Return the plant configuration dict."""
    data = load_json("config.json")
    return data[0] if isinstance(data, list) else data


# ── Filter helpers ───────────────────────────────────────────────────────────

def _apply_filters(records: list[dict], filters: dict | None) -> list[dict]:
    if not filters:
        return records
    result = records
    if filters.get("start_date") or filters.get("end_date"):
        result = apply_date_filter(result, filters.get("start_date"), filters.get("end_date"))
    if filters.get("machine_ids"):
        result = apply_machine_filter(result, filters["machine_ids"])
    if filters.get("shifts"):
        result = apply_shift_filter(result, filters["shifts"])
    return result


def apply_date_filter(records: list[dict], start_date: str | None, end_date: str | None) -> list[dict]:
    """
    Keep records whose 'date' field falls within [start_date, end_date] inclusive.
    Dates are ISO-8601 strings (YYYY-MM-DD).  None bounds are open.
    """
    out = []
    for r in records:
        d = r.get("date", "")
        if start_date and d < start_date:
            continue
        if end_date and d > end_date:
            continue
        out.append(r)
    return out


def apply_machine_filter(records: list[dict], machine_ids: list[str]) -> list[dict]:
    """Keep only records whose machine_id is in machine_ids."""
    ids = set(machine_ids)
    return [r for r in records if r.get("machine_id") in ids]


def apply_shift_filter(records: list[dict], shifts: list[str]) -> list[dict]:
    """Keep only records whose shift is in shifts."""
    s = set(shifts)
    return [r for r in records if r.get("shift") in s]


# ── Summaries ────────────────────────────────────────────────────────────────

def summarize_production(records: list[dict]) -> dict:
    """
    Aggregate production metrics across a list of records.

    Returns a dict with totals and derived KPIs.
    """
    if not records:
        return {
            "total_planned": 0, "total_actual": 0, "total_good": 0,
            "total_rejected": 0, "achievement_pct": 0, "rejection_rate_pct": 0,
            "total_paper_input_kg": 0, "total_waste_kg": 0, "waste_pct": 0,
            "total_labour_cost": 0, "total_electricity_cost": 0,
            "total_maintenance_cost": 0, "total_cost_inr": 0,
            "cost_per_1000_boxes": 0, "record_count": 0,
        }
    planned   = sum(r.get("planned_output", 0) for r in records)
    actual    = sum(r.get("actual_output", 0) for r in records)
    good      = sum(r.get("good_output", 0) for r in records)
    rejected  = sum(r.get("rejected_output", 0) for r in records)
    paper_in  = sum(r.get("paper_input_kg", 0) for r in records)
    waste     = sum(r.get("waste_kg", 0) for r in records)
    labour    = sum(r.get("labour_cost_inr", 0) for r in records)
    elec      = sum(r.get("electricity_cost_inr", 0) for r in records)
    maint     = sum(r.get("maintenance_cost_inr", 0) for r in records)
    total_cost = labour + elec + maint
    from services.validation import safe_divide
    return {
        "total_planned":        planned,
        "total_actual":         actual,
        "total_good":           good,
        "total_rejected":       rejected,
        "achievement_pct":      round(safe_divide(actual, planned) * 100, 2),
        "rejection_rate_pct":   round(safe_divide(rejected, actual) * 100, 2),
        "total_paper_input_kg": round(paper_in, 2),
        "total_waste_kg":       round(waste, 2),
        "waste_pct":            round(safe_divide(waste, paper_in) * 100, 2),
        "total_labour_cost":    labour,
        "total_electricity_cost": elec,
        "total_maintenance_cost": maint,
        "total_cost_inr":       total_cost,
        "cost_per_1000_boxes":  round(safe_divide(total_cost, good) * 1000, 2),
        "record_count":         len(records),
    }


def summarize_downtime(events: list[dict]) -> dict:
    """
    Aggregate downtime event totals and breakdown by category.

    Returns a dict with total minutes, planned/unplanned split, and
    per-category and per-machine breakdowns.
    """
    if not events:
        return {
            "total_events": 0, "total_minutes": 0,
            "planned_minutes": 0, "unplanned_minutes": 0,
            "by_category": {}, "by_machine": {},
        }
    from collections import defaultdict
    total_min = sum(e.get("duration_minutes", 0) for e in events)
    planned_min = sum(e.get("duration_minutes", 0) for e in events if e.get("is_planned"))
    unplanned_min = total_min - planned_min

    by_cat: dict[str, int] = defaultdict(int)
    by_machine: dict[str, int] = defaultdict(int)
    for e in events:
        by_cat[e.get("category", "Unknown")] += e.get("duration_minutes", 0)
        by_machine[e.get("machine_id", "Unknown")] += e.get("duration_minutes", 0)

    return {
        "total_events":       len(events),
        "total_minutes":      total_min,
        "planned_minutes":    planned_min,
        "unplanned_minutes":  unplanned_min,
        "by_category":        dict(by_cat),
        "by_machine":         dict(by_machine),
    }


def summarize_material(records: list[dict]) -> dict:
    """
    Aggregate material/waste metrics across records.

    Returns totals of paper input, waste sub-categories, and overall yield.
    """
    if not records:
        return {
            "total_paper_input_kg": 0, "total_waste_kg": 0,
            "total_good_output_kg": 0, "waste_pct": 0, "yield_pct": 0,
            "by_paper_type_kg": {}, "record_count": 0,
        }
    paper_in = sum(r.get("paper_input_kg", 0) for r in records)
    waste    = sum(r.get("total_waste_kg", 0) for r in records)
    good_kg  = sum(r.get("good_output_kg", 0) for r in records)
    from collections import defaultdict
    by_type: dict[str, float] = defaultdict(float)
    for r in records:
        by_type[r.get("paper_type", "Unknown")] += r.get("paper_input_kg", 0)
    from services.validation import safe_divide
    return {
        "total_paper_input_kg": round(paper_in, 2),
        "total_waste_kg":       round(waste, 2),
        "total_good_output_kg": round(good_kg, 2),
        "waste_pct":            round(safe_divide(waste, paper_in) * 100, 2),
        "yield_pct":            round(safe_divide(good_kg, paper_in) * 100, 2),
        "by_paper_type_kg":     {k: round(v, 2) for k, v in by_type.items()},
        "record_count":         len(records),
    }


def summarize_quality(records: list[dict]) -> dict:
    """
    Aggregate quality metrics across records.

    Returns total produced, good, rejected, rejection rate, and defect breakdown.
    """
    if not records:
        return {
            "total_produced": 0, "total_good": 0, "total_rejected": 0,
            "rejection_rate_pct": 0,
            "defect_breakdown": {
                "incorrect_dimensions": 0, "poor_printing": 0,
                "weak_adhesive": 0, "damaged_flute": 0,
                "cutting": 0, "folding": 0,
            },
            "record_count": 0,
        }
    produced  = sum(r.get("total_produced", 0) for r in records)
    good      = sum(r.get("good_units", 0) for r in records)
    rejected  = sum(r.get("rejected_units", 0) for r in records)
    defects = {
        "incorrect_dimensions": sum(r.get("defect_incorrect_dimensions", 0) for r in records),
        "poor_printing":        sum(r.get("defect_poor_printing", 0) for r in records),
        "weak_adhesive":        sum(r.get("defect_weak_adhesive", 0) for r in records),
        "damaged_flute":        sum(r.get("defect_damaged_flute", 0) for r in records),
        "cutting":              sum(r.get("defect_cutting", 0) for r in records),
        "folding":              sum(r.get("defect_folding", 0) for r in records),
    }
    from services.validation import safe_divide
    return {
        "total_produced":    produced,
        "total_good":        good,
        "total_rejected":    rejected,
        "rejection_rate_pct": round(safe_divide(rejected, produced) * 100, 2),
        "defect_breakdown":  defects,
        "record_count":      len(records),
    }

