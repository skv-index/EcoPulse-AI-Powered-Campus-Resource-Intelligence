import api from "../services/api";
import useFetch from "../hooks/useFetch";
import { sampleBuildings } from "../utils/sampleData";
import Badge from "../components/Badge";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";

function listOf(d) {
  if (!d) return null;
  if (Array.isArray(d)) return d;
  return d.buildings || d.items || d.data || null;
}

export default function Buildings() {
  const res = useFetch(() => api.get("/api/buildings"));
  const demoMode = Boolean(res.error);
  const buildings = listOf(res.data) || (demoMode ? sampleBuildings : []);

  async function handleAdd(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    const payload = {
      name: f.get("name"),
      code: f.get("code"),
      floors: Number(f.get("floors") || 1),
      area_sqft: Number(f.get("area_sqft") || 0),
      type: f.get("type"),
    };
    try {
      await api.post("/api/buildings", payload);
      e.target.reset();
      res.refetch();
    } catch (err) {
      alert("Could not add building: " + err.message);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this building?")) return;
    try {
      await api.del("/api/buildings/" + id);
      res.refetch();
    } catch (err) {
      alert("Delete failed: " + err.message);
    }
  }

  if (res.loading && !res.data && !res.error) return <LoadingSpinner text="Loading buildings..." />;

  return (
    <div>
      <h1 className="page-title">Buildings</h1>
      <p className="muted">Manage campus buildings tracked by EcoPulse.</p>
      {demoMode && (
        <AlertBanner type="warn">
          <strong>SAMPLE — demo mode:</strong> showing sample buildings (API down).{" "}
          <span className="muted">{res.error && res.error.message}</span>
        </AlertBanner>
      )}
      {res.error && <ErrorState error={res.error} onRetry={res.refetch} />}

      <div className="card">
        <h3>Add building</h3>
        <form className="form form-inline" onSubmit={handleAdd}>
          <label>
            Name <input name="name" required placeholder="New Academic Block" />
          </label>
          <label>
            Code <input name="code" placeholder="NAB" />
          </label>
          <label>
            Floors <input name="floors" type="number" min="1" defaultValue={2} />
          </label>
          <label>
            Area (sqft) <input name="area_sqft" type="number" min="0" placeholder="12000" />
          </label>
          <label>
            Type
            <select name="type" defaultValue="academic">
              <option value="academic">academic</option>
              <option value="residential">residential</option>
              <option value="commercial">commercial</option>
              <option value="admin">admin</option>
            </select>
          </label>
          <button className="btn" type="submit">
            Add
          </button>
        </form>
      </div>

      {buildings.length === 0 ? (
        <EmptyState title="No buildings found" hint="Add your first building above." />
      ) : (
        <div className="grid cards-3">
          {buildings.map((b) => (
            <div className="card" key={b.id || b.code || b.name}>
              <div className="row-between">
                <h3>{b.name}</h3>
                <Badge tone="teal">{b.type || "-"}</Badge>
              </div>
              <p className="muted">
                {b.code && <span>Code: {b.code} · </span>}
                {b.floors != null && <span>{b.floors} floors · </span>}
                {b.area_sqft != null && <span>{Number(b.area_sqft).toLocaleString()} sqft</span>}
              </p>
              {!demoMode && b.id && (
                <button className="btn btn-danger btn-sm" onClick={() => handleDelete(b.id)}>
                  Delete
                </button>
              )}
              {demoMode && <Badge tone="amber">SAMPLE</Badge>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
