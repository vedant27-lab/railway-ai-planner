
from api.railway_api import trains_between, plan_route
from agents.agents import journey_planner_agent, journey_reviewer_agent
from planner.itinerary_validator import validate_itinerary
from planner.route_scorer import rank_itineraries



def plan(origin, destination, date, preference="fastest"):
    trains = trains_between(
        from_code=origin,
        to_code=destination,
        journey_date=date,
    )

    if not trains:
        print("No train data found.")
        return

    # First attempt
    recommendation = journey_planner_agent(
        source=origin,
        destination=destination,
        date=date,
        trains=trains,
        preference=preference,
    )

    for attempt in range(2):
        print("\n=== JOURNEY PLAN ===")
        print(recommendation)

        review = journey_reviewer_agent(
            source=origin,
            destination=destination,
            trains=trains,
            recommendation=recommendation,
        )

        print("\n=== JOURNEY REVIEW ===")
        print(review)

        review_text = review.upper()

        # Stop if the reviewer says the plan is ready.
        if "NOT READY" not in review_text:
            print("\nReview did not flag the plan as NOT READY.")
            return recommendation

        if attempt == 1:
            print("\nCorrection limit reached. Manual verification needed.")
            return recommendation

        print("\nIssues found. Requesting one correction...")

        recommendation = journey_planner_agent(
            source=origin,
            destination=destination,
            date=date,
            trains=trains,
            preference=preference,
            feedback=review,
        )

    return recommendation

def find_itineraries(data):
    """Find itinerary objects inside the API response."""
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

def main():
    response = plan_route(["CSMT", "NDLS"], max_transfers=1)
    itineraries = find_itineraries(response)

    if not itineraries:
        print("No itineraries found in the API response.")
        return []

    valid_itineraries = []

    for index, itinerary in enumerate(itineraries, start=1):
        report = validate_itinerary(itinerary)

        print(f"\n--- Itinerary {index} ---")
        print("Valid:", report["valid"])

        for error in report["errors"]:
            print("ERROR:", error)

        for warning in report["warnings"]:
            print("WARNING:", warning)

        if report["valid"]:
            valid_itineraries.append(itinerary)

    print(f"\nChecked: {len(itineraries)}")
    print(f"Passed structural checks: {len(valid_itineraries)}")

    return valid_itineraries



#if __name__ == "__main__":
    #origin = input("Origin station code: ").strip().upper()
    #destination = input("Destination station code: ").strip().upper()
    #date = input("Journey date (YYYY-MM-DD): ").strip()
    #preference = input("Preference: ").strip().lower() or "fastest"

    #plan(origin, destination, date, preference)
    
if __name__ == "__main__":
    itineraries = main()

    if itineraries:
        ranked = rank_itineraries(
            itineraries,
            preference="fastest",
            limit=3,
        )

        if not ranked:
            print("\nNo rankable itineraries found.")
        else:
            print("\n========== TOP JOURNEYS ==========")

            for item in ranked:
                print(f"\n{'=' * 40}")
                print(f"RANK {item['rank']}")
                print(f"Duration: {item['duration_minutes'] // 60}h "
                      f"{item['duration_minutes'] % 60}m")
                print(f"Transfers: {item['transfers']}")
                print(f"Risk penalty: {item['risk_penalty']}")
                print("Reasons:", "; ".join(item["reasons"]))

                for leg_number, leg in enumerate(item["legs"], start=1):
                    print(f"\n  Leg {leg_number}: "
                          f"{leg['train_number']} - {leg['train_name']}")
                    print(f"  From: {leg['from_station']}")
                    print(f"  Departure: {leg['departure']} "
                          f"({leg['departure_date']})")
                    print(f"  To: {leg['to_station']}")
                    print(f"  Arrival: {leg['arrival']} "
                          f"({leg['arrival_date']})")
                    print(f"  Reliability: {leg['reliability']}")

                for transfer in item["transfer_details"]:
                    print(f"\n  Transfer {transfer['transfer_number']}:")
                    print(f"  Reported wait: "
                          f"{transfer['wait_minutes']} minutes")
                    print(f"  Connection probability: "
                          f"{transfer['connection_probability']}%")

                    if transfer["change_from"] and transfer["change_to"]:
                        print(f"  Station change: "
                              f"{transfer['change_from']} -> "
                              f"{transfer['change_to']}")
                        print(f"  Transit time: "
                              f"{transfer['transit_minutes']} minutes")

                if item["warnings"]:
                    print("\n  WARNINGS:")
                    for warning in item["warnings"]:
                        print(f"  - {warning}")
                else:
                    print("\n  No warnings detected by current checks.")


