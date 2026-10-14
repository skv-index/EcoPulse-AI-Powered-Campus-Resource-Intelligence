import {
  ResponsiveContainer,
  LineChart as RLine,
  Line,
  BarChart as RBar,
  Bar,
  AreaChart as RArea,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export function palette(i) {
  return ["#0d7a5f", "#0ea5a4", "#f59e0b", "#ef4444", "#6366f1"][i % 5];
}

// Generic chart wrapper: kind = "line" | "bar" | "area"
export default function Chart({ kind, data, xKey, series }) {
  const k = kind || "line";
  const rows = data || [];
  const xk = xKey || "date";
  const ss = series || [];
  if (!rows.length) return <p className="muted">No data to chart.</p>;
  let inner = null;
  if (k === "bar") {
    inner = (
      <RBar data={rows}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xk} tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend />
        {ss.map((s, i) => (
          <Bar key={s.key} dataKey={s.key} name={s.name || s.key} fill={s.color || palette(i)} />
        ))}
      </RBar>
    );
  } else if (k === "area") {
    inner = (
      <RArea data={rows}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xk} tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend />
        {ss.map((s, i) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.name || s.key}
            stroke={s.color || palette(i)}
            fill={s.color || palette(i)}
            fillOpacity={0.25}
          />
        ))}
      </RArea>
    );
  } else {
    inner = (
      <RLine data={rows}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xk} tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend />
        {ss.map((s, i) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.name || s.key}
            stroke={s.color || palette(i)}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </RLine>
    );
  }
  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>{inner}</ResponsiveContainer>
    </div>
  );
}
