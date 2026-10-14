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

const TYPES = ["", "electricity", "water", "waste"];

const UNIT_FOR = { electricity: "kWh", water: "L", waste: "kg" };

// Backend field names with fallbacks to the sample-data shape.
function rBuilding(r) {
  return r.building_name || r.buildingName || r.building || "";
}
function rBuildingId(r) {
  return r.building_id || r.buildingId || "";
}
function rType(r) {
  return r.resource_type || r.resourceType || "";
}
function rDate(r) {
  const d = r.recorded_at || r.date;
  return d ? String(d).slice(0, 10) : "";
}

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
    () =>
      api.get("/api/readings", {
        building_id: building,
        resource_type: resourceType,
        from,
        to,
      }),
    [fKey]
  );

  const demoMode = Boolean(rRes.error);
  const buildings = toList(bRes.data, "buildings") || sampleBuildings;

  let readings = toList(rRes.data, "readings") || sampleReadings;

  // Client-side filter so SAMPLE + odd API shapes still respect filters.
  // `building` holds a building id (or, for sample data, a name).
  const filtered = useMemo(
    () =>
      readings.filter(
        (r) =>
          (!building || rBuildingId(r) === building || rBuilding(r) === building) &&
          (!resourceType || rType(r) === resourceType) &&
          (!from || rDate(r) >= from) &&
          (!to || rDate(r) <= to)
      ),
    [readings, building, resourceType, from, to]
  );

  const perBuilding = useMemo(() => {
    const map = {};
    filtered.forEach((r) => {
      const k = rBuilding(r) || "Unknown";
      map[k] = (map[k] || 0) + Number(r.value || 0);
    });
    return Object.keys(map).map((building) => ({ building, total: map[building] }));
  }, [filtered]);

  async function handleAddReading(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    const bid = f.get("building_id");
    const rtype = f.get("resource_type");
    const chosen = buildings.find((b) => (b.id || b.name) === bid);
    const payload = {
      building_id: bid,
      building_name: (chosen && chosen.name) || "",
      resource_type: rtype,
      value: Number(f.get("value")),
      unit: UNIT_FOR[rtype] || "",
      recorded_at: f.get("date") ? new Date(f.get("date")).toISOString() : undefined,
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
                <option key={b.id || b.name} value={b.id || b.name}>
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
              <select name="building_id" required>
                {buildings.map((b) => (
                  <option key={b.id || b.name} value={b.id || b.name}>
                    {b.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Resource
              <select name="resource_type" required>
                <option value="electricity">electricity (kWh)</option>
                <option value="water">water (L)</option>
                <option value="waste">waste (kg)</option>
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
              { key: "date", label: "Date", render: (r) => fmtDate(rDate(r)) },
              { key: "building", label: "Building", render: (r) => rBuilding(r) },
              {
                key: "resourceType",
                label: "Resource",
                render: (r) => <Badge tone="teal">{rType(r)}</Badge>,
              },
              { key: "value", label: "Value", render: (r) => fmtReading(r.value, rType(r)) },
            ]}
            rows={filtered}
          />
        )}
      </div>
    </div>
  );
}
