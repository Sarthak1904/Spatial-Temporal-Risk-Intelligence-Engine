const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/v1";

export interface RiskCell {
  h3_index: string;
  time_bucket: string;
  event_count: number;
  rolling_7d_avg: number;
  growth_rate: number;
  risk_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  anomaly_flagged: boolean;
}

export async function fetchRiskByDate(date: string): Promise<RiskCell[]> {
  const response = await fetch(`${API_BASE}/risk/${date}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch risk for date ${date}`);
  }
  return response.json() as Promise<RiskCell[]>;
}

export function tileUrl(date: string, riskLevels: string[]): string {
  const query = new URLSearchParams({
    risk_date: date,
    risk_level: riskLevels.join(",")
  });
  return `${API_BASE}/tiles/{z}/{x}/{y}.mvt?${query.toString()}`;
}
