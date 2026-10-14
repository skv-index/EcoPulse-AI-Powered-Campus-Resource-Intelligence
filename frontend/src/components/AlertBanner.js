export default function AlertBanner({ type, children }) {
  const t = type || "info";
  return <div className={"banner banner-" + t}>{children}</div>;
}
