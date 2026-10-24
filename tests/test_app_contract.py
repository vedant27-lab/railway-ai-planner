from datetime import date
from unittest.mock import patch

import app as app_module
from api import railway_api
from models.model import JourneyRequest


def make_itinerary():
    return {
        "legs": [
            {
                "train": {"number": "12954", "name": "Test Express"},
                "from": {
                    "code": "NDLS",
                    "name": "NEW DELHI",
                    "date": "2026-12-03",
                    "departure": "08:00",
                },
                "to": {
                    "code": "BCT",
                    "name": "MUMBAI CENTRAL",
                    "date": "2026-12-03",
                    "arrival": "18:00",
                },
                "durationMinutes": 600,
            }
        ],
        "transfers": [],
        "totalDurationMinutes": 600,
        "overallReliability": "solid",
    }


def test_journey_request_accepts_a_date():
    request = JourneyRequest(
        origin="New Delhi",
        destination="BCT",
        journey_date="2026-12-03",
    )

    assert request.journey_date == date(2026, 12, 3)


def test_search_resolves_names_and_passes_date_to_route_planner():
    captured = {}

    def fake_plan_route(stops, max_transfers, journey_date):
        captured["stops"] = stops
        captured["max_transfers"] = max_transfers
        captured["journey_date"] = journey_date
        return {"data": make_itinerary()}

    request = JourneyRequest(
        origin="New Delhi",
        destination="Mumbai Central",
        journey_date="2026-12-03",
        max_transfers=2,
        preference="fastest",
        limit=3,
    )

    with patch.object(app_module, "plan_route", side_effect=fake_plan_route):
        result = app_module.search_journeys(request)

    assert captured == {
        "stops": ["NDLS", "BCT"],
        "max_transfers": 2,
        "journey_date": date(2026, 12, 3),
    }
    assert result["origin"] == "NDLS"
    assert result["destination"] == "BCT"
    assert result["journey_date"] == "2026-12-03"
    assert result["results_returned"] == 1
    assert result["results_total_available"] == 1


def test_station_search_uses_the_local_directory():
    result = app_module.station_search("New Delhi", limit=5)

    assert {item["code"] for item in result["results"]} >= {"NDLS"}


def test_route_client_sends_explicit_origin_date():
    response = type(
        "Response",
        (),
        {
            "raise_for_status": lambda self: None,
            "json": lambda self: {"success": True, "data": {}},
        },
    )()

    with patch.object(railway_api.os, "getenv", return_value="test-key"):
        with patch.object(railway_api.requests, "post", return_value=response) as post:
            railway_api.plan_route(
                ["New Delhi", "BCT"],
                max_transfers=2,
                journey_date=date(2026, 12, 3),
            )

    payload = post.call_args.kwargs["json"]
    assert payload == {
        "stops": [
            {"station": "NDLS", "date": "2026-12-03"},
            "BCT",
        ],
        "maxTransfers": 2,
    }
