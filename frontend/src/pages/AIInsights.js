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

export default function AIInsights() {
  const anom = useFetch(() => api.ai.get("/api/anomalies"));
  const fore = useFetch(() => api.ai.get("/api/forecast"));
  const recs = useFetch(() => api.ai.get("/api/recommendations"));
  const cost = useFetch(() => api.ai.get("/api/cost-estimate"));

  const demoMode = Boolean(anom.error && fore.error && recs.error);
  const anomalies = arr(anom.data, "anomalies") || (anom.error ? sampleAnomalies : []);
  const forecast = arr(fore.data, "forecast") || (fore.error ? sampleForecast : []);
  const recommendations = arr(recs.data, "recommendations") || (recs.error ? sampleRecommendations : []);
  const costs = arr(cost.data, "estimates") || (cost.error ? sampleCostEstimates : []);

  const stillLoading = [anom, fore, recs].every((r) => r.loading && !r.data && !r.error);
  if (stillLoading) return <LoadingSpinner text="Asking the AI service..." />;

  function retryAll() {
    anom.refetch();
    fore.refetch();
    recs.refetch();
    cost.refetch();
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
                  <strong>{a.building || a.buildingName}</strong> · {a.resourceType} —{" "}
                  {a.message || (a.value + " vs expected " + a.expected)}
                  <span className="muted"> · {fmtDate(a.date || a.createdAt)}</span>
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
                <p className="muted">{r.detail}</p>
                <p className="save">{r.impact}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <h3>Cost estimates {cost.error && <Badge tone="amber">SAMPLE</Badge>}</h3>
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
