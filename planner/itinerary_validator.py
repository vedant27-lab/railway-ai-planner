
from datetime import datetime


def _parse_datetime(date, time):
    """Parse a local railway date and HH:MM time."""
    return datetime.strptime(
        f"{date} {time}", "%Y-%m-%d %H:%M"
    )


def validate_itinerary(itinerary):
    """
    Validate the structure and timing of a RailRadar itinerary.

    Returns:
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str]
        }

    This checks supplied data; it cannot guarantee real-world train status.
    """
    errors = []
    warnings = []

    if not isinstance(itinerary, dict):
        return {
            "valid": False,
            "errors": ["Itinerary must be a dictionary"],
            "warnings": [],
        }

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

    expected_transfers = len(legs) - 1

    if len(transfers) != expected_transfers:
        warnings.append(
            f"Expected {expected_transfers} transfers for "
            f"{len(legs)} legs; received {len(transfers)}"
        )

    parsed_legs = []

    for index, leg in enumerate(legs, start=1):
        if not isinstance(leg, dict):
            errors.append(f"Leg {index}: must be an object")
            parsed_legs.append(None)
            continue

        train = leg.get("train")
        origin = leg.get("from")
        destination = leg.get("to")

        if not isinstance(train, dict):
            train = {}
        if not isinstance(origin, dict):
            origin = {}
        if not isinstance(destination, dict):
            destination = {}

        if not train.get("number"):
            errors.append(f"Leg {index}: missing train number")

        if not origin.get("code") or not destination.get("code"):
            errors.append(f"Leg {index}: missing station code")

        start = None
        end = None

        try:
            if origin.get("date") and origin.get("departure"):
                start = _parse_datetime(
                    origin["date"], origin["departure"]
                )
            else:
                errors.append(
                    f"Leg {index}: missing departure date/time"
                )
        except (ValueError, TypeError):
            errors.append(
                f"Leg {index}: invalid departure date/time"
            )

        try:
            if destination.get("date") and destination.get("arrival"):
                end = _parse_datetime(
                    destination["date"], destination["arrival"]
                )
            else:
                errors.append(
                    f"Leg {index}: missing arrival date/time"
                )
        except (ValueError, TypeError):
            errors.append(
                f"Leg {index}: invalid arrival date/time"
            )

        if start is not None and end is not None and end <= start:
            errors.append(
                f"Leg {index}: arrival is not after departure"
            )

        parsed_legs.append({
            "origin": origin,
            "destination": destination,
            "start": start,
            "end": end,
        })

    for index in range(expected_transfers):
        current = parsed_legs[index]
        following = parsed_legs[index + 1]
        transfer_number = index + 1

        if current is None or following is None:
            continue

        arrival = current["destination"]
        departure = following["origin"]
        arrived_at = current["end"]
        leaves_at = following["start"]

        arrival_code = arrival.get("code")
        departure_code = departure.get("code")

        transfer = transfers[index] if index < len(transfers) else {}

        if not isinstance(transfer, dict):
            warnings.append(
                f"Transfer {transfer_number}: transfer data "
                "must be an object"
            )
            transfer = {}

        change = transfer.get("changeStations")
        if not isinstance(change, dict):
            change = {}

        change_from = change.get("from")
        change_to = change.get("to")

        if not isinstance(change_from, dict):
            change_from = {}
        if not isinstance(change_to, dict):
            change_to = {}

        station_change = (
            arrival_code
            and departure_code
            and arrival_code != departure_code
        )

        if station_change:
            if (
                change_from.get("code") != arrival_code
                or change_to.get("code") != departure_code
            ):
                errors.append(
                    f"Transfer {transfer_number}: consecutive legs "
                    "use different stations, but station-change "
                    "details are missing or inconsistent"
                )
            else:
                warnings.append(
                    f"Transfer {transfer_number}: change stations "
                    f"from {arrival_code} to {departure_code}"
                )
        elif (
            arrival_code
            and departure_code
            and arrival_code == departure_code
            and change_from.get("code")
            and change_to.get("code")
            and change_from.get("code") != change_to.get("code")
        ):
            warnings.append(
                f"Transfer {transfer_number}: station-change "
                "metadata conflicts with the leg station codes"
            )

        if arrived_at is not None and leaves_at is not None:
            available_minutes = (
                leaves_at - arrived_at
            ).total_seconds() / 60

            if available_minutes <= 0:
                errors.append(
                    f"Transfer {transfer_number}: next train departs "
                    "before or at the previous train's arrival"
                )
            elif station_change:
                transit = change.get("transitMinutes")

                if (
                    isinstance(transit, (int, float))
                    and not isinstance(transit, bool)
                    and transit >= 0
                ):
                    if transit > available_minutes:
                        errors.append(
                            f"Transfer {transfer_number}: station "
                            "transfer takes longer than the available "
                            "connection time"
                        )
                    elif available_minutes - transit < 15:
                        warnings.append(
                            f"Transfer {transfer_number}: less than "
                            "15 minutes remain after station transit"
                        )
                elif transit is not None:
                    warnings.append(
                        f"Transfer {transfer_number}: invalid "
                        "station transit duration"
                    )
                else:
                    warnings.append(
                        f"Transfer {transfer_number}: station transit "
                        "duration is unavailable"
                    )

        probability = transfer.get("connectionProbability")

        if probability is None:
            warnings.append(
                f"Transfer {transfer_number}: connection probability "
                "unavailable"
            )
        elif (
            not isinstance(probability, (int, float))
            or isinstance(probability, bool)
            or not 0 <= probability <= 100
        ):
            warnings.append(
                f"Transfer {transfer_number}: invalid connection "
                "probability"
            )
        elif probability < 50:
            warnings.append(
                f"Transfer {transfer_number}: low connection "
                f"probability ({probability}%)"
            )

    return {
        "valid": not errors,
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
    }
