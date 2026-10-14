export default function ErrorState({ error, onRetry }) {
  return (
    <div className="state error-state">
      <div className="state-icon">!</div>
      <h3>Could not reach the API</h3>
      <p className="muted">{(error && error.message) || "Unknown error"}</p>
      {onRetry && (
        <button className="btn" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
