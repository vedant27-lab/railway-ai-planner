import os
import json

from dotenv import load_dotenv
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = os.getenv("GROQ_MODEL")

def ask_agent(role, task):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system", "content":role},
            {"role":"user", "content":task},
        ],
        max_tokens=800,
    )

    return response.choices[0].message.content or " "

def journey_planner_agent(
        source,
        destination,
        date,
        trains,
        preference="fastest",
        feedback=None,
):

    """Recommend the user, trains, using reviewer feedback when revising."""
    role ="""
    You are a railway journey agent.

    Recommend suitable trains using only the supplied data.
    Consider the user's preference.
    Never invent train numbers, timings, fares or availiabilty or connections.

    If the data is incomplete, clearly say so. 
    Explain why your recommendation is suitable.

    Follow the user's preference and correct any issues
    identified by reviewer.
    """

    task = f"""
    Plan this journey.

    Origin: {source}
    Destination: {destination}
    Date: {date}
    Preference: {preference}

    Train Records:
    {json.dumps(trains, ensure_ascii=False, default=str)}

    Reviewer feedback from a previous attempt:
    {feedback or "No previous review. Create the initial plan."}

    Recommend up to three suitable trains.
    Include train number, name, departure, arrival, duration,
    and reasons for your recommendations.

    Correct the reviewer's identified errors using the source
    records. Do not claim a correction is verified unless
    the supplied data supports it.
    """

    return ask_agent(role, task)

def journey_reviewer_agent(
        source,
        destination,
        trains,
        recommendation,
):
    """Check the proposed journey against the supplied data."""

    role = """
    You are a strict railway journey reviewer.

    Compare the recommendation with the supplied train records.
    Check train numbers, names, departure times, arrival times,
    and durations against the source data.

    Flag the upsupported details and mismatches and any unavailable data.
    Do not invent corrections or claim live availability.
    If a field connot be varified, mark it as unverified.
    """

    task = f"""
    Requested journey: {source} to {destination}

    Available train records:
    {json.dumps(trains, ensure_ascii=False, default=str)}

    Proposed recommendation:
    {recommendation}

    Report:
    1. Which recommendations match the records.
    2. Any mismatched or unsupported details.
    3. Any important missing information.
    4. Whether the recommendation is ready to present.
    """

    return ask_agent(role, task)

