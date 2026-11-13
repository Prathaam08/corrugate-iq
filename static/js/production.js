/**
 * production.js — Production metrics and logs.
 */

async function loadProduction() {
  const container = document.getElementById("production-container");
  try {
    const [prodData, chartData, lossData] = await Promise.all([
      fetchJson("/api/production" + buildQuery()),
      fetchJson("/api/production-chart" + buildQuery()),
      fetchJson("/api/production-loss" + buildQuery())
    ]);

    const s = prodData.summary || {};

    const set = (id, val, unit = "") => {
      const el = document.getElementById(id);
      if (el) el.textContent = (val != null ? Number(val).toLocaleString("en-IN") : "—") + unit;
    };

    set("kpi-prod-planned", s.total_planned);
    set("kpi-prod-actual", s.total_actual);
    set("kpi-prod-good", s.total_good);
    set("kpi-prod-achieve", s.achievement_pct, "%");
    set("kpi-prod-rej", s.rejection_rate_pct, "%");

    // Render Charts if canvas exists
    if (chartData && document.getElementById("prodDailyChart")) {
      renderChart("prodDailyChart", () =>
        makeLineChart("prodDailyChart", chartData.labels, [
          { label: "Planned", data: chartData.planned },
          { label: "Actual",  data: chartData.actual },
          { label: "Good",    data: chartData.good },
        ])
      );
    }

    if (lossData && document.getElementById("prodLossChart")) {
      renderChart("prodLossChart", () =>
        makeBarChart("prodLossChart", lossData.map(d => d.machine_id), [
          { label: "Loss Minutes", data: lossData.map(d => d.loss_minutes) }
        ])
      );
    }

    // Render Table
    if (container) {
      const records = prodData.records || [];
      container.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Date</th><th>Machine</th><th>Shift</th>
              <th>Planned</th><th>Actual</th><th>Good</th><th>Rejected</th>
              <th>Achievement</th>
            </tr>
          </thead>
          <tbody>
            ${records.slice(0, 30).map(r => {
              const ach = r.planned_output ? ((r.actual_output / r.planned_output) * 100).toFixed(1) : 0;
              const badgeClass = ach >= 90 ? "badge-low" : (ach >= 70 ? "badge-high" : "badge-critical");
              return `
              <tr>
                <td>${r.date}</td>
                <td><strong>${r.machine_id}</strong></td>
                <td>Shift ${r.shift}</td>
                <td>${Number(r.planned_output || 0).toLocaleString()}</td>
                <td>${Number(r.actual_output || 0).toLocaleString()}</td>
                <td>${Number(r.good_output || 0).toLocaleString()}</td>
                <td>${Number(r.rejected_output || 0).toLocaleString()}</td>
                <td><span class="badge ${badgeClass}">${ach}%</span></td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>`;
    }
  } catch (err) {
    if (container) container.innerHTML = `<div style="color:var(--danger);padding:1rem;">Error loading production data: ${err.message}</div>`;
  }
}

window.addEventListener("filtersChanged", loadProduction);
document.addEventListener("DOMContentLoaded", loadProduction);

