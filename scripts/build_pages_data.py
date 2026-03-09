#!/usr/bin/env python3
"""Build static dashboard data for GitHub Pages."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DOCS_DATA_DIR = ROOT / "docs" / "data"

AIRLINES_FILE = DATA_DIR / "airlines.json"
AIRPORTS_FILE = DATA_DIR / "airports.json"
SEED_FILE = DATA_DIR / "dashboard_seed.json"
OUTPUT_FILE = DOCS_DATA_DIR / "dashboard.json"

EMOJI_BY_TYPE = {
    "NEW_ROUTE": "🆕",
    "ROUTE_SUSPENDED": "🚫",
    "ROUTE_RESUMED": "✅",
    "FREQ_CHANGE": "🔄",
    "TIME_CHANGE": "⏰",
    "AIRCRAFT_CHANGE": "✈",
    "SEASONAL_START": "🌸",
    "SEASONAL_END": "🍂",
}

CRAWL_CAPABILITIES = {
    "KE": {
        "crawl_status": "live-route",
        "crawl_label": "LIVE ROUTE",
        "crawl_note": "Official page route extraction",
    },
    "OZ": {
        "crawl_status": "live-schedule",
        "crawl_label": "LIVE SCHEDULE",
        "crawl_note": "Official browser-backed schedule search",
    },
}


def load_json(path: Path) -> list[dict] | dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def format_relative_time(timestamp: str, *, now: datetime) -> str:
    target = datetime.fromisoformat(timestamp)
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)

    delta = now - target.astimezone(now.tzinfo)
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def main() -> None:
    airlines = load_json(AIRLINES_FILE)
    airports = load_json(AIRPORTS_FILE)
    seed = load_json(SEED_FILE)

    airline_map = {item["iata_code"]: item for item in airlines}
    airport_map = {item["iata_code"]: item for item in airports}

    generated_at = seed.get("generated_at") or datetime.now().astimezone().isoformat(timespec="seconds")
    generated_dt = datetime.fromisoformat(generated_at)

    routes = []
    route_counter = Counter()
    active_routes = 0
    for item in seed["routes"]:
        airline = airline_map[item["airline"]]
        origin = airport_map[item["origin"]]
        destination = airport_map[item["destination"]]
        route_counter[item["airline"]] += 1
        if item["status"] == "ACTIVE":
            active_routes += 1
        routes.append(
            {
                "airline": item["airline"],
                "airline_name": airline["name_ko"],
                "origin": item["origin"],
                "origin_city": origin["city_ko"] or origin["name_ko"],
                "destination": item["destination"],
                "destination_city": destination["city_ko"] or destination["name_ko"],
                "flight_number": item["flight_number"],
                "departure_time": item["departure_time"],
                "arrival_time": item["arrival_time"],
                "frequency_label": item["frequency_label"],
                "status": item["status"],
            }
        )

    changes = []
    high_changes = 0
    new_routes = 0
    for item in seed["changes"]:
        airline = airline_map[item["airline"]]
        route_label = f'{item["origin"]} → {item["destination"]}'
        if item["priority"] == "HIGH":
            high_changes += 1
        if item["type"] == "NEW_ROUTE":
            new_routes += 1
        changes.append(
            {
                "type": item["type"],
                "priority": item["priority"].lower(),
                "emoji": EMOJI_BY_TYPE.get(item["type"], "📡"),
                "airline": item["airline"],
                "airline_name": airline["name_ko"],
                "route": route_label,
                "od": f'{item["origin"]}-{item["destination"]}',
                "summary": item["summary"],
                "detected_at": item["detected_at"],
                "time": format_relative_time(item["detected_at"], now=generated_dt),
            }
        )

    news = []
    for item in seed["news"]:
        news.append(
            {
                "source": item["source"],
                "title": item["title"],
                "url": item["url"],
                "related_airline": item.get("related_airline"),
                "related_route": item.get("related_route"),
                "published_at": item["published_at"],
                "time": format_relative_time(item["published_at"], now=generated_dt),
            }
        )

    airlines_payload = []
    live_airlines = 0
    live_schedule_airlines = 0
    live_route_airlines = 0
    for item in airlines:
        crawl = CRAWL_CAPABILITIES.get(
            item["iata_code"],
            {
                "crawl_status": "planned",
                "crawl_label": "PLANNED",
                "crawl_note": "Crawler not implemented yet",
            },
        )
        if crawl["crawl_status"] != "planned":
            live_airlines += 1
        if crawl["crawl_status"] == "live-schedule":
            live_schedule_airlines += 1
        if crawl["crawl_status"] == "live-route":
            live_route_airlines += 1
        airlines_payload.append(
            {
                "code": item["iata_code"],
                "name": item["name_ko"],
                "country": item["country"],
                "carrier_type": item["carrier_type"],
                "routes": route_counter.get(item["iata_code"], 0),
                "website_url": item["website_url"],
                "schedule_url": item["schedule_url"],
                "crawl_status": crawl["crawl_status"],
                "crawl_label": crawl["crawl_label"],
                "crawl_note": crawl["crawl_note"],
            }
        )

    payload = {
        "generated_at": generated_dt.isoformat(timespec="seconds"),
        "source_mode": seed.get("source_mode", "seed"),
        "summary": {
            "total_routes": len(routes),
            "active_routes": active_routes,
            "active_airlines": sum(1 for item in airlines_payload if item["routes"] > 0),
            "live_airlines": live_airlines,
            "live_schedule_airlines": live_schedule_airlines,
            "live_route_airlines": live_route_airlines,
            "high_changes": high_changes,
            "new_routes": new_routes,
            "total_changes": len(changes),
        },
        "airlines": airlines_payload,
        "changes": changes,
        "routes": routes,
        "news": news,
    }

    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Wrote {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
