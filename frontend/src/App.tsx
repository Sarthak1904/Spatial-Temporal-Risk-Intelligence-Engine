import React, { useEffect } from "react";

import { RiskMap } from "./components/RiskMap";
import { useTimelineStore, type RiskLevel } from "./store/timelineStore";

const riskLevels: RiskLevel[] = ["low", "medium", "high", "critical"];

function advanceDate(date: string): string {
  const current = new Date(date);
  current.setDate(current.getDate() + 1);
  return current.toISOString().slice(0, 10);
}

export default function App(): React.JSX.Element {
  const { selectedDate, isPlaying, riskLevels: enabledLevels, setSelectedDate, togglePlayback, toggleRiskLevel } =
    useTimelineStore();

  useEffect(() => {
    if (!isPlaying) {
      return;
    }
    const interval = setInterval(() => {
      setSelectedDate(advanceDate(new Date(selectedDate).toISOString().slice(0, 10)));
    }, 1200);
    return () => clearInterval(interval);
  }, [isPlaying, selectedDate, setSelectedDate]);

  return (
    <div className="app-shell">
      <aside className="side-panel">
        <h2>Spatial-Temporal Risk Intelligence</h2>
        <div className="control-group">
          <label htmlFor="risk-date">Analysis Date</label>
          <input
            id="risk-date"
            type="date"
            value={selectedDate}
            onChange={(event) => setSelectedDate(event.target.value)}
          />
          <button type="button" onClick={togglePlayback}>
            {isPlaying ? "Pause Timeline" : "Play Timeline"}
          </button>
        </div>

        <div className="control-group">
          <strong>Risk Level Filters</strong>
          <div className="level-grid">
            {riskLevels.map((level) => (
              <button key={level} type="button" onClick={() => toggleRiskLevel(level)}>
                {enabledLevels.includes(level) ? `On - ${level}` : `Off - ${level}`}
              </button>
            ))}
          </div>
        </div>
      </aside>

      <main className="map-panel">
        <RiskMap selectedDate={selectedDate} riskLevels={enabledLevels} />
      </main>
    </div>
  );
}
