export default function DataTable({ columns, rows, rowKey }) {
  const cols = columns || [];
  const rs = rows || [];
  const rk = rowKey || "id";
  if (!rs.length) return null;
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rs.map((r, i) => (
            <tr key={r[rk] !== undefined ? r[rk] : i}>
              {cols.map((c) => (
                <td key={c.key}>{c.render ? c.render(r) : r[c.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
