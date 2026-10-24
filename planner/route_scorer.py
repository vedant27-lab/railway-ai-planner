
from planner.itinerary_validator import validate_itinerary
from datetime import datetime


VALID_PREFERENCES = {"fastest", "fewest_transfers", "safest"}



def _duration(itinerary):
    from datetime import datetime

    legs = itinerary.get("legs", [])

    if legs:
        try:
            first_origin = legs[0].get("from") or {}
            last_destination = legs[-1].get("to") or {}

            start = datetime.strptime(
                f"{first_origin['date']} {first_origin['departure']}",
                "%Y-%m-%d %H:%M",
            )
            end = datetime.strptime(
                f"{last_destination['date']} {last_destination['arrival']}",
                "%Y-%m-%d %H:%M",
            )

            elapsed = (end - start).total_seconds() / 60

            if elapsed >= 0:
                return elapsed
        except (KeyError, TypeError, ValueError):
            pass

    total = itinerary.get("totalDurationMinutes")
    if (
        isinstance(total, (int, float))
        and not isinstance(total, bool)
        and total >= 0
    ):
        return total

    durations = [leg.get("durationMinutes") for leg in legs]
    if legs and all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value >= 0
        for value in durations
    ):
        return sum(durations)

    return None


def _route_signature(itinerary):
    """Identify routes with the same trains, stations and schedules."""
    signature = []

    for leg in itinerary.get("legs", []):
        train = leg.get("train") or {}
        origin = leg.get("from") or {}
        destination = leg.get("to") or {}

        signature.append((
            str(train.get("number", "")),
            origin.get("code"),
            origin.get("date"),
            origin.get("departure"),
            destination.get("code"),
            destination.get("date"),
            destination.get("arrival"),
        ))

    return tuple(signature)


def _risk_details(itinerary):
    """Return a heuristic risk penalty and explanatory warnings."""
    penalty = 0
    warnings = []
    legs = itinerary.get("legs", [])
    transfers = itinerary.get("transfers", [])

    for index, transfer in enumerate(transfers):
        number = index + 1
        probability = transfer.get("connectionProbability")

        if (
            isinstance(probability, (int, float))
            and not isinstance(probability, bool)
            and 0 <= probability <= 100
        ):
            penalty += (100 - probability) * 2

            if probability < 50:
                warnings.append(
                    f"Transfer {number}: low connection probability "
                    f"({probability}%)"
                )
        else:
            penalty += 150
            warnings.append(
                f"Transfer {number}: connection probability "
                "missing or invalid"
            )

        risk = str(transfer.get("risk", "")).lower()

        if risk in {"high", "danger", "dangerous"}:
            penalty += 200
            warnings.append(
                f"Transfer {number}: API reports high risk"
            )
        elif risk in {"medium", "moderate"}:
            penalty += 75
            warnings.append(
                f"Transfer {number}: API reports medium risk"
            )

        change = transfer.get("changeStations") or {}
        change_from = change.get("from") or {}
        change_to = change.get("to") or {}

        if change_from.get("code") and change_to.get("code"):
            if change_from["code"] != change_to["code"]:
                penalty += 100
                warnings.append(
                    f"Transfer {number}: station change "
                    f"{change_from['code']} -> {change_to['code']}"
                )

                # Compare available connection time against transit time.
                if index < len(legs) - 1:
                    arrival = legs[index].get("to") or {}
                    departure = legs[index + 1].get("from") or {}

                    try:
                        from datetime import datetime

                        arrive_at = datetime.strptime(
                            f"{arrival['date']} {arrival['arrival']}",
                            "%Y-%m-%d %H:%M",
                        )
                        leave_at = datetime.strptime(
                            f"{departure['date']} {departure['departure']}",
                            "%Y-%m-%d %H:%M",
                        )

                        available = (leave_at - arrive_at).total_seconds() / 60
                        transit = change.get("transitMinutes")

                        if available <= 0:
                            warnings.append(
                                f"Transfer {number}: next departure "
                                "is not after the previous arrival"
                            )
                        elif (
                            isinstance(transit, (int, float))
                            and not isinstance(transit, bool)
                        ):
                            if transit > available:
                                penalty += 300
                                warnings.append(
                                    f"Transfer {number}: station transit "
                                    "exceeds available connection time"
                                )
                            elif available - transit < 15:
                                warnings.append(
                                    f"Transfer {number}: less than "
                                    "15 minutes spare after station transit"
                                )

                    except (KeyError, TypeError, ValueError):
                        warnings.append(
                            f"Transfer {number}: unable to verify "
                            "station-change timing"
                        )

        elif index < len(legs) - 1:
            arrival = legs[index].get("to") or {}
            departure = legs[index + 1].get("from") or {}

            if (
                arrival.get("code")
                and departure.get("code")
                and arrival["code"] != departure["code"]
            ):
                warnings.append(
                    f"Transfer {number}: station codes differ, "
                    "but change-station details are missing"
                )
                penalty += 150

    reliability = str(
        itinerary.get("overallReliability", "")
    ).lower()

    if reliability == "fragile":
        penalty += 100
        warnings.append("API reports fragile overall reliability")
    elif reliability in {"poor", "low"}:
        penalty += 200
        warnings.append("API reports poor overall reliability")

    return penalty, warnings


def _station_label(station):
    name = station.get("name") or "Unknown station"
    code = station.get("code") or "?"
    return f"{name} ({code})"


def _format_leg(leg):
    train = leg.get("train") or {}
    origin = leg.get("from") or {}
    destination = leg.get("to") or {}

    return {
        "train_number": train.get("number", "?"),
        "train_name": train.get("name", "Unknown train"),
        "from_station": _station_label(origin),
        "departure": origin.get("departure", "?"),
        "departure_date": origin.get("date", "?"),
        "to_station": _station_label(destination),
        "arrival": destination.get("arrival", "?"),
        "arrival_date": destination.get("date", "?"),
        "duration_minutes": leg.get("durationMinutes"),
        "reliability": leg.get("reliability", "unknown"),
    }


def _format_transfers(itinerary):
    result = []

    for index, transfer in enumerate(
        itinerary.get("transfers", []), start=1
    ):
        change = transfer.get("changeStations") or {}

        result.append({
            "transfer_number": index,
            "station": _station_label(transfer.get("station") or {}),
            "wait_minutes": transfer.get("waitMinutes"),
            "connection_probability": transfer.get(
                "connectionProbability"
            ),
            "change_from": (
                _station_label(change["from"])
                if change.get("from") else None
            ),
            "change_to": (
                _station_label(change["to"])
                if change.get("to") else None
            ),
            "transit_minutes": change.get("transitMinutes"),
            "risk": transfer.get("risk", "unknown"),
        })

    return result


def rank_itineraries(itineraries, preference="fastest", limit=3):
    """
    Validate, deduplicate and rank journeys without an LLM.

    fastest: shortest duration first, then lower risk.
    fewest_transfers: fewer transfers first, then lower risk.
    safest: lower heuristic risk first, then fewer transfers.

    Returns up to `limit` distinct journeys.
    """
    if preference not in VALID_PREFERENCES:
        raise ValueError(
            f"Preference must be one of: {', '.join(sorted(VALID_PREFERENCES))}"
        )

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("limit must be a positive integer")

    candidates = []
    seen = set()

    for itinerary in itineraries:
        report = validate_itinerary(itinerary)

        if not report["valid"]:
            continue

        legs = itinerary.get("legs", [])

        if not legs:
            continue

        duration = _duration(itinerary)

        if duration is None:
            continue

        signature = _route_signature(itinerary)

        if signature in seen:
            continue

        seen.add(signature)

        transfer_count = max(0, len(legs) - 1)
        penalty, risk_warnings = _risk_details(itinerary)

        warnings = list(dict.fromkeys(
            report.get("warnings", []) + risk_warnings
        ))

        if len(itinerary.get("transfers", [])) != transfer_count:
            warnings.append(
                "Transfer count does not match the number of legs"
            )

        if preference == "fastest":
            sort_key = (duration, penalty, transfer_count)
        elif preference == "fewest_transfers":
            sort_key = (transfer_count, penalty, duration)
        else:
            sort_key = (penalty, transfer_count, duration)

        candidates.append({
            "itinerary": itinerary,
            "duration_minutes": duration,
            "transfers": transfer_count,
            "risk_penalty": penalty,
            "warnings": list(dict.fromkeys(warnings)),
            "legs": [_format_leg(leg) for leg in legs],
            "transfer_details": _format_transfers(itinerary),
            "_sort_key": sort_key,
        })

    candidates.sort(key=lambda item: item["_sort_key"])

    results = []

    for rank, item in enumerate(candidates[:limit], start=1):
        item.pop("_sort_key")

        item["rank"] = rank
        item["reasons"] = [
            f"Duration: {item['duration_minutes'] // 60}h "
            f"{item['duration_minutes'] % 60}m",
            f"Transfers: {item['transfers']}",
            f"Heuristic risk penalty: {item['risk_penalty']}",
            f"Preference: {preference}",
        ]

        results.append(item)

    return results
