export default function KpiCard({ title, value, delta, hint, tone }) {
  const t = tone || "green";
  return (
    <div className={"card kpi kpi-" + t}>
      <div className="kpi-title">{title}</div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-row">
        {delta && <span className="kpi-delta">{delta}</span>}
        {hint && <span className="kpi-hint">{hint}</span>}
      </div>
    </div>
  );
}
