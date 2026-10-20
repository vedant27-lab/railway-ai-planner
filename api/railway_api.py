
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RAIL_RADAR_API")
BASE_URL = "https://api.railradar.in/v1"


def trains_between(from_code, to_code, journey_date=None):
    """Fetch trains between two railway stations."""

    if not API_KEY:
        raise RuntimeError(
            "RAILRADAR_API_KEY is missing from your .env file"
        )

    url = f"{BASE_URL}/trains/between/{from_code}/{to_code}"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
    }

    params = {}

    if journey_date:
        params["date"] = journey_date

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20,
        )

        response.raise_for_status()
        result = response.json()

        if not result.get("success"):
            raise RuntimeError(
                f"RailRadar API error: {result.get('error')}"
            )

        return result["data"]

    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not retrieve train data: {error}"
        ) from error


if __name__ == "__main__":
    source = input("From station code: ").strip().upper()
    destination = input("To station code: ").strip().upper()
    date = input("Journey date (YYYY-MM-DD, optional): ").strip()

    try:
        data = trains_between(
            source,
            destination,
            date or None,
        )

        print(f"\n{data['from']['name']} -> {data['to']['name']}")
        print(f"Trains found: {data['count']}\n")

        for item in data.get("trains", []):
            train = item["train"]
            departure = item.get("from", {}).get("departure", "Unknown")
            arrival = item.get("to", {}).get("arrival", "Unknown")
            duration = item.get("duration", "Unknown")

            print(
                f"{train['number']} - {train['name']}\n"
                f"  Departure: {departure}\n"
                f"  Arrival:   {arrival}\n"
                f"  Duration:  {duration} minutes\n"
            )

    except (RuntimeError, KeyError, ValueError) as error:
        print(f"Error: {error}")
