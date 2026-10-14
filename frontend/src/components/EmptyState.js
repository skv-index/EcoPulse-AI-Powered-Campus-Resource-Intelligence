export default function EmptyState({ title, hint }) {
  return (
    <div className="state">
      <div className="state-icon">O</div>
      <h3>{title || "No data yet"}</h3>
      {hint && <p className="muted">{hint}</p>}
    </div>
  );
}
