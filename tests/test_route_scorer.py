
from planner.route_scorer import rank_itineraries


def make_route(train_number, duration, probability):
    return {
        "legs": [
            {
                "train": {"number": train_number},
                "from": {
                    "code": "AAA",
                    "date": "2026-10-22",
                    "departure": "08:00",
                },
                "to": {
                    "code": "BBB",
                    "date": "2026-10-22",
                    "arrival": "12:00",
                },
                "durationMinutes": duration,
            }
        ],
        "transfers": [],
        "totalDurationMinutes": duration,
        "overallReliability": "solid",
    }


def test_fastest_route_is_ranked_first():
    routes = [
        make_route("100", 300, 90),
        make_route("200", 240, 90),
    ]

    ranked = rank_itineraries(routes, preference="fastest")

    assert ranked[0]["itinerary"]["legs"][0]["train"]["number"] == "200"
