import { useMemo } from "react";
import api from "../services/api";
import useFetch from "../hooks/useFetch";
import { sampleSummary, sampleAnomalies, sampleIssues } from "../utils/sampleData";
import { fmtNum, fmtDate } from "../utils/format";
import StatCard from "../components/StatCard";
import LineChart from "../components/LineChart";
import Badge from "../components/Badge";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";

function normalizeSummary(raw, demo) {
  if (!raw) return demo ? sampleSummary : null;
  if (raw.trend) return raw;
  return {
    totalConsumption: raw.totalConsumption || raw.totals || sampleSummary.totalConsumption,
    totalBuildings: raw.totalBuildings !== undefined ? raw.totalBuildings : (raw.buildings || sampleSummary.totalBuildings),
    activeIssues: raw.activeIssues !== undefined ? raw.activeIssues : (raw.openIssues || sampleSummary.activeIssues),
    anomaliesCount: raw.anomaliesCount !== undefined ? raw.anomaliesCount : sampleSummary.anomaliesCount,
    efficiencyScore: raw.efficiencyScore || sampleSummary.efficiencyScore,
    trend: raw.trend || raw.consumptionTrend || sampleSummary.trend,
  };
}

function toList(d, key) {
  if (!d) return null;
  if (Array.isArray(d)) return d;
  return d[key] || d.items || d.data || null;
}

export default function Dashboard() {
  const sum = useFetch(() => api.get("/api/dashboard/summary"));
  const anom = useFetch(() => api.ai.get("/api/anomalies"));
  const iss = useFetch(() => api.get("/api/issues"));

  const demoMode = Boolean(sum.error || anom.error);
  const summary = useMemo(() => normalizeSummary(sum.data, demoMode), [sum.data, demoMode]);
  const anomalies = toList(anom.data, "anomalies") || (demoMode ? sampleAnomalies : []);
  const issues = toList(iss.data, "issues") || (demoMode ? sampleIssues : []);

  if (sum.loading && !sum.data) return <LoadingSpinner text="Loading campus summary..." />;

  return (
    <div>
      <h1 className="page-title">Campus Overview</h1>
      <p className="muted">Live resource intelligence across buildings, updated from the API.</p>

      {demoMode && (
        <AlertBanner type="warn">
          <strong>SAMPLE — demo mode:</strong> API unreachable, showing sample data.{" "}
          <span className="muted">{sum.error && sum.error.message}</span>
        </AlertBanner>
      )}
      {sum.error && <ErrorState error={sum.error} onRetry={sum.refetch} />}

      {summary && (
        <div>
          <div className="grid cards-4">
            <StatCard label="Electricity" value={fmtNum(summary.totalConsumption && summary.totalConsumption.electricity) + " kWh"} sub="Total consumption" icon="E" />
            <StatCard label="Water" value={fmtNum(summary.totalConsumption && summary.totalConsumption.water) + " kL"} sub="Total consumption" icon="W" />
            <StatCard label="Buildings tracked" value={summary.totalBuildings} sub="Across campus" icon="B" />
            <StatCard label="Open issues" value={summary.activeIssues} sub={(summary.anomaliesCount !== undefined ? summary.anomaliesCount : anomalies.length) + " AI anomalies"} icon="!" />
          </div>

          <div className="grid cards-2">
            <div className="card">
              <h3>Consumption trend</h3>
              <LineChart data={summary.trend} />
            </div>
            <div className="card">
              <h3>Anomaly alerts {demoMode && <Badge tone="amber">SAMPLE</Badge>}</h3>
              {anomalies.length === 0 ? (
                <p className="muted">No anomalies detected.</p>
              ) : (
                <ul className="list">
                  {anomalies.slice(0, 5).map((a, i) => (
                    <li key={a.id || i} className="list-item">
                      <Badge tone={a.severity === "high" ? "red" : a.severity === "medium" ? "amber" : "gray"}>
                        {a.severity || "info"}
                      </Badge>{" "}
                      <strong>{a.building || a.buildingName}</strong> · {a.resourceType} —{" "}
                      {a.message || ("value " + a.value + " vs expected " + a.expected)}
                      <span className="muted"> · {fmtDate(a.date || a.createdAt)}</span>
                    </li>
                  ))}
                </ul>
              )}
              <h3 style={{ marginTop: 16 }}>Issues snapshot</h3>
              {issues.length === 0 ? (
                <p className="muted">No open issues.</p>
              ) : (
                <ul className="list">
                  {issues.slice(0, 4).map((t, i) => (
                    <li key={t.id || i} className="list-item">
                      <Badge tone={t.status === "resolved" ? "green" : t.status === "in_progress" ? "blue" : "amber"}>
                        {t.status || "open"}
                      </Badge>{" "}
                      {t.title} <span className="muted">· {t.building || t.buildingName}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
