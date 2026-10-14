import Chart from "./Chart";

// Convenience line-chart with sensible defaults for consumption trends.
export default function LineChart({ data, series }) {
  return (
    <Chart
      kind="line"
      data={data}
      xKey="date"
      series={
        series || [
          { key: "electricity", name: "Electricity (kWh)", color: "#0d7a5f" },
          { key: "water", name: "Water (kL)", color: "#0ea5a4" },
        ]
      }
    />
  );
}
