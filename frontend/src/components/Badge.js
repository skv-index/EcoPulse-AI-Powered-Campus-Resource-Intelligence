export default function Badge({ tone, children }) {
  const t = tone || "gray";
  return <span className={"badge badge-" + t}>{children}</span>;
}
