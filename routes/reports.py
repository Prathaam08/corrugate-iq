"""
routes/reports.py
Reports blueprint — renders the reports page and provides CSV and Excel (.xlsx) export endpoints.
"""
import csv
import io
from flask import Blueprint, render_template, Response, request
from services import data_service as ds

reports_bp = Blueprint("reports", __name__)


def _parse_filters() -> dict:
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


def _to_csv(records: list[dict], filename: str) -> Response:
    if not records:
        return Response("No data", mimetype="text/plain")
    si = io.StringIO()
    writer = csv.DictWriter(si, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _to_excel(records: list[dict], filename: str) -> Response:
    if not records:
        return Response("No data", mimetype="text/plain")
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    ws = wb.active
    ws.title = "Report"

    headers = list(records[0].keys())
    ws.append(headers)

    header_fill = PatternFill(start_color="1A1D2E", end_color="1A1D2E", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for r in records:
        ws.append(list(r.values()))

    # Auto-fit column widths with padding so dates and numbers are fully visible
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 5, 14)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@reports_bp.route("/reports")
def reports_page():
    return render_template("reports.html")


# ── CSV Exports ───────────────────────────────────────────────────────────────

@reports_bp.route("/api/export/production")
def export_production():
    return _to_csv(ds.get_production_records(_parse_filters()), "production.csv")


@reports_bp.route("/api/export/downtime")
def export_downtime():
    return _to_csv(ds.get_downtime_events(_parse_filters()), "downtime.csv")


@reports_bp.route("/api/export/material")
def export_material():
    return _to_csv(ds.get_material_records(_parse_filters()), "material.csv")


@reports_bp.route("/api/export/quality")
def export_quality():
    return _to_csv(ds.get_quality_records(_parse_filters()), "quality.csv")


# ── Excel (.xlsx) Exports ─────────────────────────────────────────────────────

@reports_bp.route("/api/export/production/excel")
def export_production_excel():
    return _to_excel(ds.get_production_records(_parse_filters()), "production.xlsx")


@reports_bp.route("/api/export/downtime/excel")
def export_downtime_excel():
    return _to_excel(ds.get_downtime_events(_parse_filters()), "downtime.xlsx")


@reports_bp.route("/api/export/material/excel")
def export_material_excel():
    return _to_excel(ds.get_material_records(_parse_filters()), "material.xlsx")


@reports_bp.route("/api/export/quality/excel")
def export_quality_excel():
    return _to_excel(ds.get_quality_records(_parse_filters()), "quality.xlsx")
