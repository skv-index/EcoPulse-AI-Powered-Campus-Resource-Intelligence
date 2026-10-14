# Data Models — EcoPulse (Module 1, binding)

All services and frontend MUST use these shapes. MongoDB stores them as documents;
APIs return them inside the response envelope (see `api-contracts.md`).
Dates are ISO8601 UTC strings. `_id` is the Mongo ObjectId hex string.

## Resource types (enum, binding)

| Value | Unit | Notes |
|-------|------|-------|
| `electricity` | `kWh` | building meter readings |
| `water` | `L` | litres |
| `waste` | `kg` | kilograms |

## Building

```json
{
  "_id": "66f1a2b3c4d5e6f708192a3b",
  "name": "CSE Block",
  "code": "CSE-BLK",
  "type": "academic",
  "floors": 4,
  "area_sqft": 25000.0,
  "department": "Computer Science",
  "location": "North Campus",
  "created_at": "2026-10-01T08:00:00Z"
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `_id` | string (ObjectId hex) | server-generated |
| `name` | string | required, non-empty |
| `code` | string | required, unique, e.g. `CSE-BLK` |
| `type` | enum | `academic \| hostel \| admin \| lab \| canteen`, required |
| `floors` | int | `>= 0`, required |
| `area_sqft` | float | `> 0`, required |
| `department` | string | optional, default `""` |
| `location` | string | optional, default `""` |
| `created_at` | ISO8601 | server-generated UTC |

## Reading

```json
{
  "_id": "66f1a2b3c4d5e6f708192a99",
  "building_id": "66f1a2b3c4d5e6f708192a3b",
  "building_name": "CSE Block",
  "resource_type": "electricity",
  "value": 342.5,
  "unit": "kWh",
  "recorded_at": "2026-10-05T08:00:00Z",
  "source": "seed",
  "notes": "daily meter"
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `_id` | string (ObjectId hex) | server-generated |
| `building_id` | string (ObjectId hex) | required, must reference a Building |
| `building_name` | string | denormalized copy at write time, required |
| `resource_type` | enum | `electricity \| water \| waste`, required |
| `value` | float | `>= 0`, required |
| `unit` | string | required; MUST match resource type (`kWh`/`L`/`kg`) |
| `recorded_at` | ISO8601 | required, UTC |
| `source` | enum | `manual \| sensor \| seed`, default `manual` |
| `notes` | string | optional, default `""` |

Validation rule (binding): reject `POST/PUT` with wrong unit for type
(e.g. `water` with `kWh`) → `400 INVALID_UNIT`.

## Issue

```json
{
  "_id": "66f1a2b3c4d5e6f708192b11",
  "title": "Leaking tap in washroom",
  "description": "Tap near room 204 dripping continuously",
  "building_id": "66f1a2b3c4d5e6f708192a3b",
  "category": "water_leak",
  "priority": "high",
  "status": "open",
  "reported_by": "Ananya",
  "created_at": "2026-10-06T10:00:00Z",
  "updated_at": "2026-10-06T10:00:00Z"
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `title` | string | required, non-empty |
| `description` | string | optional, default `""` |
| `building_id` | string (ObjectId hex) \| null | optional; if given must reference a Building |
| `category` | enum | `water_leak \| faulty_light \| overflowing_bin \| hvac \| other`, required |
| `priority` | enum | `low \| medium \| high \| critical`, default `medium` |
| `status` | enum | `open \| in_progress \| resolved \| closed`, server default `open` |
| `reported_by` | string | optional, default `""` |
| `created_at` / `updated_at` | ISO8601 | server-generated; `updated_at` bumps on status change |
