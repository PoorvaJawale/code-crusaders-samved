from pymongo import MongoClient, DESCENDING
import os

# -------------------
# MongoDB Config
# -------------------
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.environ.get("MONGO_DB", "trafficdb")       # default DB
VIOLATIONS_COLLECTION = "violations"
REPORTS_COLLECTION = "reports"
DENSITY_COLLECTION = "traffic_density"
PARKING_COLLECTION = "parking_status"

# -------------------
# MongoDB Client
# -------------------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
_db = client[MONGO_DB]

# Collections
violations_col = _db[VIOLATIONS_COLLECTION]
reports_col = _db[REPORTS_COLLECTION]
density_col = _db[DENSITY_COLLECTION]
parking_col = _db[PARKING_COLLECTION]

# Ensure indexes
try:
    violations_col.create_index([("violation_type", 1)])
    violations_col.create_index([("timestamp", -1)])
    reports_col.create_index([("date", -1)])
    density_col.create_index([("timestamp", -1)])
    parking_col.create_index([("timestamp", -1)])
    parking_col.create_index([("location", 1)])
except Exception as e:
    print("[DB WARN] Index creation failed:", e)


# -------------------
# Helper Functions
# -------------------
def init_db():
    """Return violations collection (for backward compatibility)."""
    return violations_col


# ------------------- Violations -------------------
def insert_violation(record: dict):
    """Insert a violation record."""
    try:
        violations_col.insert_one(dict(record))
    except Exception as e:
        print("[DB ERROR] insert_violation failed:", e)


def get_all_violations(filter_query: dict = None, limit: int = 25):
    """
    Fetch violations with optional filter.
    Always sorted by latest timestamp (newest first).
    """
    try:
        if filter_query:
            return list(
                violations_col.find(filter_query, {"_id": 0})
                .sort("timestamp", DESCENDING)
                .limit(limit)
            )
        return list(
            violations_col.find({}, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
    except Exception as e:
        print("[DB ERROR] get_all_violations failed:", e)
        return []


# ------------------- Audit Reports -------------------
def insert_report(report: dict):
    """Insert an audit report."""
    try:
        reports_col.insert_one(dict(report))
    except Exception as e:
        print("[DB ERROR] insert_report failed:", e)


def get_all_reports(limit: int = 25):
    """Fetch audit reports (latest first)."""
    try:
        return list(
            reports_col.find({}, {"_id": 0})
            .sort("date", DESCENDING)
            .limit(limit)
        )
    except Exception as e:
        print("[DB ERROR] get_all_reports failed:", e)
        return []


# ------------------- Traffic Density Tracking -------------------
def insert_density_record(record: dict):
    """Insert a traffic density record."""
    try:
        density_col.insert_one(dict(record))
    except Exception as e:
        print("[DB ERROR] insert_density_record failed:", e)


def get_density_history(limit: int = 50):
    """Fetch density history (latest first)."""
    try:
        return list(
            density_col.find({}, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
    except Exception as e:
        print("[DB ERROR] get_density_history failed:", e)
        return []


# ------------------- Parking Management -------------------
def insert_parking_status(record: dict):
    """Insert parking status record."""
    try:
        parking_col.insert_one(dict(record))
    except Exception as e:
        print("[DB ERROR] insert_parking_status failed:", e)


def get_latest_parking(location: str = None):
    """Get latest parking status for a location."""
    try:
        query = {"location": location} if location else {}
        return list(
            parking_col.find(query, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .limit(1)
        )
    except Exception as e:
        print("[DB ERROR] get_latest_parking failed:", e)
        return []


def get_parking_history(location: str = None, limit: int = 25):
    """Fetch parking history."""
    try:
        query = {"location": location} if location else {}
        return list(
            parking_col.find(query, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
    except Exception as e:
        print("[DB ERROR] get_parking_history failed:", e)
        return []
