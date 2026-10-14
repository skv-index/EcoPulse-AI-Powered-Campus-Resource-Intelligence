// Sample fallback data used ONLY when the APIs are unreachable.
// Every page shows a "SAMPLE — demo mode" banner when this is used.

export const sampleBuildings = [
  { id: "b1", name: "Science Block", code: "SCI", floors: 4, area_sqft: 25000, type: "academic" },
  { id: "b2", name: "Library", code: "LIB", floors: 3, area_sqft: 18000, type: "academic" },
  { id: "b3", name: "Girls Hostel", code: "GH", floors: 5, area_sqft: 30000, type: "residential" },
  { id: "b4", name: "Canteen", code: "CAN", floors: 2, area_sqft: 9000, type: "commercial" },
];

export const sampleSummary = {
  totalConsumption: { electricity: 12480, water: 860, gas: 320, waste: 940 },
  totalBuildings: 4,
  activeIssues: 3,
  anomaliesCount: 2,
  efficiencyScore: 78,
  trend: [
    { date: "2026-09-08", electricity: 410, water: 28, gas: 11, waste: 30 },
    { date: "2026-09-15", electricity: 455, water: 30, gas: 12, waste: 33 },
    { date: "2026-09-22", electricity: 438, water: 27, gas: 10, waste: 29 },
    { date: "2026-09-29", electricity: 492, water: 34, gas: 13, waste: 36 },
    { date: "2026-10-06", electricity: 470, water: 31, gas: 12, waste: 34 },
    { date: "2026-10-13", electricity: 505, water: 35, gas: 14, waste: 38 },
  ],
};

export const sampleReadings = [
  { id: "r1", building: "Science Block", buildingId: "b1", resourceType: "electricity", value: 505, date: "2026-10-13" },
  { id: "r2", building: "Library", buildingId: "b2", resourceType: "electricity", value: 310, date: "2026-10-13" },
  { id: "r3", building: "Girls Hostel", buildingId: "b3", resourceType: "water", value: 42, date: "2026-10-12" },
  { id: "r4", building: "Canteen", buildingId: "b4", resourceType: "gas", value: 14, date: "2026-10-12" },
  { id: "r5", building: "Science Block", buildingId: "b1", resourceType: "water", value: 35, date: "2026-10-11" },
  { id: "r6", building: "Library", buildingId: "b2", resourceType: "waste", value: 22, date: "2026-10-10" },
];

export const sampleAnomalies = [
  { id: "a1", building: "Science Block", resourceType: "electricity", value: 505, expected: 430, severity: "high", date: "2026-10-13", message: "Usage 17% above baseline — check HVAC schedule." },
  { id: "a2", building: "Girls Hostel", resourceType: "water", value: 42, expected: 30, severity: "medium", date: "2026-10-12", message: "Possible leak in Block B washrooms." },
];

export const sampleForecast = [
  { date: "2026-10-14", predicted: 510, lower: 470, upper: 550 },
  { date: "2026-10-15", predicted: 518, lower: 476, upper: 560 },
  { date: "2026-10-16", predicted: 505, lower: 465, upper: 548 },
  { date: "2026-10-17", predicted: 490, lower: 450, upper: 530 },
  { date: "2026-10-18", predicted: 430, lower: 395, upper: 468 },
  { date: "2026-10-19", predicted: 415, lower: 380, upper: 452 },
  { date: "2026-10-20", predicted: 522, lower: 480, upper: 565 },
];

export const sampleRecommendations = [
  { id: "rec1", title: "Shift HVAC start to 8:30 AM", impact: "Save ~120 kWh/week", priority: "high", detail: "Science Block HVAC runs from 6 AM with near-zero occupancy before 8:30." },
  { id: "rec2", title: "Fix hostel water leak", impact: "Save ~80 kL/month", priority: "high", detail: "Night-flow analysis suggests a continuous 0.4 kL/hr leak." },
  { id: "rec3", title: "Solar scheduling for Library", impact: "Save Rs.4,200/month", priority: "medium", detail: "Move heavy loads to 11 AM–3 PM solar peak window." },
];

export const sampleIssues = [
  { id: "i1", title: "AC left on overnight — Room 204", building: "Science Block", status: "open", priority: "medium", createdAt: "2026-10-11" },
  { id: "i2", title: "Tap leaking in hostel B2", building: "Girls Hostel", status: "in_progress", priority: "high", createdAt: "2026-10-10" },
  { id: "i3", title: "Canteen waste segregation missed", building: "Canteen", status: "resolved", priority: "low", createdAt: "2026-10-08" },
];

export const sampleCostEstimates = [
  { resourceType: "electricity", usage: 12480, rate: 8.5, cost: 106080, saving: 12700 },
  { resourceType: "water", usage: 860, rate: 60, cost: 51600, saving: 6200 },
  { resourceType: "gas", usage: 320, rate: 95, cost: 30400, saving: 2800 },
  { resourceType: "waste", usage: 940, rate: 12, cost: 11280, saving: 1500 },
];
