/**
 * filters.js — URL query-string filter helpers shared across all pages.
 */

function getFilters() {
  return {
    start_date: document.getElementById("startDate")?.value || "",
    end_date:   document.getElementById("endDate")?.value   || "",
    shifts:     document.getElementById("shiftFilter")?.value || "",
    machines:   document.getElementById("machineFilter")?.value || "",
  };
}

function buildQuery(extra = {}) {
  const f = { ...getFilters(), ...extra };
  const params = new URLSearchParams();
  Object.entries(f).forEach(([k, v]) => { if (v) params.set(k, v); });
  return params.toString() ? "?" + params.toString() : "";
}

function applyFilters() {
  window.dispatchEvent(new CustomEvent("filtersChanged", { detail: getFilters() }));
}

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${url}`);
  return r.json();
}

// ── Date Calendar Opening & Auto-Apply ───────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const startInput = document.getElementById("startDate");
  const endInput = document.getElementById("endDate");
  const shiftSelect = document.getElementById("shiftFilter");

  [startInput, endInput].forEach(inp => {
    if (!inp) return;

    // Clicking anywhere on the date input field immediately opens the native calendar picker
    inp.addEventListener("click", () => {
      try {
        if (typeof inp.showPicker === "function") {
          inp.showPicker();
        }
      } catch (e) {
        // Fallback for older browsers
      }
    });

    // Auto-update dashboard as soon as a new date is selected
    inp.addEventListener("change", () => {
      applyFilters();
    });
  });

  if (shiftSelect) {
    shiftSelect.addEventListener("change", () => {
      applyFilters();
    });
  }
});
