import { AnimatePresence, motion } from "motion/react";
import { AlertTriangle, ChevronDown, CircleCheck, Gauge, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { JourneyResult } from "../types";
import { JourneyTimeline, formatMinutes } from "./JourneyTimeline";

type JourneyCardProps = {
  journey: JourneyResult;
  badge?: string;
  efficiencyScore?: number;
  index: number;
};

export function JourneyCard({ journey, badge, efficiencyScore, index }: JourneyCardProps) {
  const [expanded, setExpanded] = useState(false);
  const warningCount = journey.warnings.length;

  return (
    <motion.article
      className="journey-card"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.08 }}
      layout
    >
      <div className="journey-card-topline">
        <div className="card-rank"><span>0{journey.rank}</span> journey</div>
        {badge && <span className="category-badge">{badge}</span>}
      </div>

      <div className="journey-card-header">
        <div className="journey-summary">
          <div className="summary-stat primary-stat">
            <span>total duration</span>
            <strong>{formatMinutes(journey.duration_minutes)}</strong>
          </div>
          <div className="summary-stat">
            <span>transfers</span>
            <strong>{journey.transfers === 0 ? "Direct" : journey.transfers}</strong>
          </div>
          <div className="summary-stat">
            <span>reliability signal</span>
            <strong className="reliability-value"><ShieldCheck size={15} /> {journey.itinerary.overallReliability || "Unavailable"}</strong>
          </div>
        </div>
        <div className="route-brief">
          <span>{journey.legs[0]?.from_station || "Origin unavailable"}</span>
          <span className="route-arrow">→</span>
          <span>{journey.legs[journey.legs.length - 1]?.to_station || "Destination unavailable"}</span>
        </div>
      </div>

      <JourneyTimeline legs={journey.legs} />

      <div className="journey-card-footer">
        <div className="journey-signals">
          <span><Gauge size={14} /> risk penalty {journey.risk_penalty}</span>
          {efficiencyScore !== undefined && <span>efficiency score {efficiencyScore}</span>}
          {warningCount > 0 ? (
            <span className="warning-signal"><AlertTriangle size={14} /> {warningCount} {warningCount === 1 ? "check" : "checks"}</span>
          ) : (
            <span className="good-signal"><CircleCheck size={14} /> validation clear</span>
          )}
        </div>
        <button type="button" className="details-toggle" onClick={() => setExpanded((current) => !current)} aria-expanded={expanded}>
          {expanded ? "Hide details" : "View journey details"}
          <ChevronDown size={16} className={expanded ? "rotated" : ""} />
        </button>
      </div>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            className="journey-details"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28 }}
          >
            <div className="details-grid">
              <div>
                <span className="details-label">Ranking explanation</span>
                <ul className="reason-list">
                  {journey.reasons.map((reason) => <li key={reason}>{reason}</li>)}
                </ul>
              </div>
              <div>
                <span className="details-label">Connection details</span>
                {journey.transfer_details.length === 0 ? (
                  <p className="muted-copy">Direct journey — no connection wait reported.</p>
                ) : (
                  <ul className="transfer-list">
                    {journey.transfer_details.map((transfer) => (
                      <li key={transfer.transfer_number}>
                        <strong>Transfer {transfer.transfer_number}</strong>
                        <span>{transfer.station || "Station unavailable"}</span>
                        <span>{typeof transfer.wait_minutes === "number" ? `${transfer.wait_minutes} min wait` : "Wait unavailable"}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
            {warningCount > 0 && (
              <div className="warning-box">
                <AlertTriangle size={16} />
                <div>
                  <strong>Verification notes</strong>
                  <ul>{journey.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}
