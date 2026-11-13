/**
 * orders.js — Customer orders status, fulfillment, and delay risk flags.
 */

async function loadOrders() {
  const container = document.getElementById("orders-container");
  try {
    const data = await fetchJson("/api/orders" + buildQuery());
    const s = data.summary || {};
    const orders = data.orders || [];

    const set = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val != null ? val : "—";
    };

    set("kpi-ord-total", s.total);
    set("kpi-ord-progress", s.in_progress);
    set("kpi-ord-completed", s.completed);
    set("kpi-ord-risk", s.at_risk);

    if (container) {
      container.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Order ID</th><th>Customer</th><th>Product</th>
              <th>Ordered</th><th>Completed</th><th>Progress</th>
              <th>Due Date</th><th>Priority</th><th>Machine</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${orders.map(o => {
              const pct = o.ordered_qty ? Math.min(100, Math.round((o.completed_qty / o.ordered_qty) * 100)) : 0;
              const prioClass = o.priority === "High" ? "badge-critical" : (o.priority === "Medium" ? "badge-high" : "badge-medium");
              const riskBadge = o.is_at_risk ? `<span class="badge badge-critical" style="margin-left:4px">⚠️ At Risk</span>` : "";
              return `
              <tr>
                <td><strong>${o.order_id}</strong></td>
                <td>${o.customer_name}</td>
                <td><code style="background:rgba(255,255,255,0.06);padding:2px 4px;border-radius:4px">${o.product_type}</code></td>
                <td>${Number(o.ordered_qty).toLocaleString()}</td>
                <td>${Number(o.completed_qty).toLocaleString()}</td>
                <td>
                  <div style="display:flex;align-items:center;gap:6px">
                    <div style="flex:1;background:var(--border);height:6px;border-radius:3px;overflow:hidden">
                      <div style="width:${pct}%;background:${pct >= 100 ? 'var(--success)' : (o.is_at_risk ? 'var(--danger)' : 'var(--accent)')};height:100%"></div>
                    </div>
                    <span style="font-size:0.75rem">${pct}%</span>
                  </div>
                </td>
                <td style="color:${o.is_at_risk ? 'var(--danger)' : 'var(--text)'}">${o.due_date}</td>
                <td><span class="badge ${prioClass}">${o.priority}</span></td>
                <td>${o.assigned_machine}</td>
                <td>
                  <span class="badge ${o.status === 'Completed' ? 'badge-low' : 'badge-medium'}">${o.status}</span>
                  ${riskBadge}
                </td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>`;
    }
  } catch (err) {
    if (container) container.innerHTML = `<div style="color:var(--danger);padding:1rem;">Error loading orders: ${err.message}</div>`;
  }
}

window.addEventListener("filtersChanged", loadOrders);
document.addEventListener("DOMContentLoaded", loadOrders);

