from fastapi import APIRouter, HTTPException, status
from ..database import missions_collection, trajectories_collection
from ..utils import *
from ..models import *

router = APIRouter(
    prefix="/missions",
    tags=["Missions"],
    responses={404: {"description": "Not found"}},
)


# Endpoint to get all missions
@router.get("/")
async def get_missions():
    """
    Get all the missions.
    Raises:
    - HTTPException 500: If there is an internal server error while fetching the missions.
    """
    cursor = missions_collection.find()
    if cursor:
        missions = extract_multiple_docs(cursor)
        return {"missions": missions}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Error: could not fetch data.",
        )


# Endpoint to create a new mission
@router.post("/")
async def create_mission(mission: Mission):
    """
    Create a new mission.

    This endpoint creates a new mission based on the provided mission data.

    Parameters:
    - mission (Mission): The data for the new mission. It should include the following fields:
        - id (int): The identifier for the mission.
        - trajectory_id (int): The ID of the trajectory associated with the mission.
        - duration (int): The duration of the mission in minutes.
        - priority (int): The priority of the mission, ranging from 1 to 10.

    Returns:
    - dict: A dictionary containing a message indicating the success of the operation and the ID of the newly created mission.

    Raises:
    - HTTPException 400: If the provided mission data contains invalid parameters.
    - HTTPException 500: If an error occurs while creating the mission.
    """
    missions_dict = mission.dict()
    if validate_duration(missions_dict["duration"]) and validate_priority(
        missions_dict["priority"]
    ):
        # TODO: check if trajectory exists in db
        result = missions_collection.insert_one(missions_dict)
        # Check if insertion was successful
        if result.inserted_id:
            return {"message": "Mission created successfully", "mission_id": mission.id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create mission",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad Parameter: durtion must be > 0 and priority must be between 1-10",
        )
