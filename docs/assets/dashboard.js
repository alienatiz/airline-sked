const DATA_URL = "./data/dashboard.json";

const state = {
  dashboard: null,
  changeFilter: "all",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatStatus(status) {
  if (status === "ACTIVE") return "ACTIVE";
  if (status === "SUSPENDED") return "SUSPENDED";
  return "SEASONAL";
}

function formatFlightWindow(route) {
  if (!route.departure_time || !route.arrival_time) {
    return "—";
  }
  return `${route.departure_time} → ${route.arrival_time}`;
}

function renderStats() {
  const { summary } = state.dashboard;
  const stats = [
    { label: "모니터링 노선", value: summary.total_routes, sub: `ACTIVE ${summary.active_routes}`, color: "var(--accent-blue)" },
    {
      label: "라이브 크롤러",
      value: summary.live_airlines,
      sub: `schedule ${summary.live_schedule_airlines} · route ${summary.live_route_airlines}`,
      color: "var(--accent-green)",
    },
    { label: "긴급 변경", value: summary.high_changes, sub: "current snapshot", color: "var(--high)" },
    { label: "신규 취항", value: summary.new_routes, sub: "current snapshot", color: "var(--accent-amber)" },
    { label: "총 감지 이벤트", value: summary.total_changes, sub: state.dashboard.source_mode, color: "var(--accent-purple)" },
  ];

  document.getElementById("statsRow").innerHTML = stats.map((item) => `
    <div class="stat-card">
      <div class="stat-label">${escapeHtml(item.label)}</div>
      <div class="stat-value" style="color:${item.color}">${escapeHtml(item.value)}</div>
      <div class="stat-sub">${escapeHtml(item.sub)}</div>
    </div>
  `).join("");
}

function renderChanges() {
  const items = state.changeFilter === "all"
    ? state.dashboard.changes
    : state.dashboard.changes.filter((item) => item.priority === state.changeFilter);

  document.getElementById("changeCount").textContent = String(items.length);
  document.getElementById("changesFeed").innerHTML = items.map((item, index) => `
    <div class="change-item ${escapeHtml(item.priority)}" style="animation-delay:${index * 0.05}s">
      <div class="change-top">
        <span class="change-emoji">${escapeHtml(item.emoji)}</span>
        <span class="change-type ${escapeHtml(item.priority)}">${escapeHtml(item.type)}</span>
        <span class="change-airline">${escapeHtml(item.airline)} ${escapeHtml(item.airline_name)}</span>
        <span class="change-route">${escapeHtml(item.route)}</span>
        <span class="change-time">${escapeHtml(item.time)}</span>
      </div>
      <div class="change-summary">${escapeHtml(item.summary)}</div>
    </div>
  `).join("");
}

function renderRoutes() {
  document.getElementById("routeCount").textContent = String(state.dashboard.routes.length);
  document.getElementById("routesBody").innerHTML = state.dashboard.routes.map((route) => `
    <tr>
      <td><span class="route-code">${escapeHtml(route.airline)}</span></td>
      <td class="route-od">${escapeHtml(route.origin)}<span class="route-arrow">→</span>${escapeHtml(route.destination)}</td>
      <td style="font-family:var(--mono); font-size:12px; color:var(--text-secondary);">${escapeHtml(route.flight_number)}</td>
      <td style="font-family:var(--mono); font-size:12px;">${escapeHtml(formatFlightWindow(route))}</td>
      <td><span class="freq-badge">${escapeHtml(route.frequency_label)}</span></td>
      <td><span class="status-badge status-${escapeHtml(route.status.toLowerCase())}">${escapeHtml(formatStatus(route.status))}</span></td>
    </tr>
  `).join("");
}

function renderAirlines() {
  document.getElementById("airlineCount").textContent = String(state.dashboard.airlines.length);
  document.getElementById("airlineGrid").innerHTML = state.dashboard.airlines.map((airline) => `
    <a class="airline-item" href="${escapeHtml(airline.schedule_url || airline.website_url || "#")}" target="_blank" rel="noreferrer">
      <span class="airline-code ${escapeHtml(airline.country.toLowerCase())}">${escapeHtml(airline.code)}</span>
      <span class="airline-meta">
        <span class="airline-name">${escapeHtml(airline.name)}</span>
        <span class="crawl-badge ${escapeHtml(airline.crawl_status)}" title="${escapeHtml(airline.crawl_note)}">${escapeHtml(airline.crawl_label)}</span>
      </span>
      <span class="airline-count">${escapeHtml(airline.routes)}</span>
    </a>
  `).join("");
}

function renderNews() {
  const items = state.dashboard.news;
  document.getElementById("newsFeed").innerHTML = items.map((item) => `
    <a class="news-item" href="${escapeHtml(item.url || "#")}" target="_blank" rel="noreferrer">
      <div class="news-source">${escapeHtml(item.source)}</div>
      <div class="news-title">${escapeHtml(item.title)}</div>
      <div class="news-time">${escapeHtml(item.time)}</div>
    </a>
  `).join("");
}

function renderGeneratedAt() {
  const generatedAt = new Date(state.dashboard.generated_at);
  document.getElementById("statusLabel").textContent = state.dashboard.summary.live_airlines > 0 ? "LIVE COVERAGE" : "SNAPSHOT";
  document.getElementById("lastScan").textContent = generatedAt.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
  document.getElementById("crawlCoverage").textContent =
    `KE route live · OZ schedule live`;
}

function setError(message) {
  document.getElementById("statusLabel").textContent = "ERROR";
  document.getElementById("lastScan").textContent = message;
  document.getElementById("crawlCoverage").textContent = "—";
}

function filterChanges(button) {
  document.querySelectorAll(".filter-tab").forEach((element) => element.classList.remove("active"));
  button.classList.add("active");
  state.changeFilter = button.dataset.filter || "all";
  renderChanges();
}

async function initDashboard() {
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    state.dashboard = await response.json();
    renderGeneratedAt();
    renderStats();
    renderChanges();
    renderRoutes();
    renderAirlines();
    renderNews();
  } catch (error) {
    console.error("Failed to load dashboard data", error);
    setError("dashboard.json load failed");
  }
}

window.filterChanges = filterChanges;
document.addEventListener("DOMContentLoaded", initDashboard);
