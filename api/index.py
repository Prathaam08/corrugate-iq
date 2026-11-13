"""
api/index.py — Vercel serverless entry point for CORRUGATE IQ.
"""
import sys
import os

# Ensure the root project directory is on the Python path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app import app

