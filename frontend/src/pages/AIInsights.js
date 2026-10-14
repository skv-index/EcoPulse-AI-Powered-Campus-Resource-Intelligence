import api from "../services/api";
import useFetch from "../hooks/useFetch";
import { sampleAnomalies, sampleForecast, sampleRecommendations, sampleCostEstimates } from "../utils/sampleData";
import { fmtDate, fmtNum } from "../utils/format";
import Chart from "../components/Chart";
import Badge from "../components/Badge";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";

function arr(d, key) {
  if (!d) return null;
  if (Array.isArray(d)) return d;
  return d[key] || d.items || d.data || null;
}

// cost_estimate from /api/ai/insights:
// { breakdown: { electricity: 123, water: 45 }, total, currency, rates, note }
function costsFromInsights(insights) {
  const ce = insights && insights.cost_estimate;
  if (!ce || !ce.breakdown) return null;
  const totals = (insights && insights.totals) || {};
  return Object.keys(ce.breakdown).map((rtype) => ({
    resourceType: rtype,
    usage: totals[rtype] || 0,
    cost: ce.breakdown[rtype],
    saving: Math.round(Number(ce.breakdown[rtype] || 0) * 0.12),
  }));
}

export default function AIInsights() {
  const anom = useFetch(() => api.ai.get("/api/ai/anomalies"));
  const fore = useFetch(() => api.ai.get("/api/ai/forecast"));
  const recs = useFetch(() => api.ai.get("/api/ai/recommendations"));
  const ins = useFetch(() => api.ai.get("/api/ai/insights"));

  const demoMode = Boolean(anom.error && fore.error && recs.error);
  const anomalies = arr(anom.data, "anomalies") || (anom.error ? sampleAnomalies : []);
  const forecastRaw = arr(fore.data, "forecast") || (fore.error ? sampleForecast : []);
  // Real forecast rows: { date, predicted_value, unit } -> chart rows { date, predicted }.
  const forecast = forecastRaw.map((f) => ({
    date: f.date,
    predicted: f.predicted !== undefined ? f.predicted : f.predicted_value,
    upper: f.upper,
    lower: f.lower,
  }));
  const recommendations = arr(recs.data, "recommendations") || (recs.error ? sampleRecommendations : []);
  const costs = costsFromInsights(ins.data) || (ins.error ? sampleCostEstimates : []);

  const stillLoading = [anom, fore, recs].every((r) => r.loading && !r.data && !r.error);
  if (stillLoading) return <LoadingSpinner text="Asking the AI service..." />;

  const forecastNote = fore.data && (fore.data.disclaimer || fore.data.message);

  function retryAll() {
    anom.refetch();
    fore.refetch();
    recs.refetch();
    ins.refetch();
  }

  return (
    <div>
      <h1 className="page-title">AI Insights</h1>
      <p className="muted">Anomaly detection, demand forecast, recommendations and cost estimates.</p>
      {demoMode && (
        <AlertBanner type="warn">
          <strong>SAMPLE — demo mode:</strong> AI service unreachable, showing sample insights.{" "}
          <span className="muted">{anom.error && anom.error.message}</span>
        </AlertBanner>
      )}
      {anom.error && <ErrorState error={anom.error} onRetry={retryAll} />}

      <div className="grid cards-2">
        <div className="card">
          <h3>Demand forecast {fore.error && <Badge tone="amber">SAMPLE</Badge>}</h3>
          {forecastNote && <p className="muted">{forecastNote}</p>}
          {forecast.length ? (
            <Chart
              kind="area"
              data={forecast}
              xKey="date"
              series={[
                { key: "predicted", name: "Predicted", color: "#0d7a5f" },
                { key: "upper", name: "Upper bound", color: "#cbd5e1" },
                { key: "lower", name: "Lower bound", color: "#94a3b8" },
              ]}
            />
          ) : (
            <p className="muted">No forecast available.</p>
          )}
        </div>
        <div className="card">
          <h3>Anomalies ({anomalies.length}) {anom.error && <Badge tone="amber">SAMPLE</Badge>}</h3>
          {anomalies.length === 0 ? (
            <p className="muted">All clear — no anomalies.</p>
          ) : (
            <ul className="list">
              {anomalies.map((a, i) => (
                <li key={a.id || i} className="list-item">
                  <Badge tone={a.severity === "high" ? "red" : a.severity === "medium" ? "amber" : "gray"}>
                    {a.severity || "info"}
                  </Badge>{" "}
                  <strong>{a.building_name || a.building || a.buildingName}</strong> · {a.resource_type || a.resourceType} —{" "}
                  {a.message || (a.value + " vs expected " + (a.expected || (a.expected_range && a.expected_range.join("–"))))}
                  <span className="muted"> · {fmtDate(a.recorded_at || a.date || a.createdAt)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="grid cards-2">
        <div className="card">
          <h3>Recommendations {recs.error && <Badge tone="amber">SAMPLE</Badge>}</h3>
          <div className="grid">
            {recommendations.map((r) => (
              <div className="rec" key={r.id || r.title}>
                <div className="row-between">
                  <strong>{r.title}</strong>
                  <Badge tone={r.priority === "high" ? "red" : r.priority === "medium" ? "amber" : "green"}>
                    {r.priority || "info"}
                  </Badge>
                </div>
                <p className="muted">{r.description || r.detail}</p>
                <p className="save">{r.impact || (r.potential_saving_pct ? "Potential saving: " + r.potential_saving_pct + "%" : "")}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h3>Cost estimates {ins.error && <Badge tone="amber">SAMPLE</Badge>}</h3>
          {ins.data && ins.data.cost_estimate && ins.data.cost_estimate.note && (
            <p className="muted">{ins.data.cost_estimate.note}</p>
          )}
          <table className="table">
            <thead>
              <tr>
                <th>Resource</th>
                <th>Usage</th>
                <th>Cost (Rs.)</th>
                <th>Potential saving</th>
              </tr>
            </thead>
            <tbody>
              {costs.map((c) => (
                <tr key={c.resourceType}>
                  <td>{c.resourceType}</td>
                  <td>{fmtNum(c.usage)}</td>
                  <td>Rs.{fmtNum(c.cost, 0)}</td>
                  <td className="save">Rs.{fmtNum(c.saving, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
