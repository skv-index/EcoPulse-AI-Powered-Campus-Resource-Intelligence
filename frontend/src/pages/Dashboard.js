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

import Chart from "../components/Chart";

// Real backend shape: { totals_30d, per_building, counts, issues_by_status, window }.
// View model used below: { totalConsumption, totalBuildings, activeIssues,
// anomaliesCount, trend (optional), perBuilding }.
function normalizeSummary(raw, demo, anomaliesCount) {
  if (!raw) return demo ? sampleSummary : null;
  if (raw.trend || raw.totalConsumption) return raw;
  const totals = raw.totals_30d || {};
  const counts = raw.counts || {};
  return {
    totalConsumption: {
      electricity: totals.electricity || 0,
      water: totals.water || 0,
      waste: totals.waste || 0,
    },
    totalBuildings: counts.buildings !== undefined ? counts.buildings : sampleSummary.totalBuildings,
    activeIssues: counts.issues_open !== undefined ? counts.issues_open : sampleSummary.activeIssues,
    anomaliesCount: anomaliesCount !== undefined ? anomaliesCount : sampleSummary.anomaliesCount,
    trend: raw.trend || null,
    perBuilding: raw.per_building || [],
  };
}

function toList(d, key) {
  if (!d) return null;
  if (Array.isArray(d)) return d;
  return d[key] || d.items || d.data || null;
}

export default function Dashboard() {
  const sum = useFetch(() => api.get("/api/dashboard/summary"));
  const anom = useFetch(() => api.ai.get("/api/ai/anomalies"));
  const iss = useFetch(() => api.get("/api/issues"));

  const anomList = toList(anom.data, "anomalies");
  const demoMode = Boolean(sum.error || anom.error);
  const summary = useMemo(
    () => normalizeSummary(sum.data, demoMode, anomList ? anomList.length : undefined),
    [sum.data, demoMode, anomList ? anomList.length : 0]
  );
  const anomalies = anomList || (demoMode ? sampleAnomalies : []);
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
              <h3>Consumption (last 30 days)</h3>
              {summary.trend ? (
                <LineChart data={summary.trend} />
              ) : summary.perBuilding && summary.perBuilding.length ? (
                <Chart
                  kind="bar"
                  data={summary.perBuilding}
                  xKey="building_name"
                  series={[
                    { key: "electricity", name: "Electricity (kWh)", color: "#0d7a5f" },
                    { key: "water", name: "Water (L)", color: "#0ea5a4" },
                    { key: "waste", name: "Waste (kg)", color: "#b45309" },
                  ]}
                />
              ) : (
                <p className="muted">No consumption data yet.</p>
              )}
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
                      <strong>{a.building_name || a.building || a.buildingName}</strong> · {a.resource_type || a.resourceType} —{" "}
                      {a.message ||
                        ("value " + a.value + " vs expected " + (a.expected || (a.expected_range && a.expected_range.join("–"))))}
                      <span className="muted"> · {fmtDate(a.recorded_at || a.date || a.createdAt)}</span>
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
