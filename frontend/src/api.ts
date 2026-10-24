import type {
  JourneyRequest,
  JourneyResponse,
  StationSuggestion,
} from "./types";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      const detail = body.detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail)) {
        return detail
          .map((item) => {
            if (typeof item === "object" && item !== null && "msg" in item) {
              return String(item.msg);
            }
            return String(item);
          })
          .join(" ");
      }
    }
  } catch {
    // The response may not be JSON. The status-specific fallback is clearer.
  }

  if (response.status === 502) {
    return "The railway data service is temporarily unavailable. Please try again.";
  }
  if (response.status >= 500) {
    return "The planner hit an unexpected server error. Please try again.";
  }
  if (response.status === 422) {
    return "Please check the journey details and try again.";
  }
  return `Request failed (${response.status}). Please try again.`;
}

async function request<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch {
    throw new ApiError(
      "The planner is unreachable. Make sure the Python backend is running.",
    );
  }

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError("The planner returned an unreadable response.", response.status);
  }
}

export function searchJourneys(
  payload: JourneyRequest,
  signal?: AbortSignal,
): Promise<JourneyResponse> {
  return request<JourneyResponse>("/journeys", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
}

export function searchStations(
  query: string,
  signal?: AbortSignal,
): Promise<{ results: StationSuggestion[] }> {
  const params = new URLSearchParams({ q: query, limit: "8" });
  return request<{ results: StationSuggestion[] }>(`/stations?${params}`, {
    signal,
  });
}

export function checkHealth(): Promise<{ status: string }> {
  return request<{ status: string }>("/health");
}
