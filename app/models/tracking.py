import uuid
from datetime import date

from sqlalchemy import UUID, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Tracking(Base):
    __tablename__ = "tracking"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    habit_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("habits.id"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    date: Mapped[date]

    habit: Mapped["Habit"] = relationship(back_populates="trackings")
    user: Mapped["User"] = relationship(back_populates="trackings")

    __table_args__ = (
        UniqueConstraint("habit_id", "user_id", "date", name="uix_tracking_unique_per_day"),
    )
