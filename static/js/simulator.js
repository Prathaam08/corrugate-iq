/**
 * simulator.js — What-if simulator UI.
 */

function getSimParams() {
  return {
    downtime_reduction_pct:  parseFloat(document.getElementById("dtReduction")?.value  || 0),
    waste_reduction_pct:     parseFloat(document.getElementById("wstReduction")?.value || 0),
    rejection_reduction_pct: parseFloat(document.getElementById("rejReduction")?.value || 0),
    speed_improvement_pct:   parseFloat(document.getElementById("spdImprovement")?.value || 0),
  };
}

async function runSimulation() {
  const params = getSimParams();
  const r = await fetch("/api/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ params }),
  });
  const data = await r.json();
  renderSimResults(data);
}

function renderSimResults(data) {
  const { baseline, simulated, delta } = data;
  const container = document.getElementById("simResults");
  if (!container) return;

  const fmt = (v, unit = "") => (v != null ? Number(v).toLocaleString("en-IN") + unit : "—");
  const fmtDelta = (d) => {
    const abs = d?.abs ?? 0;
    const pctStr = d?.pct != null ? ` (${abs >= 0 ? "+" : ""}${d.pct}%)` : "";
    const sign = abs >= 0 ? "+" : "";
    const color = abs >= 0 ? "#22c55e" : "#ef4444";
    const span = document.createElement("span");
    span.style.color = color;
    span.textContent = `${sign}${fmt(abs)}${pctStr}`;
    return span.outerHTML;
  };

  container.innerHTML = `
    <div class="sim-result-grid">
      ${[
        ["Good Boxes",   fmt(baseline.total_good_boxes),   fmt(simulated.total_good_boxes),   fmtDelta(delta.total_good_boxes)],
        ["Waste Kg",     fmt(baseline.total_waste_kg,"kg"),fmt(simulated.total_waste_kg,"kg"),fmtDelta(delta.total_waste_kg)],
        ["Rejection %",  fmt(baseline.rejection_rate_pct,"%"),fmt(simulated.rejection_rate_pct,"%"),""],
        ["OEE",          fmt((baseline.oee*100).toFixed(1),"%"),fmt((simulated.oee*100).toFixed(1),"%"),fmtDelta(delta.oee)],
        ["Total Cost ₹", fmt(baseline.total_cost_inr),     fmt(simulated.total_cost_inr),     fmtDelta(delta.total_cost_inr)],
        ["Waste Saving", "—", "—", `<span style="color:#22c55e">₹${fmt(delta.waste_saving_inr)}</span>`],
      ].map(([label, base, sim, chg]) => `
        <div class="sim-result-card">
          <div style="font-size:0.78rem;color:#64748b;margin-bottom:0.3rem">${label}</div>
          <div style="font-size:0.9rem">Base: ${base}</div>
          <div style="font-size:0.9rem">Sim: ${sim}</div>
          <div style="font-size:0.85rem;margin-top:0.2rem">${chg}</div>
        </div>`).join("")}
    </div>
    <details style="margin-top:1rem;font-size:0.82rem;color:#64748b">
      <summary>Assumptions & Caveats</summary>
      <ul style="padding:0.5rem 1rem">${data.assumptions.map(a => `<li>${a}</li>`).join("")}</ul>
    </details>`;
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("runSim")?.addEventListener("click", runSimulation);
});

