from fastapi import APIRouter, HTTPException, status
from ..database import missions_collection, drones_collection
from ..utils import *
from ..models import *

router = APIRouter(
    prefix="/schedules",
    tags=["Schedules"],
    responses={404: {"description": "Not found"}},
)


# Endpoint to get all schedules
@router.get("/")
async def get_schedules():
    """
    Get all the schedules.
    Raises:
    - HTTPException 500: If there is an internal server error while fetching the schedules.

    """
    cursor = schedules_collection.find()
    if cursor:
        schedules = extract_multiple_docs(cursor)
        return {"schedules": schedules}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Error: could not fetch data.",
        )


# Endpoint to create a new schedule
@router.post("/")
async def create_schedule(schedule: Schedule):
    """
    Create a new schedule.

    This endpoint allows the creation of a new schedule for a drone to perform a mission.
    It checks if the specified drone is available for the specified time range before creating the schedule.

    Parameters:
    - schedule (Schedule): The schedule object containing details of the mission schedule.
        - drone_id (int): The ID of the drone for which the schedule is being created.
        - mission_id (int): The ID of the mission the drone is scheduled to perform.
        - start_time (datetime): The start time of the scheduled mission.
        - end_time (datetime): The end time of the scheduled mission.
        - status (str): The status of the scheduled mission (e.g., "available", "pending", "on-mission").

    Returns:
    - dict: A dictionary containing a message indicating the success of the operation and the ID of the newly created schedule.

    Raises:
    - HTTPException 409: If the specified drone is not available for the specified time range.
    - HTTPException 500: If there is an internal server error while creating the schedule.
    - HTTPException 400: If the provided status is invalid.
    - HTTPException 404: If the provided drone if or mission id is not found.
    """

    # Check if the drone is available for the specified time range
    if not is_drone_available(
        schedule.drone_id, schedule.start_time, schedule.end_time
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The drone is not available for the specified time range.",
        )

        # Check if the mission_id exists in the missions collection
    mission = missions_collection.find_one({"id": schedule.mission_id})
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {schedule.mission_id} does not exist.",
        )

    # Check if the drone_id exists in the drones collection
    drone = drones_collection.find_one({"id": schedule.drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drone with ID {schedule.drone_id} does not exist.",
        )
    if validate_schedule_status(schedule.status):
        schedule_dict = schedule.dict()

        result = schedules_collection.insert_one(schedule_dict)
        # Check if insertion was successful
        if result.inserted_id:
            return {
                "message": "Schedule created successfully",
                "schedule_id": schedule.id,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create schedule",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad Request: status can only be one of the following- available, pending, on-mission",
        )


# Endpoint to update a schedule's status
@router.put("/{id}")
async def update_schedule_status(id: int, status_request: ScheduleStatusRequest):
    """
    Update the status of a schedule.

    This endpoint updates the status of a schedule identified by its ID.

    Parameters:
    - id (int): The ID of the schedule to update.
    - status_request (ScheduleStatusRequest): The request containing the new status.

    Returns:
    - dict: A dictionary containing the updated schedule.

    Raises:
    - HTTPException 404: If the schedule with the specified ID is not found.
    - HTTPException 400: If the provided status is invalid.
    """

    update_data = status_request.dict()

    if validate_schedule_status(update_data["status"]):
        schedule = schedules_collection.find_one({"id": id})
        # Check if the schedule exists
        if schedule:
            # Update the status of the schedule
            schedules_collection.update_one(
                {"id": id}, {"$set": {"status": update_data["status"]}}
            )

            # Return the updated schedule
            updated_schedule = schedules_collection.find_one({"id": id})
            return {"updated schedule": extract_doc(updated_schedule)}
        else:
            # If the schedule does not exist, raise a 404 Not Found error
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule with id {id} not found.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad Request: status can only be one of the following- in-progress, scheduled, completed or pending",
        )


# Endpoint to get schedules date range
@router.get("/{start_date}/{end_date}")
async def get_schedules_date_range(start_date: datetime, end_date: datetime):
    """
    Get schedules within a specified date range.

    This endpoint retrieves schedules from the database that fall within the specified date range.

    Parameters:
    - start_date (datetime): The start date of the range.
    - end_date (datetime): The end date of the range.

    Returns:
    - dict: A dictionary containing a list of schedules within the specified date range.

    Raises:
    - HTTPException 500: If an internal server error occurs or if no schedules are found.
    """
    # Query the database to find schedules within the specified date range
    schedules = schedules_collection.find(
        {"start_time": {"$gte": start_date}, "end_time": {"$lte": end_date}}
    )
    if not schedules:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error: Failed to fatch schedules",
        )

    result = extract_multiple_docs(schedules)

    return {"schedules": result}


# Endpoint to get schedules by drone
@router.get("/{drone_id}")
async def get_schedules_by_drone(drone_id: int):
    """
    Get schedules associated with a specific drone.

    This endpoint retrieves schedules associated with the specified drone ID from the database.

    Parameters:
    - drone_id (int): The ID of the drone for which schedules are being retrieved.

    Returns:
    - dict: A dictionary containing a list of schedules associated with the specified drone.

    Raises:
    - HTTPException 404: If no schedules are found for the specified drone ID.
    """
    # Query the database to find schedules associated with the specified drone_id
    schedules = schedules_collection.find({"drone_id": drone_id})
    if not schedules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedules for drone {drone_id} not found.",
        )

    result = extract_multiple_docs(schedules)

    return {"schedules": result}
