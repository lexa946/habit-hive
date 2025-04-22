from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TeamCreate(BaseModel):
    name: str
    description: str | None = None


class TeamResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    owner_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
