"""
services/validation.py
Utility validation helpers shared across all service modules.
"""
from __future__ import annotations
from typing import Any


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Return numerator / denominator, or *default* when denominator is zero or None."""
    try:
        if denominator is None or denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def validate_non_negative(value: Any, field_name: str) -> float:
    """
    Assert that *value* is a non-negative number.
    Raises ValueError with a descriptive message if not.
    Returns the float value on success.
    """
    if value is None:
        raise ValueError(f"Field '{field_name}' must not be None.")
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Field '{field_name}' must be numeric, got {type(value).__name__}.")
    if v < 0:
        raise ValueError(f"Field '{field_name}' must be non-negative, got {v}.")
    return v


def validate_record(record: dict, required_fields: list[str]) -> list[str]:
    """
    Check that all *required_fields* are present and non-None in *record*.
    Returns a list of missing/null field names (empty list = valid).
    """
    missing = []
    for field in required_fields:
        if field not in record or record[field] is None:
            missing.append(field)
    return missing


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp *value* to the closed interval [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def is_estimate(value: Any) -> bool:
    """
    Return True when *value* is flagged as estimated data.
    Checks for the string sentinel '~' prefix or an 'is_estimate' key
    when value is a dict.
    """
    if isinstance(value, dict):
        return bool(value.get("is_estimate", False))
    if isinstance(value, str):
        return value.startswith("~")
    return False

