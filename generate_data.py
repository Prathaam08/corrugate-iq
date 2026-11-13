"""
Data generator for CORRUGATE IQ dashboard.
Run once to produce all JSON datasets in the data/ directory.
"""
import json, random, math
from datetime import date, timedelta

random.seed(42)

BASE = r"c:\Users\Shravani Mankar\Downloads\dashboard\corrugate-iq\data"

# ── helpers ──────────────────────────────────────────────────────────────────
def jdump(obj, name):
    with open(f"{BASE}\\{name}", "w") as f:
        json.dump(obj, f, indent=2)
    print(f"  wrote {name}  ({len(obj) if isinstance(obj,list) else 1} records)")

def rnd(lo, hi): return round(random.uniform(lo, hi), 2)
def rndint(lo, hi): return random.randint(lo, hi)

DAYS = [date(2026, 10, d) for d in range(1, 31)]
SHIFTS = ["A", "B", "C"]

# ── machines.json ─────────────────────────────────────────────────────────────
machines = [
    {"id":"COR-001","name":"Corrugation Machine Alpha","type":"Corrugation Machine",
     "ply_options":["3-ply","5-ply"],"ideal_speed_boxes_per_hour":120,
     "planned_hours_per_day":24,"shifts":3,"paper_rate_inr_per_kg":42,
     "status":"operational","location":"Line 1","year_installed":2019},
    {"id":"COR-002","name":"Corrugation Machine Beta","type":"Corrugation Machine",
     "ply_options":["5-ply","7-ply"],"ideal_speed_boxes_per_hour":100,
     "planned_hours_per_day":24,"shifts":3,"paper_rate_inr_per_kg":42,
     "status":"maintenance","location":"Line 2","year_installed":2015},
    {"id":"FLX-001","name":"Flexo Printer Unit 1","type":"Flexo Printer",
     "ply_options":["3-ply","5-ply","7-ply"],"ideal_speed_boxes_per_hour":90,
     "planned_hours_per_day":24,"shifts":3,"paper_rate_inr_per_kg":38,
     "status":"operational","location":"Print Bay","year_installed":2018},
    {"id":"SLT-001","name":"Slotter Die Cutter 1","type":"Slotter/Die Cutter",
     "ply_options":["3-ply","5-ply"],"ideal_speed_boxes_per_hour":110,
     "planned_hours_per_day":24,"shifts":3,"paper_rate_inr_per_kg":38,
     "status":"operational","location":"Cutting Bay","year_installed":2020},
    {"id":"FLD-001","name":"Folder Gluer 1","type":"Folder Gluer",
     "ply_options":["3-ply","5-ply"],"ideal_speed_boxes_per_hour":95,
     "planned_hours_per_day":24,"shifts":3,"paper_rate_inr_per_kg":35,
     "status":"operational","location":"Finishing Bay","year_installed":2021},
    {"id":"SHT-001","name":"Sheet Cutter Slitter 1","type":"Sheet Cutter/Slitter",
     "ply_options":["3-ply","5-ply","7-ply"],"ideal_speed_boxes_per_hour":130,
     "planned_hours_per_day":24,"shifts":3,"paper_rate_inr_per_kg":35,
     "status":"operational","location":"Slitting Bay","year_installed":2022},
]
jdump(machines, "machines.json")

# ── machine profiles ──────────────────────────────────────────────────────────
# availability ~ running_time / planned_time
# performance  ~ actual / (ideal_speed * running_hours)
# quality      ~ good / actual
PROFILES = {
    # avail_lo, avail_hi, perf_lo, perf_hi, qual_lo, qual_hi, waste_factor
    "COR-001": (0.90, 0.96, 0.88, 0.95, 0.97, 0.99, 1.0),
    "COR-002": (0.50, 0.62, 0.78, 0.88, 0.95, 0.98, 1.1),
    "FLX-001": (0.80, 0.90, 0.60, 0.70, 0.95, 0.98, 1.05),
    "SLT-001": (0.85, 0.93, 0.82, 0.90, 0.88, 0.95, 1.0),  # higher rejection on RSC-B2 handled separately
    "FLD-001": (0.86, 0.94, 0.83, 0.92, 0.96, 0.99, 1.0),
    "SHT-001": (0.88, 0.95, 0.85, 0.93, 0.97, 0.99, 0.98),
}
IDEAL_SPEEDS = {m["id"]: m["ideal_speed_boxes_per_hour"] for m in machines}

PAPER_TYPES = ["Kraft Liner","Fluting Medium","Test Liner"]
PRODUCTS = ["RSC-B1","RSC-B2","HSC-A1","FOL-C1","DIE-D1","TEL-E1"]

# ── production.json ───────────────────────────────────────────────────────────
production = []
rec_id = 1
for day in DAYS:
    for shift in SHIFTS:
        for m in machines:
            mid = m["id"]
            al, ah, pl, ph, ql, qh, wf = PROFILES[mid]
            planned_min = 480  # 8 hours per shift
            avail = rnd(al, ah)
            running_min = round(planned_min * avail)
            running_hr = running_min / 60
            ideal_spd = IDEAL_SPEEDS[mid]
            perf = rnd(pl, ph)
            actual_out = max(0, int(ideal_spd * running_hr * perf))
            qual = rnd(ql, qh)
            # Shift C: higher waste
            shift_waste_factor = 1.17 if shift == "C" else 1.0
            kg_per_box = rnd(1.5, 2.5)
            paper_input = round(actual_out * kg_per_box * wf * shift_waste_factor, 1)
            waste_rate = rnd(0.04, 0.08) * wf * shift_waste_factor
            waste_kg = round(paper_input * waste_rate, 1)
            good_kg = round(paper_input - waste_kg, 1)
            good_out = int(actual_out * qual)
            rejected = actual_out - good_out
            planned_out = int(ideal_spd * (planned_min / 60))
            labour = round(rnd(2500, 4000), 0)
            elec   = round(rnd(1800, 3200), 0)
            maint  = round(rnd(200, 800) * (2.0 if mid == "COR-002" else 1.0), 0)
            production.append({
                "record_id": f"PR-{rec_id:04d}",
                "date": day.isoformat(),
                "shift": shift,
                "machine_id": mid,
                "planned_output": planned_out,
                "actual_output": actual_out,
                "good_output": good_out,
                "rejected_output": rejected,
                "planned_time_minutes": planned_min,
                "running_time_minutes": running_min,
                "ideal_speed": ideal_spd,
                "paper_input_kg": paper_input,
                "good_output_kg": good_kg,
                "waste_kg": waste_kg,
                "labour_cost_inr": labour,
                "electricity_cost_inr": elec,
                "maintenance_cost_inr": maint,
            })
            rec_id += 1
jdump(production, "production.json")

# ── downtime.json ─────────────────────────────────────────────────────────────
downtime = []
ev_id = 1

CATEGORIES = ["Mechanical Breakdown","Electrical Failure","Paper Breakage",
               "Changeover","Material Shortage","Planned Maintenance","Operator Stoppage"]

DESCRIPTIONS = {
    "Mechanical Breakdown": ["Drive belt snapped","Gear box failure","Bearing seized",
                              "Hydraulic pump failure","Chain drive broken","Roller misalignment"],
    "Electrical Failure":   ["Panel short circuit","Sensor malfunction","VFD tripped",
                              "PLC fault","Motor overcurrent","Wiring fault"],
    "Paper Breakage":       ["Web break at splicing","Moisture in reel","Paper jam",
                              "Reel defect from supplier","Tension control failure"],
    "Changeover":           ["Flute profile change","Size changeover","Ink colour change",
                              "Order changeover","Die change","Ply configuration change"],
    "Material Shortage":    ["Starch supply delayed","Liner reel exhausted",
                              "Medium reel not available","Ink stock out"],
    "Planned Maintenance":  ["Preventive maintenance","Lubrication schedule",
                              "Blade replacement","Roll cleaning","Calibration"],
    "Operator Stoppage":    ["Meal break overrun","Toilet break","Training pause",
                              "Safety inspection","Handover delay"],
}

PLANNED_CATS = {"Planned Maintenance","Changeover"}

def add_event(date_obj, shift, mid, category, dur_min, start_hr=None):
    global ev_id
    if start_hr is None:
        sh_base = {"A":6,"B":14,"C":22}[shift]
        start_hr = sh_base + rndint(0, 6)
    desc = random.choice(DESCRIPTIONS[category])
    downtime.append({
        "event_id": f"DT-{ev_id:04d}",
        "date": date_obj.isoformat(),
        "shift": shift,
        "machine_id": mid,
        "start_time": f"{start_hr % 24:02d}:{rndint(0,59):02d}",
        "duration_minutes": dur_min,
        "category": category,
        "description": desc,
        "is_planned": category in PLANNED_CATS,
    })
    ev_id += 1

# COR-002: 40+ Mechanical Breakdown events totaling 800+ minutes
cor002_mb_count = 0
for day in DAYS:
    if rnd(0,1) < 0.70:          # ~70% of days have at least 1 breakdown
        n = rndint(1, 3)
        for _ in range(n):
            sh = random.choice(SHIFTS)
            dur = rndint(15, 60)
            add_event(day, sh, "COR-002", "Mechanical Breakdown", dur)
            cor002_mb_count += 1
    # Planned maintenance weekly
    if day.weekday() == 5:
        add_event(day, "A", "COR-002", "Planned Maintenance", 60)

# FLX-001: Many Changeover events
for day in DAYS:
    n = rndint(1, 3)
    for _ in range(n):
        sh = random.choice(SHIFTS)
        add_event(day, sh, "FLX-001", "Changeover", rndint(20, 50))
    if rnd(0,1) < 0.3:
        sh = random.choice(SHIFTS)
        add_event(day, sh, "FLX-001", "Paper Breakage", rndint(10, 30))

# Other machines: mixed events
for day in DAYS:
    for mid in ["COR-001","SLT-001","FLD-001","SHT-001"]:
        if rnd(0,1) < 0.40:
            sh = random.choice(SHIFTS)
            cat = random.choices(CATEGORIES, weights=[1,1,2,3,1,2,1])[0]
            dur = rndint(10, 45)
            add_event(day, sh, mid, cat, dur)
    # COR-001 planned maintenance Saturdays
    if day.weekday() == 5:
        add_event(day, "A", "COR-001", "Planned Maintenance", 30)

# Extra unplanned events across all machines to reach ~200 total
while ev_id < 200:
    day = random.choice(DAYS)
    mid = random.choice([m["id"] for m in machines])
    sh  = random.choice(SHIFTS)
    cat = random.choices(CATEGORIES, weights=[2,2,3,2,1,1,2])[0]
    dur = rndint(5, 40)
    add_event(day, sh, mid, cat, dur)

jdump(downtime, "downtime.json")

# ── material.json ─────────────────────────────────────────────────────────────
material = []
mat_id = 1
for day in DAYS:
    for shift in SHIFTS:
        for m in machines:
            mid = m["id"]
            # Find matching production record
            prod_rec = next((p for p in production
                             if p["date"]==day.isoformat()
                             and p["shift"]==shift
                             and p["machine_id"]==mid), None)
            if not prod_rec:
                continue
            paper_in = prod_rec["paper_input_kg"]
            waste_total = prod_rec["waste_kg"]
            good_kg = prod_rec["good_output_kg"]
            # distribute waste sub-categories
            trim = round(waste_total * rnd(0.30, 0.45), 2)
            setup = round(waste_total * rnd(0.10, 0.20), 2)
            breakage = round(waste_total * rnd(0.08, 0.18), 2)
            printing_def = round(waste_total * rnd(0.05, 0.15) if mid=="FLX-001" else rnd(0.0,0.02)*waste_total, 2)
            gluing_def   = round(waste_total * rnd(0.03, 0.10) if mid=="FLD-001" else rnd(0.0,0.02)*waste_total, 2)
            handling_dmg = round(max(0, waste_total - trim - setup - breakage - printing_def - gluing_def), 2)
            paper_type = random.choices(PAPER_TYPES, weights=[0.5,0.3,0.2])[0]
            gsm = random.choice([100,110,120,140,150,180,200])
            yld = round(good_kg / paper_in * 100, 2) if paper_in > 0 else 0
            material.append({
                "record_id": f"MT-{mat_id:04d}",
                "date": day.isoformat(),
                "shift": shift,
                "machine_id": mid,
                "paper_type": paper_type,
                "gsm": gsm,
                "paper_input_kg": paper_in,
                "trim_waste_kg": trim,
                "setup_waste_kg": setup,
                "breakage_waste_kg": breakage,
                "printing_defect_kg": printing_def,
                "gluing_defect_kg": gluing_def,
                "handling_damage_kg": handling_dmg,
                "total_waste_kg": round(trim+setup+breakage+printing_def+gluing_def+handling_dmg, 2),
                "good_output_kg": good_kg,
                "yield_percentage": yld,
            })
            mat_id += 1
jdump(material, "material.json")

# ── quality.json ──────────────────────────────────────────────────────────────
quality = []
q_id = 1
for day in DAYS:
    for shift in SHIFTS:
        for m in machines:
            mid = m["id"]
            prod_rec = next((p for p in production
                             if p["date"]==day.isoformat()
                             and p["shift"]==shift
                             and p["machine_id"]==mid), None)
            if not prod_rec:
                continue
            total = prod_rec["actual_output"]
            if total == 0:
                continue
            # choose a product; SLT-001 may get RSC-B2 for elevated rejection
            if mid == "SLT-001" and rnd(0,1) < 0.45:
                product = "RSC-B2"
                reject_rate = rnd(0.08, 0.12)
            else:
                product = random.choice(PRODUCTS)
                reject_rate = rnd(0.005, 0.025)
            rejected = int(total * reject_rate)
            good = total - rejected
            # Distribute defect counts across categories
            def def_split(n):
                parts = [rndint(0, max(0,n//3)) for _ in range(5)]
                parts.append(max(0, n - sum(parts)))
                random.shuffle(parts)
                return parts
            d = def_split(rejected)
            quality.append({
                "record_id": f"QC-{q_id:04d}",
                "date": day.isoformat(),
                "shift": shift,
                "machine_id": mid,
                "product_type": product,
                "total_produced": total,
                "good_units": good,
                "rejected_units": rejected,
                "rejection_rate": round(reject_rate * 100, 3),
                "defect_incorrect_dimensions": d[0],
                "defect_poor_printing": d[1],
                "defect_weak_adhesive": d[2],
                "defect_damaged_flute": d[3],
                "defect_cutting": d[4],
                "defect_folding": d[5],
            })
            q_id += 1
jdump(quality, "quality.json")

# ── orders.json ───────────────────────────────────────────────────────────────
CUSTOMERS = ["Reliance Packaging","Flipkart Logistics","Marico Industries",
             "Godrej Consumer","Amazon India","Tata Consumer","ITC Limited",
             "Dabur India","Hindustan Unilever","Nestlé India","Asian Paints",
             "Pidilite Industries","Emami Ltd","Reckitt India","Haldirams"]
orders = []
machine_ids = [m["id"] for m in machines]
for i in range(1, 16):
    oid = f"ORD-{i:03d}"
    ordered = rndint(5000, 50000)
    machine = machine_ids[(i-1) % len(machine_ids)]
    # ORD-007 is at risk
    if i == 7:
        completed = int(ordered * rnd(0.30, 0.50))
        due = date(2026, 10, 20)
        est_completion = date(2026, 11, 5)
        at_risk = True
        status = "In Progress"
        priority = "Critical"
    else:
        pct = rnd(0.60, 0.98) if i <= 10 else rnd(0.10, 0.60)
        completed = int(ordered * pct)
        base_due = date(2026, 10, 15 + (i * 2) % 15)
        due = base_due
        est_completion = due + timedelta(days=rndint(-3, 5))
        at_risk = est_completion > due and completed < ordered * 0.85
        if completed >= ordered:
            status = "Completed"
        elif pct > 0.85:
            status = "In Progress"
        else:
            status = "In Progress"
        priority = random.choice(["Critical","High","Medium","Low"])
    orders.append({
        "order_id": oid,
        "customer_name": CUSTOMERS[i-1],
        "product_type": PRODUCTS[(i-1) % len(PRODUCTS)],
        "ordered_qty": ordered,
        "completed_qty": completed,
        "due_date": due.isoformat(),
        "priority": priority,
        "assigned_machine": machine,
        "status": status,
        "estimated_completion_date": est_completion.isoformat(),
        "is_at_risk": at_risk,
    })
jdump(orders, "orders.json")

# ── config.json ────────────────────────────────────────────────────────────────
config = {
    "oee_target": 0.75,
    "waste_target_pct": 5.0,
    "rejection_target_pct": 2.0,
    "paper_rate_inr_per_kg": {
        "Kraft Liner": 42,
        "Fluting Medium": 35,
        "Test Liner": 38,
    },
    "shift_hours": 8,
    "demo_mode": True,
    "plant_name": "CORRUGATE IQ Plant 1",
    "currency": "INR",
    "timezone": "Asia/Kolkata",
    "working_days_per_month": 26,
}
jdump([config], "config.json")

print("Done. All datasets written.")

