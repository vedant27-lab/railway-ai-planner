export type Preference = "fastest" | "fewest_transfers" | "safest";

export type JourneyRequest = {
  origin: string;
  destination: string;
  journey_date: string;
  max_transfers: number;
  preference: Preference;
  limit: number;
};

export type StationSuggestion = {
  code: string;
  name: string;
};

export type StationPoint = {
  code?: string;
  name?: string;
  date?: string;
  departure?: string;
  arrival?: string;
};

export type Train = {
  number?: string | number;
  name?: string;
  type?: string;
  category?: string;
};

export type JourneyLeg = {
  train?: Train;
  from?: StationPoint;
  to?: StationPoint;
  durationMinutes?: number;
  reliability?: string;
  expectedDelayMinutes?: number;
  delayKnown?: boolean;
};

export type JourneyTransfer = {
  station?: StationPoint;
  waitMinutes?: number;
  connectionProbability?: number;
  risk?: string;
  changeStations?: {
    from?: StationPoint;
    to?: StationPoint;
    transitMinutes?: number;
  };
};

export type RawItinerary = {
  legs?: JourneyLeg[];
  transfers?: JourneyTransfer[];
  totalDurationMinutes?: number;
  overallReliability?: string;
};

export type FormattedLeg = {
  train_number?: string | number;
  train_name?: string;
  from_station?: string;
  departure?: string;
  departure_date?: string;
  to_station?: string;
  arrival?: string;
  arrival_date?: string;
  duration_minutes?: number;
  reliability?: string;
};

export type FormattedTransfer = {
  transfer_number: number;
  station?: string;
  wait_minutes?: number;
  connection_probability?: number;
  change_from?: string | null;
  change_to?: string | null;
  transit_minutes?: number;
  risk?: string;
};

export type JourneyResult = {
  itinerary: RawItinerary;
  duration_minutes: number;
  transfers: number;
  risk_penalty: number;
  warnings: string[];
  legs: FormattedLeg[];
  transfer_details: FormattedTransfer[];
  reasons: string[];
  rank: number;
};

export type JourneyResponse = {
  origin: string;
  destination: string;
  journey_date?: string | null;
  preference: Preference;
  itineraries_found: number;
  valid_itineraries: number;
  results_returned: number;
  results_total_available?: number;
  results: JourneyResult[];
  all_results?: JourneyResult[];
  message?: string;
};

export type Category =
  | "fastest"
  | "fewest_transfers"
  | "efficient"
  | "safest"
  | "all";
