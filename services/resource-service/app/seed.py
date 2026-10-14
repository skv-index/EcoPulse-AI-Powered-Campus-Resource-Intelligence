"""Seed script — run with:  py -m app.seed   (from services/resource-service).

Creates 5 buildings, ~60 readings spread across the last 30 days
(electricity / water / waste), and 6 maintenance issues.
Safe to re-run: it wipes the three collections first.
"""
import random
from datetime import datetime, timedelta, timezone

from app.db import get_db, reset_memory_db


BUILDINGS = [
    {"name": "CSE Block", "code": "CSE", "type": "academic",
     "floors": 4, "area_sqft": 25000, "department": "Computer Science",
     "location": "North Campus"},
    {"name": "ECE Block", "code": "ECE", "type": "academic",
     "floors": 3, "area_sqft": 20000, "department": "Electronics",
     "location": "North Campus"},
    {"name": "Boys Hostel", "code": "BH1", "type": "hostel",
     "floors": 5, "area_sqft": 30000, "department": "Hostels",
     "location": "East Campus"},
    {"name": "Admin Block", "code": "ADM", "type": "admin",
     "floors": 2, "area_sqft": 12000, "department": "Administration",
     "location": "Main Gate"},
    {"name": "Central Library", "code": "LIB", "type": "academic",
     "floors": 3, "area_sqft": 18000, "department": "Library",
     "location": "Central Campus"},
]

ISSUES = [
    {"title": "Water leak in CSE washroom", "description": "Tap leaking on floor 2.",
     "code": "CSE", "category": "water_leak", "priority": "high",
     "status": "open", "reported_by": "caretaker"},
    {"title": "Faulty corridor lights", "description": "Flickering lights in ECE corridor.",
     "code": "ECE", "category": "faulty_light", "priority": "medium",
     "status": "in_progress", "reported_by": "student"},
    {"title": "Overflowing bin near mess", "description": "Bin full for 2 days.",
     "code": "BH1", "category": "overflowing_bin", "priority": "medium",
     "status": "open", "reported_by": "warden"},
    {"title": "AC not cooling in seminar hall", "description": "HVAC weak in Admin seminar hall.",
     "code": "ADM", "category": "hvac", "priority": "high",
     "status": "open", "reported_by": "staff"},
    {"title": "Library basement dampness", "description": "Seepage near archive room.",
     "code": "LIB", "category": "other", "priority": "low",
     "status": "resolved", "reported_by": "librarian"},
    {"title": "Street light outside hostel", "description": "Light pole not working.",
     "code": "BH1", "category": "faulty_light", "priority": "low",
     "status": "closed", "reported_by": "guard"},
]


def main():
    random.seed(42)
    db = get_db()
    # Works on both backends (delete_many({}) clears a collection).
    for name in ("buildings", "readings", "issues"):
        try:
            db[name].delete_many({})
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    id_by_code = {}
    for b in BUILDINGS:
        doc = {**b, "created_at": now, "updated_at": now}
        bid = db["buildings"].insert_one(doc).inserted_id
        id_by_code[b["code"]] = (str(bid), b["name"])

    # ~60 readings: 30 days x 2 readings/day across rotating buildings/types.
    kinds = [("electricity", "kWh", 120, 260),
             ("water", "L", 800, 2000),
             ("waste", "kg", 8, 40)]
    codes = list(id_by_code.keys())
    n = 0
    for day_ago in range(30):
        for _ in range(2):  # 2 readings per day -> 60 total
            rtype, unit, lo, hi = kinds[n % 3]
            code = codes[n % len(codes)]
            bid, bname = id_by_code[code]
            db["readings"].insert_one({
                "building_id": bid,
                "building_name": bname,
                "resource_type": rtype,
                "value": round(random.uniform(lo, hi), 2),
                "unit": unit,
                "recorded_at": now - timedelta(days=day_ago,
                                               hours=random.randint(0, 23)),
                "source": "seed",
                "notes": f"Demo {rtype} reading for {bname}",
                "created_at": now,
                "updated_at": now,
            })
            n += 1

    for item in ISSUES:
        bid, _ = id_by_code[item.pop("code")]
        db["issues"].insert_one({
            "building_id": bid, **item,
            "created_at": now, "updated_at": now,
        })

    print(f"Seeded {db['buildings'].count_documents({})} buildings, "
          f"{db['readings'].count_documents({})} readings, "
          f"{db['issues'].count_documents({})} issues.")


if __name__ == "__main__":
    main()
