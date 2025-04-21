from pydantic import BaseModel
from uuid import UUID

class HabitCreate(BaseModel):
    name: str
    description: str | None = None

class HabitResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    user_id: UUID

    class Config:
        from_attributes = True
