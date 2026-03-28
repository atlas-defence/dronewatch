const state = {
  autoRefresh: true,
  timerId: null,
  lastStatus: null,
};

const severityRank = {
  info: 1,
  warning: 2,
  critical: 3,
};

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function getControls() {
  return {
    limit: Number(document.getElementById("event-limit").value),
    severity: document.getElementById("severity-filter").value,
    source: document.getElementById("source-filter").value,
  };
}

function severityPasses(event, minimumSeverity) {
  if (minimumSeverity === "all") {
    return true;
  }
  return severityRank[event.severity] >= severityRank[minimumSeverity];
}

function sourcePasses(event, sourceFilter) {
  return sourceFilter === "all" || event.reading.source === sourceFilter;
}

function formatTimestamp(isoValue) {
  return new Date(isoValue).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatConfidence(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

function formatModuleMetric(module) {
  const reading = module.last_reading;
  if (!reading || !reading.metadata) {
    return "No telemetry";
  }

  if (module.name === "rf") {
    return `${reading.metadata.band || "band ?"} // ${reading.metadata.signal_strength_dbm ?? "--"} dBm`;
  }

  if (module.name === "audio") {
    return `${reading.metadata.dominant_frequency_hz ?? "--"} Hz // ${reading.metadata.profile || "profile ?"}`;
  }

  if (module.name === "vision") {
    return `${reading.metadata.camera_id || "cam ?"} // track ${reading.metadata.track_id ?? "--"}`;
  }

  return "Telemetry active";
}

function formatModuleDetails(module) {
  const reading = module.last_reading;
  if (!reading || !reading.metadata) {
    return ["Awaiting first scanner sample", `Pulse ${module.interval_seconds}s`];
  }

  if (module.name === "rf") {
    return [
      `Vendor hint ${reading.metadata.vendor_hint || "unknown"}`,
      `Pulse ${module.interval_seconds}s`,
      reading.message,
    ];
  }

  if (module.name === "audio") {
    return [
      `Noise floor ${reading.metadata.noise_floor_db ?? "--"} dB`,
      `Pulse ${module.interval_seconds}s`,
      reading.message,
    ];
  }

  if (module.name === "vision") {
    const box = reading.metadata.bounding_box;
    const boxText = box
      ? `Box ${box.x},${box.y} ${box.w}x${box.h}`
      : "Bounding box unavailable";
    return [boxText, `Pulse ${module.interval_seconds}s`, reading.message];
  }

  return [`Pulse ${module.interval_seconds}s`, reading.message];
}

function renderModules(modules) {
  const root = document.getElementById("module-status");
  root.innerHTML = "";

  Object.values(modules).forEach((module) => {
    const reading = module.last_reading;
    const confidence = reading ? formatConfidence(reading.confidence) : "0%";
    const meterWidth = reading ? Math.max(6, Math.round(reading.confidence * 100)) : 4;
    const backend = (reading?.metadata?.backend || module.backend || "simulation").toUpperCase();
    const statusText = module.enabled ? (module.simulation_mode ? `Sim / ${backend}` : `Live / ${backend}`) : "Offline";
    const details = formatModuleDetails(module)
      .map((line) => `<div>${line}</div>`)
      .join("");

    const card = document.createElement("article");
    card.className = "scanner-card";
    card.innerHTML = `
      <div class="scanner-head">
        <div class="scanner-name">${module.name}</div>
        <span class="muted-pill">${statusText}</span>
      </div>
      <div class="scanner-flags">
        <span>${formatModuleMetric(module)}</span>
        <span>${confidence}</span>
      </div>
      <div class="signal-meter"><div class="signal-fill" style="width:${meterWidth}%"></div></div>
      <div class="scanner-body">${details}</div>
    `;
    root.appendChild(card);
  });
}

function eventMarkup(event) {
  return `
    <div class="event-topline">
      <div class="event-title">${event.reading.source.toUpperCase()} // ${event.title}</div>
      <span class="severity ${event.severity}">${event.severity}</span>
    </div>
    <div class="event-meta">${event.reading.message}</div>
    <div class="event-meta-row">
      <span class="muted-pill">${formatConfidence(event.reading.confidence)}</span>
      <span class="muted-pill">${formatTimestamp(event.created_at)}</span>
    </div>
  `;
}

function renderLatestEvent(event) {
  const root = document.getElementById("latest-event");
  if (!event) {
    root.className = "latest-event empty";
    root.textContent = "No contact matching current filters.";
    return;
  }

  root.className = "latest-event";
  root.innerHTML = `<article class="latest-card">${eventMarkup(event)}</article>`;
}

function renderEvents(events) {
  const root = document.getElementById("event-list");
  const count = document.getElementById("feed-count");
  root.innerHTML = "";
  count.textContent = `${events.length} entr${events.length === 1 ? "y" : "ies"}`;

  if (events.length === 0) {
    root.innerHTML = `<div class="event-card empty">No feed entries match the active filters.</div>`;
    return;
  }

  events.forEach((event) => {
    const card = document.createElement("article");
    card.className = "event-card";
    card.innerHTML = eventMarkup(event);
    root.appendChild(card);
  });
}

function pickPrimaryScanner(modules) {
  let topModule = null;
  for (const module of Object.values(modules)) {
    const reading = module.last_reading;
    if (!reading) {
      continue;
    }
    if (!topModule || reading.confidence > topModule.last_reading.confidence) {
      topModule = module;
    }
  }
  return topModule;
}

function updateSummary(status, filteredEvents) {
  document.getElementById("events-recorded").textContent = String(status.events_recorded).padStart(3, "0");

  const primaryScanner = pickPrimaryScanner(status.modules);
  document.getElementById("primary-scanner").textContent = primaryScanner
    ? primaryScanner.name.toUpperCase()
    : "---";

  const highestSeverity = filteredEvents[0]?.severity || status.latest_event?.severity || "info";
  const threatText =
    highestSeverity === "critical" ? "High" : highestSeverity === "warning" ? "Elevated" : "Nominal";
  document.getElementById("threat-level").textContent = threatText;

  const latestSummary = filteredEvents[0]?.reading.message || "Awaiting scanner telemetry";
  document.getElementById("latest-summary").textContent = latestSummary;

  const blip = document.getElementById("radar-blip");
  const positions = {
    rf: { top: "28%", left: "66%" },
    audio: { top: "64%", left: "38%" },
    vision: { top: "42%", left: "52%" },
  };
  const source = filteredEvents[0]?.reading.source || primaryScanner?.name;
  const position = positions[source] || { top: "50%", left: "50%" };
  blip.style.top = position.top;
  blip.style.left = position.left;
}

function applyFilters(status, events) {
  const controls = getControls();
  const filteredEvents = events
    .filter((event) => severityPasses(event, controls.severity))
    .filter((event) => sourcePasses(event, controls.source));

  renderModules(status.modules);
  renderLatestEvent(filteredEvents[0] || null);
  renderEvents(filteredEvents);
  updateSummary(status, filteredEvents);
}

async function refreshDashboard() {
  try {
    const { limit } = getControls();
    const [health, status, events] = await Promise.all([
      fetchJson("/api/health"),
      fetchJson("/api/status"),
      fetchJson(`/api/events?limit=${limit}`),
    ]);

    state.lastStatus = {
      status,
      events: events.events,
    };

    const indicator = document.getElementById("health-indicator");
    const healthText = document.getElementById("health-text");
    indicator.classList.toggle("ok", health.status === "ok");
    healthText.textContent = health.status === "ok" ? "Operational" : "Degraded";

    applyFilters(status, events.events);
  } catch (error) {
    document.getElementById("health-text").textContent = "Refresh failed";
    console.error(error);
  }
}

function handleFilterChange() {
  if (state.lastStatus) {
    applyFilters(state.lastStatus.status, state.lastStatus.events);
  }
  refreshDashboard();
}

function setAutoRefresh(enabled) {
  state.autoRefresh = enabled;
  const button = document.getElementById("refresh-toggle");
  button.classList.toggle("active", enabled);
  button.textContent = enabled ? "ON" : "OFF";

  if (state.timerId) {
    clearInterval(state.timerId);
    state.timerId = null;
  }

  if (enabled) {
    state.timerId = setInterval(refreshDashboard, 3000);
  }
}

function bindControls() {
  document.getElementById("event-limit").addEventListener("change", handleFilterChange);
  document.getElementById("severity-filter").addEventListener("change", handleFilterChange);
  document.getElementById("source-filter").addEventListener("change", handleFilterChange);
  document.getElementById("refresh-now").addEventListener("click", refreshDashboard);
  document.getElementById("refresh-toggle").addEventListener("click", () => {
    setAutoRefresh(!state.autoRefresh);
  });
}

bindControls();
refreshDashboard();
setAutoRefresh(true);
