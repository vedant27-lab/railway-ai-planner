from api.railway_api import trains_between
from agents.agents import journey_planner_agent, journey_reviewer_agent

def plan(
    origin,
    destination,
    date,
    preference="fastest"   
):
    trains = trains_between(
        from_code= origin, to_code=destination, journey_date=date
    )
    if not trains:
        raise FileNotFoundError("No trains data found. Please check the stations or date.")

    plan_details = journey_planner_agent(
        train=trains,
        source=origin,
        destination=destination,
        date=date,
        preference=preference
    )
    print("\n=== Journey Plan ===\n")
    print(plan_details)

    plan_review = journey_reviewer_agent(
        source=origin,
        destination=destination,
        trains=trains,
        recommendation=plan_details,
    )

    print("\n=== Journey Review ===\n")
    print(plan_review)


if __name__ == "__main__":
    origin = input("Origin station code: ").strip().upper()
    destination = input("Destination station code: ").strip().upper()
    date = input("Journey date (YYYY-MM-DD): ").strip()
    preference = input(
        "Preference (fastest, cheapest, or convenient): "
    ).strip().lower() or "fastest"

    plan(origin, destination, date, preference)
