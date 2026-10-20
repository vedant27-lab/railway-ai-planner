
from api.railway_api import trains_between
from agents.agents import journey_planner_agent, journey_reviewer_agent


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


if __name__ == "__main__":
    origin = input("Origin station code: ").strip().upper()
    destination = input("Destination station code: ").strip().upper()
    date = input("Journey date (YYYY-MM-DD): ").strip()
    preference = input("Preference: ").strip().lower() or "fastest"

    plan(origin, destination, date, preference)
