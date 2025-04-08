from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TeamCreate(BaseModel):
    name: str


class TeamResponse(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
