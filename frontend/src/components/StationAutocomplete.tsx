import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { MapPin, Search, X } from "lucide-react";
import { searchStations } from "../api";
import type { StationSuggestion } from "../types";

type StationAutocompleteProps = {
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  error?: string;
};

export function StationAutocomplete({
  label,
  value,
  placeholder,
  onChange,
  error,
}: StationAutocompleteProps) {
  const inputId = useId();
  const listId = `${inputId}-suggestions`;
  const [suggestions, setSuggestions] = useState<StationSuggestion[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(-1);
  const [isSearching, setIsSearching] = useState(false);
  const requestRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const query = value.trim();
    requestRef.current?.abort();

    if (query.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      setIsSearching(false);
      return;
    }

    const timer = window.setTimeout(async () => {
      const controller = new AbortController();
      requestRef.current = controller;
      setIsSearching(true);
      try {
        const response = await searchStations(query, controller.signal);
        setSuggestions(response.results);
        setHighlighted(-1);
        setIsOpen(response.results.length > 0);
      } catch (requestError) {
        if (!(requestError instanceof DOMException && requestError.name === "AbortError")) {
          setSuggestions([]);
          setIsOpen(false);
        }
      } finally {
        if (!controller.signal.aborted) setIsSearching(false);
      }
    }, 160);

    return () => window.clearTimeout(timer);
  }, [value]);

  function chooseStation(station: StationSuggestion) {
    onChange(station.name);
    setSuggestions([]);
    setIsOpen(false);
    setHighlighted(-1);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!isOpen || suggestions.length === 0) {
      if (event.key === "Escape") setIsOpen(false);
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlighted((current) => (current + 1) % suggestions.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlighted((current) => (current <= 0 ? suggestions.length - 1 : current - 1));
    } else if (event.key === "Enter" && highlighted >= 0) {
      event.preventDefault();
      chooseStation(suggestions[highlighted]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setIsOpen(false);
    }
  }

  return (
    <div className={`station-field ${error ? "has-error" : ""}`}>
      <label htmlFor={inputId}>{label}</label>
      <div className="station-input-wrap">
        <MapPin size={18} aria-hidden="true" className="input-icon" />
        <input
          id={inputId}
          value={value}
          placeholder={placeholder}
          autoComplete="off"
          onChange={(event) => onChange(event.target.value)}
          onFocus={() => suggestions.length > 0 && setIsOpen(true)}
          onBlur={() => window.setTimeout(() => setIsOpen(false), 120)}
          onKeyDown={handleKeyDown}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={isOpen}
          aria-controls={listId}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${inputId}-error` : undefined}
        />
        {value && (
          <button
            type="button"
            className="clear-input"
            aria-label={`Clear ${label.toLowerCase()}`}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => onChange("")}
          >
            <X size={15} />
          </button>
        )}
        {isSearching && <Search size={16} className="search-spinner" aria-label="Searching stations" />}
      </div>
      {isOpen && suggestions.length > 0 && (
        <ul className="station-suggestions" id={listId} role="listbox">
          {suggestions.map((station, index) => (
            <li key={`${station.code}-${station.name}`} role="option" aria-selected={index === highlighted}>
              <button
                type="button"
                className={index === highlighted ? "suggestion active" : "suggestion"}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => chooseStation(station)}
              >
                <span>
                  <strong>{station.name}</strong>
                  <small>Indian Railways station</small>
                </span>
                <code>{station.code}</code>
              </button>
            </li>
          ))}
        </ul>
      )}
      {error && <p className="field-error" id={`${inputId}-error`}>{error}</p>}
    </div>
  );
}
