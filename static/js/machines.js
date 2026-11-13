/**
 * machines.js — Machine list, fleet performance, and root-cause diagnostic modal.
 */

async function loadMachines() {
  const container = document.getElementById("machines-container");
  if (!container) return;

  try {
    const machines = await fetchJson("/api/machines" + buildQuery());

    // Update summary cards if present
    const fleetEl = document.getElementById("kpiFleetCount");
    const runningEl = document.getElementById("kpiRunningCount");
    const avgOeeEl = document.getElementById("kpiAvgOee");
    const underEl = document.getElementById("kpiUnderperforming");

    if (fleetEl) fleetEl.textContent = machines.length;
    if (runningEl) runningEl.textContent = machines.filter(m => m.status === "Running" || m.status === "operational").length;

    if (machines.length > 0) {
      const avgOee = (machines.reduce((sum, m) => sum + (m.oee || 0), 0) / machines.length).toFixed(1);
      if (avgOeeEl) avgOeeEl.textContent = avgOee + "%";
      if (underEl) underEl.textContent = machines.filter(m => (m.oee || 0) < 60).length;
    }

    container.innerHTML = `
      <table>
        <thead><tr>
          <th>ID</th><th>Machine Name</th><th>Type</th>
          <th>OEE %</th><th>Availability %</th><th>Performance %</th><th>Quality %</th>
          <th>Status</th><th>Action</th>
        </tr></thead>
        <tbody>
          ${machines.map(m => {
            const oeeVal = m.oee ?? 0;
            const oeeClass = oeeVal >= 75 ? "badge-low" : (oeeVal >= 60 ? "badge-high" : "badge-critical");
            const isRun = m.status === "Running" || m.status === "operational";
            const statusClass = isRun ? "badge-low" : (m.status === "Maintenance" ? "badge-critical" : "badge-medium");
            return `
            <tr style="cursor:pointer" onclick="openMachineModal('${m.id}')">
              <td><strong>${m.id}</strong></td>
              <td>${m.name}</td>
              <td style="color:var(--text-muted)">${m.type}</td>
              <td><span class="badge ${oeeClass}">${oeeVal}%</span></td>
              <td>${m.availability ?? 0}%</td>
              <td>${m.performance ?? 0}%</td>
              <td>${m.quality ?? 0}%</td>
              <td><span class="badge ${statusClass}">${m.status || "Operational"}</span></td>
              <td>
                <button class="table-action-btn" onclick="event.stopPropagation(); openMachineModal('${m.id}')">
                  🔍 Diagnostics
                </button>
              </td>
            </tr>`;
          }).join("")}
        </tbody>
      </table>`;
  } catch (err) {
    container.innerHTML = `<div style="color:var(--danger);padding:1rem;">Error loading machine metrics: ${err.message}</div>`;
  }
}

// ── Feature 1: Machine Diagnostic Drilldown Modal ────────────────────────────

async function openMachineModal(machineId) {
  const modal = document.getElementById("machineModal");
  const titleEl = document.getElementById("modalMachineTitle");
  const statusBadge = document.getElementById("modalMachineStatusBadge");
  const bodyEl = document.getElementById("modalMachineBody");

  if (!modal || !bodyEl) return;

  modal.classList.add("active");
  titleEl.textContent = `Machine Diagnostics — ${machineId}`;
  bodyEl.innerHTML = `<div style="color:var(--text-muted);padding:2rem;text-align:center">Loading telemetry & diagnostic data...</div>`;

  try {
    const [detailData, dtData] = await Promise.all([
      fetchJson(`/api/machines/${machineId}` + buildQuery()),
      fetchJson(`/api/machines/${machineId}/downtime` + buildQuery())
    ]);

    const m = detailData.machine || {};
    const o = detailData.oee || {};
    const p = detailData.production || {};
    const dtSum = dtData.summary || {};
    const byCat = dtSum.by_category || {};

    const oeePct = ((o.oee || 0) * 100).toFixed(1);
    const availPct = ((o.availability || 0) * 100).toFixed(1);
    const perfPct = ((o.performance || 0) * 100).toFixed(1);
    const qualPct = ((o.quality || 0) * 100).toFixed(1);

    if (statusBadge) {
      statusBadge.className = `badge ${oeePct >= 75 ? 'badge-low' : (oeePct >= 60 ? 'badge-high' : 'badge-critical')}`;
      statusBadge.textContent = `${oeePct}% OEE`;
    }

    bodyEl.innerHTML = `
      <!-- Machine Metadata & Specs -->
      <div style="display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,0.03);padding:0.75rem 1rem;border-radius:8px;margin-bottom:1.25rem;font-size:0.85rem">
        <div><strong>${m.name || machineId}</strong> (${m.type || 'Equipment'})</div>
        <div style="color:var(--text-muted)">Location: <strong>${m.location || 'Bay 1'}</strong> | Installed: <strong>${m.year_installed || '—'}</strong> | Speed: <strong>${m.ideal_speed_boxes_per_hour || 100} bph</strong></div>
      </div>

      <!-- OEE 3-Component Drilldown -->
      <h4 style="font-size:0.9rem;margin-bottom:0.75rem;color:var(--text-muted)">OEE PILLARS BREAKDOWN</h4>
      <div class="drilldown-grid">
        <div class="drilldown-card">
          <div class="drilldown-card-label">Overall OEE</div>
          <div class="drilldown-card-val" style="color:${oeePct >= 75 ? 'var(--success)' : (oeePct >= 60 ? 'var(--accent2)' : 'var(--danger)')}">${oeePct}%</div>
          <div class="oee-bar-wrap"><div class="oee-bar-fill" style="width:${Math.min(100, oeePct)}%;background:${oeePct >= 75 ? 'var(--success)' : (oeePct >= 60 ? 'var(--accent2)' : 'var(--danger)')}"></div></div>
        </div>
        <div class="drilldown-card">
          <div class="drilldown-card-label">Availability</div>
          <div class="drilldown-card-val">${availPct}%</div>
          <div class="oee-bar-wrap"><div class="oee-bar-fill" style="width:${Math.min(100, availPct)}%;background:var(--accent)"></div></div>
        </div>
        <div class="drilldown-card">
          <div class="drilldown-card-label">Performance</div>
          <div class="drilldown-card-val">${perfPct}%</div>
          <div class="oee-bar-wrap"><div class="oee-bar-fill" style="width:${Math.min(100, perfPct)}%;background:#a855f7"></div></div>
        </div>
        <div class="drilldown-card">
          <div class="drilldown-card-label">Quality Rate</div>
          <div class="drilldown-card-val">${qualPct}%</div>
          <div class="oee-bar-wrap"><div class="oee-bar-fill" style="width:${Math.min(100, qualPct)}%;background:var(--success)"></div></div>
        </div>
        <div class="drilldown-card">
          <div class="drilldown-card-label">Good Units Output</div>
          <div class="drilldown-card-val">${Number(o.total_good || p.total_good || 0).toLocaleString()}</div>
          <div style="font-size:0.72rem;color:var(--text-muted);margin-top:0.3rem">Total Produced: ${Number(o.total_actual || p.total_actual || 0).toLocaleString()}</div>
        </div>
        <div class="drilldown-card">
          <div class="drilldown-card-label">Running Runtime</div>
          <div class="drilldown-card-val">${((o.total_running_min || 0)/60).toFixed(1)} hrs</div>
          <div style="font-size:0.72rem;color:var(--text-muted);margin-top:0.3rem">Planned: ${((o.total_planned_min || 0)/60).toFixed(1)} hrs</div>
        </div>
      </div>

      <!-- Downtime Analysis -->
      <h4 style="font-size:0.9rem;margin-bottom:0.75rem;color:var(--text-muted)">DOWNTIME ROOT-CAUSE AUDIT</h4>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem">
        <div style="background:rgba(255,255,255,0.02);padding:0.75rem;border-radius:6px;font-size:0.85rem">
          <div>Total Downtime Events: <strong>${dtSum.total_events || 0} incidents</strong></div>
          <div style="margin-top:0.3rem">Unplanned Downtime: <strong style="color:var(--danger)">${dtSum.unplanned_minutes || 0} mins</strong></div>
          <div style="margin-top:0.3rem">Planned Maintenance: <strong style="color:var(--text-muted)">${dtSum.planned_minutes || 0} mins</strong></div>
        </div>
        <div style="background:rgba(255,255,255,0.02);padding:0.75rem;border-radius:6px;font-size:0.85rem">
          <div style="font-size:0.78rem;color:var(--text-muted);margin-bottom:0.4rem">TOP DOWNTIME CONTRIBUTORS</div>
          ${Object.entries(byCat).slice(0, 3).map(([cat, mins]) => `
            <div style="display:flex;justify-content:space-between;margin-bottom:0.25rem">
              <span>• ${cat}</span>
              <strong>${mins} mins</strong>
            </div>
          `).join("") || '<div style="color:var(--text-muted)">No downtime recorded</div>'}
        </div>
      </div>
    `;
  } catch (err) {
    bodyEl.innerHTML = `<div style="color:var(--danger);padding:1.5rem;">Failed to load diagnostic details: ${err.message}</div>`;
  }
}

function closeMachineModal() {
  const modal = document.getElementById("machineModal");
  if (modal) modal.classList.remove("active");
}

// Close on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeMachineModal();
});

window.addEventListener("filtersChanged", loadMachines);
document.addEventListener("DOMContentLoaded", loadMachines);
