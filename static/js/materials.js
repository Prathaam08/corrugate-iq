/**
 * materials.js — Paper input, waste metrics, and material logs.
 */

async function loadMaterials() {
  const container = document.getElementById("materials-container");
  try {
    const [matData, wasteData] = await Promise.all([
      fetchJson("/api/materials" + buildQuery()),
      fetchJson("/api/waste-breakdown" + buildQuery())
    ]);

    const s = matData.summary || {};

    const set = (id, val, unit = "") => {
      const el = document.getElementById(id);
      if (el) el.textContent = (val != null ? Number(val).toLocaleString("en-IN") : "—") + unit;
    };

    set("kpi-mat-input", s.total_paper_input_kg, " kg");
    set("kpi-mat-waste", s.total_waste_kg, " kg");
    set("kpi-mat-yield", s.yield_pct, "%");
    set("kpi-mat-waste-pct", s.waste_pct, "%");

    // Render Doughnut Chart for Waste
    if (wasteData && document.getElementById("matWasteChart")) {
      renderChart("matWasteChart", () =>
        makeDoughnutChart("matWasteChart",
          wasteData.map(r => r.label),
          wasteData.map(r => r.kg)
        )
      );
    }

    // Render Bar Chart for Paper Types
    if (s.by_paper_type_kg && document.getElementById("matTypeChart")) {
      const types = Object.keys(s.by_paper_type_kg);
      const values = Object.values(s.by_paper_type_kg);
      renderChart("matTypeChart", () =>
        makeBarChart("matTypeChart", types, [
          { label: "Paper Input (kg)", data: values }
        ])
      );
    }

    if (container) {
      const records = matData.records || [];
      container.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Date</th><th>Machine</th><th>Shift</th>
              <th>Paper Type</th><th>Input (kg)</th><th>Good (kg)</th><th>Waste (kg)</th>
              <th>Yield %</th>
            </tr>
          </thead>
          <tbody>
            ${records.slice(0, 30).map(r => {
              const yld = r.paper_input_kg ? ((r.good_output_kg / r.paper_input_kg) * 100).toFixed(1) : 0;
              const yldBadge = yld >= 92 ? "badge-low" : (yld >= 85 ? "badge-high" : "badge-critical");
              return `
              <tr>
                <td>${r.date}</td>
                <td><strong>${r.machine_id}</strong></td>
                <td>Shift ${r.shift}</td>
                <td>${r.paper_type || "Standard"}</td>
                <td>${Number(r.paper_input_kg || 0).toLocaleString()}</td>
                <td>${Number(r.good_output_kg || 0).toLocaleString()}</td>
                <td>${Number(r.total_waste_kg || 0).toLocaleString()}</td>
                <td><span class="badge ${yldBadge}">${yld}%</span></td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>`;
    }
  } catch (err) {
    if (container) container.innerHTML = `<div style="color:var(--danger);padding:1rem;">Error loading materials: ${err.message}</div>`;
  }
}

window.addEventListener("filtersChanged", loadMaterials);
document.addEventListener("DOMContentLoaded", loadMaterials);

