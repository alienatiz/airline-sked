"""Airline scraper helper tests."""

from __future__ import annotations

from datetime import date

from airline_sked.scrapers.airlines import (
    _build_oz_search_payload,
    _build_oz_weekly_schedules,
    _extract_ke_routes_from_text,
    _extract_oz_direct_segments,
)


def test_extract_ke_routes_from_text_filters_to_kr_jp_routes():
    text = """
    Seoul (ICN) to Tokyo (NRT)
    Seoul (ICN) to Osaka (KIX)
    Seoul (ICN) to Los Angeles (LAX)
    Busan (PUS) to Fukuoka (FUK)
    """

    routes = _extract_ke_routes_from_text(text)

    assert routes == [("ICN", "NRT"), ("ICN", "KIX"), ("PUS", "FUK")]


def test_build_oz_search_payload_uses_city_mapping():
    payload = _build_oz_search_payload("ICN", "NRT", date(2026, 3, 11))

    assert payload["departureAirport"] == "ICN"
    assert payload["departureCity"] == "SEL"
    assert payload["arrivalAirport"] == "NRT"
    assert payload["departureDate"] == "20260311"
    assert payload["tripType"] == "OW"


def test_extract_oz_direct_segments_filters_direct_oz_rows():
    payload = {
        "timeTable": {
            "departureTimeTableAvailDataList": [
                {
                    "flightInfoDataList": [[
                        {
                            "carrierCode": "OZ",
                            "flightNo": "101",
                            "departureAirport": "ICN",
                            "arrivalAirport": "NRT",
                            "departureDate": "202603110930",
                            "arrivalDate": "202603111145",
                            "aircraftType": "A321",
                        }
                    ]]
                },
                {
                    "flightInfoDataList": [[
                        {
                            "carrierCode": "OZ",
                            "flightNo": "201",
                            "departureAirport": "ICN",
                            "arrivalAirport": "KIX",
                            "departureDate": "202603110930",
                            "arrivalDate": "202603111145",
                            "aircraftType": "A321",
                        }
                    ]]
                },
                {
                    "flightInfoDataList": [[
                        {
                            "carrierCode": "OZ",
                            "flightNo": "301",
                            "departureAirport": "ICN",
                            "arrivalAirport": "NRT",
                            "departureDate": "202603110930",
                            "arrivalDate": "202603111145",
                            "aircraftType": "A321",
                        },
                        {
                            "carrierCode": "OZ",
                            "flightNo": "999",
                            "departureAirport": "NRT",
                            "arrivalAirport": "CTS",
                            "departureDate": "202603111300",
                            "arrivalDate": "202603111430",
                            "aircraftType": "A321",
                        },
                    ]]
                },
            ]
        }
    }

    segments = _extract_oz_direct_segments(payload, "ICN", "NRT")

    assert len(segments) == 1
    assert segments[0]["flightNo"] == "101"


def test_build_oz_weekly_schedules_merges_days_by_flight():
    segments = [
        {
            "carrierCode": "OZ",
            "flightNo": "101",
            "departureAirport": "ICN",
            "arrivalAirport": "NRT",
            "departureDate": "202603090930",
            "arrivalDate": "202603091145",
            "aircraftType": "A321",
        },
        {
            "carrierCode": "OZ",
            "flightNo": "101",
            "departureAirport": "ICN",
            "arrivalAirport": "NRT",
            "departureDate": "202603110930",
            "arrivalDate": "202603111145",
            "aircraftType": "A321",
        },
    ]

    schedules = _build_oz_weekly_schedules("OZ", segments)

    assert len(schedules) == 1
    assert schedules[0].flight_number == "OZ101"
    assert schedules[0].days_of_week == "1,3"
    assert schedules[0].frequency_weekly == 2
    assert schedules[0].departure_time == "09:30"
