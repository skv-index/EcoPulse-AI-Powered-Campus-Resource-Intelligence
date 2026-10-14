import api from "../services/api";
import useFetch from "../hooks/useFetch";
import { sampleIssues } from "../utils/sampleData";
import { fmtDate } from "../utils/format";
import Badge from "../components/Badge";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";

const STATUSES = ["open", "in_progress", "resolved"];

function toList(d) {
  if (!d) return null;
  if (Array.isArray(d)) return d;
  return d.issues || d.items || d.data || null;
}

export default function Issues() {
  const res = useFetch(() => api.get("/api/issues"));
  const demoMode = Boolean(res.error);
  const issues = toList(res.data) || sampleIssues;

  async function handleReport(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    const payload = {
      title: f.get("title"),
      building: f.get("building"),
      priority: f.get("priority") || "medium",
      description: f.get("description"),
      status: "open",
    };
    try {
      await api.post("/api/issues", payload);
      e.target.reset();
      res.refetch();
    } catch (err) {
      alert("Could not report issue: " + err.message);
    }
  }

  async function setStatus(id, status) {
    try {
      await api.patch("/api/issues/" + id, { status });
      res.refetch();
    } catch (err) {
      alert("Status update failed: " + err.message);
    }
  }

  if (res.loading && !res.data && !res.error) return <LoadingSpinner text="Loading issues..." />;

  return (
    <div>
      <h1 className="page-title">Issues</h1>
      <p className="muted">Report wastage and track resolution.</p>
      {demoMode && (
        <AlertBanner type="warn">
          <strong>SAMPLE — demo mode:</strong> showing sample issues (API down).{" "}
          <span className="muted">{res.error && res.error.message}</span>
        </AlertBanner>
      )}
      {res.error && <ErrorState error={res.error} onRetry={res.refetch} />}

      <div className="grid cards-2">
        <div className="card">
          <h3>Report an issue</h3>
          <form className="form" onSubmit={handleReport}>
            <label>
              Title <input name="title" required placeholder="e.g. Lights left on in Lab 3" />
            </label>
            <label>
              Building <input name="building" required placeholder="e.g. Science Block" />
            </label>
            <label>
              Priority
              <select name="priority" defaultValue="medium">
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </label>
            <label>
              Description <textarea name="description" rows={3} placeholder="What did you observe?" />
            </label>
            <button className="btn" type="submit">
              Submit issue
            </button>
          </form>
        </div>
        <div className="card">
          <h3>
            All issues ({issues.length}) {demoMode && <Badge tone="amber">SAMPLE</Badge>}
          </h3>
          {issues.length === 0 ? (
            <EmptyState title="No issues" hint="Nothing reported yet — use the form." />
          ) : (
            <ul className="list">
              {issues.map((t) => (
                <li key={t.id || t.title} className="list-item">
                  <div className="row-between">
                    <strong>{t.title}</strong>
                    <Badge tone={t.status === "resolved" ? "green" : t.status === "in_progress" ? "blue" : "amber"}>
                      {t.status || "open"}
                    </Badge>
                  </div>
                  <div className="muted">
                    {t.building || t.buildingName} · {t.priority} · {fmtDate(t.createdAt || t.date)}
                  </div>
                  {t.description && <div>{t.description}</div>}
                  {!demoMode && t.id && (
                    <div className="btn-row">
                      {STATUSES.map((s) => (
                        <button
                          key={s}
                          className={"btn btn-sm" + (t.status === s ? " btn-active" : " btn-ghost")}
                          onClick={() => setStatus(t.id, s)}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
