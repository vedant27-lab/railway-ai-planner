"""Resolve railway station names to the codes expected by RailRadar."""

import json
from functools import lru_cache
from pathlib import Path


STATION_DATA_FILE = Path(__file__).with_name("station_codes.json")


def _normalise(value):
    return " ".join(value.strip().casefold().split())


@lru_cache(maxsize=1)
def _station_indexes():
    with STATION_DATA_FILE.open(encoding="utf-8-sig") as station_file:
        stations = json.load(station_file)

    codes = {}
    names = {}

    for station in stations:
        code = station.get("code")
        name = station.get("name")

        if not isinstance(code, str) or not isinstance(name, str):
            continue

        code = code.strip()
        name = name.strip()
        if not code or not name:
            continue

        codes[_normalise(code)] = code
        names.setdefault(_normalise(name), []).append(code)

    return codes, names


@lru_cache(maxsize=1)
def _station_records():
    with STATION_DATA_FILE.open(encoding="utf-8-sig") as station_file:
        stations = json.load(station_file)

    return tuple(
        {
            "code": station["code"].strip(),
            "name": station["name"].strip(),
        }
        for station in stations
        if isinstance(station, dict)
        and isinstance(station.get("code"), str)
        and isinstance(station.get("name"), str)
        and station["code"].strip()
        and station["name"].strip()
    )


def resolve_station(value):
    """Return a station code for a code or station name.

    Unknown values are returned unchanged so existing code-based behaviour is
    preserved for values that are not in the local directory.
    """

    if not isinstance(value, str):
        return value

    normalised = _normalise(value)
    codes, names = _station_indexes()

    if normalised in codes:
        return codes[normalised]

    matching_codes = names.get(normalised, [])
    if len(matching_codes) == 1:
        return matching_codes[0]

    return value


def resolve_stops(stops):
    """Resolve station values in the existing RailRadar stops structure."""

    resolved = []
    for stop in stops:
        if isinstance(stop, str):
            resolved.append(resolve_station(stop))
            continue

        if isinstance(stop, dict):
            copied_stop = dict(stop)
            for key in ("station", "code"):
                if key in copied_stop:
                    copied_stop[key] = resolve_station(copied_stop[key])
            resolved.append(copied_stop)
            continue

        resolved.append(stop)

    return resolved


def search_stations(query, limit=8):
    """Return local station suggestions ordered by relevance."""

    normalised_query = _normalise(query)
    if not normalised_query:
        return []

    matches = []
    seen_codes = set()

    for station in _station_records():
        code = station["code"]
        name = station["name"]
        normalised_code = _normalise(code)
        normalised_name = _normalise(name)

        if normalised_query == normalised_code:
            score = 0
        elif normalised_code.startswith(normalised_query):
            score = 1
        elif normalised_name.startswith(normalised_query):
            score = 2
        elif normalised_query in normalised_name:
            score = 3
        elif normalised_query in normalised_code:
            score = 4
        else:
            continue

        if code in seen_codes:
            continue

        seen_codes.add(code)
        matches.append((score, len(name), name.casefold(), station))

    matches.sort(key=lambda item: item[:3])
    return [station for _, _, _, station in matches[:limit]]
