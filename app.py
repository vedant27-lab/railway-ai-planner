from typing import Literal
import traceback
import requests
from fastapi import FastAPI, HTTPException
from models.model import JourneyRequest
from api.railway_api import plan_route
from planner.itinerary_validator import validate_itinerary
from planner.route_scorer import rank_itineraries

app = FastAPI(
    title="Railway Journey Planner",
    description=(
        "Find, validate and rank railway journeys"
        "using the RailRadar API"
    ),
    version="1.0.0"
)

def find_itineraries(data):
    """Extract itinerary objects from the API response."""
    if isinstance(data, dict):
        if isinstance(data.get("legs"), list):
            return [data]

        found = []
        for value in data.values():
            found.extend(find_itineraries(value))
        return found

    if isinstance(data, list):
        found = []

        for item in data:
            found.extend(find_itineraries(item))

        return found
    return []

@app.get("/")
def home():
    return {
        "message": "Railway Journey Planner API is running.",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/journeys")
def search_journeys(request: JourneyRequest):
    """Find and rank journeys between two stations."""

    origin = request.origin.strip().upper()

    destination = request.destination.strip().upper()

    if origin == destination:
        raise HTTPException(
            status_code=400,
            detail="Origin and destination must be different.",
        )

    try:
        response = plan_route(
            [origin, destination],
            max_transfers=request.max_transfers,
        )

        itineraries = find_itineraries(response)

        if not itineraries:
            return {
                "origin": origin,
                "destination": destination,
                "preference": request.preference,
                "itineraries_found": 0,
                "valid_itineraries": 0,
                "results": [],
                "message": "No itineraries found in the API response.",
            }

        validation_reports = [
            validate_itinerary(item) for item in itineraries
        ]

        valid_itineraries = [
            item
            for item, report in zip(itineraries, validation_reports)
            if report["valid"]
        ]

        ranked = rank_itineraries(
            valid_itineraries,
            preference=request.preference,
            limit=request.limit,
        )

        return {
            "origin": origin,
            "destination": destination,
            "preference": request.preference,
            "itineraries_found": len(itineraries),
            "valid_itineraries": len(valid_itineraries),
            "results_returned": len(ranked),
            "results":ranked,
        }

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"Railway API request failed: {error}",
        ) from error

    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="An unexcepted error occurred while planning the journey.",
        ) from error

    