from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Define Pydantic models


class Mission(BaseModel):
    id: int
    trajectory_id: int
    duration: int
    priority: int


class Drone(BaseModel):
    id: int
    name: str
    status: str
    possible_missions_ids: List[int]
    current_mission_id: Optional[int] = None


class DronePossibleMissionRequest(BaseModel):
    possible_missions_ids: List[int]


class DroneStatusRequest(BaseModel):
    status: str


class Schedule(BaseModel):
    id: int
    drone_id: int
    mission_id: int
    start_time: datetime
    end_time: datetime
    status: str


class ScheduleStatusRequest(BaseModel):
    status: str
