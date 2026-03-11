"""Build and refresh the static docs dashboard payload."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
DOCS_DATA_DIR = ROOT / "docs" / "data"
DB_FILE = DATA_DIR / "airline_sked.db"

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

DEFAULT_CRAWL_CAPABILITY = {
    "crawl_status": "planned",
    "crawl_label": "PLANNED",
    "crawl_note": "Crawler not implemented yet",
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


def pick_related_news(
    item: dict,
    news_items: list[dict],
) -> dict | None:
    route_key = f'{item["origin"]}-{item["destination"]}'

    for news in news_items:
        if news.get("related_route") == route_key:
            return news
    for news in news_items:
        if news.get("related_airline") == item["airline"]:
            return news
    return None


def get_crawl_capability(airline_code: str) -> dict[str, str]:
    return CRAWL_CAPABILITIES.get(airline_code, DEFAULT_CRAWL_CAPABILITY)


def extract_primary_flight_number(flight_number: str | None) -> str | None:
    if not flight_number:
        return None

    compact = "".join(flight_number.upper().split())
    if not compact:
        return None

    primary = compact.split("/", maxsplit=1)[0]
    return primary or None


def build_flightradar24_url(flight_number: str | None) -> str | None:
    primary = extract_primary_flight_number(flight_number)
    if not primary:
        return None
    return f"https://www.flightradar24.com/data/flights/{primary.lower()}"


def build_route_source_metadata(
    *,
    airline_code: str,
    snapshot_source: str,
) -> dict[str, str | bool]:
    if snapshot_source == "seed":
        return {
            "route_source": "sample",
            "route_source_label": "SAMPLE",
            "route_source_note": "Docs sample route data",
            "has_live_data": False,
        }

    crawl = get_crawl_capability(airline_code)
    if crawl["crawl_status"] == "live-schedule":
        return {
            "route_source": "live-schedule",
            "route_source_label": "LIVE SCHEDULE",
            "route_source_note": "Latest DB snapshot from the live schedule crawler",
            "has_live_data": True,
        }
    if crawl["crawl_status"] == "live-route":
        return {
            "route_source": "live-route",
            "route_source_label": "LIVE ROUTE",
            "route_source_note": "Latest DB snapshot from the live route crawler",
            "has_live_data": True,
        }

    return {
        "route_source": "database",
        "route_source_label": "DB SNAPSHOT",
        "route_source_note": "Latest DB snapshot",
        "has_live_data": False,
    }


def build_route_payload(
    *,
    airline_code: str,
    origin_code: str,
    destination_code: str,
    flight_number: str | None,
    departure_time: str | None,
    arrival_time: str | None,
    frequency_label: str,
    status: str,
    aircraft_type: str | None,
    snapshot_source: str,
    airline_map: dict[str, dict],
    airport_map: dict[str, dict],
) -> dict:
    airline = airline_map.get(airline_code, {"name_ko": airline_code})
    origin = airport_map.get(origin_code, {"city_ko": origin_code, "name_ko": origin_code})
    destination = airport_map.get(destination_code, {"city_ko": destination_code, "name_ko": destination_code})
    primary_flight_number = extract_primary_flight_number(flight_number)
    source_meta = build_route_source_metadata(
        airline_code=airline_code,
        snapshot_source=snapshot_source,
    )
    return {
        "airline": airline_code,
        "airline_name": airline["name_ko"],
        "origin": origin_code,
        "origin_city": origin["city_ko"] or origin["name_ko"],
        "destination": destination_code,
        "destination_city": destination["city_ko"] or destination["name_ko"],
        "flight_number": flight_number,
        "primary_flight_number": primary_flight_number,
        "flight_history_url": build_flightradar24_url(primary_flight_number),
        "departure_time": departure_time,
        "arrival_time": arrival_time,
        "frequency_label": frequency_label,
        "status": status,
        "aircraft_type": aircraft_type,
        **source_meta,
    }


def build_seed_routes(
    seed_routes: list[dict],
    airline_map: dict[str, dict],
    airport_map: dict[str, dict],
) -> list[dict]:
    return [
        build_route_payload(
            airline_code=item["airline"],
            origin_code=item["origin"],
            destination_code=item["destination"],
            flight_number=item.get("flight_number"),
            departure_time=item.get("departure_time"),
            arrival_time=item.get("arrival_time"),
            frequency_label=item["frequency_label"],
            status=item["status"],
            aircraft_type=item.get("aircraft_type"),
            snapshot_source="seed",
            airline_map=airline_map,
            airport_map=airport_map,
        )
        for item in seed_routes
    ]


def has_required_tables(connection: sqlite3.Connection) -> bool:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name IN ('routes', 'schedules')
        """
    )
    return {row[0] for row in cursor.fetchall()} == {"routes", "schedules"}


def is_placeholder_flight_number(
    flight_number: str | None,
    airline_code: str,
    origin_code: str,
    destination_code: str,
) -> bool:
    if not flight_number:
        return False
    return flight_number == f"{airline_code}-{origin_code}-{destination_code}"


def format_frequency_label(
    *,
    status: str,
    frequency_weekly: int | None,
    days_of_week: str | None,
) -> str:
    if status == "SUSPENDED":
        return "Suspended"

    weekly = frequency_weekly
    if weekly is None and days_of_week:
        weekly = len([day for day in days_of_week.split(",") if day.strip()])

    if weekly == 7:
        base = "Daily"
    elif weekly:
        base = f"{weekly}x weekly"
    else:
        base = "TBD"

    if status == "SEASONAL":
        return base if base == "TBD" else f"Seasonal {base}"
    return base


def load_database_routes(
    airline_map: dict[str, dict],
    airport_map: dict[str, dict],
) -> tuple[list[dict], datetime | None]:
    if not DB_FILE.exists():
        return [], None

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row

    try:
        if not has_required_tables(connection):
            return [], None

        cursor = connection.cursor()
        cursor.execute("SELECT MAX(collected_at) FROM schedules")
        latest_collected_at = cursor.fetchone()[0]
        if not latest_collected_at:
            return [], None

        cursor.execute(
            """
            SELECT
                r.airline_code AS airline_code,
                r.origin AS origin_code,
                r.destination AS destination_code,
                r.status AS route_status,
                s.flight_number AS flight_number,
                s.departure_time AS departure_time,
                s.arrival_time AS arrival_time,
                s.aircraft_type AS aircraft_type,
                s.frequency_weekly AS frequency_weekly,
                s.days_of_week AS days_of_week
            FROM routes AS r
            LEFT JOIN schedules AS s
              ON s.id = (
                SELECT s2.id
                FROM schedules AS s2
                WHERE s2.route_id = r.id
                ORDER BY s2.collected_at DESC, s2.id DESC
                LIMIT 1
              )
            ORDER BY
              CASE r.status
                WHEN 'ACTIVE' THEN 0
                WHEN 'SEASONAL' THEN 1
                ELSE 2
              END,
              r.airline_code,
              r.origin,
              r.destination
            """
        )

        routes: list[dict] = []
        for row in cursor.fetchall():
            flight_number = row["flight_number"]
            if is_placeholder_flight_number(
                flight_number,
                row["airline_code"],
                row["origin_code"],
                row["destination_code"],
            ):
                flight_number = None

            routes.append(
                build_route_payload(
                    airline_code=row["airline_code"],
                    origin_code=row["origin_code"],
                    destination_code=row["destination_code"],
                    flight_number=flight_number,
                    departure_time=row["departure_time"],
                    arrival_time=row["arrival_time"],
                    frequency_label=format_frequency_label(
                        status=row["route_status"],
                        frequency_weekly=row["frequency_weekly"],
                        days_of_week=row["days_of_week"],
                    ),
                    status=row["route_status"],
                    aircraft_type=row["aircraft_type"],
                    snapshot_source="database",
                    airline_map=airline_map,
                    airport_map=airport_map,
                )
            )

        return routes, datetime.fromisoformat(latest_collected_at)
    finally:
        connection.close()


def build_dashboard_payload() -> dict:
    airlines = load_json(AIRLINES_FILE)
    airports = load_json(AIRPORTS_FILE)
    seed = load_json(SEED_FILE)

    airline_map = {item["iata_code"]: item for item in airlines}
    airport_map = {item["iata_code"]: item for item in airports}

    generated_at = seed.get("generated_at") or datetime.now().astimezone().isoformat(timespec="seconds")
    generated_dt = datetime.fromisoformat(generated_at)
    routes = build_seed_routes(seed["routes"], airline_map, airport_map)
    source_mode = seed.get("source_mode", "seed")

    database_routes, database_generated_dt = load_database_routes(airline_map, airport_map)
    if database_routes:
        routes = database_routes
        source_mode = "database"
        generated_dt = database_generated_dt or generated_dt

    route_counter = Counter(route["airline"] for route in routes)
    live_route_counter = Counter(route["airline"] for route in routes if route["has_live_data"])
    active_routes = sum(1 for route in routes if route["status"] == "ACTIVE")

    changes = []
    high_changes = 0
    new_routes = 0
    for item in seed["changes"]:
        airline = airline_map[item["airline"]]
        route_label = f'{item["origin"]} → {item["destination"]}'
        related_news = pick_related_news(item, seed["news"])
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
                "source_name": item.get("source_name") or (related_news.get("source") if related_news else None),
                "source_url": item.get("source_url") or (related_news.get("url") if related_news else None),
                "source_lang": item.get("source_lang") or (related_news.get("lang") if related_news else None),
            }
        )

    news = []
    for item in seed["news"]:
        news.append(
            {
                "source": item["source"],
                "title": item["title"],
                "url": item["url"],
                "lang": item.get("lang", "ko"),
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
        crawl = get_crawl_capability(item["iata_code"])
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
                "live_routes": live_route_counter.get(item["iata_code"], 0),
                "website_url": item["website_url"],
                "schedule_url": item["schedule_url"],
                "crawl_status": crawl["crawl_status"],
                "crawl_label": crawl["crawl_label"],
                "crawl_note": crawl["crawl_note"],
            }
        )

    return {
        "generated_at": generated_dt.isoformat(timespec="seconds"),
        "source_mode": source_mode,
        "summary": {
            "total_routes": len(routes),
            "active_routes": active_routes,
            "total_airlines": len(airlines_payload),
            "kr_airlines": sum(1 for item in airlines_payload if item["country"] == "KR"),
            "jp_airlines": sum(1 for item in airlines_payload if item["country"] == "JP"),
            "active_airlines": sum(1 for item in airlines_payload if item["routes"] > 0),
            "live_airlines": live_airlines,
            "live_schedule_airlines": live_schedule_airlines,
            "live_route_airlines": live_route_airlines,
            "live_snapshot_airlines": sum(1 for count in live_route_counter.values() if count > 0),
            "live_snapshot_routes": sum(live_route_counter.values()),
            "high_changes": high_changes,
            "new_routes": new_routes,
            "total_changes": len(changes),
        },
        "airlines": airlines_payload,
        "changes": changes,
        "routes": routes,
        "news": news,
    }


def refresh_dashboard_data(output_file: Path = OUTPUT_FILE) -> Path:
    payload = build_dashboard_payload()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return output_file
