// Formatting helpers: dates, numbers, units.

export function fmtDate(d) {
  if (!d) return "—";
  const dt = d instanceof Date ? d : new Date(d);
  if (Number.isNaN(dt.getTime())) return String(d);
  return dt.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function fmtDateTime(d) {
  if (!d) return "—";
  const dt = d instanceof Date ? d : new Date(d);
  if (Number.isNaN(dt.getTime())) return String(d);
  return dt.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function fmtNum(n, digits) {
  const dg = digits === undefined ? 1 : digits;
  if (n == null || Number.isNaN(Number(n))) return "—";
  return Number(n).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: dg,
  });
}

const UNIT_LABEL = { electricity: "kWh", water: "kL", gas: "m3", waste: "kg" };

export function unitFor(resourceType) {
  return UNIT_LABEL[String(resourceType || "").toLowerCase()] || "";
}

export function fmtReading(value, resourceType) {
  const u = unitFor(resourceType);
  return fmtNum(value) + (u ? " " + u : "");
}

export function toISODateInput(d) {
  if (!d) return "";
  const dt = d instanceof Date ? d : new Date(d);
  if (Number.isNaN(dt.getTime())) return "";
  return dt.toISOString().slice(0, 10);
}
