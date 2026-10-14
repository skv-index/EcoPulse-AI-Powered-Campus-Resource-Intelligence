import { useMemo } from "react";
import api from "../services/api";
import useFetch from "../hooks/useFetch";
import { sampleSummary, sampleCostEstimates, sampleAnomalies, sampleIssues } from "../utils/sampleData";
import { fmtNum } from "../utils/format";
import KpiCard from "../components/KpiCard";
import Chart from "../components/Chart";
import Badge from "../components/Badge";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";

// Sustainability score (estimate): 100 minus penalties.
// Penalties: anomaly rate, open-issue rate, waste share. Clearly labeled as estimate.
function computeScore(o) {
  const anomalies = o.anomalies || 0;
  const openIssues = o.openIssues || 0;
  const totalIssues = o.totalIssues || 1;
  const waste = o.waste || 0;
  const total = o.total || 1;
  const anomalyPenalty = Math.min(30, anomalies * 6);
  const issuePenalty = Math.min(30, (openIssues / Math.max(1, totalIssues)) * 30);
  const wastePenalty = Math.min(25, (waste / Math.max(1, total)) * 25);
  return Math.max(0, Math.round(100 - anomalyPenalty - issuePenalty - wastePenalty));
}

function toList(d, key) {
  if (!d) return null;
  if (Array.isArray(d)) return d;
  return d[key] || d.items || d.data || null;
}

export default function Reports() {
  const sum = useFetch(() => api.get("/api/dashboard/summary"));
  const cost = useFetch(() => api.ai.get("/api/cost-estimate"));
  const demoMode = Boolean(sum.error);

  const summary = sum.data && sum.data.trend ? sum.data : demoMode ? sampleSummary : sum.data;
  const costs = toList(cost.data, "estimates") || sampleCostEstimates;

  const score = useMemo(() => {
    const t = (summary && summary.totalConsumption) || sampleSummary.totalConsumption;
    const total = (t.electricity || 0) + (t.water || 0) * 10 + (t.gas || 0) * 5 + (t.waste || 0);
    return computeScore({
      anomalies: (summary && summary.anomaliesCount) !== undefined ? summary.anomaliesCount : sampleAnomalies.length,
      openIssues: sampleIssues.filter((i) => i.status !== "resolved").length,
      totalIssues: sampleIssues.length,
      waste: t.waste || 0,
      total,
    });
  }, [summary]);

  if (sum.loading && !sum.data && !sum.error) return <LoadingSpinner text="Compiling report..." />;

  const estSavings = costs.reduce((s, c) => s + Number(c.saving || 0), 0);
  const estSpend = costs.reduce((s, c) => s + Number(c.cost || 0), 0);

  return (
    <div>
      <h1 className="page-title">Reports</h1>
      <p className="muted">Sustainability snapshot and savings opportunities.</p>
      {demoMode && (
        <AlertBanner type="warn">
          <strong>SAMPLE — demo mode:</strong> report built from sample data (API down).{" "}
          <span className="muted">{sum.error && sum.error.message}</span>
        </AlertBanner>
      )}
      {sum.error && <ErrorState error={sum.error} onRetry={sum.refetch} />}

      <div className="grid cards-3">
        <KpiCard title="Sustainability score (estimate)" value={score + " / 100"} delta={score >= 75 ? "Good" : score >= 50 ? "Fair" : "Needs work"} hint="100 minus waste/efficiency penalties" tone={score >= 75 ? "green" : score >= 50 ? "amber" : "red"} />
        <KpiCard
          title="Est. monthly savings"
          value={"Rs." + fmtNum(estSavings, 0)}
          hint="Sum of per-resource opportunities"
        />
        <KpiCard
          title="Est. monthly spend"
          value={"Rs." + fmtNum(estSpend, 0)}
          hint="Across electricity, water, gas, waste"
        />
      </div>

      <div className="card">
        <h3>Savings estimate {cost.error && <Badge tone="amber">SAMPLE</Badge>}</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Resource</th>
              <th>Usage</th>
              <th>Cost (Rs.)</th>
              <th>Saving (Rs.)</th>
              <th>Saving %</th>
            </tr>
          </thead>
          <tbody>
            {costs.map((c) => (
              <tr key={c.resourceType}>
                <td>
                  <Badge tone="teal">{c.resourceType}</Badge>
                </td>
                <td>{fmtNum(c.usage)}</td>
                <td>Rs.{fmtNum(c.cost, 0)}</td>
                <td className="save">Rs.{fmtNum(c.saving, 0)}</td>
                <td>{c.cost ? fmtNum((c.saving / c.cost) * 100) + "%" : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {summary && summary.trend && (
        <div className="card">
          <h3>Consumption trend (report view)</h3>
          <Chart
            kind="area"
            data={summary.trend}
            xKey="date"
            series={[
              { key: "electricity", name: "Electricity", color: "#0d7a5f" },
              { key: "water", name: "Water", color: "#0ea5a4" },
            ]}
          />
        </div>
      )}
    </div>
  );
}
