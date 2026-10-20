# Railway Journey Planner

> A command-line railway assistant that turns live train records into a clear, preference-aware journey plan—and then checks its own recommendation against the source data.

Railway Journey Planner combines the [RailRadar API](https://api.railradar.in/) with Groq-hosted language models to help compare trains between two stations. The planner is deliberately grounded in the returned train records: it is instructed not to invent train numbers, timings, fares, availability, or connections, and a separate reviewer gets a chance to flag unsupported details before the result is accepted.

## Why this project is useful

Finding a train is easy; choosing one and presenting the choice reliably is harder. This project demonstrates a compact agent workflow for that problem:

1. Retrieve train data for an origin, destination, and optional date.
2. Ask a planning agent to recommend up to three suitable trains.
3. Ask an independent review agent to compare the recommendation with the returned records.
4. Give the planner one opportunity to correct issues identified by the reviewer.

The result is intended as a helpful planning aid—not a ticketing, booking, or live-seat-availability system.

## Architecture

```text
                    ┌──────────────────────┐
                    │  Command-line input  │
                    │ origin / destination │
                    │ date / preference    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   RailRadar API      │
                    │ train records        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Journey planner     │◄──────────────┐
                    │  Groq language model │               │
                    └──────────┬───────────┘               │
                               │ recommendation            │ feedback
                               ▼                           │
                    ┌──────────────────────┐               │
                    │  Journey reviewer    │───────────────┘
                    │  Groq language model │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Printed plan +      │
                    │  review / correction │
                    └──────────────────────┘
```

## Features

- Fetches trains between two station codes using RailRadar.
- Supports an optional journey date.
- Accepts a user preference such as `fastest`.
- Produces recommendations with train number, name, departure, arrival, duration, and reasoning.
- Reviews recommendations against the original API response.
- Allows one planner revision when the reviewer reports `NOT READY`.
- Includes a lightweight duration parser and a direct train-listing utility for basic ranking.
- Fails loudly when API credentials are missing or an upstream request fails.

## Requirements

- Python 3.10 or newer recommended
- A RailRadar API key
- A Groq API key
- A Groq model name available to your account
- Internet access for both API calls

## Quick start

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root. The file is ignored by Git and should never be committed.

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model_name
RAIL_RADAR_API=your_railradar_api_key
```

`RAIL_RADAR_API` is the variable name currently read by the application. Make sure the model value is a model available in your Groq account.

### 4. Run the planner

```bash
python main.py
```

You will be prompted for values similar to:

```text
Origin station code: NDLS
Destination station code: BCT
Journey date (YYYY-MM-DD): 2026-11-15
Preference: fastest
```

The program prints the generated journey plan, the reviewer’s findings, and—when necessary—one corrected recommendation.

## Using the Python API

The main orchestration function can also be called from another Python module:

```python
from main import plan

recommendation = plan(
    origin="NDLS",
    destination="BCT",
    date="2026-11-15",
    preference="fastest",
)
```

The function prints the plan and review as it works, then returns the latest recommendation text. The current implementation expects station codes and a date string in `YYYY-MM-DD` format.

## Project layout

```text
.
├── main.py                      # CLI and planner/reviewer orchestration
├── api/
│   └── railway_api.py            # RailRadar HTTP client
├── agents/
│   └── agents.py                 # Groq planner and reviewer agents
├── planner/
│   └── journey_planner.py        # Direct duration ranking utility
├── tests/                        # Reserved for automated tests
├── requirements.txt              # Runtime dependencies
└── .env                         # Local secrets; ignored by Git
```

## How the agent loop works

The planner receives the complete train payload and is instructed to use only those records. The reviewer receives both the same payload and the generated recommendation, then checks the details that matter most:

- train number and name
- departure and arrival times
- reported duration
- missing or unverifiable information

If the review contains `NOT READY`, the planner is called once more with the review as feedback. After the second attempt, the application stops and asks for manual verification instead of looping indefinitely.

## Data and safety boundaries

This project intentionally does not claim to:

- book or reserve tickets;
- verify seat availability, fares, delays, cancellations, or platform information;
- guarantee that the upstream data is current or complete;
- infer connections or details that are absent from the API response.

Always confirm important travel details through an official railway or booking channel before travelling.

## Troubleshooting

### `RAILRADAR_API_KEY is missing from your .env file`

Check that `.env` is in the project root and contains the exact key used by the code:

```dotenv
RAIL_RADAR_API=your_railradar_api_key
```

### Groq authentication or model errors

Verify `GROQ_API_KEY` and set `GROQ_MODEL` to a model name supported by your Groq account. Also ensure the virtual environment has been activated before installing and running the project.

### No train data found

Confirm that both station codes are valid, the date is correctly formatted, and the RailRadar response contains records for the requested route and date.

## Development status

This is an early command-line prototype. The `tests/` directory is currently reserved for future automated coverage. Natural next steps include structured return values, input validation, retry and rate-limit handling, richer preference ranking, logging, and unit/integration tests around the API and agent loop.

## License

No license has been declared yet. Add a license before distributing or accepting external contributions.
