
import unittest

from planner.itinerary_validator import validate_itinerary
from planner.route_scorer import rank_itineraries


def make_leg(number, origin, destination, departure, arrival,
             departure_date="2026-12-03", arrival_date="2026-12-03"):
    return {
        "train": {"number": number, "name": f"Train {number}"},
        "from": {
            "code": origin,
            "name": origin,
            "date": departure_date,
            "departure": departure,
        },
        "to": {
            "code": destination,
            "name": destination,
            "date": arrival_date,
            "arrival": arrival,
        },
        "durationMinutes": 120,
    }


def make_itinerary(train1="10001", train2="10002",
                   probability=90, duration=300):
    return {
        "legs": [
            make_leg(train1, "PUNE", "KYN", "08:00", "10:00"),
            make_leg(train2, "KYN", "TNA", "11:00", "13:00"),
        ],
        "transfers": [
            {
                "station": {"code": "KYN", "name": "Kalyan"},
                "waitMinutes": 60,
                "connectionProbability": probability,
                "risk": "low",
            }
        ],
        "totalDurationMinutes": duration,
        "overallReliability": "reliable",
    }


class TestItineraryValidator(unittest.TestCase):

    def test_valid_itinerary(self):
        report = validate_itinerary(make_itinerary())
        self.assertTrue(report["valid"], report["errors"])

    def test_departure_before_previous_arrival_is_invalid(self):
        itinerary = make_itinerary()
        itinerary["legs"][1]["from"]["departure"] = "09:30"

        report = validate_itinerary(itinerary)

        self.assertFalse(report["valid"])
        self.assertTrue(report["errors"])

    def test_station_mismatch_without_change_details_is_invalid(self):
        itinerary = make_itinerary()
        itinerary["legs"][1]["from"]["code"] = "TNA"

        report = validate_itinerary(itinerary)

        self.assertFalse(report["valid"])

    def test_low_probability_is_a_warning(self):
        report = validate_itinerary(make_itinerary(probability=20))

        self.assertTrue(report["valid"])
        self.assertTrue(
            any("low connection probability" in warning
                for warning in report["warnings"])
        )

    def test_empty_legs_are_invalid(self):
        report = validate_itinerary({"legs": [], "transfers": []})
        self.assertFalse(report["valid"])


class TestRouteScorer(unittest.TestCase):

    def test_duplicate_routes_are_removed(self):
        route = make_itinerary()
        ranked = rank_itineraries([route, route.copy()], limit=3)

        self.assertEqual(len(ranked), 1)

    def test_fastest_prefers_shorter_journey(self):
        slow = make_itinerary("10001", "10002", duration=400)
        fast = make_itinerary("20001", "20002", duration=250)

        ranked = rank_itineraries(
            [slow, fast], preference="fastest", limit=2
        )

        self.assertEqual(ranked[0]["duration_minutes"], 250)

    def test_invalid_preference_is_rejected(self):
        with self.assertRaises(ValueError):
            rank_itineraries(
                [make_itinerary()], preference="cheapest"
            )


if __name__ == "__main__":
    unittest.main()
