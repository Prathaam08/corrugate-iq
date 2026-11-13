/**
 * dashboard.js — Loads and renders all dashboard widgets.
 * Depends on filters.js and charts.js.
 */

async function loadKPIs() {
  const data = await fetchJson("/api/kpis" + buildQuery());
  const prod  = data.production || {};
  const oee   = data.plant_oee  || {};

  const set = (id, val, unit = "", cls = "") => {
    const card = document.getElementById(id);
    if (!card) return;
    card.querySelector(".kpi-value").textContent = val + unit;
    if (cls) card.classList.add(cls);
  };

  const oeePct = ((oee.oee || 0) * 100).toFixed(1);
  set("kpi-oee", oeePct, "%", oeePct >= 75 ? "success" : oeePct >= 60 ? "warning" : "danger");
  set("kpi-achievement", (prod.achievement_pct || 0).toFixed(1), "%");
  const wp = (prod.waste_pct || 0).toFixed(1);
  set("kpi-waste", wp, "%", wp > 5 ? "danger" : "success");
  const rr = (prod.rejection_rate_pct || 0).toFixed(2);
  set("kpi-rejection", rr, "%", rr > 2 ? "danger" : "success");
  const dt = data.downtime || {};
  if (dt.unplanned_minutes != null) {
    const hrs = (dt.unplanned_minutes / 60).toFixed(1);
    set("kpi-downtime", hrs, " hrs", dt.unplanned_minutes > 1000 ? "danger" : "warning");
  } else {
    set("kpi-downtime", "—");
  }
}

async function loadProductionChart() {
  const d = await fetchJson("/api/production-chart" + buildQuery());
  renderChart("productionChart", () =>
    makeLineChart("productionChart", d.labels, [
      { label: "Planned", data: d.planned },
      { label: "Actual",  data: d.actual  },
      { label: "Good",    data: d.good    },
    ])
  );
}

async function loadOEEChart() {
  const d = await fetchJson("/api/oee-comparison" + buildQuery());
  const labels = d.map(m => m.machine_id);
  renderChart("oeeChart", () =>
    makeBarChart("oeeChart", labels, [
      { label: "OEE %",          data: d.map(m => m.oee)          },
      { label: "Availability %", data: d.map(m => m.availability) },
      { label: "Performance %",  data: d.map(m => m.performance)  },
      { label: "Quality %",      data: d.map(m => m.quality)      },
    ])
  );
}

async function loadDowntimePareto() {
  const d = await fetchJson("/api/downtime-pareto" + buildQuery());
  const rows = (d.pareto || []).slice(0, 7);
  renderChart("downtimePareto", () =>
    makeParetoChart("downtimePareto",
      rows.map(r => r.category),
      rows.map(r => r.minutes),
      rows.map(r => r.cumulative_pct)
    )
  );
}

async function loadWasteChart() {
  const d = await fetchJson("/api/waste-breakdown" + buildQuery());
  renderChart("wasteChart", () =>
    makeDoughnutChart("wasteChart",
      d.map(r => r.label),
      d.map(r => r.kg)
    )
  );
}

async function loadShiftChart() {
  const d = await fetchJson("/api/shift-performance" + buildQuery());
  renderChart("shiftChart", () =>
    makeBarChart("shiftChart", d.map(s => "Shift " + s.shift), [
      { label: "Achievement %", data: d.map(s => s.achievement_pct) },
      { label: "Waste %",       data: d.map(s => s.waste_pct)       },
      { label: "Rejection %",   data: d.map(s => s.rejection_pct)   },
    ])
  );
}

async function loadInsights() {
  const insights = await fetchJson("/api/insights" + buildQuery());
  const container = document.getElementById("insightsList");
  if (!container) return;
  container.innerHTML = insights.slice(0, 10).map(ins => `
    <div class="insight-card ${ins.severity}">
      <div class="insight-title">
        <span class="badge badge-${ins.severity.toLowerCase()}">${ins.severity}</span>
        &nbsp;${ins.title}
      </div>
      <div class="insight-meta">
        <span>🏭 ${ins.affected_entity}</span>
        <span>💰 ₹${Number(ins.financial_impact_inr).toLocaleString('en-IN')}</span>
        <span>🏷 ${ins.responsible_department}</span>
      </div>
      <div style="font-size:0.82rem;color:#94a3b8;margin-top:0.4rem">${ins.recommended_action}</div>
    </div>
  `).join("");
}

async function loadAll() {
  await Promise.all([
    loadKPIs(),
    loadProductionChart(),
    loadOEEChart(),
    loadDowntimePareto(),
    loadWasteChart(),
    loadShiftChart(),
    loadInsights(),
  ]);
}

window.addEventListener("filtersChanged", loadAll);
document.addEventListener("DOMContentLoaded", loadAll);

