from pydantic import BaseModel
from datetime import date
from uuid import UUID


class TrackingCreate(BaseModel):
    habit_id: UUID
    user_id: UUID
    date: date


class TrackingResponse(BaseModel):
    id: UUID
    habit_id: UUID
    user_id: UUID
    date: date

    class Config:
        orm_mode = True
