export default function LoadingSpinner({ text }) {
  return (
    <div className="state">
      <div className="spinner" />
      <p className="muted">{text || "Loading..."}</p>
    </div>
  );
}
