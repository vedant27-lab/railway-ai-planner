
from datetime import datetime


def _minutes(date, time):
    """Convert a date and HH:MM time into comparable minutes."""
    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    return int(dt.timestamp() // 60)


def validate_itinerary(itinerary):
    """
    Return a validation report for one RailRadar itinerary.
    Does not modify the original API response.
    """
    errors = []
    warnings = []

    legs = itinerary.get("legs")
    transfers = itinerary.get("transfers", [])

    if not isinstance(legs, list) or not legs:
        return {
            "valid": False,
            "errors": ["Missing or empty legs list"],
            "warnings": [],
        }

    if not isinstance(transfers, list):
        return {
            "valid": False,
            "errors": ["Transfers must be a list"],
            "warnings": [],
        }

    if len(transfers) != len(legs) - 1:
        warnings.append(
            f"Expected {len(legs) - 1} transfers for "
            f"{len(legs)} legs; received {len(transfers)}"
        )
    for index, leg in enumerate(legs, start=1):
        train = leg.get("train") or {}
        origin = leg.get("from") or {}
        destination = leg.get("to") or {}

        if not train.get("number"):
            errors.append(f"Leg {index}: missing train number")

        if not origin.get("code") or not destination.get("code"):
            errors.append(f"Leg {index}: missing station code")

        if not origin.get("date") or not origin.get("departure"):
            errors.append(f"Leg {index}: missing departure date/time")

        if not destination.get("date") or not destination.get("arrival"):
            errors.append(f"Leg {index}: missing arrival date/time")

        try:
            if (
                origin.get("date")
                and origin.get("departure")
                and destination.get("date")
                and destination.get("arrival")
            ):
                start = _minutes(
                    origin["date"], origin["departure"]
                )
                end = _minutes(
                    destination["date"], destination["arrival"]
                )

                if end <= start:
                    errors.append(
                        f"Leg {index}: arrival is not after departure"
                    )
        except (ValueError, TypeError):
            errors.append(f"Leg {index}: invalid date/time format")
    for index in range(len(legs) - 1):
        current = legs[index]
        following = legs[index + 1]

        arrival = current.get("to") or {}
        departure = following.get("from") or {}

        if not (
            arrival.get("date")
            and arrival.get("arrival")
            and departure.get("date")
            and departure.get("departure")
        ):
            continue

        try:
            arrived_at = _minutes(
                arrival["date"], arrival["arrival"]
            )
            leaves_at = _minutes(
                departure["date"], departure["departure"]
            )
        except (ValueError, TypeError):
            continue

        if leaves_at <= arrived_at:
            errors.append(
                f"Transfer {index + 1}: next train departs "
                "before the previous train arrives"
            )
            continue
        if arrival.get("code") != departure.get("code"):
            transfer = (
                transfers[index]
                if index < len(transfers)
                else {}
            )
            change = transfer.get("changeStations") or {}
            change_from = change.get("from") or {}
            change_to = change.get("to") or {}

            if (
                change_from.get("code") != arrival.get("code")
                or change_to.get("code") != departure.get("code")
            ):
                warnings.append(
                    f"Transfer {index + 1}: station change is "
                    "missing or does not match the leg stations"
                )
            else:
                transit = change.get("transitMinutes")

                if isinstance(transit, (int, float)):
                    available = leaves_at - arrived_at

                    if transit > available:
                        errors.append(
                            f"Transfer {index + 1}: station transfer "
                            "takes longer than the available connection"
                        )
                    elif available - transit < 15:
                        warnings.append(
                            f"Transfer {index + 1}: less than "
                            "15 minutes remain after station transit"
                        )

        transfer = (
            transfers[index]
            if index < len(transfers)
            else {}
        )

        probability = transfer.get("connectionProbability")

        if isinstance(probability, (int, float)):
            if not 0 <= probability <= 100:
                warnings.append(
                    f"Transfer {index + 1}: invalid connection "
                    "probability"
                )
            elif probability < 50:
                warnings.append(
                    f"Transfer {index + 1}: low connection "
                    f"probability ({probability}%)"
                )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
