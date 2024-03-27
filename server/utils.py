from datetime import datetime
from .database import schedules_collection


# validation functions
def validate_status(status: str):
    return status in ["available", "pending", "on-mission"]


def validate_schedule_status(status: str):
    return status in ["in-progress", "scheduled", "completed", "pending"]


def validate_priority(priority):
    return priority >= 1 and priority <= 10


def validate_duration(duration: int):
    return duration > 0


# helper function to extract all the data from a document, usually done with the pydantic. couldnt figure out
# why it doesnt work
def extract_multiple_docs(cursor):
    return [
        {**doc, "_id": str(doc["_id"])} for doc in cursor  # Convert ObjectId to string
    ]


def extract_doc(doc):
    return {**doc, "_id": str(doc["_id"])}


# Helper function to check if a drone is available for a new mission in a certain time range
def is_drone_available(drone_id: int, start_time: datetime, end_time: datetime):
    existing_schedules = schedules_collection.count_documents(
        {
            "drone_id": drone_id,
            "start_time": {"$lt": end_time},
            "end_time": {"$gt": start_time},
        }
    )

    return existing_schedules == 0
