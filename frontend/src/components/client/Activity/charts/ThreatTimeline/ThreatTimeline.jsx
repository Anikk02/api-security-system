import React, { useEffect, useRef, useState } from "react";
import "./ThreatTimeline.css";

function ThreatTimeline({ events = [] }) {
  const containerRef = useRef(null);
  const [expandedIndex, setExpandedIndex] = useState(null);

  // 🔄 Latest first
  const sortedEvents = [...events].reverse();

  // ⚡ Auto scroll to top
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [events]);

  return (
    <div className="timeline-card">
      <h2 className="timeline-title">🚨 Threat Timeline</h2>

      {sortedEvents.length === 0 ? (
        <p className="timeline-empty">No recent threats detected</p>
      ) : (
        <div ref={containerRef} className="timeline-container">
          {sortedEvents.map((event, index) => {
            const isCritical = event.severity === "critical";
            const isExpanded = expandedIndex === index;

            return (
              <div
                key={index}
                className={`timeline-item ${isCritical ? "critical" : ""}`}
                onClick={() =>
                  setExpandedIndex(isExpanded ? null : index)
                }
              >
                {/* Left side */}
                <div className="timeline-left">
                  <div
                    className={`timeline-dot ${event.severity}`}
                  />
                  {index !== sortedEvents.length - 1 && (
                    <div className="timeline-line" />
                  )}
                </div>

                {/* Content */}
                <div className="timeline-content">
                  <div className="timeline-header">
                    <span className="timeline-time">{event.time}</span>
                    <span className={`badge ${event.severity}`}>
                      {event.severity?.toUpperCase()}
                    </span>
                  </div>

                  <p className="timeline-event">{event.event}</p>

                  {isExpanded && (
                    <p className="timeline-desc">
                      {event.description}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ThreatTimeline;