import { useMemo, useState } from "react";
import api from "../services/api";
import useFetch from "../hooks/useFetch";
import { sampleReadings, sampleBuildings } from "../utils/sampleData";
import { fmtDate, fmtReading } from "../utils/format";
import Chart from "../components/Chart";
import DataTable from "../components/DataTable";
import Badge from "../components/Badge";
import AlertBanner from "../components/AlertBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";

const TYPES = ["", "electricity", "water", "gas", "waste"];

function toList(d, key) {
  if (!d) return null;
  if (Array.isArray(d)) return d;
  return d[key] || d.items || d.data || null;
}

export default function Analytics() {
  const [building, setBuilding] = useState("");
  const [resourceType, setResourceType] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  const bRes = useFetch(() => api.get("/api/buildings"));
  const fKey = building + "|" + resourceType + "|" + from + "|" + to;
  const rRes = useFetch(
    () => api.get("/api/readings", { building, resourceType, from, to }),
    [fKey]
  );

  const demoMode = Boolean(rRes.error);
  const buildings = toList(bRes.data, "buildings") || sampleBuildings;

  let readings = toList(rRes.data, "readings") || sampleReadings;

  // Client-side filter so SAMPLE + odd API shapes still respect filters
  const filtered = useMemo(
    () =>
      readings.filter(
        (r) =>
          (!building || r.building === building || r.buildingId === building || r.buildingName === building) &&
          (!resourceType || r.resourceType === resourceType) &&
          (!from || String(r.date) >= from) &&
          (!to || String(r.date) <= to)
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [readings, building, resourceType, from, to]
  );

  const perBuilding = useMemo(() => {
    const map = {};
    filtered.forEach((r) => {
      const k = r.building || r.buildingName || "Unknown";
      map[k] = (map[k] || 0) + Number(r.value || 0);
    });
    return Object.keys(map).map((building) => ({ building, total: map[building] }));
  }, [filtered]);

  async function handleAddReading(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    const payload = {
      building: f.get("building"),
      resourceType: f.get("resourceType"),
      value: Number(f.get("value")),
      date: f.get("date"),
    };
    try {
      await api.post("/api/readings", payload);
      e.target.reset();
      rRes.refetch();
    } catch (err) {
      alert("Could not save reading: " + err.message);
    }
  }

  if (rRes.loading && !rRes.data && !rRes.error) return <LoadingSpinner text="Loading readings..." />;

  return (
    <div>
      <h1 className="page-title">Analytics</h1>
      <p className="muted">Filter readings and compare consumption per building.</p>
      {demoMode && (
        <AlertBanner type="warn">
          <strong>SAMPLE — demo mode:</strong> showing sample readings (API down).{" "}
          <span className="muted">{rRes.error && rRes.error.message}</span>
        </AlertBanner>
      )}
      {rRes.error && <ErrorState error={rRes.error} onRetry={rRes.refetch} />}

      <div className="card">
        <div className="filters">
          <label>
            Building
            <select value={building} onChange={(e) => setBuilding(e.target.value)}>
              <option value="">All</option>
              {buildings.map((b) => (
                <option key={b.id || b.name} value={b.name || b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Resource
            <select value={resourceType} onChange={(e) => setResourceType(e.target.value)}>
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t || "All"}
                </option>
              ))}
            </select>
          </label>
          <label>
            From <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          </label>
          <label>
            To <input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
          </label>
          <button
            className="btn btn-ghost"
            onClick={() => {
              setBuilding("");
              setResourceType("");
              setFrom("");
              setTo("");
            }}
          >
            Clear
          </button>
        </div>
      </div>

      <div className="grid cards-2">
        <div className="card">
          <h3>Per-building comparison {demoMode && <Badge tone="amber">SAMPLE</Badge>}</h3>
          <Chart kind="bar" data={perBuilding} xKey="building" series={[{ key: "total", name: "Total", color: "#0d7a5f" }]} />
        </div>
        <div className="card">
          <h3>Add reading</h3>
          <form className="form" onSubmit={handleAddReading}>
            <label>
              Building
              <select name="building" required>
                {buildings.map((b) => (
                  <option key={b.id || b.name} value={b.name}>
                    {b.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Resource
              <select name="resourceType" required>
                <option value="electricity">electricity</option>
                <option value="water">water</option>
                <option value="gas">gas</option>
                <option value="waste">waste</option>
              </select>
            </label>
            <label>
              Value <input name="value" type="number" step="any" min="0" required placeholder="e.g. 120" />
            </label>
            <label>
              Date <input name="date" type="date" required />
            </label>
            <button className="btn" type="submit">
              Save reading
            </button>
          </form>
        </div>
      </div>

      <div className="card">
        <h3>
          Readings ({filtered.length}) {demoMode && <Badge tone="amber">SAMPLE</Badge>}
        </h3>
        {filtered.length === 0 ? (
          <EmptyState title="No readings match" hint="Try widening the filters." />
        ) : (
          <DataTable
            columns={[
              { key: "date", label: "Date", render: (r) => fmtDate(r.date) },
              { key: "building", label: "Building", render: (r) => r.building || r.buildingName },
              {
                key: "resourceType",
                label: "Resource",
                render: (r) => <Badge tone="teal">{r.resourceType}</Badge>,
              },
              { key: "value", label: "Value", render: (r) => fmtReading(r.value, r.resourceType) },
            ]}
            rows={filtered}
          />
        )}
      </div>
    </div>
  );
}
