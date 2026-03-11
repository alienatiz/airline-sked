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

function buildTranslatedUrl(url, lang) {
  if (!url) return "#";
  if (!lang || lang === "ko") return url;
  const sourceLang = lang === "ja" || lang === "en" ? lang : "auto";
  return `https://translate.google.com/translate?sl=${sourceLang}&tl=ko&u=${encodeURIComponent(url)}`;
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

function formatFlightNumber(route) {
  return route.flight_number || "미수집";
}

function formatAircraftType(route) {
  return route.aircraft_type || "미수집";
}

function formatSourceMode(mode) {
  return mode === "database" ? "DB 최신" : "문서 샘플";
}

function formatRouteSource(route) {
  return route.route_source_label || (route.has_live_data ? "LIVE" : "SAMPLE");
}

function formatAirlineSnapshot(airline) {
  if (airline.live_routes > 0) {
    return `${airline.live_routes} live routes`;
  }
  if (airline.routes > 0) {
    return `${airline.routes} ${state.dashboard.source_mode === "database" ? "current" : "sample"} routes`;
  }
  if (airline.crawl_status !== "planned") {
    return "crawler ready";
  }
  return airline.carrier_type;
}

function buildCoverageText() {
  const configured = state.dashboard.airlines
    .filter((airline) => airline.crawl_status !== "planned")
    .map((airline) => `${airline.code} ${airline.crawl_status === "live-schedule" ? "schedule" : "route"}`);

  if (state.dashboard.source_mode !== "database") {
    return configured.length > 0
      ? `Configured crawlers: ${configured.map((item) => `${item} live`).join(" · ")}`
      : "Configured crawlers: none";
  }

  const liveByAirline = new Map();
  state.dashboard.routes.forEach((route) => {
    if (!route.has_live_data) return;
    liveByAirline.set(route.airline, (liveByAirline.get(route.airline) || 0) + 1);
  });

  if (liveByAirline.size === 0) {
    return "Current snapshot has no live rows";
  }

  return `Current live routes: ${Array.from(liveByAirline.entries())
    .map(([airline, count]) => `${airline} ${count}`)
    .join(" · ")}`;
}

function buildRouteSourceNote() {
  if (state.dashboard.source_mode === "database") {
    return `DB latest · ${state.dashboard.summary.live_snapshot_routes} live routes`;
  }
  return "Sample snapshot · live crawlers shown separately";
}

function renderStats() {
  const { summary } = state.dashboard;
  const liveCrawlerStat = state.dashboard.source_mode === "database"
    ? {
      label: "라이브 스냅샷",
      value: summary.live_snapshot_airlines,
      sub: `${summary.live_snapshot_routes} current routes`,
      color: "var(--accent-green)",
    }
    : {
      label: "구성된 크롤러",
      value: summary.live_airlines,
      sub: `schedule ${summary.live_schedule_airlines} · route ${summary.live_route_airlines}`,
      color: "var(--accent-green)",
    };
  const stats = [
    {
      label: "등록 항공사",
      value: summary.total_airlines,
      sub: `KR ${summary.kr_airlines} · JP ${summary.jp_airlines}`,
      color: "var(--accent-blue)",
    },
    liveCrawlerStat,
    { label: "긴급 변경", value: summary.high_changes, sub: "current snapshot", color: "var(--high)" },
    { label: "신규 취항", value: summary.new_routes, sub: "current snapshot", color: "var(--accent-amber)" },
    { label: "총 감지 이벤트", value: summary.total_changes, sub: formatSourceMode(state.dashboard.source_mode), color: "var(--accent-purple)" },
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
  document.getElementById("changesFeed").innerHTML = items.map((item, index) => {
    const content = `
      <div class="change-top">
        <span class="change-emoji">${escapeHtml(item.emoji)}</span>
        <span class="change-type ${escapeHtml(item.priority)}">${escapeHtml(item.type)}</span>
        <span class="change-airline">${escapeHtml(item.airline)} ${escapeHtml(item.airline_name)}</span>
        <span class="change-route">${escapeHtml(item.route)}</span>
        ${item.source_name ? `<span class="change-source">${escapeHtml(item.source_name)}</span>` : ""}
        <span class="change-time">${escapeHtml(item.time)}</span>
      </div>
      <div class="change-summary">${escapeHtml(item.summary)}</div>
    `;

    if (!item.source_url) {
      return `
        <div
          class="change-item ${escapeHtml(item.priority)}"
          style="animation-delay:${index * 0.05}s"
        >
          ${content}
        </div>
      `;
    }

    return `
      <a
        class="change-item ${escapeHtml(item.priority)} is-link"
        style="animation-delay:${index * 0.05}s"
        href="${escapeHtml(buildTranslatedUrl(item.source_url, item.source_lang))}"
        target="_blank"
        rel="noreferrer"
      >
        ${content}
      </a>
    `;
  }).join("");
}

function renderRoutes() {
  document.getElementById("routeCount").textContent = String(state.dashboard.routes.length);
  document.getElementById("routesBody").innerHTML = state.dashboard.routes.map((route) => `
    <tr>
      <td><span class="route-code">${escapeHtml(route.airline)}</span></td>
      <td class="route-od">${escapeHtml(route.origin)}<span class="route-arrow">→</span>${escapeHtml(route.destination)}</td>
      <td class="route-meta ${route.flight_number ? "" : "missing"}">
        <div class="route-flight">
          ${route.flight_history_url
            ? `<a class="route-flight-link" href="${escapeHtml(route.flight_history_url)}" target="_blank" rel="noreferrer">${escapeHtml(formatFlightNumber(route))}</a>`
            : escapeHtml(formatFlightNumber(route))}
          <div class="route-source-row">
            <span class="route-source-badge ${escapeHtml(route.route_source)}" title="${escapeHtml(route.route_source_note || "")}">${escapeHtml(formatRouteSource(route))}</span>
            ${route.flight_history_url
              ? `<a class="route-source-link" href="${escapeHtml(route.flight_history_url)}" target="_blank" rel="noreferrer">FR24</a>`
              : ""}
          </div>
        </div>
      </td>
      <td class="route-meta ${route.aircraft_type ? "" : "missing"}">${escapeHtml(formatAircraftType(route))}</td>
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
      <span class="airline-count" title="${escapeHtml(airline.carrier_type)}">${escapeHtml(formatAirlineSnapshot(airline))}</span>
    </a>
  `).join("");
}

function renderNews() {
  const items = state.dashboard.news;
  document.getElementById("newsFeed").innerHTML = items.map((item) => `
    <a class="news-item" href="${escapeHtml(buildTranslatedUrl(item.url, item.lang))}" target="_blank" rel="noreferrer">
      <div class="news-source">${escapeHtml(item.source)}</div>
      <div class="news-title">${escapeHtml(item.title)}</div>
      <div class="news-time">${escapeHtml(item.time)}</div>
    </a>
  `).join("");
}

function renderGeneratedAt() {
  const generatedAt = new Date(state.dashboard.generated_at);
  document.getElementById("statusLabel").textContent =
    state.dashboard.source_mode === "database" ? "LIVE SNAPSHOT" : "SAMPLE SNAPSHOT";
  document.getElementById("lastScan").textContent = generatedAt.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
  document.getElementById("crawlCoverage").textContent = buildCoverageText();
  document.getElementById("routeSourceNote").textContent = buildRouteSourceNote();
}

function setError(message) {
  document.getElementById("statusLabel").textContent = "ERROR";
  document.getElementById("lastScan").textContent = message;
  document.getElementById("crawlCoverage").textContent = "—";
  document.getElementById("routeSourceNote").textContent = "로드 실패";
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
