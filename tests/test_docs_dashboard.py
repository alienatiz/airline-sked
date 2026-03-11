"""Dashboard data builder tests."""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

import airline_sked.docs_dashboard as docs_dashboard


def test_load_database_routes_prefers_latest_schedule_and_hides_placeholders(tmp_path, monkeypatch):
    db_path = tmp_path / "airline_sked.db"
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE routes (
            id INTEGER PRIMARY KEY,
            airline_code TEXT,
            origin TEXT,
            destination TEXT,
            status TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE schedules (
            id INTEGER PRIMARY KEY,
            route_id INTEGER,
            flight_number TEXT,
            departure_time TEXT,
            arrival_time TEXT,
            aircraft_type TEXT,
            frequency_weekly INTEGER,
            days_of_week TEXT,
            collected_at TEXT
        )
        """
    )
    cursor.execute("INSERT INTO routes VALUES (1, 'KE', 'ICN', 'NRT', 'ACTIVE')")
    cursor.execute("INSERT INTO routes VALUES (2, 'OZ', 'ICN', 'HND', 'ACTIVE')")
    cursor.execute(
        "INSERT INTO schedules VALUES "
        "(1, 1, 'KE-ICN-NRT', NULL, NULL, NULL, NULL, NULL, '2026-03-09T01:00:00'),"
        "(2, 2, 'OZ178', '08:00', '10:15', 'A321', 7, '1,2,3,4,5,6,7', '2026-03-09T02:00:00')"
    )
    connection.commit()
    connection.close()

    monkeypatch.setattr(docs_dashboard, "DB_FILE", db_path)

    airline_map = {
        "KE": {"name_ko": "대한항공"},
        "OZ": {"name_ko": "아시아나항공"},
    }
    airport_map = {
        "ICN": {"city_ko": "인천", "name_ko": "인천"},
        "NRT": {"city_ko": "도쿄", "name_ko": "도쿄"},
        "HND": {"city_ko": "도쿄", "name_ko": "도쿄"},
    }

    routes, generated_dt = docs_dashboard.load_database_routes(airline_map, airport_map)

    assert generated_dt is not None
    assert generated_dt.isoformat() == "2026-03-09T02:00:00"
    assert routes[0]["airline"] == "KE"
    assert routes[0]["flight_number"] is None
    assert routes[0]["route_source"] == "live-route"
    assert routes[0]["route_source_label"] == "OFFICIAL ROUTE"
    assert routes[0]["flight_history_url"] is None
    assert routes[0]["has_live_data"] is True
    assert routes[0]["aircraft_type"] is None
    assert routes[0]["frequency_label"] == "TBD"
    assert routes[1]["airline"] == "OZ"
    assert routes[1]["flight_number"] == "OZ178"
    assert routes[1]["primary_flight_number"] == "OZ178"
    assert routes[1]["route_source"] == "live-schedule"
    assert routes[1]["flight_history_url"] == "https://www.flightradar24.com/data/flights/oz178"
    assert routes[1]["has_live_data"] is True
    assert routes[1]["aircraft_type"] == "A321"
    assert routes[1]["frequency_label"] == "Daily"


def test_load_database_routes_prefers_latest_informative_schedule_over_newer_placeholder(tmp_path, monkeypatch):
    db_path = tmp_path / "airline_sked.db"
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE routes (
            id INTEGER PRIMARY KEY,
            airline_code TEXT,
            origin TEXT,
            destination TEXT,
            status TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE schedules (
            id INTEGER PRIMARY KEY,
            route_id INTEGER,
            flight_number TEXT,
            departure_time TEXT,
            arrival_time TEXT,
            aircraft_type TEXT,
            frequency_weekly INTEGER,
            days_of_week TEXT,
            collected_at TEXT
        )
        """
    )
    cursor.execute("INSERT INTO routes VALUES (1, 'KE', 'ICN', 'NRT', 'ACTIVE')")
    cursor.execute(
        "INSERT INTO schedules VALUES "
        "(1, 1, 'KE701', '09:20', '11:40', 'B787', 7, '1,2,3,4,5,6,7', '2026-03-09T01:00:00'),"
        "(2, 1, 'KE-ICN-NRT', '00:00', '00:00', NULL, NULL, 'UNKNOWN', '2026-03-09T02:00:00')"
    )
    connection.commit()
    connection.close()

    monkeypatch.setattr(docs_dashboard, "DB_FILE", db_path)

    airline_map = {"KE": {"name_ko": "대한항공"}}
    airport_map = {
        "ICN": {"city_ko": "인천", "name_ko": "인천"},
        "NRT": {"city_ko": "도쿄", "name_ko": "도쿄"},
    }

    routes, generated_dt = docs_dashboard.load_database_routes(airline_map, airport_map)

    assert generated_dt is not None
    assert generated_dt.isoformat() == "2026-03-09T02:00:00"
    assert routes[0]["flight_number"] == "KE701"
    assert routes[0]["departure_time"] == "09:20"
    assert routes[0]["arrival_time"] == "11:40"
    assert routes[0]["flight_history_url"] == "https://www.flightradar24.com/data/flights/ke701"


def test_build_route_payload_marks_sample_route_and_adds_flightradar_link():
    route = docs_dashboard.build_route_payload(
        airline_code="KE",
        origin_code="ICN",
        destination_code="NRT",
        flight_number="KE701/702",
        departure_time="09:20",
        arrival_time="11:40",
        frequency_label="Daily",
        status="ACTIVE",
        aircraft_type="B787-9",
        snapshot_source="seed",
        airline_map={"KE": {"name_ko": "대한항공", "schedule_url": "https://example.com/ke-schedule"}},
        airport_map={
            "ICN": {"city_ko": "인천", "name_ko": "인천"},
            "NRT": {"city_ko": "도쿄", "name_ko": "도쿄"},
        },
    )

    assert route["route_source"] == "sample"
    assert route["route_source_label"] == "SAMPLE DATA"
    assert route["has_live_data"] is False
    assert route["primary_flight_number"] == "KE701"
    assert route["flight_history_url"] == "https://www.flightradar24.com/data/flights/ke701"
    assert route["schedule_source_url"] == "https://example.com/ke-schedule"


def test_build_pages_script_bootstraps_src_path(monkeypatch):
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "build_pages_data.py"
    src_path = str(script_path.parent.parent / "src")

    monkeypatch.setattr(sys, "path", [entry for entry in sys.path if entry != src_path])

    spec = importlib.util.spec_from_file_location("build_pages_data_test", script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert sys.path[0] == src_path
