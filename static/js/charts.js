/**
 * charts.js — Chart.js wrapper factories for CORRUGATE IQ.
 * Requires Chart.js loaded from CDN in base.html or via script tag.
 */

const CHART_COLORS = {
  blue:   "#3b82f6",
  amber:  "#f59e0b",
  red:    "#f43f5e",
  green:  "#10b981",
  purple: "#a855f7",
  cyan:   "#06b6d4",
  indigo: "#6366f1",
  slate:  "#64748b",
};

const MULTI_COLORS = Object.values(CHART_COLORS);

const DEFAULT_OPTS = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      labels: {
        color: "#94a3b8",
        font: { family: "'Inter', sans-serif", size: 11, weight: 500 },
        boxWidth: 12,
        padding: 14,
      }
    },
    tooltip: {
      backgroundColor: "#131826",
      titleColor: "#f8fafc",
      bodyColor: "#cbd5e1",
      borderColor: "rgba(255, 255, 255, 0.12)",
      borderWidth: 1,
      padding: 10,
      cornerRadius: 8,
      titleFont: { family: "'Inter', sans-serif", weight: 600, size: 12 },
      bodyFont: { family: "'Inter', sans-serif", size: 11 },
    },
  },
  scales: {
    x: {
      ticks: { color: "#64748b", font: { family: "'Inter', sans-serif", size: 10 } },
      grid: { color: "rgba(255, 255, 255, 0.04)" }
    },
    y: {
      ticks: { color: "#64748b", font: { family: "'Inter', sans-serif", size: 10 } },
      grid: { color: "rgba(255, 255, 255, 0.04)" }
    },
  },
};

function makeLineChart(canvasId, labels, datasets) {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js is not loaded.");
    return null;
  }
  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "line",
    data: { labels, datasets: datasets.map((d, i) => ({
      borderColor: MULTI_COLORS[i % MULTI_COLORS.length],
      backgroundColor: "transparent",
      tension: 0.3, pointRadius: 2, borderWidth: 2,
      ...d
    })) },
    options: { ...DEFAULT_OPTS },
  });
}

function makeBarChart(canvasId, labels, datasets, stacked = false) {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js is not loaded.");
    return null;
  }
  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: datasets.map((d, i) => ({
      backgroundColor: MULTI_COLORS[i % MULTI_COLORS.length] + "cc",
      borderColor:     MULTI_COLORS[i % MULTI_COLORS.length],
      borderWidth: 1,
      ...d
    })) },
    options: {
      ...DEFAULT_OPTS,
      scales: {
        ...DEFAULT_OPTS.scales,
        x: { ...DEFAULT_OPTS.scales.x, stacked },
        y: { ...DEFAULT_OPTS.scales.y, stacked },
      },
    },
  });
}

function makeDoughnutChart(canvasId, labels, data) {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js is not loaded.");
    return null;
  }
  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data, backgroundColor: MULTI_COLORS, borderColor: "#1a1d2e", borderWidth: 2 }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "right", labels: { color: "#94a3b8", font: { size: 11 }, padding: 10 } },
        tooltip: DEFAULT_OPTS.plugins.tooltip,
      },
    },
  });
}

function makeParetoChart(canvasId, labels, counts, cumulativePct) {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js is not loaded.");
    return null;
  }
  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        { type: "bar",  label: "Minutes",        data: counts,       backgroundColor: CHART_COLORS.blue + "bb" },
        { type: "line", label: "Cumulative %",   data: cumulativePct, borderColor: CHART_COLORS.amber,
          backgroundColor: "transparent", yAxisID: "y2", tension: 0.3, pointRadius: 3 },
      ],
    },
    options: {
      ...DEFAULT_OPTS,
      scales: {
        x:  { ...DEFAULT_OPTS.scales.x },
        y:  { ...DEFAULT_OPTS.scales.y, title: { display: true, text: "Minutes", color: "#64748b" } },
        y2: { position: "right", min: 0, max: 100,
              ticks: { color: "#64748b", callback: v => v + "%" },
              grid: { drawOnChartArea: false } },
      },
    },
  });
}

// Destroy and recreate a chart in a canvas
const _chartInstances = {};
function renderChart(id, factory) {
  if (_chartInstances[id]) { _chartInstances[id].destroy(); }
  _chartInstances[id] = factory();
}

