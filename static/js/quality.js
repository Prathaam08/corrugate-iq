/**
 * quality.js — Quality metrics, defect breakdown, and rejection rates.
 */

async function loadQuality() {
  const container = document.getElementById("quality-container");
  try {
    const data = await fetchJson("/api/quality-breakdown" + buildQuery());
    const s = data.summary || {};
    const byMachine = data.by_machine || [];

    const set = (id, val, unit = "") => {
      const el = document.getElementById(id);
      if (el) el.textContent = (val != null ? Number(val).toLocaleString("en-IN") : "—") + unit;
    };

    set("kpi-q-produced", s.total_produced);
    set("kpi-q-good", s.total_good);
    set("kpi-q-rejected", s.total_rejected);
    set("kpi-q-rate", s.rejection_rate_pct, "%");

    // Render Defect Breakdown Chart
    if (s.defect_breakdown && document.getElementById("defectChart")) {
      const labels = Object.keys(s.defect_breakdown).map(k => k.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()));
      const counts = Object.values(s.defect_breakdown);
      renderChart("defectChart", () =>
        makeBarChart("defectChart", labels, [
          { label: "Defects Count", data: counts }
        ])
      );
    }

    // Render Machine Rejection Chart
    if (byMachine.length > 0 && document.getElementById("machineRejectionChart")) {
      renderChart("machineRejectionChart", () =>
        makeBarChart("machineRejectionChart", byMachine.map(m => m.machine_id), [
          { label: "Rejection %", data: byMachine.map(m => m.rejection_rate_pct) }
        ])
      );
    }

    // Render Table
    if (container) {
      container.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Machine ID</th><th>Total Produced</th><th>Rejected Units</th>
              <th>Rejection Rate</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${byMachine.map(m => {
              const rr = m.rejection_rate_pct ?? 0;
              const badgeClass = rr <= 1.5 ? "badge-low" : (rr <= 3.0 ? "badge-high" : "badge-critical");
              return `
              <tr>
                <td><strong>${m.machine_id}</strong></td>
                <td>${Number(m.total || 0).toLocaleString()}</td>
                <td>${Number(m.rejected || 0).toLocaleString()}</td>
                <td><strong>${rr}%</strong></td>
                <td><span class="badge ${badgeClass}">${rr <= 2.0 ? "Target Met" : "Exceeds Target"}</span></td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>`;
    }
  } catch (err) {
    if (container) container.innerHTML = `<div style="color:var(--danger);padding:1rem;">Error loading quality data: ${err.message}</div>`;
  }
}

window.addEventListener("filtersChanged", loadQuality);
document.addEventListener("DOMContentLoaded", loadQuality);

