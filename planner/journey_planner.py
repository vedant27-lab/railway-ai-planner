
from datetime import datetime
from railway_api import trains_between


def duration_minutes(value):
    """Convert a duration into minutes where possible."""

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        # Handle formats such as "18h 30m" or "18:30".
        try:
            if "h" in value.lower():
                hours = 0
                minutes = 0

                parts = value.lower().split("h")
                hours = int(parts[0].strip())

                if len(parts) > 1:
                    minute_text = parts[1].lower().replace("m", "").strip()
                    if minute_text:
                        minutes = int(minute_text)

                return hours * 60 + minutes

            if ":" in value:
                hours, minutes = map(int, value.split(":"))
                return hours * 60 + minutes

        except ValueError:
            pass

    return float("inf")


def plan_journey(source, destination, date=None):
    data = trains_between(source, destination, date)

    trains = data.get("trains", [])

    if not trains:
        print("No trains were returned for this journey.")
        return

    # Shortest reported duration first.
    ranked = sorted(
        trains,
        key=lambda item: duration_minutes(item.get("duration")),
    )

    print(f"\nJourney: {source} -> {destination}")
    print(f"Trains found: {len(ranked)}")

    for index, item in enumerate(ranked[:10], start=1):
        train = item.get("train", {})

        print(f"\n{index}. {train.get('name', 'Unknown train')}")
        print(f"   Number: {train.get('number', 'Unknown')}")
        print(
            "   Departure:",
            item.get("from", {}).get("departure", "Unknown"),
        )
        print(
            "   Arrival:",
            item.get("to", {}).get("arrival", "Unknown"),
        )
        print(
            "   Duration:",
            item.get("duration", "Unknown"),
        )


if __name__ == "__main__":
    source = input("From station code: ").strip().upper()
    destination = input("To station code: ").strip().upper()
    date = input("Journey date (YYYY-MM-DD): ").strip()

    plan_journey(source, destination, date or None)
