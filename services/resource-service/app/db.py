"""Database layer — pymongo when MONGO_URI is set, in-memory dicts otherwise.

Viva: get_db() returns something that supports db["buildings"],
db["readings"], db["issues"] whether we run on real MongoDB or on the
local demo fallback. Routes never need to know which backend is active.
"""
from datetime import datetime, timezone

try:
    from bson import ObjectId
except ImportError:  # pragma: no cover - fallback if bson missing
    ObjectId = None

from app import config


# ---------------------------------------------------------------------------
# In-memory fallback (used for local demo / tests when no MONGO_URI works)
# ---------------------------------------------------------------------------

class _InsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _UpdateResult:
    def __init__(self, matched_count, modified_count):
        self.matched_count = matched_count
        self.modified_count = modified_count


class _DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


def _matches(doc, flt):
    """Very small subset of Mongo query matching: equality + $gte/$lte/$gt/$lt."""
    for key, cond in (flt or {}).items():
        val = doc.get(key)
        if isinstance(cond, dict):
            for op, target in cond.items():
                # Compare datetimes as datetimes, everything else directly.
                if op == "$gte" and not (val is not None and val >= target):
                    return False
                elif op == "$lte" and not (val is not None and val <= target):
                    return False
                elif op == "$gt" and not (val is not None and val > target):
                    return False
                elif op == "$lt" and not (val is not None and val < target):
                    return False
                elif op == "$eq" and not (val == target):
                    return False
                elif op not in ("$gte", "$lte", "$gt", "$lt", "$eq"):
                    return False
        else:
            if key == "_id":
                if val != cond:
                    return False
            elif val != cond:
                return False
    return True


class InMemoryCollection:
    """Mimics the pymongo Collection methods our routes use."""

    def __init__(self):
        self._docs = {}  # ObjectId -> document dict

    # -- writes ----------------------------------------------------------
    def insert_one(self, doc):
        from bson import ObjectId as _Oid
        doc = dict(doc)
        doc.setdefault("_id", _Oid())
        now = datetime.now(timezone.utc)
        doc.setdefault("created_at", now)
        doc.setdefault("updated_at", now)
        self._docs[doc["_id"]] = doc
        return _InsertResult(doc["_id"])

    def update_one(self, flt, update):
        for _id, doc in self._docs.items():
            if _matches(doc, flt):
                changes = update.get("$set", {})
                doc.update(changes)
                doc["updated_at"] = datetime.now(timezone.utc)
                return _UpdateResult(1, 1)
        return _UpdateResult(0, 0)

    def delete_one(self, flt):
        for _id, doc in list(self._docs.items()):
            if _matches(doc, flt):
                del self._docs[_id]
                return _DeleteResult(1)
        return _DeleteResult(0)

    def delete_many(self, flt):
        if not flt:
            n = len(self._docs)
            self._docs.clear()
            return _DeleteResult(n)
        doomed = [_id for _id, d in self._docs.items() if _matches(d, flt)]
        for _id in doomed:
            del self._docs[_id]
        return _DeleteResult(len(doomed))

    # -- reads -----------------------------------------------------------
    def find_one(self, flt):
        for doc in self._docs.values():
            if _matches(doc, flt):
                return dict(doc)
        return None

    def find(self, flt=None, sort=None, limit=0):
        rows = [dict(d) for d in self._docs.values() if _matches(d, flt or {})]
        if sort:
            for key, direction in reversed(list(sort)):
                rows.sort(key=lambda d: d.get(key), reverse=(direction < 0))
        if limit and limit > 0:
            rows = rows[:limit]
        return rows

    def count_documents(self, flt):
        return sum(1 for d in self._docs.values() if _matches(d, flt or {}))


class InMemoryDB:
    """Mimics pymongo Database: db['buildings'] style access."""

    def __init__(self):
        self._cols = {
            "buildings": InMemoryCollection(),
            "readings": InMemoryCollection(),
            "issues": InMemoryCollection(),
        }

    def __getitem__(self, name):
        return self._cols[name]

    def __getattr__(self, name):
        if name in ("_cols",):
            raise AttributeError(name)
        try:
            return self._cols[name]
        except KeyError:
            raise AttributeError(name)


_MEMORY_DB = InMemoryDB()
_MONGO_CLIENT = None
_MONGO_DB = None


def reset_memory_db():
    """Clear the in-memory store (used by tests and the seed script)."""
    global _MEMORY_DB
    _MEMORY_DB = InMemoryDB()
    return _MEMORY_DB


def using_memory():
    """True when the service runs on the in-memory fallback."""
    return get_db() is _MEMORY_DB or isinstance(get_db(), InMemoryDB)


def get_db():
    """Return a Mongo database or the in-memory fallback.

    Tries pymongo only when MONGO_URI is configured; ANY failure
    (no package, no network, bad URI) falls back to memory so the
    local demo and pytest suite always work.
    """
    global _MONGO_CLIENT, _MONGO_DB
    uri = (config.MONGO_URI or "").strip()
    if not uri:
        return _MEMORY_DB
    try:
        from pymongo import MongoClient
        if _MONGO_CLIENT is None:
            _MONGO_CLIENT = MongoClient(uri, serverSelectionTimeoutMS=3000)
            # Fail fast if the server is unreachable.
            _MONGO_CLIENT.admin.command("ping")
            _MONGO_DB = _MONGO_CLIENT[config.DB_NAME]
        return _MONGO_DB
    except Exception:
        return _MEMORY_DB


def buildings_col():
    return get_db()["buildings"]


def readings_col():
    return get_db()["readings"]


def issues_col():
    return get_db()["issues"]
