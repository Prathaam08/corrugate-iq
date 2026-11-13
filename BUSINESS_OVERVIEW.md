# 📦 CORRUGATE IQ — Executive Business Case & Problem-Solving Guide

---

## 1. Executive Summary (The 30-Second Elevator Pitch)

> **CORRUGATE IQ** is an industrial analytics platform designed specifically for the **paper corrugation and corrugated box packaging industry**. 
> 
> In traditional box plants, high raw material costs (paper roll kraft/fluting) make up **60% to 70% of total manufacturing costs**, while unplanned machine breakdowns and trim waste severely erode operating margins. 
> 
> CORRUGATE IQ aggregates real-time plant telemetry, standardizes World-Class Manufacturing metrics (OEE, Availability, Performance, Quality), identifies the 80/20 downtime root causes via Pareto analysis, and runs predictive what-if improvement simulations to **protect profit margins, reduce paper scrap below the 5% threshold, and ensure on-time customer delivery.**

---

## 2. Core Business Problems Solved

### 🔴 Problem 1: Silent Paper Waste & High Raw Material Burn Rate
* **Industry Reality:** Raw paper (Kraft Liner, Fluting Medium, Testliner) costs ₹35 to ₹42 per kg. In a plant processing 850+ tonnes of paper monthly, a 1% to 2% excess in trim, setup, or defect waste represents **tens of lakhs in direct financial loss**.
* **How CORRUGATE IQ Solves It:**
  * Tracks material yield and categorizes waste into **6 distinct root causes** (*Trim Waste, Setup Waste, Breakage, Printing Defect, Gluing Defect, Handling Damage*).
  * Automatically fires the `RULE_HIGH_WASTE` alarm whenever plant waste exceeds the 5.0% tolerance ceiling, quantifying the exact Rupee loss.

---

### 🔴 Problem 2: Hidden Machine Inefficiencies & OEE Deficits
* **Industry Reality:** Plant managers often know the total box count at the end of a shift, but cannot see whether underproduction was caused by **stoppage (Availability)**, **slow running speeds (Performance)**, or **defective scrap (Quality)**.
* **How CORRUGATE IQ Solves It:**
  * Computes automated **OEE (Overall Equipment Effectiveness)** across all 6 production lines (*Corrugators, Flexo Printers, Slotters, Folder Gluers, Cutters*).
  * Immediately flags underperforming assets (e.g. `COR-002` at 52% OEE) and provides a **1-click root-cause drill-down modal** showing Availability vs. Performance vs. Quality ratios.

---

### 🔴 Problem 3: Reactive Downtime Management (The 80/20 Trap)
* **Industry Reality:** Maintenance teams frequently react to whichever breakdown happened last rather than fixing the recurring failures that cause 80% of total plant downtime.
* **How CORRUGATE IQ Solves It:**
  * Utilizes **Downtime Pareto Analysis** (80/20 rule) to separate minor stoppages from high-cost mechanical and electrical breakdowns (e.g. Gearbox failures vs. splice changeovers).
  * Measures cumulative stoppage hours per machine so reliability engineers can schedule targeted preventative maintenance before catastrophic line failure occurs.

---

### 🔴 Problem 4: Customer Order Penalties & Late Delivery Risks
* **Industry Reality:** Corrugated box manufacturers produce on tight JIT (Just-In-Time) schedules for e-commerce, FMCG, and automotive clients (Flipkart, Godrej, Marico, Reliance). Late deliveries lead to heavy contractual penalties or canceled purchase orders.
* **How CORRUGATE IQ Solves It:**
  * Real-time order progress tracking with automatic **Delay Risk Detection (`⚠️ At Risk`)**.
  * Flags orders that are more than 15% behind schedule relative to their due dates, allowing production supervisors to reallocate capacity or reschedule shifts before the deadline is missed.

---

### 🔴 Problem 5: Capital Allocation Blind Spots (No "What-If" Modeling)
* **Industry Reality:** Factory general managers struggle to justify capital investments (e.g., automated splicers or faster die cutters) to board members without clear financial projections.
* **How CORRUGATE IQ Solves It:**
  * Includes a built-in **What-If Improvement Simulator**.
  * Plant managers can slide parameters (e.g. *Reduce Downtime by 20%, Reduce Waste by 15%*) to instantly calculate the exact projected **Good Box Output Increase**, **New Plant OEE**, and **Net Rupee Cost Savings**.

---

## 3. Module-by-Module Business Value Breakdown

| Module / Page | Primary User Persona | Core Metric / Action | Business ROI |
| :--- | :--- | :--- | :--- |
| **📊 Plant Overview** | Plant Head / GM | Real-time OEE, Achievement %, Waste %, Insights | High-level operational health & instant bottleneck discovery |
| **🏭 Production** | Shift Supervisor | Planned vs. Actual output, Loss minutes per machine | Shift-level accountability and volume gap elimination |
| **⚙️ Machines** | Maintenance Lead | Fleet OEE, 1-Click Root-Cause Diagnostics modal | Reduced MTTR (Mean Time to Repair) and targeted PMs |
| **📄 Materials** | Supply Chain / Inventory | Paper Grade Consumption, 6-Waste Categorization | Raw paper yield optimization and reduced roll scrap |
| **✅ Quality** | Quality Assurance (QA) | Defect breakdown (Flute damage, glue, printing) | Customer rejection prevention below 2.0% ceiling |
| **📋 Orders** | Operations Scheduler | Real-time completion bars, Due Date risk tagging | 99%+ On-Time In-Full (OTIF) fulfillment rate |
| **📁 Reports & Exports** | Data Analysts / Audit | Auto-adjusted Excel (.xlsx) & CSV downloads | Compliance, monthly ERP reconciliation, zero data loss |
| **🔮 What-If Simulator** | Executive Leadership | Scenario planning (Downtime vs Waste vs Speed) | ROI justification for capital expenditure (CapEx) |

---

## 4. How to Pitch This in an Interview / Demo

### When asked: *"Walk me through the architecture of this project."*
> *"CORRUGATE IQ is a full-stack industrial analytics web platform built with a Python/Flask backend and an enterprise dark-mode frontend utilizing vanilla JavaScript and Chart.js. 
> 
> The core analytics layer uses a clean separation of concerns:
> 1. A centralized `data_service` that handles dynamic time-window filtering and normalization.
> 2. A dedicated `kpi_calculator` implementing world-class manufacturing formulas for Availability, Performance, and Quality.
> 3. An automated `insights_engine` that evaluates production anomalies against 8 deterministic plant rules to surface quantified financial risks.
> 4. A `simulator` service modeling non-linear production gain curves based on waste and downtime reductions.
> 
> The application includes live SCADA telemetry simulation and dual-format reporting (auto-fitted Excel `.xlsx` and standard `.csv`)."*

---

### When asked: *"What makes this better than a generic dashboard template?"*
> *"Most generic dashboards simply display static charts. CORRUGATE IQ is purpose-built for the domain:
> - **Domain Specificity:** It models paper corrugation concepts—fluting grades, trim waste, reel splicing, and changeover delays.
> - **Actionable Intelligence:** It doesn't just show that OEE is 62%; the diagnostics modal tells the engineer that Machine COR-002 lost 230 minutes specifically to mechanical gearbox failures.
> - **Financial Quantification:** Insights don't just say 'Waste is high'; they calculate that 7.1% waste on Kraft Liner created an excess material loss of ₹1.4 Lakhs this month."*

---

## 5. Technology Stack & Reliability

* **Backend:** Python 3.12, Flask, Pandas, OpenPyXL (Excel automation)
* **Frontend:** Vanilla JavaScript (ES6+), Chart.js (custom dark glassmorphic theme), CSS Grid/Flexbox
* **Testing:** Pytest (88 unit tests covering KPIs, insights, and simulator)
* **Data Sources:** Normalized JSON storage simulating real-time SCADA telemetry

