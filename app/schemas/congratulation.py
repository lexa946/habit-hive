from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CongratulationBase(BaseModel):
    message: str
    type: str


class CongratulationCreate(CongratulationBase):
    pass


class Congratulation(CongratulationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True 