import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { motion } from "motion/react";
import {
  ArrowRight,
  CalendarDays,
  Check,
  ChevronDown,
  CircleHelp,
  Moon,
  RefreshCw,
  Search,
  Sparkles,
  Sun,
  TrainFront,
  Waves,
} from "lucide-react";
import { ApiError, checkHealth, searchJourneys } from "./api";
import { JourneyCard } from "./components/JourneyCard";
import { StationAutocomplete } from "./components/StationAutocomplete";
import type {
  Category,
  JourneyRequest,
  JourneyResponse,
  JourneyResult,
  Preference,
} from "./types";
import "./styles.css";

const preferenceLabels: Record<Preference, string> = {
  fastest: "Fastest",
  fewest_transfers: "Fewest transfers",
  safest: "Reliability signals",
};

const categoryLabels: Record<Category, string> = {
  fastest: "Fastest",
  fewest_transfers: "Fewest transfers",
  efficient: "Most efficient",
  safest: "Safest / reliability",
  all: "All journeys",
};

function todayString() {
  const date = new Date();
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
}

function formatDate(date: string) {
  if (!date) return "Date not selected";
  return new Intl.DateTimeFormat("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(`${date}T12:00:00`));
}

function formatCount(count: number) {
  return new Intl.NumberFormat("en-IN").format(count);
}

function efficiencyScore(journey: JourneyResult) {
  const waitMinutes = journey.transfer_details.reduce(
    (total, transfer) => total + (transfer.wait_minutes ?? 0),
    0,
  );
  return Math.round(journey.duration_minutes + journey.transfers * 45 + waitMinutes * 0.25);
}

function sortJourneys(journeys: JourneyResult[], category: Category) {
  const copy = [...journeys];
  if (category === "fastest") {
    return copy.sort((a, b) => a.duration_minutes - b.duration_minutes || a.transfers - b.transfers || a.risk_penalty - b.risk_penalty);
  }
  if (category === "fewest_transfers") {
    return copy.sort((a, b) => a.transfers - b.transfers || a.risk_penalty - b.risk_penalty || a.duration_minutes - b.duration_minutes);
  }
  if (category === "safest") {
    return copy.sort((a, b) => a.risk_penalty - b.risk_penalty || a.transfers - b.transfers || a.duration_minutes - b.duration_minutes);
  }
  if (category === "efficient") {
    return copy.sort((a, b) => efficiencyScore(a) - efficiencyScore(b) || a.duration_minutes - b.duration_minutes);
  }
  return copy.sort((a, b) => a.rank - b.rank);
}

function categoryForPreference(preference: Preference): Category {
  return preference;
}

export default function App() {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [journeyDate, setJourneyDate] = useState(todayString());
  const [maxTransfers, setMaxTransfers] = useState(1);
  const [preference, setPreference] = useState<Preference>("fastest");
  const [limit, setLimit] = useState(5);
  const [category, setCategory] = useState<Category>("fastest");
  const [response, setResponse] = useState<JourneyResponse | null>(null);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({ origin: "", destination: "", journeyDate: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const requestController = useRef<AbortController | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    checkHealth().then(() => setApiHealthy(true)).catch(() => setApiHealthy(false));
  }, []);

  const availableJourneys = response?.all_results ?? response?.results ?? [];
  const displayedJourneys = useMemo(
    () => sortJourneys(availableJourneys, category),
    [availableJourneys, category],
  );

  function swapStations() {
    setOrigin(destination);
    setDestination(origin);
    setFieldErrors((current) => ({ ...current, origin: "", destination: "" }));
  }

  function applyExample(nextOrigin: string, nextDestination: string) {
    setOrigin(nextOrigin);
    setDestination(nextDestination);
    setResponse(null);
    setError("");
  }

  async function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = { origin: "", destination: "", journeyDate: "" };
    if (!origin.trim()) nextErrors.origin = "Choose an origin station.";
    if (!destination.trim()) nextErrors.destination = "Choose a destination station.";
    if (origin.trim().toLowerCase() === destination.trim().toLowerCase()) {
      nextErrors.destination = "Origin and destination must be different.";
    }
    if (!journeyDate) nextErrors.journeyDate = "Choose a journey date.";
    if (journeyDate && journeyDate < todayString()) nextErrors.journeyDate = "Choose today or a future date.";
    setFieldErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) return;

    requestController.current?.abort();
    const controller = new AbortController();
    requestController.current = controller;
    setIsLoading(true);
    setError("");
    setCategory(categoryForPreference(preference));

    const payload: JourneyRequest = {
      origin: origin.trim(),
      destination: destination.trim(),
      journey_date: journeyDate,
      max_transfers: maxTransfers,
      preference,
      limit,
    };

    try {
      const result = await searchJourneys(payload, controller.signal);
      setResponse(result);
      setApiHealthy(true);
      window.setTimeout(() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (requestError) {
      if (!(requestError instanceof DOMException && requestError.name === "AbortError")) {
        setError(requestError instanceof ApiError ? requestError.message : "Something went wrong while finding journeys.");
        setApiHealthy(false);
      }
    } finally {
      if (!controller.signal.aborted) setIsLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />
      <header className="topbar page-width">
        <a href="#top" className="brand" aria-label="Railwise AI home">
          <span className="brand-mark"><TrainFront size={18} /></span>
          <span>railwise<span className="brand-accent">.ai</span></span>
        </a>
        <div className="topbar-actions">
          <span className="status-pill">
            <span className={`status-dot ${apiHealthy === false ? "offline" : ""}`} />
            {apiHealthy === false ? "Backend offline" : "Live planning"}
          </span>
          <button type="button" className="icon-button" onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>
            {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
          </button>
        </div>
      </header>

      <main id="top">
        <section className="hero page-width">
          <div className="hero-copy">
            <motion.div className="eyebrow" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
              <Sparkles size={14} /> intelligent rail planning <span>·</span> India
            </motion.div>
            <motion.h1 initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.08 }}>
              Make the journey<br /><em>worth taking.</em>
            </motion.h1>
            <motion.p className="hero-description" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.18 }}>
              Compare real railway routes across speed, transfers and reliability signals — then choose the one that fits your day.
            </motion.p>
          </div>
          <div className="hero-visual" aria-hidden="true">
            <div className="orbit orbit-large" />
            <div className="orbit orbit-small" />
            <div className="route-node node-start" />
            <div className="route-node node-end" />
            <svg viewBox="0 0 560 220" className="route-art">
              <path d="M30 178 C150 40 230 204 336 90 S470 43 530 72" />
              <path className="route-art-dash" d="M30 178 C150 40 230 204 336 90 S470 43 530 72" />
            </svg>
            <span className="route-label route-label-start">west</span>
            <span className="route-label route-label-end">north</span>
            <div className="route-train"><TrainFront size={20} /></div>
          </div>
        </section>

        <section className="search-panel page-width" aria-labelledby="search-title">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Plan a route</span>
              <h2 id="search-title">Where are you headed?</h2>
            </div>
            <span className="panel-note"><Waves size={14} /> powered by live route data</span>
          </div>
          <form onSubmit={submitSearch} noValidate>
            <div className="station-row">
              <StationAutocomplete label="From" value={origin} placeholder="Station name or code" onChange={setOrigin} error={fieldErrors.origin} />
              <button type="button" className="swap-button" onClick={swapStations} aria-label="Swap origin and destination"><RefreshCw size={17} /></button>
              <StationAutocomplete label="To" value={destination} placeholder="Station name or code" onChange={setDestination} error={fieldErrors.destination} />
            </div>
            <div className="search-controls">
              <label className={`control-field ${fieldErrors.journeyDate ? "has-error" : ""}`}>
                <span>Date</span>
                <span className="control-input"><CalendarDays size={17} /><input type="date" value={journeyDate} min={todayString()} onChange={(event) => setJourneyDate(event.target.value)} aria-invalid={Boolean(fieldErrors.journeyDate)} /></span>
                {fieldErrors.journeyDate && <small className="field-error">{fieldErrors.journeyDate}</small>}
              </label>
              <label className="control-field">
                <span>Max transfers</span>
                <span className="control-input"><ArrowRight size={17} /><select value={maxTransfers} onChange={(event) => setMaxTransfers(Number(event.target.value))}>{[0, 1, 2, 3, 4, 5].map((value) => <option value={value} key={value}>{value === 0 ? "Direct only" : `${value} ${value === 1 ? "transfer" : "transfers"}`}</option>)}</select><ChevronDown size={15} /></span>
              </label>
              <label className="control-field">
                <span>Rank by</span>
                <span className="control-input"><GaugeIcon /><select value={preference} onChange={(event) => setPreference(event.target.value as Preference)}>{Object.entries(preferenceLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><ChevronDown size={15} /></span>
              </label>
              <label className="control-field limit-field">
                <span>Results</span>
                <span className="control-input"><span className="limit-number">{limit}</span><input type="range" min="1" max="10" value={limit} onChange={(event) => setLimit(Number(event.target.value))} aria-label="Number of results" /></span>
              </label>
              <button className="find-button" type="submit" disabled={isLoading}>
                {isLoading ? <span className="button-loader" /> : <Search size={18} />}
                {isLoading ? "Finding routes" : "Find journeys"}
                {!isLoading && <ArrowRight size={16} />}
              </button>
            </div>
          </form>
          <div className="example-row">
            <span>Try an example</span>
            <button type="button" onClick={() => applyExample("CSMT", "Bhopal Jn")}>CSMT <ArrowRight size={12} /> Bhopal Jn</button>
            <button type="button" onClick={() => applyExample("New Delhi", "Mumbai Central")}>New Delhi <ArrowRight size={12} /> Mumbai Central</button>
          </div>
        </section>

        {error && <motion.div className="error-banner page-width" role="alert" initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}><CircleHelp size={18} /><span>{error}</span><button type="button" onClick={() => setError("")}>Dismiss</button></motion.div>}

        {isLoading && <LoadingState />}

        {response && !isLoading && (
          <ResultsSection
            response={response}
            category={category}
            setCategory={setCategory}
            displayedJourneys={displayedJourneys}
            availableJourneys={availableJourneys}
          />
        )}
      </main>
      <footer className="footer page-width"><span>railwise.ai</span><span>Thoughtful routes for real journeys.</span><span>Indian Railways data · verify before travel</span></footer>
    </div>
  );
}

function GaugeIcon() {
  return <span className="gauge-icon" aria-hidden="true">↗</span>;
}

function LoadingState() {
  return (
    <section className="loading-state page-width" aria-live="polite" aria-label="Finding journeys">
      <div className="loading-track"><span /><span /><span /><span /><div className="loading-train"><TrainFront size={20} /></div></div>
      <span className="section-kicker">Searching live corridors</span>
      <h2>Finding a route that fits.</h2>
      <p>Checking connections, transfer timing and the signals available in the railway data.</p>
    </section>
  );
}

type ResultsSectionProps = {
  response: JourneyResponse;
  category: Category;
  setCategory: (category: Category) => void;
  displayedJourneys: JourneyResult[];
  availableJourneys: JourneyResult[];
};

function ResultsSection({ response, category, setCategory, displayedJourneys, availableJourneys }: ResultsSectionProps) {
  const hasResults = availableJourneys.length > 0;
  return (
    <section className="results-section page-width" id="results" aria-labelledby="results-title">
      <div className="results-heading">
        <div>
          <span className="section-kicker">Your route brief</span>
          <h2 id="results-title">{response.origin} <span>to</span> {response.destination}</h2>
          <p><CalendarDays size={15} /> {response.journey_date ? formatDate(response.journey_date) : "Date not supplied"} <i /> {formatCount(response.valid_itineraries)} valid of {formatCount(response.itineraries_found)} found</p>
        </div>
        <button type="button" className="modify-button" onClick={() => document.getElementById("search-title")?.scrollIntoView({ behavior: "smooth" })}>Modify search <RefreshCw size={15} /></button>
      </div>

      <div className="category-bar" role="tablist" aria-label="Journey ranking categories">
        {(Object.keys(categoryLabels) as Category[]).map((item) => (
          <button type="button" role="tab" aria-selected={category === item} className={category === item ? "category-tab active" : "category-tab"} onClick={() => setCategory(item)} key={item}>
            {categoryLabels[item]}
            {item === "all" && <span className="tab-count">{availableJourneys.length}</span>}
          </button>
        ))}
      </div>

      {!hasResults ? (
        <EmptyState response={response} />
      ) : (
        <>
          <div className="category-context">
            <div><strong>{categoryLabels[category]}</strong><span>{category === "safest" ? "Uses the planner's heuristic reliability signals, not a real-world safety guarantee." : category === "efficient" ? "Duration + transfer count + reported waiting time, compared transparently." : `Showing ${displayedJourneys.length} of ${availableJourneys.length} valid journeys returned by the planner.`}</span></div>
            <span className="result-count">{displayedJourneys.length} results</span>
          </div>
          <ComparisonStrip journeys={displayedJourneys} />
          <div className="journey-list">
            {displayedJourneys.map((journey, index) => (
              <JourneyCard
                journey={journey}
                index={index}
                key={`${journey.rank}-${journey.legs.map((leg) => leg.train_number).join("-")}`}
                badge={index === 0 && category !== "all" ? `${categoryLabels[category]} option` : undefined}
                efficiencyScore={category === "efficient" ? efficiencyScore(journey) : undefined}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function ComparisonStrip({ journeys }: { journeys: JourneyResult[] }) {
  if (journeys.length < 2) return null;
  const longest = Math.max(...journeys.map((journey) => journey.duration_minutes), 1);
  return (
    <div className="comparison-strip" aria-label="Journey comparison">
      <div className="comparison-title"><span>Quick comparison</span><small>duration across returned options</small></div>
      <div className="comparison-bars">
        {journeys.slice(0, 5).map((journey) => (
          <div className="comparison-row" key={journey.rank}>
            <span>#{journey.rank}</span>
            <div className="bar-track"><span style={{ width: `${Math.max(10, (journey.duration_minutes / longest) * 100)}%` }} /></div>
            <strong>{Math.round(journey.duration_minutes / 60)}h {journey.duration_minutes % 60}m</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyState({ response }: { response: JourneyResponse }) {
  return (
    <div className="empty-state">
      <div className="empty-icon"><TrainFront size={25} /></div>
      <h3>{response.itineraries_found > 0 ? "No journeys cleared validation" : "No journey found for this corridor"}</h3>
      <p>{response.itineraries_found > 0 ? "The planner received route data, but the available journeys did not pass the structural checks." : "Try a nearby major station, increase the transfer limit, or choose another date."}</p>
      <span><Check size={14} /> No results were fabricated</span>
    </div>
  );
}
