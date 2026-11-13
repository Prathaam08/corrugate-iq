# CORRUGATE IQ — Industrial Analytics Dashboard

An industrial analytics dashboard for paper corrugation and corrugated cardboard box manufacturing.

## Features
- OEE (Overall Equipment Effectiveness) tracking across 6 machines
- 30-day production trend analysis
- Downtime Pareto analysis
- Paper waste & material yield tracking
- Quality & rejection rate monitoring
- Customer order status with delay risk flagging
- Rule-based insight engine (8 actionable rules)
- What-if simulator for improvement scenarios
- CSV export for all datasets

## Setup

```bash
pip install -r requirements.txt
python app.py
```

App runs on http://localhost:5000

## Project Structure

```
corrugate-iq/
  app.py              — Flask entry point
  requirements.txt
  data/               — JSON datasets (30-day, 6 machines)
  services/           — KPI calculator, insights engine, simulator
  routes/             — Flask blueprints
  templates/          — Jinja2 HTML templates
  static/             — CSS + JS
  tests/              — Unit tests
```

## Key Machines
| ID      | Type                    | Role          |
|---------|-------------------------|---------------|
| COR-001 | Corrugation (3/5-ply)   | Star performer|
| COR-002 | Corrugation (5/7-ply)   | Breakdown-prone|
| FLX-001 | Flexo Printer           | Speed-limited |
| SLT-001 | Slotter/Die Cutter      | Good performer|
| FLD-001 | Folder Gluer            | Good performer|
| SHT-001 | Sheet Cutter/Slitter    | Good performer|

## Insight Rules
1. HIGH_WASTE — plant waste > 5%
2. LOW_OEE_MACHINE — machine OEE < 60%
3. RECURRING_BREAKDOWN — machine > 5 mechanical breakdowns
4. LOW_PERFORMANCE — machine performance < 70%
5. HIGH_REJECTION — rejection rate > 2%
6. ORDER_AT_RISK — order >15% behind schedule
7. SHIFT_WASTE — shift waste above plant average
8. HIGH_CHANGEOVER — changeover >20% of machine downtime

