/**
 * telemetry.js — Feature 2: Factory Floor Live Digital Twin Simulation.
 * Simulates real-time IoT machine telemetry, dynamic box counters, and live plant status.
 */

let _telemetryActive = false;
let _telemetryTimer = null;
let _simulatedLiveBoxes = 0;

function initTelemetry() {
  const toggleBtn = document.getElementById("liveTelemetryToggle");
  const ticker = document.getElementById("telemetryTicker");
  if (!toggleBtn || !ticker) return;

  // Restore state if previously active
  const saved = localStorage.getItem("corrugate_telemetry") === "true";
  if (saved) {
    setTelemetryActive(true);
  }
}

function toggleTelemetry() {
  setTelemetryActive(!_telemetryActive);
}

function setTelemetryActive(active) {
  _telemetryActive = active;
  localStorage.setItem("corrugate_telemetry", active ? "true" : "false");

  const toggleBtn = document.getElementById("liveTelemetryToggle");
  const stateLabel = document.getElementById("liveStateLabel");
  const ticker = document.getElementById("telemetryTicker");

  if (active) {
    if (toggleBtn) toggleBtn.classList.add("active");
    if (stateLabel) stateLabel.textContent = "LIVE";
    if (ticker) ticker.classList.add("active");

    startTelemetryStream();
  } else {
    if (toggleBtn) toggleBtn.classList.remove("active");
    if (stateLabel) stateLabel.textContent = "OFF";
    if (ticker) ticker.classList.remove("active");

    stopTelemetryStream();
  }
}

function startTelemetryStream() {
  if (_telemetryTimer) clearInterval(_telemetryTimer);

  _telemetryTimer = setInterval(() => {
    // Increment live counter
    const addedBoxes = Math.floor(Math.random() * 3) + 1;
    _simulatedLiveBoxes += addedBoxes;

    // Simulate varying factory speed (95 to 118 boxes/min)
    const currentSpeed = 100 + Math.floor(Math.random() * 18);
    const speedEl = document.getElementById("telCurrentSpeed");
    if (speedEl) speedEl.textContent = currentSpeed + " boxes/min";

    const boxEl = document.getElementById("telLiveBoxes");
    if (boxEl) boxEl.textContent = "+" + _simulatedLiveBoxes.toLocaleString("en-IN") + " boxes";

    // Optional: update dashboard achievement if present
    const achieveEl = document.getElementById("kpi-achievement");
    if (achieveEl) {
      const valElem = achieveEl.querySelector(".kpi-value");
      if (valElem && valElem.textContent.includes("%")) {
        // Flash subtle green
        valElem.style.transition = "color 0.3s";
        valElem.style.color = "#86efac";
        setTimeout(() => { valElem.style.color = ""; }, 400);
      }
    }
  }, 1800);
}

function stopTelemetryStream() {
  if (_telemetryTimer) {
    clearInterval(_telemetryTimer);
    _telemetryTimer = null;
  }
}

document.addEventListener("DOMContentLoaded", initTelemetry);

