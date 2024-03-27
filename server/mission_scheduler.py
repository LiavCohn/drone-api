from datetime import datetime
from .database import schedules_collection, drones_collection
from .notifications import send_notification


async def check_and_fire_missions():
    # Logic to query the database for scheduled missions
    # Check if a mission's start time has been reached
    # If so, mark the associated drone as "on-mission"
    # Send a desktop notification
    current_time = datetime.now()
    missions_to_fire = schedules_collection.find(
        {
            "start_time": {"$lte": current_time},
            "status": {"$in": ["pending", "scheduled"]},
        }
    )

    for mission in missions_to_fire:
        drone_id = mission["drone_id"]
        try:
            # TODO: mark the schedule is in-progress status
            mark_drone_as_on_mission(drone_id)
        except DroneNotFoundError as e:
            print(f"Drone not found: {str(e)}")
            continue
        except OverlappingError as e:
            # print("Drone already on a mission.")
            continue
        except UpdateFailedError as e:
            print(f"Failed to update drone status: {str(e)}")
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            continue

        send_notification(drone_id)


class DroneNotFoundError(Exception):
    pass


class UpdateFailedError(Exception):
    pass


class OverlappingError(Exception):
    pass


def mark_drone_as_on_mission(drone_id: int):
    try:
        drone = drones_collection.find_one(
            {"id": drone_id, "status": {"$ne": "on-mission"}}
        )
        if drone:
            result = drones_collection.update_one(
                {"id": drone_id}, {"$set": {"status": "on-mission"}}
            )
            if result.modified_count != 1:
                raise UpdateFailedError(
                    f"Failed to update drone status with id {drone_id}"
                )
        else:
            raise OverlappingError(f"Drone with id {drone_id} is already on a mission")
    except Exception as e:
        raise
