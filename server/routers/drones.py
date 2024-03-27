from fastapi import APIRouter, HTTPException, status
from ..database import drones_collection, missions_collection
from ..utils import *
from ..models import *

router = APIRouter(
    prefix="/drones",
    tags=["Drone"],
    responses={404: {"description": "Not found"}},
)


# Endpoint to get all drones
@router.get("/")
async def get_drones():
    """
    Get all the drones.
    Raises:
    - HTTPException 500: If there is an internal server error while fetching the drones.
    """
    cursor = drones_collection.find()
    if cursor:
        drones = extract_multiple_docs(cursor)
        return {"drones": drones}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Error: could not fetch data.",
        )


# Endpoint to get all drones by availability status
@router.get("/{drone_status}")
async def get_drones_by_status(drone_status: str):
    """
    Get drones by their status.

    This endpoint retrieves drones from the database based on their status.

    Parameters:
    - drone_status (str): The status of the drones to retrieve. Should be one of "available", "pending", or "on-mission".

    Returns:
    - dict: A dictionary containing a list of drones with the specified status.

    Raises:
    - HTTPException 400: If the provided status is not one of the accepted values.
    """
    if validate_status(drone_status):
        cursor = drones_collection.find({"status": drone_status})
        drones = extract_multiple_docs(cursor)
        return {"drones": drones}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad Request: status can only be one of the following- available, pending, on-mission",
        )


# Endpoint to get a specific drone by ID
@router.get("/{id}")
async def get_drone_by_id(id: int):
    """
    Get a drone by its ID.

    This endpoint retrieves information about a drone based on its ID.

    Parameters:
    - id (int): The ID of the drone to retrieve.

    Returns:
    - dict: A dictionary containing the details of the drone.

    Raises:
    - HTTPException 404: If the specified drone ID is not found in the database.
    """
    drone = drones_collection.find_one({"id": id})
    if drone is not None:
        return {"drone": extract_doc(drone)}

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Drone {id} not found"
        )


# Endpoint to update a drone's statusdrones_collection
@router.put("/{id}")
async def update_drone_status(id: int, status_request: DroneStatusRequest):
    """
    Update the status of a drone.

    This endpoint allows updating the status of a drone identified by its ID.

    Parameters:
    - id (int): The ID of the drone whose status is to be updated.
    - status_request (DroneStatusRequest): a string representing the updated status.

    Returns:
    - dict: A dictionary containing the updated drone document.

    Raises:
    - HTTPException 404: If the specified drone ID is not found in the database.
    - HTTPException 400: If the provided status is invalid.
    """
    update_data = status_request.dict()
    if validate_status(update_data["status"]):
        # Retrieve the drone document from the database
        drone = drones_collection.find_one({"id": id})

        # Check if the drone exists
        if drone:
            # Update the status of the drone
            drones_collection.update_one(
                {"id": id}, {"$set": {"status": update_data["status"]}}
            )

            # Return the updated drone
            updated_drone = drones_collection.find_one({"id": id})
            return {"updated_drone": extract_doc(updated_drone)}
        else:
            # If the drone does not exist, raise a 404 Not Found error
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drone with id {id} not found.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad Request: status can only be one of the following- available, pending, on-mission",
        )


# Endpoint to create a new drone
@router.post("/")
async def create_drone(drone: Drone):
    """
    Create a new drone.

    Parameters:
    - drone-
    - id (str): identifier for the drone.
    - name (str): The name of the drone.
    - status (str): The status of the drone (e.g., "available", "pending", "on-mission").
    - current_mission_id (str): The ID of the current mission the drone is assigned to.
    - possible_missions_ids (List[str]): A list of mission IDs .

    Returns:
    - dict: A dictionary containing a message indicating the success of the operation and the ID of the newly created drone.
    """
    if validate_status(drone.status):
        drone_dict = drone.dict()

        result = drones_collection.insert_one(drone_dict)
        # Check if insertion was successful
        if result.inserted_id:
            return {"message": "Drone created successfully", "drone_id": drone.id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create drone",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad Request: status can only be one of the following- available, pending, on-mission",
        )


# Endpoint to modify possible missions for a drone
@router.put("/{id}/possible_missions")
async def modify_possible_missions(
    id: int, possible_missions_ids: DronePossibleMissionRequest
):
    """
    Modify the possible missions for a drone.

    This endpoint allows updating the list of possible mission IDs for a specific drone.

    Parameters:
    - id (int): The ID of the drone whose possible missions are to be modified.
    - possible_missions_ids (DronePossibleMissionRequest): The updated list of possible mission IDs (ints) for the drone.

    Returns:
    - dict: A dictionary containing a message indicating the success of the operation.

    Raises:
    - HTTPException 400: If one of the specified mission ids is not found in the database.
    - HTTPException 404: If the specified drone ID is not found in the database.
    - HTTPException 500: If an error occurs while updating the possible missions for the drone.
    """
    # Find the drone document in the database by ID
    drone = drones_collection.find_one({"id": id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drone with id {id} not found",
        )

    # Check if all provided mission IDs exist in the database
    provided_mission_ids = possible_missions_ids.possible_missions_ids
    existing_missions = missions_collection.find({"id": {"$in": provided_mission_ids}})
    existing_mission_ids = [mission["id"] for mission in existing_missions]
    missing_missions = set(provided_mission_ids) - set(existing_mission_ids)

    if missing_missions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The following mission IDs do not exist: {missing_missions}",
        )
    update_data = possible_missions_ids.dict()
    # Update the possible missions IDs for the drone
    update_result = drones_collection.update_one(
        {"id": id},
        {"$set": {"possible_missions_ids": update_data["possible_missions_ids"]}},
    )

    if update_result.modified_count == 1:
        return {"message": "Possible missions updated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update possible missions for the drone",
        )
