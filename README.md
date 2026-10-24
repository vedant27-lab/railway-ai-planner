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

- Fetches railway journeys between station names or station codes using RailRadar.
- Provides a local station directory and `/stations` autocomplete endpoint.
- Supports an optional journey date.
- Accepts `fastest`, `fewest_transfers`, or `safest` ranking preferences.
- Produces recommendations with train number, name, departure, arrival, duration, and reasoning.
- Reviews recommendations against the original API response.
- Allows one planner revision when the reviewer reports `NOT READY`.
- Includes a lightweight duration parser and a direct train-listing utility for basic ranking.
- Fails loudly when API credentials are missing or an upstream request fails.

## Requirements

- Python 3.10 or newer recommended
- Node.js 20 or newer and npm for the web frontend
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

### 4. Run the backend API

From the project root in Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

The backend is available at `http://127.0.0.1:8000`.

- Swagger API documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- Station autocomplete: `http://127.0.0.1:8000/stations?q=delhi`

### 5. Run the Railwise AI frontend

In a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/health`, `/stations`, and `/journeys` to the local FastAPI server, so no public backend URL or browser API key is required.

From the project root, the equivalent shortcuts are `npm run install:frontend`, `npm run dev`, `npm run build`, and `npm run preview`.

### 6. Run the original command-line planner

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

The function prints the plan and review as it works, then returns the latest recommendation text. Station codes and station names from `station_codes.json` are accepted at the API boundary.

## Journey API contract

`POST /journeys` accepts:

```json
{
  "origin": "New Delhi",
  "destination": "BCT",
  "journey_date": "2026-12-03",
  "max_transfers": 2,
  "preference": "fastest",
  "limit": 5
}
```

`journey_date` is passed to the RailRadar journey planner as the date on the origin stop. The API keeps the existing snake_case request fields and adds this optional field for backward compatibility. The response keeps the existing `results` field and also exposes `all_results` for the frontend's client-side category comparisons.

The frontend categories are based on returned data:

- **Fastest** sorts by total duration, then transfers and heuristic risk.
- **Fewest transfers** sorts by transfer count, then heuristic risk and duration.
- **Most efficient** uses a transparent client-side comparison of duration, transfer count, and reported waiting time.
- **Safest / reliability** uses the backend's heuristic risk/reliability signals. It is not a real-world safety guarantee.
- **All journeys** shows all valid journeys returned by the backend; it does not claim to enumerate theoretical routes beyond the upstream response.

The backend never exposes `RAIL_RADAR_API` or `GROQ_API_KEY` to the frontend. Station suggestions are read from the local `station_codes.json` directory.

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
├── tests/                        # Backend and ranking tests
├── frontend/                     # React + TypeScript + Vite web application
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

### Frontend cannot reach the backend

Start the backend first with `uvicorn app:app --reload --host 127.0.0.1 --port 8000`, then restart the Vite development server. The frontend expects the backend at port `8000` through its development proxy.

### Date or reliability questions

The selected date is sent to the journey-planning request. Reliability and risk values come only from the upstream response and the existing structural/heuristic checks. This project does not provide ticket booking, fares, seat availability, cancellation guarantees, or a real-world safety score.

## Development status

The project now includes a local React frontend alongside the original Python planner. The upstream RailRadar response remains the source of journey data; the frontend only compares and presents the journeys returned by the backend.

## License

No license has been declared yet. Add a license before distributing or accepting external contributions.
