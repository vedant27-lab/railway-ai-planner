import { ArrowDown, Clock3, TrainFront } from "lucide-react";
import type { FormattedLeg } from "../types";

type JourneyTimelineProps = {
  legs: FormattedLeg[];
};

function stationName(label: string | undefined) {
  if (!label) return "Station details unavailable";
  const match = label.match(/^(.*) \(([^()]*)\)$/);
  return match ? match[1] : label;
}

export function JourneyTimeline({ legs }: JourneyTimelineProps) {
  return (
    <div className="journey-timeline">
      {legs.map((leg, index) => (
        <div className="timeline-leg" key={`${leg.train_number ?? "train"}-${index}`}>
          <div className="timeline-rail" aria-hidden="true">
            <span className="timeline-dot" />
            <span className="timeline-line" />
            <span className="timeline-dot timeline-dot-end" />
          </div>
          <div className="timeline-content">
            <div className="timeline-station timeline-origin">
              <div>
                <strong>{leg.departure || "—"}</strong>
                <span>{stationName(leg.from_station)}</span>
              </div>
              <small>{leg.departure_date || "Date unavailable"}</small>
            </div>
            <div className="timeline-train">
              <div className="train-icon"><TrainFront size={15} /></div>
              <span>{leg.train_number || "Train number unavailable"}</span>
              <span className="timeline-train-name">{leg.train_name || "Train name unavailable"}</span>
              {typeof leg.duration_minutes === "number" && (
                <span className="timeline-duration">
                  <Clock3 size={13} /> {formatMinutes(leg.duration_minutes)}
                </span>
              )}
            </div>
            <div className="timeline-station timeline-destination">
              <div>
                <strong>{leg.arrival || "—"}</strong>
                <span>{stationName(leg.to_station)}</span>
              </div>
              <small>{leg.arrival_date || "Date unavailable"}</small>
            </div>
          </div>
          {index < legs.length - 1 && <div className="timeline-transfer"><ArrowDown size={13} /> connection</div>}
        </div>
      ))}
    </div>
  );
}

export function formatMinutes(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const remainder = Math.round(minutes % 60);
  if (!hours) return `${remainder}m`;
  if (!remainder) return `${hours}h`;
  return `${hours}h ${remainder}m`;
}
